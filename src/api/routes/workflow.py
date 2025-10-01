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
    node_retrieval: bool,
    edge_retrieval: bool,
    episode_retrieval: bool,
    community_retrieval: bool,
    enable_retrieved_document_grading: bool,
    enable_hallucination_checking: bool,
    enable_answer_quality_checking: bool,
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
            enable_retrieved_document_grading=enable_retrieved_document_grading,
            enable_hallucination_checking=enable_hallucination_checking,
            enable_answer_quality_checking=enable_answer_quality_checking,
        )
    ).compile()

    inputs = {
        "question": question,
        "n_retrieved_documents": n_documents,
        "n_web_searches": n_requests,
        "node_retrieval": node_retrieval,
        "edge_retrieval": edge_retrieval,
        "episode_retrieval": episode_retrieval,
        "community_retrieval": community_retrieval,
        "node_contents": [],
        "edge_contents": [],
        "web_contents": [],
        "node_citations": [],
        "edge_citations": [],
        "web_citations": [],
        "citations": [],
        "query_transformation_retry_count": 0,
        "hallucination_retry_count": 0,
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
                        "query_transformation_retry_count": state.get(
                            "query_transformation_retry_count", 0
                        ),
                        "hallucination_retry_count": state.get(
                            "hallucination_retry_count", 0
                        ),
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
            citations = final_state.get("citations", [])
            for citation in citations:
                _current_citations.append(
                    {
                        "title": citation.get("title", ""),
                        "url": citation.get("url", ""),
                    }
                )

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
    - Intelligently routes the question to one of three sources:
        * **Knowledge Graph**: Domain-specific durian pest/disease questions
        * **Web Search**: Latest pest/disease information
        * **LLM Internal**: Out-of-domain questions (no retrieval needed)
    - Retrieves relevant documents (for KG and Web routes)
    - Optionally grades documents for relevance (if `enable_retrieved_document_grading=true`)
    - Generates an answer
    - Optionally checks answer grounding and quality (independently configurable)
    - Returns the answer with citations and workflow steps

    **Generation Grading Options:**
    You can independently control two types of generation checks:
    - **Hallucination Checking** (`enable_hallucination_checking`): Verifies answer is grounded in context
        * If not grounded → regenerate answer
    - **Answer Quality Checking** (`enable_answer_quality_checking`): Validates answer addresses the question
        * If doesn't address question → transform query and retry

    These can be enabled independently or together for maximum quality control.

    **Performance vs Quality Trade-off:**
    - **Default mode** (all checks disabled): Maximum speed, good quality
    - Enable `enable_retrieved_document_grading=true` for better relevance (~2s slower)
    - Enable `enable_hallucination_checking=true` for grounding verification (~1-2s slower)
    - Enable `enable_answer_quality_checking=true` for answer validation (~2-3s slower)
    - All checks enabled = highest quality (~5-7s slower) with comprehensive validation

    **Example Request (Speed Mode - Default):**
    ```json
    {
        "question": "What causes durian leaf curl?",
        "n_retrieved_documents": 3,
        "n_web_searches": 3,
        "node_retrieval": true,
        "edge_retrieval": false,
        "episode_retrieval": false,
        "community_retrieval": false,
        "enable_retrieved_documents_grading": false,
        "enable_hallucination_checking": false,
        "enable_answer_quality_checking": false
    }
    ```

    **Example Request (Quality Mode):**
    ```json
    {
        "question": "What causes durian leaf curl?",
        "n_retrieved_documents": 3,
        "n_web_searches": 3,
        "node_retrieval": true,
        "edge_retrieval": true,
        "episode_retrieval": true,
        "community_retrieval": true,
        "enable_retrieved_documents_grading": true,
        "enable_hallucination_checking": true,
        "enable_answer_quality_checking": true
    }
    ```
    """
    try:
        # Run the workflow
        result = await run_workflow_internal(
            question=request.question,
            n_documents=request.n_retrieved_documents,
            n_requests=request.n_web_searches,
            node_retrieval=request.node_retrieval,
            edge_retrieval=request.edge_retrieval,
            episode_retrieval=request.episode_retrieval,
            community_retrieval=request.community_retrieval,
            enable_retrieved_document_grading=request.enable_retrieved_documents_grading,
            enable_hallucination_checking=request.enable_hallucination_checking,
            enable_answer_quality_checking=request.enable_answer_quality_checking,
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
                "n_retrieved_documents": request.n_retrieved_documents,
                "n_web_searches": request.n_web_searches,
                "node_retrieval": request.node_retrieval,
                "edge_retrieval": request.edge_retrieval,
                "episode_retrieval": request.episode_retrieval,
                "community_retrieval": request.community_retrieval,
                "document_grading_enabled": request.enable_retrieved_documents_grading,
                "hallucination_checking_enabled": request.enable_hallucination_checking,
                "answer_quality_checking_enabled": request.enable_answer_quality_checking,
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
