"""Pydantic models for ingestion API."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class IngestionRequest(BaseModel):
    """Request model for document ingestion."""

    data_dir: str = Field(
        ...,
        description="Directory path containing JSON files to ingest",
        min_length=1,
        examples=["/path/to/data", "data/documents"],
    )
    clear_existing_data: bool = Field(
        default=False,
        description="Whether to clear existing graph data before ingestion",
    )
    max_coroutines: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Maximum number of concurrent coroutines for processing",
    )
    add_communities: bool = Field(
        default=False,
        description="Whether to build communities after ingestion",
    )


class FileUploadIngestionRequest(BaseModel):
    """Request model for file upload ingestion."""

    clear_existing_data: bool = Field(
        default=False,
        description="Whether to clear existing graph data before ingestion",
    )
    max_coroutines: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Maximum number of concurrent coroutines for processing",
    )
    add_communities: bool = Field(
        default=False,
        description="Whether to build communities after ingestion",
    )


class DocumentProcessingResult(BaseModel):
    """Processing result for a single document."""

    document_id: Optional[str] = Field(None, description="Document ID")
    document_name: str = Field(..., description="Document filename")
    total_chunks: int = Field(..., description="Total number of chunks in document", ge=0)
    successful_chunks: int = Field(..., description="Number of successfully processed chunks", ge=0)
    failed_chunks: int = Field(..., description="Number of failed chunks", ge=0)
    text_chunks: int = Field(..., description="Number of text chunks", ge=0)
    image_chunks: int = Field(..., description="Number of image caption chunks", ge=0)
    table_chunks: int = Field(..., description="Number of table chunks", ge=0)


class IngestionResponse(BaseModel):
    """Response model for document ingestion."""

    success: bool = Field(..., description="Whether ingestion completed successfully")
    message: str = Field(..., description="Status message")
    total_documents: int = Field(..., description="Total number of documents processed", ge=0)
    processed_documents: List[DocumentProcessingResult] = Field(
        default_factory=list,
        description="Details of each processed document",
    )
    total_chunks: int = Field(..., description="Total number of chunks processed", ge=0)
    successful_chunks: int = Field(..., description="Number of successfully processed chunks", ge=0)
    failed_chunks: int = Field(..., description="Number of failed chunks", ge=0)
    success_rate: float = Field(..., description="Success rate percentage", ge=0, le=100)


class GraphStatistics(BaseModel):
    """Statistics about the knowledge graph."""

    total_nodes: int = Field(..., description="Total number of nodes in the graph", ge=0)
    total_edges: int = Field(..., description="Total number of edges in the graph", ge=0)
    entity_nodes: int = Field(..., description="Number of entity nodes", ge=0)
    episode_nodes: int = Field(..., description="Number of episode nodes", ge=0)
    community_nodes: int = Field(..., description="Number of community nodes", ge=0)


class GraphStatisticsResponse(BaseModel):
    """Response model for graph statistics."""

    success: bool = Field(..., description="Whether the request was successful")
    statistics: GraphStatistics = Field(..., description="Graph statistics")


class NodeData(BaseModel):
    """Data model for a graph node."""

    id: str = Field(..., description="Node UUID")
    name: str = Field(..., description="Node name")
    labels: List[str] = Field(default_factory=list, description="Node labels")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")


class NodesResponse(BaseModel):
    """Response model for node listing."""

    success: bool = Field(..., description="Whether the request was successful")
    nodes: List[NodeData] = Field(default_factory=list, description="List of nodes")
    count: int = Field(..., description="Number of nodes returned", ge=0)


class EdgeData(BaseModel):
    """Data model for a graph edge."""

    source: str = Field(..., description="Source node name")
    target: str = Field(..., description="Target node name")
    relationship_type: str = Field(..., description="Type of relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge properties")


class EdgesResponse(BaseModel):
    """Response model for edge listing."""

    success: bool = Field(..., description="Whether the request was successful")
    edges: List[EdgeData] = Field(default_factory=list, description="List of edges")
    count: int = Field(..., description="Number of edges returned", ge=0)


class IngestionStatusResponse(BaseModel):
    """Response model for ingestion status check."""

    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Status message")
    graph_initialized: bool = Field(..., description="Whether the graph is initialized")
    statistics: Optional[GraphStatistics] = Field(None, description="Current graph statistics")
