"""Ingestion API routes."""

import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse

from src.ingestion.service import IngestionService
from src.ingestion.models import (
    GraphStatisticsResponse,
    NodesResponse,
    EdgesResponse,
    IngestionStatusResponse,
    DocumentProcessingResult,
    IngestionResponse,
)
from src.logger import setup_logging


logger = setup_logging()
router = APIRouter(prefix="/ingestion", tags=["ingestion"])

# Shared ingestion service instance
_ingestion_service: Optional[IngestionService] = None


async def get_ingestion_service() -> IngestionService:
    """Get or create the ingestion service instance."""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service


@router.post(
    "/ingest",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest documents via file upload",
    description="""
    Ingest documents by uploading JSON files directly.
    
    This endpoint:
    - Accepts one or more JSON file uploads
    - Processes documents and chunks from uploaded files
    - Adds episodes to the knowledge graph
    - Optionally builds communities
    - Returns detailed processing statistics
    
    **Performance Tips:**
    - Use `max_coroutines > 1` for faster processing of large datasets
    - Set `add_communities=true` only after all documents are ingested
    - Use `clear_existing_data=true` carefully as it will delete all existing graph data
    
    **File Requirements:**
    - Only JSON files are accepted
    - Multiple files can be uploaded in a single request
    - Each file should contain an array of document chunks
    """,
    responses={
        200: {
            "description": "Files ingested successfully",
            "model": IngestionResponse,
        },
        400: {
            "description": "Invalid files or parameters",
        },
        500: {
            "description": "Internal server error during ingestion",
        },
    },
)
async def ingest_documents(
    files: List[UploadFile] = File(..., description="JSON files to ingest"),
    clear_existing_data: bool = Form(False, description="Clear existing graph data"),
    max_coroutines: int = Form(1, ge=1, le=10, description="Max concurrent coroutines"),
    add_communities: bool = Form(False, description="Build communities after ingestion"),
) -> IngestionResponse:
    """
    Ingest documents via file upload.
    
    Upload one or more JSON files to be processed and added to the knowledge graph.
    
    **Example using curl:**
    ```bash
    curl -X POST "http://localhost:8000/ingestion/ingest" \\
      -F "files=@document1.json" \\
      -F "files=@document2.json" \\
      -F "clear_existing_data=false" \\
      -F "max_coroutines=3" \\
      -F "add_communities=false"
    ```
    
    **Example using Python requests:**
    ```python
    import requests
    
    files = [
        ('files', open('document1.json', 'rb')),
        ('files', open('document2.json', 'rb'))
    ]
    data = {
        'clear_existing_data': False,
        'max_coroutines': 3,
        'add_communities': False
    }
    response = requests.post('http://localhost:8000/ingestion/ingest', 
                           files=files, data=data)
    ```
    """
    service = await get_ingestion_service()
    
    try:
        # Validate files
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided",
            )
        
        # Create temporary directory for uploaded files
        temp_dir = Path(tempfile.mkdtemp())
        file_paths = []
        
        try:
            for file in files:
                if not file.filename:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File name is required",
                    )
                
                if not file.filename.endswith('.json'):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid file type: {file.filename}. Only JSON files are accepted.",
                    )
                
                # Save file to temporary location
                file_path = temp_dir / file.filename
                with open(file_path, 'wb') as f:
                    content = await file.read()
                    f.write(content)
                file_paths.append(file_path)
            
            logger.info(f"Received {len(file_paths)} files for ingestion")
            
            # Initialize client
            await service.initialize_client(
                clear_existing_graphdb_data=clear_existing_data,
                max_coroutines=max_coroutines,
            )
            
            # Load documents
            documents = service.load_documents(file_paths)
            
            if not documents:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid documents found to process",
                )
            
            # Ingest documents
            result = await service.ingest_documents(
                documents=documents,
                add_communities=add_communities,
            )
            
            # Build response
            return IngestionResponse(
                success=True,
                message=f"Successfully processed {result['total_documents']} documents",
                total_documents=result["total_documents"],
                processed_documents=[
                    DocumentProcessingResult(**doc) 
                    for doc in result["processed_documents"]
                ],
                total_chunks=result["total_chunks"],
                successful_chunks=result["successful_chunks"],
                failed_chunks=result["failed_chunks"],
                success_rate=result["success_rate"],
            )
            
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during file ingestion")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File ingestion failed: {str(e)}",
        )
    finally:
        # Close client connection
        await service.close_client()


@router.get(
    "/status",
    response_model=IngestionStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check ingestion status",
    description="Get the current status of the knowledge graph and ingestion system.",
)
async def get_ingestion_status() -> IngestionStatusResponse:
    """
    Check the current status of the knowledge graph.
    
    Returns basic statistics about the graph if it's initialized.
    """
    service = await get_ingestion_service()
    
    try:
        # Try to initialize and get statistics
        await service.initialize_client()
        
        try:
            stats = await service.get_graph_statistics()
            
            return IngestionStatusResponse(
                success=True,
                message="Knowledge graph is initialized and accessible",
                graph_initialized=True,
                statistics=stats,
            )
        except Exception as e:
            logger.warning(f"Could not retrieve graph statistics: {e}")
            return IngestionStatusResponse(
                success=True,
                message="Knowledge graph client initialized but statistics unavailable",
                graph_initialized=True,
                statistics=None,
            )
        
    except Exception as e:
        logger.exception("Error checking ingestion status")
        return IngestionStatusResponse(
            success=False,
            message=f"Error accessing knowledge graph: {str(e)}",
            graph_initialized=False,
            statistics=None,
        )
    finally:
        await service.close_client()


@router.get(
    "/statistics",
    response_model=GraphStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get knowledge graph statistics",
    description="""
    Get detailed statistics about the knowledge graph.
    
    Returns counts for:
    - Total nodes and edges
    - Entity nodes
    - Episode nodes
    - Community nodes
    """,
)
async def get_graph_statistics() -> GraphStatisticsResponse:
    """Get statistics about the knowledge graph."""
    service = await get_ingestion_service()
    
    try:
        await service.initialize_client()
        stats = await service.get_graph_statistics()
        
        return GraphStatisticsResponse(
            success=True,
            statistics=stats,
        )
        
    except Exception as e:
        logger.exception("Error getting graph statistics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve graph statistics: {str(e)}",
        )
    finally:
        await service.close_client()


@router.get(
    "/nodes",
    response_model=NodesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sample nodes from knowledge graph",
    description="""
    Retrieve sample nodes from the knowledge graph.
    
    You can filter by node type and limit the number of results.
    """,
)
async def get_nodes(
    limit: int = 10,
    node_type: Optional[str] = None,
) -> NodesResponse:
    """
    Get sample nodes from the knowledge graph.
    
    Args:
        limit: Maximum number of nodes to return (default: 10)
        node_type: Optional filter by node type (e.g., 'Entity', 'Episode', 'Community')
    """
    service = await get_ingestion_service()
    
    try:
        await service.initialize_client()
        nodes = await service.get_sample_nodes(limit=limit, node_type=node_type)
        
        return NodesResponse(
            success=True,
            nodes=nodes,
            count=len(nodes),
        )
        
    except Exception as e:
        logger.exception("Error getting nodes")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve nodes: {str(e)}",
        )
    finally:
        await service.close_client()


@router.get(
    "/edges",
    response_model=EdgesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sample edges from knowledge graph",
    description="""
    Retrieve sample edges (relationships) from the knowledge graph.
    """,
)
async def get_edges(limit: int = 10) -> EdgesResponse:
    """
    Get sample edges from the knowledge graph.
    
    Args:
        limit: Maximum number of edges to return (default: 10)
    """
    service = await get_ingestion_service()
    
    try:
        await service.initialize_client()
        edges = await service.get_sample_edges(limit=limit)
        
        return EdgesResponse(
            success=True,
            edges=edges,
            count=len(edges),
        )
        
    except Exception as e:
        logger.exception("Error getting edges")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve edges: {str(e)}",
        )
    finally:
        await service.close_client()
