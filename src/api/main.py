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
    - **Web Search**: Real-time web information for latest pest/disease updates
    - **LLM Internal Knowledge**: Direct LLM answers for out-of-domain questions
    - **Smart Routing**: Automatically chooses the best data source based on question type
    - **Two-Stage Quality Control**: Optional document relevance and generation quality grading
    - **Citation Tracking**: Provides sources for all answers
    
    ## Features
    
    - 🔄 **3-Way Adaptive Routing**: 
      * Knowledge Graph for domain-specific durian pest/disease questions
      * Web Search for latest pest/disease information
      * LLM Internal for out-of-domain questions (general knowledge, greetings, etc.)
    - ⚡ **Performance Optimization**: Toggle quality checks for faster responses
    - 📚 **Source Citations**: Track where information comes from
    - 🔍 **Document Grading**: Optional relevance checking of retrieved documents
    - 🎯 **Generation Grading**: Two-step validation (hallucination check → answer quality check)
    - 🔄 **Auto-Retry**: Query transformation when results are poor
    
    ## Endpoints
    
    - `POST /workflow/run`: Full workflow execution with detailed steps and citations
    - `POST /workflow/run-simple`: Simplified endpoint returning only question and answer
    - `GET /health`: Health check endpoint
    
    ## Quick Start
    
    ```bash
    # Domain question (routes to Knowledge Graph)
    curl -X POST "http://localhost:8000/workflow/run" \\
      -H "Content-Type: application/json" \\
      -d '{
        "question": "What causes durian leaf curl?",
        "n_documents": 3,
        "enable_document_grading": true,
        "enable_generation_grading": true
      }'
    
    # Latest information question (routes to Web Search)
    curl -X POST "http://localhost:8000/workflow/run-simple" \\
      -H "Content-Type: application/json" \\
      -d '{"question": "What are the latest news about durian pests?"}'
    
    # Out-of-domain question (routes to LLM Internal)
    curl -X POST "http://localhost:8000/workflow/run-simple" \\
      -H "Content-Type: application/json" \\
      -d '{"question": "What is the capital of France?"}'
    ```
    
    ## Performance Tips
    
    - For **fastest responses** (~5-7s): Disable both grading options
    - For **balanced performance** (~10s): Enable document grading, disable generation grading
    - For **highest quality** (~12-15s): Enable all options (default)
    
    ## Workflow Details
    
    ### Intelligent Routing
    
    The system automatically routes questions to the optimal source:
    
    1. **Knowledge Graph** → Durian pest/disease domain questions
       - Examples: "What causes leaf curl?", "How to treat stem borers?"
       
    2. **Web Search** → Latest pest/disease information
       - Examples: "Latest durian pest news?", "New treatment methods?"
       
    3. **LLM Internal** → Out-of-domain questions
       - Examples: "Hello!", "What is Paris?", "Explain machine learning"
       - Fast response, no retrieval overhead
    
    ### Generation Grading (Combined Two-Step Process)
    
    When `enable_generation_grading=true`, answers go through sequential checks in one decision point:
    
    1. **Hallucination Check**:
       - Verifies answer is grounded in retrieved context
       - If not grounded → regenerates answer
       
    2. **Answer Quality Check** (only if grounded):
       - Validates answer addresses the question
       - If not useful → transforms query and retries
       - If useful → returns final answer
    
    Both checks run sequentially without intermediate nodes, providing efficient quality control.
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
    return {
        "name": "Adaptive RAG API",
        "version": "0.1.0",
        "description": "Intelligent Q&A system for durian pests and diseases",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "workflow_full": "POST /workflow/run",
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
    return HealthResponse(status="healthy", version="0.1.0")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
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
