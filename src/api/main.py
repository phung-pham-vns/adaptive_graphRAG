"""FastAPI main application."""

import warnings
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Fix for event loop issues with Python 3.13 + gRPC + LangChain
import nest_asyncio

nest_asyncio.apply()

# Suppress gRPC warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="grpc")

from src.api.routes import workflow
from src.api.models import HealthResponse
from src.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    # Startup
    print("🚀 Starting Adaptive RAG API...")
    print(f"📊 Environment: {settings.environment}")
    print(f"🔧 LLM Model: {settings.llm.llm_model}")

    yield

    # Shutdown
    print("👋 Shutting down Adaptive RAG API...")


# Create FastAPI application
app = FastAPI(
    title="Adaptive RAG API",
    description="""
    🌿 **Adaptive RAG API for Durian Pest & Disease Q&A**
    
    This API provides intelligent question-answering capabilities using:
    - **Knowledge Graph Retrieval**: Domain-specific knowledge about durian pests and diseases
    - **Web Search Fallback**: Real-time web information when KG doesn't have answers
    - **Adaptive Routing**: Automatically chooses the best data source
    - **Quality Control**: Optional document and answer quality grading
    - **Citation Tracking**: Provides sources for all answers
    
    ## Features
    
    - 🔄 **Adaptive Workflow**: Routes questions to optimal data source
    - ⚡ **Performance Optimization**: Toggle quality checks for faster responses
    - 📚 **Source Citations**: Track where information comes from
    - 🔍 **Quality Grading**: Optional relevance and hallucination checking
    - 🔄 **Auto-Retry**: Query transformation when results are poor
    
    ## Endpoints
    
    - `POST /workflow/run`: Full workflow execution with detailed steps and citations
    - `POST /workflow/run-simple`: Simplified endpoint returning only question and answer
    - `GET /health`: Health check endpoint
    
    ## Quick Start
    
    ```bash
    # Full workflow with details
    curl -X POST "http://localhost:8000/workflow/run" \\
      -H "Content-Type: application/json" \\
      -d '{
        "question": "What causes durian leaf curl?",
        "n_documents": 3,
        "enable_document_grading": true,
        "enable_generation_grading": true
      }'
    
    # Simple question-answer
    curl -X POST "http://localhost:8000/workflow/run-simple" \\
      -H "Content-Type: application/json" \\
      -d '{"question": "What causes durian leaf curl?"}'
    ```
    
    ## Performance Tips
    
    - For **fastest responses** (~5-7s): Disable both grading options
    - For **balanced performance** (~10s): Disable document grading only
    - For **highest quality** (~12-15s): Enable all options (default)
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(workflow.router)


@app.get(
    "/",
    summary="Root endpoint",
    description="Returns basic API information",
)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Adaptive RAG API",
        "version": "0.1.0",
        "description": "Intelligent Q&A system for durian pests and diseases",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "workflow_full": "POST /workflow/run",
            "workflow_simple": "POST /workflow/run-simple",
        },
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the API is running and healthy",
)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers_count,
        log_level=settings.log_level.value.lower(),
    )
