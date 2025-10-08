# Adaptive RAG Workflow Architecture

## Overview

This document describes the architecture of the Adaptive RAG (Retrieval-Augmented Generation) workflow system, which intelligently routes questions to the most appropriate data source and generates high-quality answers with optional quality control mechanisms.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  • REST API Clients (curl, Python requests, JavaScript, etc.)   │
│  • CLI (workflow.py command-line interface)                     │
│  • Web UI (Swagger, ReDoc)                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API Layer (FastAPI)                       │
├─────────────────────────────────────────────────────────────────┤
│  src/api/routes/workflow.py                                    │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  POST   /workflow/run      - Full workflow execution    │  │
│  │                               with steps & citations     │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Validation Layer (Pydantic)                  │
├─────────────────────────────────────────────────────────────────┤
│  src/api/models.py                                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  • WorkflowRequest        - Input parameters            │  │
│  │  • WorkflowResponse       - Complete response           │  │
│  │  • WorkflowStep           - Individual step info        │  │
│  │  • Citation               - Source citations            │  │
│  │  • ErrorResponse          - Error information           │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Workflow Orchestration (LangGraph)             │
├─────────────────────────────────────────────────────────────────┤
│  src/core/workflow.py                                          │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Graph Builder:                                         │  │
│  │  • build_workflow()        - Construct state graph      │  │
│  │  • run_workflow()          - Execute workflow           │  │
│  │                                                           │  │
│  │  Routing Nodes:                                          │  │
│  │  • route_question()        - Intelligent routing        │  │
│  │  • decide_to_generate()    - Generate/retry decision    │  │
│  │                                                           │  │
│  │  Quality Control Nodes:                                  │  │
│  │  • grade_generation_and_context()                        │  │
│  │                            - Hallucination check         │  │
│  │  • grade_generation_and_question()                       │  │
│  │                            - Answer quality check        │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Processing Functions                       │
├─────────────────────────────────────────────────────────────────┤
│  src/core/functions.py                                         │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Data Retrieval:                                        │  │
│  │  • knowledge_graph_retrieval() - Search knowledge graph │  │
│  │  • web_search()                - Tavily web search      │  │
│  │                                                           │  │
│  │  Processing:                                             │  │
│  │  • retrieved_documents_grading() - Grade relevance      │  │
│  │  • query_transformation()      - Refine query           │  │
│  │  • answer_generation()         - Generate answer        │  │
│  │  • format_context()            - Format context         │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Chains (LangChain)                       │
├─────────────────────────────────────────────────────────────────┤
│  src/core/chains.py                                            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  • question_router         - Route to data source       │  │
│  │  • retrieval_grader        - Grade document relevance   │  │
│  │  • hallucination_grader    - Check answer grounding     │  │
│  │  • answer_grader           - Check answer quality       │  │
│  │  • question_rewriter       - Refine questions           │  │
│  │  • answer_generator        - Generate from context      │  │
│  │  • llm_internal_answer_generator                         │  │
│  │                            - Generate without context    │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐│
│  │  LLM Service │  Knowledge   │  Web Search  │  Vector DB   ││
│  │  (Gemini/    │  Graph       │  (Tavily)    │  (for KG     ││
│  │   OpenAI)    │  (Neo4j)     │              │   search)    ││
│  └──────────────┴──────────────┴──────────────┴──────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Workflow State Machine

The workflow is implemented as a state graph using LangGraph, with conditional edges based on configuration and grading results.

### Complete Workflow Graph

```
                           START
                             │
                             ▼
                    ┌────────────────┐
                    │ route_question │ (Intelligent Routing)
                    └────────┬───────┘
                             │
                 ┌───────────┼───────────┐
                 │           │           │
                 ▼           ▼           ▼
    ┌────────────────┐  ┌───────────────────────┐  ┌──────────────────┐
    │  web_search    │  │ knowledge_graph       │  │ answer_generation│
    │                │  │    _retrieval         │  │ (LLM internal)   │
    └────────┬───────┘  └───────┬───────────────┘  └────────┬─────────┘
             │                  │                            │
             │           ┌──────┴──────┐                     │
             │           │ (optional)  │                     │
             │           ▼             │                     │
             │    ┌──────────────────┐ │                     │
             │    │retrieved_documents│                      │
             │    │    _grading      │                      │
             │    └──────┬───────────┘                      │
             │           │                                  │
             │    ┌──────┴──────┐                          │
             │    │ decide_to_  │                          │
             │    │  generate   │                          │
             │    └──────┬──────┘                          │
             │           │                                  │
             │    ┌──────┴──────┬──────────────┐          │
             │    │             │              │          │
             │    ▼             ▼              ▼          │
             │  answer    query_trans   web_search       │
             │  generation   formation   (fallback)      │
             │    │             │              │          │
             │    │             └──────┐       │          │
             │    │                    │       │          │
             └────┴────────────────────┴───────┴──────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │answer_generation│
                    └────────┬───────┘
                             │
             ┌───────────────┴──────────────┐
             │      (Quality Control)       │
             ▼                              ▼
    ┌────────────────────┐       ┌──────────────────┐
    │ (optional)         │       │ (optional)       │
    │grade_generation   │       │grade_generation  │
    │  _and_context      │       │  _and_question   │
    │(Hallucination)     │       │(Answer Quality)  │
    └────────┬───────────┘       └────────┬─────────┘
             │                            │
        ┌────┴─────┐                 ┌───┴────┐
        │          │                 │        │
        ▼          ▼                 ▼        ▼
    grounded   not_grounded      correct  incorrect
        │          │                 │        │
        │          └─→ regenerate    │        └─→ query_
        │              answer        │            transformation
        │                            │
        └────────────┬───────────────┘
                     │
                     ▼
                    END
```

## Three-Way Intelligent Routing

The system intelligently routes questions to one of three data sources:

### 1. Knowledge Graph Retrieval (kg_retrieval)
**When**: Domain-specific durian pest and disease questions

**Examples**:
- "What causes durian leaf curl?"
- "How to treat stem borers in durian?"
- "What are symptoms of Phytophthora palmivora?"

**Process**:
1. Search knowledge graph (nodes, edges, episodes, communities)
2. Retrieve relevant entities and relationships
3. Optionally grade documents for relevance
4. Generate answer from retrieved context

### 2. Web Search (web_search)
**When**: Latest pest/disease information or recent news

**Examples**:
- "What are the latest news about durian pests?"
- "New treatment methods for durian diseases?"
- "Recent research on durian leaf curl?"

**Process**:
1. Perform Tavily web search
2. Retrieve top results
3. Generate answer from web content

### 3. LLM Internal (llm_internal)
**When**: Out-of-domain questions or general knowledge

**Examples**:
- "Hello, how are you?"
- "What is the capital of France?"
- "Explain machine learning"

**Process**:
1. Skip retrieval entirely
2. Generate answer using LLM's internal knowledge
3. Fast response with no context overhead

## Knowledge Graph Retrieval Flow

```
┌─────────────────────────────────────────────┐
│  1. Question Input                          │
│     "What causes durian leaf curl?"         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  2. Route to Knowledge Graph                │
│     question_router determines route        │
│     → "kg_retrieval"                        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  3. Knowledge Graph Search                  │
│     Parallel searches (if enabled):         │
│     • Node Search (entities)                │
│     • Edge Search (relationships)           │
│     • Episode Search (text chunks)          │
│     • Community Search (clusters)           │
│                                             │
│     Uses: BM25 + Cosine + BFS + Reranking  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  4. Optional: Grade Documents               │
│     For each retrieved document:            │
│     • Check relevance to question           │
│     • Keep only relevant (yes) documents    │
│     • Discard irrelevant (no) documents     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  5. Decide to Generate                      │
│     • If relevant docs exist → generate     │
│     • If no relevant docs:                  │
│       - Try query_transformation (retry)    │
│       - Or fallback to web_search           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  6. Generate Answer                         │
│     Format context from:                    │
│     • Node contents (entities)              │
│     • Edge contents (relationships)         │
│     • Web contents (if any)                 │
│     • Citations                             │
│                                             │
│     Generate structured answer with LLM     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  7. Optional: Quality Control               │
│     Step 1 - Hallucination Check:           │
│     • Is answer grounded in context?        │
│     • If no → regenerate (max retries: 2)   │
│                                             │
│     Step 2 - Answer Quality Check:          │
│     • Does answer address question?         │
│     • If no → transform query (max: 2)      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  8. Return Final Answer                     │
│     {                                       │
│       "answer": "Durian leaf curl is...",   │
│       "citations": [...]                    │
│     }                                       │
└─────────────────────────────────────────────┘
```

## Data Flow

### Request → Response Flow

```
┌──────────────────────────────────────────────────────────┐
│  Client Request (POST /workflow/run)                     │
├──────────────────────────────────────────────────────────┤
│  {                                                       │
│    "question": "What causes durian leaf curl?",          │
│    "n_retrieved_documents": 3,                           │
│    "node_retrieval": true,                               │
│    "enable_retrieved_documents_grading": true,           │
│    "enable_hallucination_checking": true,                │
│    "enable_answer_quality_checking": true                │
│  }                                                       │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  API Layer (src/api/routes/workflow.py)                 │
│  • Validate request with WorkflowRequest model           │
│  • Initialize workflow state                             │
│  • Track workflow steps with timestamps                  │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  Build Workflow (src/core/workflow.py)                  │
│  • Create StateGraph with GraphState                     │
│  • Add nodes based on configuration                      │
│  • Add conditional edges                                 │
│  • Compile graph                                         │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  Execute Workflow (LangGraph)                            │
│  • Stream through graph nodes                            │
│  • Update state at each node                             │
│  • Follow conditional edges                              │
│  • Track progress                                        │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  Workflow Nodes Execute                                  │
│                                                          │
│  1. route_question                                       │
│     → Determine data source (KG/Web/Internal)            │
│                                                          │
│  2. knowledge_graph_retrieval (or web_search)            │
│     → Retrieve relevant documents                        │
│                                                          │
│  3. retrieved_documents_grading (optional)               │
│     → Grade document relevance                           │
│                                                          │
│  4. decide_to_generate                                   │
│     → Check if ready to generate                         │
│                                                          │
│  5. answer_generation                                    │
│     → Generate answer from context                       │
│                                                          │
│  6. grade_generation_and_context (optional)              │
│     → Check hallucination                                │
│                                                          │
│  7. grade_generation_and_question (optional)             │
│     → Check answer quality                               │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  Final State Extraction                                  │
│  • Extract final answer                                  │
│  • Extract citations                                     │
│  • Calculate total processing time                       │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│  Response (WorkflowResponse)                             │
├──────────────────────────────────────────────────────────┤
│  {                                                       │
│    "success": true,                                      │
│    "answer": "Durian leaf curl is caused by...",         │
│    "question": "What causes durian leaf curl?",          │
│    "workflow_steps": [                                   │
│      {"name": "route_question", "time": 0.5, ...},       │
│      {"name": "knowledge_graph_retrieval", "time": 2.3}  │
│    ],                                                    │
│    "citations": [                                        │
│      {"title": "...", "url": "..."}                      │
│    ],                                                    │
│    "metadata": {                                         │
│      "total_processing_time": 5.2,                       │
│      "total_steps": 4                                    │
│    }                                                     │
│  }                                                       │
└──────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### API Layer (`src/api/routes/workflow.py`)
**Responsibilities**:
- HTTP request handling
- Input validation via Pydantic models
- Workflow execution orchestration
- Response formatting
- Error handling and HTTP status codes
- Step-by-step timing and tracking
- Citation extraction

**Key Functions**:
- `run_workflow_internal()` - Core workflow execution
- `add_workflow_step()` - Track individual steps
- `run_workflow()` - API endpoint handler

### Workflow Layer (`src/core/workflow.py`)
**Responsibilities**:
- State graph construction with LangGraph
- Node and edge definitions
- Conditional routing logic
- Quality control flow
- Retry management
- Configuration-based graph building

**Key Functions**:
- `build_workflow()` - Construct state graph
- `route_question()` - Intelligent routing
- `decide_to_generate()` - Generation decision
- `grade_generation_and_context()` - Hallucination check
- `grade_generation_and_question()` - Quality check

### Processing Functions (`src/core/functions.py`)
**Responsibilities**:
- Knowledge graph retrieval
- Web search integration
- Document grading
- Query transformation
- Answer generation
- Context formatting

**Key Functions**:
- `knowledge_graph_retrieval()` - Search knowledge graph
- `web_search()` - Tavily web search
- `retrieved_documents_grading()` - Grade documents
- `query_transformation()` - Refine queries
- `answer_generation()` - Generate answers
- `format_context()` - Format context for LLM

### LLM Chains (`src/core/chains.py`)
**Responsibilities**:
- LLM prompt configuration
- Structured output parsing
- Chain composition with LangChain
- Provider abstraction (Gemini/OpenAI)

**Key Chains**:
- `question_router` - Route questions to data source
- `retrieval_grader` - Grade document relevance
- `hallucination_grader` - Check answer grounding
- `answer_grader` - Check answer quality
- `question_rewriter` - Refine questions
- `answer_generator` - Generate contextual answers
- `llm_internal_answer_generator` - Generate without context

### Schema Layer (`src/core/schema.py`)
**Responsibilities**:
- Define structured output schemas
- Type safety for LLM outputs
- Validation of LLM responses

**Key Schemas**:
- `RouteQuery` - Routing decisions
- `GradeDocuments` - Document relevance scores
- `GradeHallucinations` - Hallucination scores
- `GradeAnswer` - Answer quality scores
- `QueryRefinement` - Refined questions
- `GenerateAnswer` - Generated answers

### GraphState (`src/core/functions.py`)
**Central State Object** passed through workflow:

```python
class GraphState(TypedDict):
    # Input
    question: str
    n_retrieved_documents: int
    n_web_searches: int
    
    # Retrieval configuration
    node_retrieval: bool
    edge_retrieval: bool
    episode_retrieval: bool
    community_retrieval: bool
    
    # Retrieved content
    node_contents: list[str]
    edge_contents: list[str]
    web_contents: list[str]
    
    # Citations
    node_citations: list[dict]
    edge_citations: list[dict]
    web_citations: list[dict]
    citations: list[dict]
    
    # Output
    generation: Optional[str]
    
    # Retry tracking
    query_transformation_retry_count: int
    hallucination_retry_count: int
```

## Key Design Patterns

### 1. State Machine Pattern (LangGraph)
- Workflow modeled as finite state machine
- Nodes represent processing steps
- Edges represent transitions
- Conditional edges for dynamic routing

**Example**:
```python
workflow.add_conditional_edges(
    START,
    route_question,
    {
        "web_search": "web_search",
        "kg_retrieval": "knowledge_graph_retrieval",
        "answer_generation": "answer_generation",
    },
)
```

### 2. Strategy Pattern (Routing)
- Different retrieval strategies based on question type
- Runtime selection of strategy (KG/Web/Internal)
- Encapsulated algorithms for each strategy

### 3. Chain of Responsibility (Quality Control)
- Multiple optional quality checks
- Each check can pass or trigger retry
- Configurable chain based on flags

### 4. Circuit Breaker Pattern (Retry Logic)
- Maximum retry limits prevent infinite loops
- Graceful degradation on max retries
- Best-effort answers when retries exhausted

**Example**:
```python
if current_retry >= MAX_RETRIES:
    print("Max retries reached, returning best effort")
    return "grounded"  # End with best effort answer
```

### 5. Pipeline Pattern (LLM Chains)
- LangChain pipes: prompt | llm | parser
- Structured output with Pydantic
- Reusable chain components

**Example**:
```python
question_router = (
    question_routing_prompt 
    | llm.with_structured_output(RouteQuery)
)
```

## Configuration Options

### Retrieval Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_retrieved_documents` | int | 3 | Number of documents to retrieve from KG |
| `n_web_searches` | int | 3 | Number of web search results |
| `node_retrieval` | bool | true | Enable node/entity retrieval |
| `edge_retrieval` | bool | false | Enable edge/relationship retrieval |
| `episode_retrieval` | bool | false | Enable episode/chunk retrieval |
| `community_retrieval` | bool | false | Enable community retrieval |

### Quality Control Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_retrieved_documents_grading` | bool | false | Grade document relevance |
| `enable_hallucination_checking` | bool | false | Check answer grounding |
| `enable_answer_quality_checking` | bool | false | Check answer quality |

### Performance Modes

**Speed Mode** (Default):
```json
{
  "enable_retrieved_documents_grading": false,
  "enable_hallucination_checking": false,
  "enable_answer_quality_checking": false
}
```
⚡ **~5-7 seconds** - Maximum speed, good quality

**Balanced Mode**:
```json
{
  "enable_retrieved_documents_grading": true,
  "enable_hallucination_checking": false,
  "enable_answer_quality_checking": false
}
```
⚖️ **~7-9 seconds** - Better relevance, moderate speed

**Quality Mode**:
```json
{
  "enable_retrieved_documents_grading": true,
  "enable_hallucination_checking": true,
  "enable_answer_quality_checking": true
}
```
🎯 **~12-15 seconds** - Highest quality, comprehensive validation

## Error Handling Strategy

### Multi-Layer Error Handling

```
┌─────────────────────────────────────┐
│  API Layer                          │
│  • HTTP exceptions                  │
│  • Validation errors                │
│  • 400/500 status codes             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Workflow Layer                     │
│  • Routing errors → default route   │
│  • Node errors → logged & continued │
│  • Fallback to best effort          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Function Layer                     │
│  • Try/except in each function      │
│  • Graceful degradation             │
│  • Empty results on errors          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Chain Layer                        │
│  • LLM invocation errors            │
│  • Parsing errors                   │
│  • Timeout handling                 │
└─────────────────────────────────────┘
```

### Error Handling Examples

**Routing Error**:
```python
try:
    source = await question_router.ainvoke({"question": state["question"]})
    return source.data_source
except Exception as e:
    print(f"Error in routing: {e}, defaulting to answer generation")
    return "answer_generation"  # Safe fallback
```

**Retrieval Error**:
```python
try:
    result = await graphiti.search(query, search_config)
    return node_contents, edge_contents
except Exception as e:
    logger.exception("Error in knowledge graph retrieval")
    return [], []  # Return empty, workflow continues
```

**Quality Check Error**:
```python
try:
    score = await hallucination_grader.ainvoke(...)
    return "grounded" if score.binary_score == "yes" else "not_grounded"
except Exception as e:
    print(f"Error in grading: {e}")
    return "grounded"  # Best effort, end workflow
```

## Performance Optimization

### 1. Parallel Retrieval
Multiple knowledge graph searches execute concurrently:
```python
search_config = SearchConfig(
    node_config=NodeSearchConfig(...),    # Parallel
    edge_config=EdgeSearchConfig(...),    # Parallel
    episode_config=EpisodeSearchConfig(...),  # Parallel
    community_config=CommunitySearchConfig(...)  # Parallel
)
```

### 2. Optional Nodes
Disable expensive operations when speed is critical:
- Document grading: ~2s savings
- Hallucination checking: ~1-2s savings
- Answer quality checking: ~2-3s savings

### 3. Caching (Future Enhancement)
- Cache routing decisions for similar questions
- Cache embeddings for repeated queries
- Cache LLM responses for identical inputs

### 4. Retry Limits
Prevent infinite loops with max retry counts:
- Query transformation: Max 2 retries
- Hallucination regeneration: Max 2 retries

### 5. Streaming Execution
LangGraph streams through nodes for progressive updates

## Monitoring and Observability

### Workflow Step Tracking

Every execution tracks:
```python
{
  "name": "knowledge_graph_retrieval",
  "timestamp": "14:32:15",
  "processing_time": 2.341,
  "details": {
    "query_transformation_retry_count": 0,
    "hallucination_retry_count": 0,
    "has_node_contents": true,
    "num_node_contents": 3,
    "num_edge_contents": 2,
    "num_web_contents": 0
  }
}
```

### Logging

Structured logging at each step:
```
[INFO] === ROUTING QUESTION ===
[INFO] Route to: KNOWLEDGE_GRAPH_RETRIEVAL
[INFO] === KNOWLEDGE GRAPH RETRIEVAL ===
[INFO] Retrieved 3 node contents, 2 edge contents
[INFO] === ASSESSING GRADED DOCUMENTS ===
[INFO] Decision: GENERATE
[INFO] === GENERATING ANSWER ===
```

### Metrics (Future)

Potential metrics to track:
- Average processing time per node
- Routing distribution (KG/Web/Internal)
- Quality control trigger rates
- Retry frequency
- Success/failure rates

## Security Considerations

### Input Validation
- Pydantic models enforce type safety
- Field limits prevent abuse:
  - `question`: max 2000 characters
  - `n_retrieved_documents`: 1-10 range
  - `n_web_searches`: 1-10 range

### Prompt Injection Protection
- Structured outputs prevent injection
- LLM responses parsed into typed schemas
- No direct string interpolation

### Rate Limiting (Future)
- Per-user request limits
- Global throughput limits
- Retry exponential backoff

### API Key Security
- Keys stored in environment variables
- Never exposed in responses
- Separate keys per service

## Testing Strategy

### Unit Tests

Test individual components:

```python
async def test_route_question():
    state = {"question": "What causes durian leaf curl?"}
    route = await route_question(state)
    assert route == "kg_retrieval"

async def test_knowledge_graph_retrieval():
    state = {
        "question": "durian pests",
        "n_retrieved_documents": 3,
        "node_retrieval": True
    }
    result = await knowledge_graph_retrieval(state)
    assert len(result["node_contents"]) > 0
```

### Integration Tests

Test complete workflows:

```python
async def test_full_workflow_kg_route():
    result = await run_workflow(
        question="What causes durian leaf curl?",
        enable_retrieved_documents_grading=True
    )
    assert result["success"] == True
    assert len(result["answer"]) > 0
    assert len(result["workflow_steps"]) > 0
```

### End-to-End Tests

Test via API:

```python
def test_workflow_api():
    response = client.post("/workflow/run", json={
        "question": "What causes durian leaf curl?",
        "n_retrieved_documents": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "answer" in data
```

## Extension Points

### 1. New Routing Destinations
Add new data sources by:
- Adding route to `RouteQuery` schema
- Adding conditional edge in workflow
- Implementing retrieval function

### 2. Custom Grading Functions
Replace or add graders:
```python
workflow.add_node("custom_grader", my_custom_grader)
workflow.add_conditional_edges("custom_grader", ...)
```

### 3. Additional Quality Checks
Chain more quality checks:
```python
workflow.add_node("fact_check", fact_checker)
workflow.add_edge("answer_quality_check", "fact_check")
```

### 4. Alternative LLM Providers
Swap LLM provider in `chains.py`:
```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4", ...)
```

### 5. Custom State Fields
Extend `GraphState` with new fields:
```python
class GraphState(TypedDict):
    # Existing fields...
    custom_field: Optional[str]
```

## Related Documentation

- [API Models](../src/api/models.py) - Request/response schemas
- [Workflow Implementation](../src/core/workflow.py) - LangGraph workflow
- [Processing Functions](../src/core/functions.py) - Core functions
- [LLM Chains](../src/core/chains.py) - LangChain chains
- [API Docs](http://localhost:8000/docs) - Interactive API documentation
- [Ingestion Architecture](./INGESTION_ARCHITECTURE.md) - Knowledge graph ingestion

## Appendix: Complete Example

### API Request
```bash
curl -X POST "http://localhost:8000/workflow/run" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What causes durian leaf curl?",
    "n_retrieved_documents": 3,
    "node_retrieval": true,
    "edge_retrieval": true,
    "enable_retrieved_documents_grading": true,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": true
  }'
```

### API Response
```json
{
  "success": true,
  "answer": "Durian leaf curl is primarily caused by Phytoplasma pathogens...",
  "question": "What causes durian leaf curl?",
  "workflow_steps": [
    {
      "name": "route_question",
      "timestamp": "14:32:10",
      "processing_time": 0.523,
      "details": {...}
    },
    {
      "name": "knowledge_graph_retrieval",
      "timestamp": "14:32:12",
      "processing_time": 2.341,
      "details": {
        "num_node_contents": 3,
        "num_edge_contents": 2
      }
    },
    {
      "name": "retrieved_documents_grading",
      "timestamp": "14:32:14",
      "processing_time": 1.823,
      "details": {}
    },
    {
      "name": "answer_generation",
      "timestamp": "14:32:16",
      "processing_time": 2.156,
      "details": {}
    },
    {
      "name": "answer_quality_check",
      "timestamp": "14:32:18",
      "processing_time": 1.234,
      "details": {}
    }
  ],
  "citations": [
    {
      "title": "Phytoplasma diseases of durian",
      "url": null
    }
  ],
  "metadata": {
    "n_retrieved_documents": 3,
    "total_steps": 5,
    "total_citations": 1,
    "total_processing_time": 8.077,
    "average_step_time": 1.615,
    "document_grading_enabled": true,
    "hallucination_checking_enabled": true,
    "answer_quality_checking_enabled": true
  }
}
```

### CLI Usage
```bash
python -m src.core.workflow \
  --question "What causes durian leaf curl?" \
  --n-retrieved-documents 3 \
  --node-retrieval \
  --edge-retrieval \
  --enable-document-grading \
  --enable-hallucination-check \
  --enable-quality-check
```

---

**Last Updated**: 2025-10-06  
**Version**: 0.1.0
