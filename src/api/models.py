from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WorkflowRequest(BaseModel):
    """Request model for workflow execution."""

    question: str = Field(
        ...,
        description="The question to ask the adaptive RAG system",
        min_length=1,
        max_length=2000,
        examples=["What causes durian leaf curl?"],
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
    enable_retrieved_documents_grading: bool = Field(
        default=True,
        description="Enable document relevance grading (slower but higher quality)",
    )
    enable_generation_grading: bool = Field(
        default=True,
        description="Enable answer quality checking (slower but more accurate)",
    )


class WorkflowStep(BaseModel):
    """Model for a single workflow step."""

    name: str = Field(..., description="Name of the workflow step")
    timestamp: str = Field(..., description="Timestamp of step execution (HH:MM:SS)")
    processing_time: float = Field(
        ..., description="Time taken to execute this step in seconds", ge=0
    )
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional details about the step"
    )


class Citation(BaseModel):
    """Model for a source citation."""

    title: Optional[str] = Field(None, description="Title of the source (for web)")
    url: Optional[str] = Field(None, description="URL of the source (for web)")
    content: Optional[str] = Field(None, description="Content snippet (for KG)")


class WorkflowResponse(BaseModel):
    """Response model for workflow execution."""

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
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    question: Optional[str] = Field(
        None, description="The question that caused the error"
    )
