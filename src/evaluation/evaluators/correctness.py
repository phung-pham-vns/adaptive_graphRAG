from typing import Dict, Any, Optional

from src.evaluation.evaluators.base import LLMBasedEvaluator, EvaluatorResult
from src.evaluation.config import EVAL_SYSTEM_PROMPT


class CorrectnessEvaluator(LLMBasedEvaluator):
    def __init__(self, llm_client):
        """
        Initialize the correctness evaluator.

        Args:
            llm_client: EvaluationLLMClient instance
        """
        super().__init__("correctness", llm_client)

    def evaluate(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        reference_outputs: Optional[Dict[str, Any]] = None,
    ) -> EvaluatorResult:
        """Evaluate correctness of the answer.
        Args:
            inputs: Input data containing 'question'
            outputs: Model outputs containing 'response'
            reference_outputs: Ground truth containing 'answer'

        Returns:
            EvaluatorResult with binary score (0 or 1)
        """
        if reference_outputs is None:
            return EvaluatorResult(
                key=self.metric_name,
                score=0.0,
                comment="No reference answer provided",
            )

        question = inputs.get("question", "")
        predicted_answer = outputs.get("response", "")
        reference_answer = reference_outputs.get("answer", "")

        user_prompt = f"""Agriculture Question:
{question}

Reference Answer (ground truth):
{reference_answer}

Predicted Answer (prediction):
{predicted_answer}

Is the student's answer correct?
Respond with exactly one word: CORRECT or INCORRECT."""

        try:
            response = self.llm_client.evaluate_with_prompt(
                system_prompt=EVAL_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            is_correct = self.parse_grade_response(response, "CORRECT")
            is_incorrect = "INCORRECT" in response

            score = 0.0 if is_incorrect else 1.0

            return EvaluatorResult(
                key=self.metric_name,
                score=score,
                comment=response,
                metadata={
                    "question": question,
                    "predicted_answer_length": len(predicted_answer),
                    "reference_answer_length": len(reference_answer),
                },
            )
        except Exception as e:
            return EvaluatorResult(
                key=self.metric_name,
                score=0.0,
                comment=f"Evaluation error: {str(e)}",
            )
