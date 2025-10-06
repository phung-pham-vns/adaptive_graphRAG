import argparse
from typing import Any, Dict, List

from dotenv import load_dotenv
from langsmith import Client

from src.core.workflow import run_workflow
from src.evaluation.config import (
    EvaluationConfig,
    EvaluationPreset,
    WorkflowConfig,
)

from src.evaluation.async_utils import (
    get_global_loop_manager,
    cleanup_global_loop_manager,
)
from src.evaluation.llm_client import create_llm_client
from src.evaluation.evaluators import (
    CorrectnessEvaluator,
    ConcisionEvaluator,
    RelevanceEvaluator,
    FaithfulnessEvaluator,
)

# Load environment variables
load_dotenv(".env")


class RAGEvaluationPipeline:
    def __init__(self, config: EvaluationConfig):
        """
        Initialize the evaluation pipeline.

        Args:
            config: Evaluation configuration
        """
        self.config = config
        self.langsmith_client = Client()
        self.llm_client = create_llm_client(config.llm)
        self.loop_manager = get_global_loop_manager()

    async def workflow_wrapper(
        self, inputs: dict, workflow_config: WorkflowConfig
    ) -> Dict[str, Any]:
        """
        Wrapper function to run the workflow asynchronously.

        Args:
            inputs: Dictionary containing 'question' and optional workflow configuration
            workflow_config: Workflow configuration to use

        Returns:
            Dictionary with 'answer' and 'citations'
        """
        question = inputs.get("question", "")

        try:
            response = await run_workflow(
                question=question,
                n_retrieved_documents=workflow_config.n_retrieved_documents,
                n_web_searches=workflow_config.n_web_searches,
                node_retrieval=workflow_config.node_retrieval,
                edge_retrieval=workflow_config.edge_retrieval,
                episode_retrieval=workflow_config.episode_retrieval,
                community_retrieval=workflow_config.community_retrieval,
                enable_retrieved_document_grading=workflow_config.enable_retrieved_document_grading,
                enable_hallucination_checking=workflow_config.enable_hallucination_checking,
                enable_answer_quality_checking=workflow_config.enable_answer_quality_checking,
            )
            return response
        except Exception as e:
            print(f"Error in workflow_wrapper: {e}")
            return {"answer": "", "citations": []}

    def ls_target(self, inputs: dict) -> dict:
        """
        Synchronous target function for LangSmith evaluation.

        Wraps the async workflow_wrapper using a persistent event loop.

        Args:
            inputs: Dictionary containing 'question'

        Returns:
            Dictionary with 'response' (answer) and 'citations'
        """
        try:
            result = self.loop_manager.run_coroutine(
                self.workflow_wrapper(inputs, self.config.workflow),
                timeout=self.config.llm.timeout,
            )

            return {
                "response": result.get("answer", ""),
                "citations": result.get("citations", []),
            }
        except Exception as e:
            print(f"Error in ls_target: {e}")
            import traceback

            traceback.print_exc()
            return {"response": "", "citations": []}

    def get_evaluators(self) -> List:
        """
        Get the list of enabled evaluators.

        Returns:
            List of evaluator functions
        """
        evaluators = []

        if self.config.enable_correctness:
            evaluators.append(CorrectnessEvaluator(self.llm_client))

        if self.config.enable_concision:
            evaluators.append(ConcisionEvaluator())

        # if self.config.enable_relevance:
        #     evaluators.append(RelevanceEvaluator(self.llm_client))

        # if self.config.enable_faithfulness:
        #     evaluators.append(FaithfulnessEvaluator(self.llm_client))

        return evaluators

    def run_evaluation(self):
        """
        Run the LangSmith evaluation with all enabled evaluators.

        Returns:
            Experiment results from LangSmith
        """
        print("=" * 80)
        print("Starting LangSmith Evaluation")
        print("=" * 80)
        print(f"Dataset: {self.config.dataset_name}")
        print(f"Experiment Prefix: {self.config.experiment_prefix}")
        print(f"Max Concurrency: {self.config.max_concurrency}")
        print(f"Evaluator Model: {self.config.llm.eval_model}")
        print("\nWorkflow Configuration:")
        for key, value in self.config.workflow.to_dict().items():
            print(f"  {key}: {value}")
        print("\nEnabled Evaluators:")
        for evaluator in self.get_evaluators():
            print(f"  - {evaluator.metric_name}")
        print("=" * 80)
        print()

        # Run evaluation
        experiment_results = self.langsmith_client.evaluate(
            self.ls_target,
            data=self.config.dataset_name,
            evaluators=self.get_evaluators(),
            experiment_prefix=self.config.experiment_prefix,
            max_concurrency=self.config.max_concurrency,
            metadata=self.config.to_dict(),
        )

        print("\n" + "=" * 80)
        print("Evaluation Complete!")
        print(f"Results: {experiment_results}")
        print("=" * 80)

        return experiment_results

    def cleanup(self):
        """Cleanup resources."""
        cleanup_global_loop_manager()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Evaluate RAG system using LangSmith")

    # Preset selection
    parser.add_argument(
        "--preset",
        type=str,
        choices=[p.value for p in EvaluationPreset],
        default=EvaluationPreset.BALANCED.value,
        help="Use a predefined evaluation preset",
    )

    # Dataset arguments
    parser.add_argument(
        "--dataset-name",
        type=str,
        default="Durian Pest and Disease",
        help="Name of the LangSmith dataset to evaluate",
    )

    parser.add_argument(
        "--experiment-prefix",
        type=str,
        help="Custom experiment prefix (default: auto-generated)",
    )

    # Concurrency
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=1,
        help="Maximum number of concurrent evaluations",
    )

    # Evaluator toggles
    parser.add_argument(
        "--disable-correctness",
        action="store_true",
        help="Disable correctness evaluator",
    )

    parser.add_argument(
        "--disable-concision",
        action="store_true",
        help="Disable concision evaluator",
    )

    parser.add_argument(
        "--enable-relevance",
        action="store_true",
        help="Enable relevance evaluator",
    )

    parser.add_argument(
        "--enable-faithfulness",
        action="store_true",
        help="Enable faithfulness evaluator",
    )

    # Workflow overrides
    parser.add_argument(
        "--n-retrieved-documents",
        type=int,
        help="Override number of retrieved documents",
    )

    parser.add_argument(
        "--n-web-searches",
        type=int,
        help="Override number of web searches",
    )

    return parser.parse_args()


def main():
    """Main entry point for evaluation."""
    args = parse_arguments()

    # Create base config from preset
    preset = EvaluationPreset(args.preset)
    config = EvaluationConfig.from_preset(preset)

    # Apply overrides
    config.dataset_name = args.dataset_name
    if args.experiment_prefix:
        config.experiment_prefix = args.experiment_prefix
    config.max_concurrency = args.max_concurrency

    # Apply evaluator toggles
    config.enable_correctness = not args.disable_correctness
    config.enable_concision = not args.disable_concision
    config.enable_relevance = args.enable_relevance
    config.enable_faithfulness = args.enable_faithfulness

    # Apply workflow overrides
    if args.n_retrieved_documents is not None:
        config.workflow.n_retrieved_documents = args.n_retrieved_documents
    if args.n_web_searches is not None:
        config.workflow.n_web_searches = args.n_web_searches

    # Print configuration summary
    print("\nConfiguration Summary:")
    print("-" * 80)
    print(f"Preset: {preset.value}")
    print(f"Dataset: {config.dataset_name}")
    print(f"Experiment Prefix: {config.experiment_prefix}")
    print(f"Max Concurrency: {config.max_concurrency}")
    print()

    # Run evaluation
    pipeline = RAGEvaluationPipeline(config)
    try:
        results = pipeline.run_evaluation()
        return results
    finally:
        print("\nCleaning up...")
        pipeline.cleanup()


if __name__ == "__main__":
    main()
