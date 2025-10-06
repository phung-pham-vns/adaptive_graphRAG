"""Concision evaluator implementation."""

from typing import Dict, Any, Optional

from src.evaluation.evaluators.base import BaseEvaluator, EvaluatorResult


class ConcisionEvaluator(BaseEvaluator):
    """
    Evaluates if the answer is concise (not excessively longer than reference).
    
    This is a simple rule-based evaluator that compares answer lengths.
    """

    def __init__(self, max_ratio: float = 4.0):
        """
        Initialize the concision evaluator.
        
        Args:
            max_ratio: Maximum acceptable ratio of response length to reference length
        """
        super().__init__("concision")
        self.max_ratio = max_ratio

    def evaluate(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        reference_outputs: Optional[Dict[str, Any]] = None,
    ) -> EvaluatorResult:
        """
        Evaluate concision of the answer.
        
        Args:
            inputs: Input data (unused for this evaluator)
            outputs: Model outputs containing 'response'
            reference_outputs: Ground truth containing 'answer'
            
        Returns:
            EvaluatorResult with binary score (0 or 1)
        """
        if reference_outputs is None:
            return EvaluatorResult(
                key=self.metric_name,
                score=1.0,
                comment="No reference answer provided",
            )

        response_len = len(outputs.get("response", ""))
        reference_len = len(reference_outputs.get("answer", ""))

        if reference_len == 0:
            return EvaluatorResult(
                key=self.metric_name,
                score=1.0,
                comment="Reference answer is empty",
            )

        ratio = response_len / reference_len
        score = 1.0 if ratio <= self.max_ratio else 0.0

        comment = (
            f"Length ratio: {ratio:.2f} "
            f"(response: {response_len} chars, reference: {reference_len} chars)"
        )

        if score == 0.0:
            comment += f" - Exceeds max ratio of {self.max_ratio}"

        return EvaluatorResult(
            key=self.metric_name,
            score=score,
            comment=comment,
            metadata={
                "response_length": response_len,
                "reference_length": reference_len,
                "ratio": ratio,
                "max_ratio": self.max_ratio,
            },
        )
