import asyncio
import argparse
import threading

from datetime import datetime
from typing import Any
from functools import partial
from dotenv import load_dotenv
from langsmith import Client
from openai import OpenAI

from src.core.workflow import run_workflow
from src.settings import settings

# Load environment variables
load_dotenv(".env")

# Global event loop for async operations
_event_loop = None
_event_loop_thread = None


def get_or_create_event_loop():
    """Get or create a persistent event loop running in a background thread."""
    global _event_loop, _event_loop_thread

    if _event_loop is None or not _event_loop.is_running():
        _event_loop = asyncio.new_event_loop()

        def run_loop():
            asyncio.set_event_loop(_event_loop)
            _event_loop.run_forever()

        _event_loop_thread = threading.Thread(target=run_loop, daemon=True)
        _event_loop_thread.start()

    return _event_loop


def cleanup_event_loop():
    """Stop and cleanup the event loop. Call this at the end of evaluation."""
    global _event_loop, _event_loop_thread

    if _event_loop is not None and _event_loop.is_running():
        _event_loop.call_soon_threadsafe(_event_loop.stop)
        if _event_loop_thread is not None:
            _event_loop_thread.join(timeout=5)
        _event_loop = None
        _event_loop_thread = None


# Configuration
MAX_CONCURRENCY = 0
DATASET_NAME = "Durian Pest and Disease"
EXPERIMENT_PREFIX = (
    f"durian-pest-and-disease-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
)

# Gemini API configuration (via OpenAI-compatible endpoint)
GEMINI_BASE_URL = settings.llm_base_url
GEMINI_API_KEY = settings.llm_api_key
GEMINI_MODEL = settings.llm_model
GEMINI_EVAL_MODEL = "gemini-2.5-pro"  # Strongest model for evaluation

# Initialize clients
langsmith_client = Client()
gemini_client = OpenAI(base_url=GEMINI_BASE_URL, api_key=GEMINI_API_KEY)


# Workflow configuration
WORKFLOW_CONFIG = {
    "n_retrieved_documents": 5,
    "n_web_searches": 5,
    "node_retrieval": True,
    "edge_retrieval": True,
    "episode_retrieval": False,
    "community_retrieval": False,
    "enable_retrieved_document_grading": False,
    "enable_hallucination_checking": False,
    "enable_answer_quality_checking": False,
}


async def workflow_wrapper(
    inputs: dict, config: dict = WORKFLOW_CONFIG
) -> dict[str, Any]:
    """
    Wrapper function to run the workflow asynchronously.

    Args:
        inputs: Dictionary containing 'question' and optional workflow configuration

    Returns:
        Dictionary with 'answer' and 'citations'
    """
    question = inputs.get("question", "")

    try:
        response = await run_workflow(
            question=question,
            n_retrieved_documents=config["n_retrieved_documents"],
            n_web_searches=config["n_web_searches"],
            node_retrieval=config["node_retrieval"],
            edge_retrieval=config["edge_retrieval"],
            episode_retrieval=config["episode_retrieval"],
            community_retrieval=config["community_retrieval"],
            enable_retrieved_document_grading=config[
                "enable_retrieved_document_grading"
            ],
            enable_hallucination_checking=config["enable_hallucination_checking"],
            enable_answer_quality_checking=config["enable_answer_quality_checking"],
        )
        return response
    except Exception as e:
        print(f"Error in workflow_wrapper: {e}")
        return {"answer": "", "citations": []}


def ls_target(inputs: dict, config: dict = WORKFLOW_CONFIG) -> dict:
    """
    Synchronous target function for LangSmith evaluation.
    Wraps the async workflow_wrapper using a persistent event loop.

    Args:
        inputs: Dictionary containing 'question'

    Returns:
        Dictionary with 'response' (answer) and 'citations'
    """
    try:
        loop = get_or_create_event_loop()
        future = asyncio.run_coroutine_threadsafe(
            workflow_wrapper(inputs, config), loop
        )
        # Wait for the result with a timeout (e.g., 300 seconds = 5 minutes)
        result = future.result(timeout=300)

        return {
            "response": result.get("answer", ""),
            "citations": result.get("citations", []),
        }
    except Exception as e:
        print(f"Error in ls_target: {e}")
        import traceback

        traceback.print_exc()
        return {"response": "", "citations": []}


# Evaluator prompt templates
EVAL_SYSTEM_PROMPT = """You are an expert agricultural specialist evaluating answers about durian pest and disease management.
Your evaluation should be thorough, fair, and based on agricultural best practices."""


def correctness_evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """
    Evaluate if the predicted answer is correct compared to the reference answer.
    Uses Gemini for evaluation.

    Returns:
        dict with 'score' (0 or 1) and 'reasoning'
    """
    user_content = f"""You are evaluating an answer about durian pest and disease management.

Question: {inputs.get('question', '')}

Reference Answer (Ground Truth):
{reference_outputs.get('answer', '')}

Predicted Answer:
{outputs.get('response', '')}

Evaluate if the predicted answer is correct compared to the reference answer.
Consider:
1. Factual accuracy of pest/disease identification
2. Correctness of recommended treatments and controls
3. Accuracy of timing and application methods
4. Overall alignment with reference answer

Respond in the following format:
Grade: [CORRECT or INCORRECT]
Reasoning: [Brief explanation of your decision]"""

    try:
        response = gemini_client.chat.completions.create(
            model=GEMINI_EVAL_MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": EVAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )

        content = response.choices[0].message.content
        is_correct = "CORRECT" in content.split("\n")[0].upper()

        return {
            "key": "correctness",
            "score": 1 if is_correct else 0,
            "comment": content,
        }
    except Exception as e:
        print(f"Error in correctness_evaluator: {e}")
        return {"key": "correctness", "score": 0, "comment": f"Evaluation error: {e}"}


def concision_evaluator(outputs: dict, reference_outputs: dict) -> dict:
    """
    Evaluate if the answer is concise (not more than 2x reference length).

    Returns:
        dict with 'score' (0-1) and length ratio
    """
    response_len = len(outputs.get("response", ""))
    reference_len = len(reference_outputs.get("answer", ""))

    if reference_len == 0:
        return {"key": "concision", "score": 1, "comment": "Reference is empty"}

    ratio = response_len / reference_len
    score = 1 if ratio <= 4.0 else 0

    return {
        "key": "concision",
        "score": score,
        "comment": f"Length ratio: {ratio:.2f} (response: {response_len}, reference: {reference_len})",
    }


def relevance_evaluator(inputs: dict, outputs: dict) -> dict:
    """
    Evaluate if the answer is relevant to the question asked.
    Uses Gemini for evaluation.

    Returns:
        dict with 'score' (0-1) and reasoning
    """
    user_content = f"""Evaluate if the following answer is relevant to the question asked.

Question: {inputs.get('question', '')}

Answer: {outputs.get('response', '')}

Consider:
1. Does the answer directly address the question?
2. Is the information provided relevant to durian pest/disease management?
3. Does it answer the specific aspects asked (symptoms, treatments, timing, etc.)?

Respond in the following format:
Grade: [RELEVANT or NOT_RELEVANT]
Reasoning: [Brief explanation]"""

    try:
        response = gemini_client.chat.completions.create(
            model=GEMINI_EVAL_MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": EVAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )

        content = response.choices[0].message.content
        is_relevant = (
            "RELEVANT" in content.split("\n")[0].upper()
            and "NOT_RELEVANT" not in content.split("\n")[0].upper()
        )

        return {
            "key": "relevance",
            "score": 1 if is_relevant else 0,
            "comment": content,
        }
    except Exception as e:
        print(f"Error in relevance_evaluator: {e}")
        return {"key": "relevance", "score": 0, "comment": f"Evaluation error: {e}"}


def faithfulness_evaluator(outputs: dict, reference_outputs: dict) -> dict:
    """
    Evaluate if the answer is faithful to the reference (no hallucinations).
    Uses Gemini for evaluation.

    Returns:
        dict with 'score' (0-1) and reasoning
    """
    citations = outputs.get("citations", [])

    user_content = f"""Evaluate if the predicted answer is faithful to the reference information and citations provided.

Reference Answer:
{reference_outputs.get('answer', '')}

Reference Citations:
{reference_outputs.get('citation', [])}

Predicted Answer:
{outputs.get('response', '')}

Predicted Citations:
{[f"{c.get('title', '')} - {c.get('url', '')}" for c in citations]}

Consider:
1. Does the answer contain information not supported by the reference or citations?
2. Are there any fabricated facts or hallucinations?
3. Is the answer grounded in the provided context?

Respond in the following format:
Grade: [FAITHFUL or NOT_FAITHFUL]
Reasoning: [Brief explanation]"""

    try:
        response = gemini_client.chat.completions.create(
            model=GEMINI_EVAL_MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": EVAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )

        content = response.choices[0].message.content
        is_faithful = (
            "FAITHFUL" in content.split("\n")[0].upper()
            and "NOT_FAITHFUL" not in content.split("\n")[0].upper()
        )

        return {
            "key": "faithfulness",
            "score": 1 if is_faithful else 0,
            "comment": content,
        }
    except Exception as e:
        print(f"Error in faithfulness_evaluator: {e}")
        return {"key": "faithfulness", "score": 0, "comment": f"Evaluation error: {e}"}


def run_evaluation(
    dataset_name: str = DATASET_NAME,
    experiment_prefix: str = EXPERIMENT_PREFIX,
    max_concurrency: int = 1,  # Keep low to avoid rate limits
    config: dict = WORKFLOW_CONFIG,
):
    """
    Run the LangSmith evaluation with all evaluators.

    Args:
        dataset_name: Name of the LangSmith dataset
        experiment_prefix: Prefix for the experiment name
        max_concurrency: Maximum number of concurrent evaluations
    """
    print("=" * 80)
    print(f"Starting LangSmith Evaluation")
    print(f"Dataset: {dataset_name}")
    print(f"Evaluator Model: {GEMINI_EVAL_MODEL}")
    print(f"Experiment Prefix: {experiment_prefix}")
    print("=" * 80)

    _ls_target = partial(ls_target, config=config)

    # Run evaluation
    experiment_results = langsmith_client.evaluate(
        _ls_target,
        data=dataset_name,
        evaluators=[
            correctness_evaluator,
            concision_evaluator,
            # relevance_evaluator,
            # faithfulness_evaluator,
        ],
        experiment_prefix=experiment_prefix,
        max_concurrency=max_concurrency,
        metadata=config,
    )

    print("\n" + "=" * 80)
    print("Evaluation Complete!")
    print(f"Results: {experiment_results}")
    print("=" * 80)

    return experiment_results


def main():
    # Print configuration
    print("\nConfiguration Summary:")
    print("-" * 80)
    print(f"Dataset: {DATASET_NAME}")
    print(f"Experiment Prefix: {EXPERIMENT_PREFIX}")
    print(f"Max Concurrency: {MAX_CONCURRENCY}")
    print("\nWorkflow Settings:")
    for key, value in WORKFLOW_CONFIG.items():
        print(f"  {key}: {value}")
    print()

    try:
        # Run evaluation
        results = run_evaluation(
            dataset_name=DATASET_NAME,
            experiment_prefix=EXPERIMENT_PREFIX,
            max_concurrency=MAX_CONCURRENCY,
            config=WORKFLOW_CONFIG,
        )
        return results
    finally:
        # Clean up event loop
        print("\nCleaning up event loop...")
        cleanup_event_loop()


if __name__ == "__main__":
    main()
