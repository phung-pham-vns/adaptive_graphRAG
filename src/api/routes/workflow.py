"""Workflow API routes."""

import asyncio
from typing import Dict, Any
from datetime import datetime
from time import time

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from src.api.models import (
    WorkflowRequest,
    WorkflowResponse,
    WorkflowStep,
    Citation,
    ErrorResponse,
)
from src.core.workflow import build_workflow
from src.core.constants import Defaults

router = APIRouter(prefix="/workflow", tags=["workflow"])


# Storage for workflow steps and citations during execution
_current_workflow_steps = []
_current_citations = []
_last_step_time = None
_workflow_start_time = None


def add_workflow_step(
    step_name: str, processing_time: float, details: Dict[str, Any] = None
):
    """Add a workflow step to the current execution with timing."""
    step = {
        "name": step_name,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "processing_time": round(processing_time, 3),
        "details": details or {},
    }
    _current_workflow_steps.append(step)


async def run_workflow_internal(
    question: str,
    n_documents: int,
    n_requests: int,
    enable_document_grading: bool,
    enable_generation_grading: bool,
) -> Dict[str, Any]:
    """Run the workflow and track execution with timing."""
    global _current_workflow_steps, _current_citations, _last_step_time, _workflow_start_time

    # Clear previous execution data
    _current_workflow_steps = []
    _current_citations = []
    _last_step_time = None
    _workflow_start_time = time()

    workflow = (
        await build_workflow(
            enable_document_grading=enable_document_grading,
            enable_generation_grading=enable_generation_grading,
        )
    ).compile()

    inputs = {
        "question": question,
        "n_documents": n_documents,
        "n_requests": n_requests,
        "node_contents": [],
        "edge_contents": [],
        "web_contents": [],
        "web_citations": [],
        "retry_count": 0,
    }

    final_state = None

    try:
        async for output in workflow.astream(inputs):
            for node_name, state in output.items():
                # Calculate processing time for this step
                current_time = time()
                if _last_step_time is None:
                    # First step: measure from workflow start
                    processing_time = current_time - _workflow_start_time
                else:
                    # Subsequent steps: measure from last step completion
                    processing_time = current_time - _last_step_time

                _last_step_time = current_time

                # Track workflow step with timing
                add_workflow_step(
                    node_name,
                    processing_time,
                    details={
                        "retry_count": state.get("retry_count", 0),
                        "has_node_contents": bool(state.get("node_contents")),
                        "has_edge_contents": bool(state.get("edge_contents")),
                        "has_web_contents": bool(state.get("web_contents")),
                        "num_node_contents": len(state.get("node_contents", [])),
                        "num_edge_contents": len(state.get("edge_contents", [])),
                        "num_web_contents": len(state.get("web_contents", [])),
                    },
                )
                final_state = state

        # Ensure all async tasks complete
        await asyncio.sleep(0.1)

        # Extract citations
        if final_state:
            web_citations = final_state.get("web_citations", [])
            for citation in web_citations:
                _current_citations.append(
                    {
                        "type": "web",
                        "title": citation.get("title", ""),
                        "url": citation.get("url", ""),
                    }
                )

            kg_citations = final_state.get("kg_citations", [])
            for citation in kg_citations:
                _current_citations.append({"type": "kg", "content": citation})

        answer = (
            final_state.get("generation", "No answer generated.")
            if final_state
            else "No answer generated."
        )

        return {
            "success": True,
            "answer": answer,
            "workflow_steps": _current_workflow_steps,
            "citations": _current_citations,
            "state": final_state,
        }

    except Exception as e:
        add_workflow_step("error", details={"error": str(e)})
        return {
            "success": False,
            "answer": f"Error: {str(e)}",
            "workflow_steps": _current_workflow_steps,
            "citations": _current_citations,
            "state": None,
        }

    finally:
        # Clean up any pending async tasks
        await asyncio.sleep(0.1)


@router.post(
    "/run",
    response_model=WorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Run the adaptive RAG workflow",
    description="Execute the adaptive RAG workflow with a question and return the generated answer along with citations and workflow steps.",
    responses={
        200: {
            "description": "Workflow executed successfully",
            "model": WorkflowResponse,
        },
        400: {
            "description": "Invalid request parameters",
            "model": ErrorResponse,
        },
        500: {
            "description": "Internal server error during workflow execution",
            "model": ErrorResponse,
        },
    },
)
async def run_workflow(request: WorkflowRequest) -> WorkflowResponse:
    """
    Run the adaptive RAG workflow with the provided question.

    This endpoint:
    - Routes the question to knowledge graph or web search
    - Retrieves relevant documents
    - Optionally grades documents for relevance
    - Generates an answer
    - Optionally checks answer quality
    - Returns the answer with citations and workflow steps

    **Performance Optimization:**
    - Set `enable_document_grading=false` to skip document filtering (~2s faster)
    - Set `enable_generation_grading=false` to skip quality checks (~3-5s faster)
    - Both disabled = maximum speed (~5-7s faster) but lower quality

    **Example Request:**
    ```json
    {
        "question": "What causes durian leaf curl?",
        "n_documents": 3,
        "n_requests": 3,
        "enable_document_grading": true,
        "enable_generation_grading": true
    }
    ```
    """
    try:
        # Run the workflow
        result = await run_workflow_internal(
            question=request.question,
            n_documents=request.n_documents,
            n_requests=request.n_requests,
            enable_document_grading=request.enable_document_grading,
            enable_generation_grading=request.enable_generation_grading,
        )

        # Calculate total processing time
        total_time = sum(step["processing_time"] for step in result["workflow_steps"])

        # Build response
        response = WorkflowResponse(
            success=result["success"],
            answer=result["answer"],
            question=request.question,
            workflow_steps=[WorkflowStep(**step) for step in result["workflow_steps"]],
            citations=[Citation(**citation) for citation in result["citations"]],
            metadata={
                "n_documents": request.n_documents,
                "n_requests": request.n_requests,
                "document_grading_enabled": request.enable_document_grading,
                "generation_grading_enabled": request.enable_generation_grading,
                "total_steps": len(result["workflow_steps"]),
                "total_citations": len(result["citations"]),
                "total_processing_time": round(total_time, 3),
                "average_step_time": (
                    round(total_time / len(result["workflow_steps"]), 3)
                    if result["workflow_steps"]
                    else 0
                ),
            },
        )

        return response

    except ValueError as e:
        # Validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid request parameters",
                "detail": str(e),
                "question": request.question,
            },
        )
    except Exception as e:
        # Unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Workflow execution failed",
                "detail": str(e),
                "question": request.question,
            },
        )


@router.post(
    "/run-simple",
    summary="Run workflow with simple request/response",
    description="Simplified endpoint that only returns the answer without workflow details.",
    response_model=Dict[str, str],
)
async def run_workflow_simple(request: WorkflowRequest) -> Dict[str, str]:
    """
    Simplified endpoint that returns only the question and answer.

    Useful for quick integrations where workflow details are not needed.

    **Example Response:**
    ```json
    {
        "question": "What causes durian leaf curl?",
        "answer": "Durian leaf curl can be caused by..."
    }
    ```
    """
    try:
        result = await run_workflow_internal(
            question=request.question,
            n_documents=request.n_documents,
            n_requests=request.n_requests,
            enable_document_grading=request.enable_document_grading,
            enable_generation_grading=request.enable_generation_grading,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["answer"],
            )

        return {
            "question": request.question,
            "answer": result["answer"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
