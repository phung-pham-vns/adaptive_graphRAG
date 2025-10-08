from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WorkflowRequest(BaseModel):
    question: str = Field(
        ...,
        description="The question to ask the adaptive RAG system",
        min_length=1,
        max_length=2000,
        examples=["What symptom distinguishes Phomopsis leaf spot?"],
    )
    image: Optional[str] = Field(
        default=None,
        description="Base64 encoded image data for visual question answering",
        examples=["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."],
    )
    n_retrieved_documents: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retrieved documents to retrieve from knowledge graph",
    )
    n_web_searches: int = Field(
        default=3, ge=1, le=10, description="Number of web searches to fetch"
    )
    node_retrieval: bool = Field(
        default=True,
        description="Enable node retrieval from knowledge graph",
    )
    edge_retrieval: bool = Field(
        default=False,
        description="Enable edge retrieval from knowledge graph",
    )
    episode_retrieval: bool = Field(
        default=False,
        description="Enable episode retrieval from knowledge graph",
    )
    community_retrieval: bool = Field(
        default=False,
        description="Enable community retrieval from knowledge graph",
    )
    enable_retrieved_documents_grading: bool = Field(
        default=False,
        description="Enable document relevance grading (slower but higher quality)",
    )
    enable_hallucination_checking: bool = Field(
        default=False,
        description="Enable hallucination checking to verify answer is grounded in context",
    )
    enable_answer_quality_checking: bool = Field(
        default=False,
        description="Enable answer quality checking to verify answer addresses the question",
    )


class WorkflowStep(BaseModel):
    name: str = Field(..., description="Name of the workflow step")
    timestamp: str = Field(..., description="Timestamp of step execution (HH:MM:SS)")
    processing_time: float = Field(
        ..., description="Time taken to execute this step in seconds", ge=0
    )
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional details about the step"
    )


class Citation(BaseModel):
    title: Optional[str] = Field(None, description="Title of the source (for web)")
    url: Optional[str] = Field(None, description="URL of the source (for web)")
    content: Optional[str] = Field(None, description="Content snippet (for KG)")


class WorkflowResponse(BaseModel):
    success: bool = Field(
        ..., description="Whether the workflow completed successfully"
    )
    answer: str = Field(..., description="Generated answer to the question")
    question: str = Field(..., description="The original question")
    workflow_steps: List[WorkflowStep] = Field(
        default_factory=list, description="List of workflow steps executed"
    )
    citations: List[Citation] = Field(
        default_factory=list, description="List of source citations"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the execution"
    )


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    question: Optional[str] = Field(
        None, description="The question that caused the error"
    )
