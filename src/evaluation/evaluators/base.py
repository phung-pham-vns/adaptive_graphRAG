"""Base classes for evaluators."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class EvaluatorResult:
    """
    Result of an evaluation.
    
    Attributes:
        key: Metric name/key
        score: Numeric score (typically 0-1)
        comment: Human-readable explanation of the score
        metadata: Additional metadata about the evaluation
    """

    key: str
    score: float
    comment: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format expected by LangSmith."""
        result = {
            "key": self.key,
            "score": self.score,
            "comment": self.comment,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class BaseEvaluator(ABC):
    """
    Abstract base class for all evaluators.
    
    All evaluators should inherit from this class and implement
    the evaluate method.
    """

    def __init__(self, metric_name: str):
        """
        Initialize the evaluator.
        
        Args:
            metric_name: Name of the metric this evaluator computes
        """
        self.metric_name = metric_name

    @abstractmethod
    def evaluate(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        reference_outputs: Optional[Dict[str, Any]] = None,
    ) -> EvaluatorResult:
        """
        Evaluate the outputs against inputs and optional reference outputs.
        
        Args:
            inputs: Input data (e.g., {"question": "..."})
            outputs: Model outputs (e.g., {"response": "...", "citations": [...]})
            reference_outputs: Ground truth outputs (e.g., {"answer": "...", "citation": [...]})
            
        Returns:
            EvaluatorResult with score and explanation
        """
        pass

    def __call__(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        reference_outputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make the evaluator callable as a function.
        
        This allows the evaluator to be used directly in LangSmith's
        evaluate() function.
        
        Args:
            inputs: Input data
            outputs: Model outputs
            reference_outputs: Ground truth outputs
            
        Returns:
            Dictionary with 'key', 'score', and 'comment'
        """
        try:
            result = self.evaluate(inputs, outputs, reference_outputs)
            return result.to_dict()
        except Exception as e:
            # Return error result
            return EvaluatorResult(
                key=self.metric_name,
                score=0.0,
                comment=f"Evaluation error: {str(e)}",
            ).to_dict()


class LLMBasedEvaluator(BaseEvaluator):
    """
    Base class for evaluators that use LLMs.
    
    This provides common functionality for LLM-based evaluation.
    """

    def __init__(self, metric_name: str, llm_client):
        """
        Initialize the LLM-based evaluator.
        
        Args:
            metric_name: Name of the metric
            llm_client: EvaluationLLMClient instance
        """
        super().__init__(metric_name)
        self.llm_client = llm_client

    def parse_grade_response(self, content: str, positive_key: str) -> bool:
        """
        Parse the LLM response to extract a binary grade.
        
        Args:
            content: Response content from LLM
            positive_key: The string to look for indicating positive grade
                         (e.g., "CORRECT", "RELEVANT", "FAITHFUL")
            
        Returns:
            True if positive grade found, False otherwise
        """
        first_line = content.split("\n")[0].upper()
        return positive_key in first_line
