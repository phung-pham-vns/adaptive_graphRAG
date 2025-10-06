"""Faithfulness evaluator implementation."""

from typing import Dict, Any, Optional, List

from src.evaluation.evaluators.base import LLMBasedEvaluator, EvaluatorResult
from src.evaluation.config import EVAL_SYSTEM_PROMPT


class FaithfulnessEvaluator(LLMBasedEvaluator):
    """
    Evaluates if the answer is faithful to the reference and citations.
    
    Checks for hallucinations and whether the answer is grounded in
    the provided context.
    """

    def __init__(self, llm_client):
        """
        Initialize the faithfulness evaluator.
        
        Args:
            llm_client: EvaluationLLMClient instance
        """
        super().__init__("faithfulness", llm_client)

    def _format_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Format citations for display."""
        if not citations:
            return "No citations provided"
        return "\n".join(
            [
                f"- {c.get('title', 'Unknown')} ({c.get('url', 'No URL')})"
                for c in citations
            ]
        )

    def evaluate(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        reference_outputs: Optional[Dict[str, Any]] = None,
    ) -> EvaluatorResult:
        """
        Evaluate faithfulness of the answer.
        
        Args:
            inputs: Input data (unused for this evaluator)
            outputs: Model outputs containing 'response' and 'citations'
            reference_outputs: Ground truth containing 'answer' and 'citation'
            
        Returns:
            EvaluatorResult with binary score (0 or 1)
        """
        if reference_outputs is None:
            return EvaluatorResult(
                key=self.metric_name,
                score=0.0,
                comment="No reference outputs provided",
            )

        predicted_answer = outputs.get("response", "")
        predicted_citations = outputs.get("citations", [])
        reference_answer = reference_outputs.get("answer", "")
        reference_citations = reference_outputs.get("citation", [])

        user_prompt = f"""Evaluate if the predicted answer is faithful to the reference information and citations provided.

Reference Answer:
{reference_answer}

Reference Citations:
{self._format_citations(reference_citations)}

Predicted Answer:
{predicted_answer}

Predicted Citations:
{self._format_citations(predicted_citations)}

Consider:
1. Does the answer contain information not supported by the reference or citations?
2. Are there any fabricated facts or hallucinations?
3. Is the answer grounded in the provided context?

Respond in the following format:
Grade: [FAITHFUL or NOT_FAITHFUL]
Reasoning: [Brief explanation]"""

        try:
            response = self.llm_client.evaluate_with_prompt(
                system_prompt=EVAL_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            is_faithful = self.parse_grade_response(response, "FAITHFUL")
            is_not_faithful = "NOT_FAITHFUL" in response.split("\n")[0].upper()

            # Handle edge case where both might appear
            score = 1.0 if is_faithful and not is_not_faithful else 0.0

            return EvaluatorResult(
                key=self.metric_name,
                score=score,
                comment=response,
                metadata={
                    "num_predicted_citations": len(predicted_citations),
                    "num_reference_citations": len(reference_citations),
                },
            )
        except Exception as e:
            return EvaluatorResult(
                key=self.metric_name,
                score=0.0,
                comment=f"Evaluation error: {str(e)}",
            )
