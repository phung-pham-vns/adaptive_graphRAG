"""
Evaluation module for the adaptive RAG system.

This module provides comprehensive evaluation capabilities including:
- LangSmith-based evaluation pipelines
- Multiple evaluation metrics (correctness, concision, relevance, faithfulness)
- Dataset ingestion utilities
- Async workflow support
- Configurable evaluation presets

Example usage:
    from src.evaluation import RAGEvaluationPipeline, EvaluationConfig
    
    config = EvaluationConfig.from_preset("balanced")
    pipeline = RAGEvaluationPipeline(config)
    results = pipeline.run_evaluation()
"""

from src.evaluation.config import (
    EvaluationConfig,
    WorkflowConfig,
    LLMConfig,
    EvaluationPreset,
    EVAL_SYSTEM_PROMPT,
)
from src.evaluation.evaluators import (
    BaseEvaluator,
    EvaluatorResult,
    CorrectnessEvaluator,
    ConcisionEvaluator,
    RelevanceEvaluator,
    FaithfulnessEvaluator,
)
from src.evaluation.llm_client import EvaluationLLMClient, create_llm_client
from src.evaluation.async_utils import (
    AsyncEventLoopManager,
    get_global_loop_manager,
    cleanup_global_loop_manager,
)

__all__ = [
    # Configuration
    "EvaluationConfig",
    "WorkflowConfig",
    "LLMConfig",
    "EvaluationPreset",
    "EVAL_SYSTEM_PROMPT",
    # Evaluators
    "BaseEvaluator",
    "EvaluatorResult",
    "CorrectnessEvaluator",
    "ConcisionEvaluator",
    "RelevanceEvaluator",
    "FaithfulnessEvaluator",
    # LLM Client
    "EvaluationLLMClient",
    "create_llm_client",
    # Async utilities
    "AsyncEventLoopManager",
    "get_global_loop_manager",
    "cleanup_global_loop_manager",
]

__version__ = "1.0.0"
