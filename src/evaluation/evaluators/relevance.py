"""Relevance evaluator implementation."""

from typing import Dict, Any, Optional

from src.evaluation.evaluators.base import LLMBasedEvaluator, EvaluatorResult
from src.evaluation.config import EVAL_SYSTEM_PROMPT


class RelevanceEvaluator(LLMBasedEvaluator):
    """
    Evaluates if the answer is relevant to the question asked.
    
    Uses an LLM to assess whether the response addresses the question.
    """

    def __init__(self, llm_client):
        """
        Initialize the relevance evaluator.
        
        Args:
            llm_client: EvaluationLLMClient instance
        """
        super().__init__("relevance", llm_client)

    def evaluate(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        reference_outputs: Optional[Dict[str, Any]] = None,
    ) -> EvaluatorResult:
        """
        Evaluate relevance of the answer to the question.
        
        Args:
            inputs: Input data containing 'question'
            outputs: Model outputs containing 'response'
            reference_outputs: Ground truth (unused for this evaluator)
            
        Returns:
            EvaluatorResult with binary score (0 or 1)
        """
        question = inputs.get("question", "")
        answer = outputs.get("response", "")

        user_prompt = f"""Evaluate if the following answer is relevant to the question asked.

Question: {question}

Answer: {answer}

Consider:
1. Does the answer directly address the question?
2. Is the information provided relevant to durian pest/disease management?
3. Does it answer the specific aspects asked (symptoms, treatments, timing, etc.)?

Respond in the following format:
Grade: [RELEVANT or NOT_RELEVANT]
Reasoning: [Brief explanation]"""

        try:
            response = self.llm_client.evaluate_with_prompt(
                system_prompt=EVAL_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            is_relevant = self.parse_grade_response(response, "RELEVANT")
            is_not_relevant = "NOT_RELEVANT" in response.split("\n")[0].upper()

            # Handle edge case where both might appear
            score = 1.0 if is_relevant and not is_not_relevant else 0.0

            return EvaluatorResult(
                key=self.metric_name,
                score=score,
                comment=response,
                metadata={
                    "question": question,
                    "answer_length": len(answer),
                },
            )
        except Exception as e:
            return EvaluatorResult(
                key=self.metric_name,
                score=0.0,
                comment=f"Evaluation error: {str(e)}",
            )
