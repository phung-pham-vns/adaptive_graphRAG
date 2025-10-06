"""Configuration management for evaluation system."""

from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.settings import settings


class EvaluationPreset(str, Enum):
    """Predefined evaluation configuration presets."""

    QUICK = "quick"
    BALANCED = "balanced"
    ACCURACY = "accuracy"
    MINIMAL = "minimal"
    NO_CHECKS = "no_checks"
    GRAPH_ONLY = "graph_only"
    WEB_FALLBACK = "web_fallback"


@dataclass
class WorkflowConfig:
    """Configuration for the RAG workflow during evaluation."""

    n_retrieved_documents: int = 20
    n_web_searches: int = 5
    node_retrieval: bool = True
    edge_retrieval: bool = True
    episode_retrieval: bool = False
    community_retrieval: bool = False
    enable_retrieved_document_grading: bool = False
    enable_hallucination_checking: bool = True
    enable_answer_quality_checking: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "n_retrieved_documents": self.n_retrieved_documents,
            "n_web_searches": self.n_web_searches,
            "node_retrieval": self.node_retrieval,
            "edge_retrieval": self.edge_retrieval,
            "episode_retrieval": self.episode_retrieval,
            "community_retrieval": self.community_retrieval,
            "enable_retrieved_document_grading": self.enable_retrieved_document_grading,
            "enable_hallucination_checking": self.enable_hallucination_checking,
            "enable_answer_quality_checking": self.enable_answer_quality_checking,
        }

    @classmethod
    def from_preset(cls, preset: EvaluationPreset) -> "WorkflowConfig":
        """Create config from a preset."""
        presets = {
            EvaluationPreset.QUICK: cls(
                n_retrieved_documents=10,
                n_web_searches=2,
                enable_retrieved_document_grading=False,
                enable_hallucination_checking=False,
                enable_answer_quality_checking=False,
            ),
            EvaluationPreset.BALANCED: cls(
                n_retrieved_documents=20,
                n_web_searches=5,
                enable_retrieved_document_grading=False,
                enable_hallucination_checking=True,
                enable_answer_quality_checking=True,
            ),
            EvaluationPreset.ACCURACY: cls(
                n_retrieved_documents=30,
                n_web_searches=8,
                enable_retrieved_document_grading=True,
                enable_hallucination_checking=True,
                enable_answer_quality_checking=True,
            ),
            EvaluationPreset.MINIMAL: cls(
                n_retrieved_documents=5,
                n_web_searches=0,
                enable_retrieved_document_grading=False,
                enable_hallucination_checking=False,
                enable_answer_quality_checking=False,
            ),
            EvaluationPreset.NO_CHECKS: cls(
                n_retrieved_documents=20,
                n_web_searches=5,
                enable_retrieved_document_grading=False,
                enable_hallucination_checking=False,
                enable_answer_quality_checking=False,
            ),
            EvaluationPreset.GRAPH_ONLY: cls(
                n_retrieved_documents=25,
                n_web_searches=0,
                enable_retrieved_document_grading=False,
                enable_hallucination_checking=True,
                enable_answer_quality_checking=True,
            ),
            EvaluationPreset.WEB_FALLBACK: cls(
                n_retrieved_documents=15,
                n_web_searches=15,
                enable_retrieved_document_grading=False,
                enable_hallucination_checking=True,
                enable_answer_quality_checking=True,
            ),
        }
        return presets.get(preset, cls())


@dataclass
class LLMConfig:
    """Configuration for LLM clients used in evaluation."""

    base_url: str = field(default_factory=lambda: settings.llm_base_url)
    api_key: str = field(default_factory=lambda: settings.llm_api_key)
    model: str = field(default_factory=lambda: settings.llm_model)
    eval_model: str = "gemini-2.5-pro"  # Strongest model for evaluation
    temperature: float = 0.0
    timeout: int = 300  # 5 minutes


@dataclass
class EvaluationConfig:
    """Main evaluation configuration."""

    # Dataset settings
    dataset_name: str = "Durian Pest and Disease"
    data_file: str = "data/QA_17_pest_disease.json"
    source: str = "17-document-durian-pest-and-disease"

    # Experiment settings
    experiment_prefix: Optional[str] = None
    max_concurrency: int = 1

    # Workflow configuration
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)

    # LLM configuration
    llm: LLMConfig = field(default_factory=LLMConfig)

    # Evaluation settings
    enable_correctness: bool = True
    enable_concision: bool = True
    enable_relevance: bool = False
    enable_faithfulness: bool = False

    def __post_init__(self):
        """Initialize computed fields."""
        if self.experiment_prefix is None:
            self.experiment_prefix = (
                f"durian-pest-and-disease-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
            )

    @classmethod
    def from_preset(
        cls, preset: EvaluationPreset, **overrides
    ) -> "EvaluationConfig":
        """Create evaluation config from a preset with optional overrides."""
        workflow = WorkflowConfig.from_preset(preset)
        return cls(workflow=workflow, **overrides)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for metadata."""
        return {
            "dataset_name": self.dataset_name,
            "experiment_prefix": self.experiment_prefix,
            "max_concurrency": self.max_concurrency,
            "workflow": self.workflow.to_dict(),
            "evaluators": {
                "correctness": self.enable_correctness,
                "concision": self.enable_concision,
                "relevance": self.enable_relevance,
                "faithfulness": self.enable_faithfulness,
            },
        }


# System prompt for agricultural evaluation
EVAL_SYSTEM_PROMPT = """You are an expert agricultural specialist evaluating answers about durian pest and disease management.
Your evaluation should be thorough, fair, and based on agricultural best practices."""
