# Ingestion API Architecture

## Overview

This document describes the architecture of the refactored ingestion system.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  • CLI (constructor.py)                                         │
│  • REST API Clients (curl, Python requests, etc.)               │
│  • Web UI (Swagger, ReDoc)                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API Layer (FastAPI)                       │
├─────────────────────────────────────────────────────────────────┤
│  src/api/routes/ingestion.py                                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  POST   /ingestion/ingest          - Directory ingest   │  │
│  │  POST   /ingestion/ingest-files    - File upload        │  │
│  │  GET    /ingestion/status          - System status      │  │
│  │  GET    /ingestion/statistics      - Graph stats        │  │
│  │  GET    /ingestion/nodes           - Sample nodes       │  │
│  │  GET    /ingestion/edges           - Sample edges       │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Validation Layer (Pydantic)                  │
├─────────────────────────────────────────────────────────────────┤
│  src/ingestion/models.py                                       │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  • IngestionRequest                                     │  │
│  │  • IngestionResponse                                    │  │
│  │  • GraphStatistics                                      │  │
│  │  • NodeData / EdgeData                                  │  │
│  │  • DocumentProcessingResult                             │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Service Layer                               │
├─────────────────────────────────────────────────────────────────┤
│  src/ingestion/service.py - IngestionService                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Core Methods:                                          │  │
│  │  • initialize_client()     - Setup Graphiti client      │  │
│  │  • close_client()          - Cleanup connections        │  │
│  │  • load_documents()        - Parse JSON files           │  │
│  │  • ingest_documents()      - Process & ingest chunks    │  │
│  │                                                           │  │
│  │  Inspection Methods:                                     │  │
│  │  • get_graph_statistics()  - Get node/edge counts       │  │
│  │  • get_sample_nodes()      - Retrieve sample nodes      │  │
│  │  • get_sample_edges()      - Retrieve sample edges      │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Graphiti Client Wrapper                        │
├─────────────────────────────────────────────────────────────────┤
│  src/core/graphiti.py - GraphitiClient                         │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  • create_client()         - Initialize Graphiti        │  │
│  │  • LLM Client (Gemini/OpenAI)                           │  │
│  │  • Embedder (Gemini/OpenAI)                             │  │
│  │  • Reranker (Gemini/OpenAI)                             │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Graphiti Core Library                        │
├─────────────────────────────────────────────────────────────────┤
│  graphiti_core                                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  • add_episode()           - Add text episodes          │  │
│  │  • search()                - Search graph               │  │
│  │  • build_communities()     - Community detection        │  │
│  │  • build_indices()         - DB indices                 │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Graph Database (Neo4j)                      │
├─────────────────────────────────────────────────────────────────┤
│  Neo4j Instance                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Nodes:                                                  │  │
│  │  • Entity nodes      - Named entities from text         │  │
│  │  • Episode nodes     - Text chunks/episodes             │  │
│  │  • Community nodes   - Detected communities             │  │
│  │                                                           │  │
│  │  Relationships:                                          │  │
│  │  • Entity -> Entity  - Relations between entities       │  │
│  │  • Episode -> Entity - Episodes mentioning entities     │  │
│  │  • Community -> *    - Community memberships            │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Document Ingestion Flow

```
┌─────────────┐
│  JSON Files │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  1. load_documents()                        │
│     • Read JSON files                       │
│     • Parse document structure              │
│     • Extract text/image/table chunks       │
│     • Create document objects               │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  2. ingest_documents()                      │
│     For each document:                      │
│       For each chunk:                       │
│         • Create episode                    │
│         • Extract entities                  │
│         • Build relationships               │
│         • Update embeddings                 │
│         • Track success/failure             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  3. graphiti.add_episode()                  │
│     • Parse chunk text                      │
│     • Extract entities (LLM)                │
│     • Generate embeddings                   │
│     • Create/update nodes                   │
│     • Create/update edges                   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  4. Neo4j Storage                           │
│     • Store Entity nodes                    │
│     • Store Episode nodes                   │
│     • Store relationships                   │
│     • Update indices                        │
└─────────────────────────────────────────────┘
```

### 2. Graph Inspection Flow

```
┌─────────────────────────────────────────────┐
│  API Request                                │
│  GET /ingestion/statistics                  │
│  GET /ingestion/nodes?limit=10&type=Entity  │
│  GET /ingestion/edges?limit=10              │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  IngestionService                           │
│  • get_graph_statistics()                   │
│  • get_sample_nodes()                       │
│  • get_sample_edges()                       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Neo4j Cypher Queries                       │
│  • MATCH (n) RETURN count(n)                │
│  • MATCH (n:Entity) RETURN n LIMIT 10       │
│  • MATCH (a)-[r]->(b) RETURN a,r,b LIMIT 10 │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Format & Return Response                   │
│  • GraphStatisticsResponse                  │
│  • NodesResponse                            │
│  • EdgesResponse                            │
└─────────────────────────────────────────────┘
```

## Component Responsibilities

### API Layer (`src/api/routes/ingestion.py`)
- HTTP request handling
- Input validation via Pydantic
- Response formatting
- Error handling and HTTP status codes
- Temporary file management (for uploads)
- Service instance management

### Service Layer (`src/ingestion/service.py`)
- Core business logic
- Document parsing and processing
- Graphiti client lifecycle management
- Progress tracking
- Statistics calculation
- Neo4j query execution
- Error handling and logging

### Model Layer (`src/ingestion/models.py`)
- Request/response schemas
- Data validation
- Type safety
- API documentation (via Pydantic)

### Graphiti Client (`src/core/graphiti.py`)
- Provider abstraction (Gemini/OpenAI)
- LLM client configuration
- Embedder configuration
- Reranker configuration
- Neo4j driver setup

## Key Design Patterns

### 1. Service Pattern
- `IngestionService` encapsulates business logic
- Reusable across API and CLI
- Single responsibility principle

### 2. Repository Pattern
- `GraphitiClient` abstracts database operations
- Clean separation of concerns
- Easy to mock for testing

### 3. Facade Pattern
- API routes provide simplified interface
- Hide complexity of service operations
- Consistent error handling

### 4. Factory Pattern
- `GraphitiClient` creates appropriate clients based on config
- Runtime provider selection (Gemini vs OpenAI)

## Configuration Flow

```
┌─────────────────────────────────────────────┐
│  .env file                                  │
│  • LLM_PROVIDER=gemini                      │
│  • EMBEDDING_PROVIDER=gemini                │
│  • GRAPH_DB_URL=bolt://localhost:7687       │
│  • etc.                                     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  src/settings.py                            │
│  • ProjectSettings (Pydantic)               │
│  • Load from .env                           │
│  • Type validation                          │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  GraphitiClient                             │
│  • Select LLM based on settings             │
│  • Select embedder based on settings        │
│  • Configure Neo4j connection               │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  IngestionService                           │
│  • Use configured GraphitiClient            │
│  • Execute operations                       │
└─────────────────────────────────────────────┘
```

## Error Handling Strategy

### API Layer
```python
try:
    result = await service.ingest_documents(...)
    return IngestionResponse(success=True, ...)
except HTTPException:
    raise  # Re-raise FastAPI exceptions
except Exception as e:
    logger.exception("Error during ingestion")
    raise HTTPException(
        status_code=500,
        detail=f"Ingestion failed: {str(e)}"
    )
finally:
    await service.close_client()  # Always cleanup
```

### Service Layer
```python
for chunk in chunks:
    try:
        await graphiti.add_episode(...)
        successful_chunks += 1
    except Exception as e:
        logger.exception(f"Failed chunk {chunk['id']}")
        failed_chunks += 1
        continue  # Don't stop on single chunk failure
```

## Security Considerations

### Current Implementation
- Input validation via Pydantic
- Path traversal prevention (Path object validation)
- File type validation (JSON only)
- Temporary file cleanup
- SQL injection prevention (parameterized queries)

### Future Enhancements
- Authentication/Authorization
- Rate limiting
- Input sanitization
- File size limits
- Request throttling
- API key management

## Performance Optimization

### Concurrent Processing
```python
# Use max_coroutines for parallel processing
await service.initialize_client(max_coroutines=5)
```

### Batch Operations
- Process documents in batches
- Build communities after all ingestion
- Reuse client connections

### Resource Management
- Proper connection pooling
- Client lifecycle management
- Cleanup in finally blocks

## Testing Strategy

### Unit Tests
- Test service methods in isolation
- Mock GraphitiClient
- Test edge cases and error handling

### Integration Tests
- Test API endpoints
- Test with real Neo4j instance
- Verify end-to-end flow

### Example Test
```python
async def test_ingest_documents():
    service = IngestionService()
    await service.initialize_client()
    
    documents = [{"id": "test", "chunks": [...]}]
    result = await service.ingest_documents(documents)
    
    assert result["success_rate"] > 95.0
    await service.close_client()
```

## Monitoring and Observability

### Logging
- Structured logging throughout
- Log levels: INFO, WARNING, ERROR
- Context-rich error messages

### Metrics (Future)
- Ingestion rate
- Success/failure rates
- Processing time
- Graph size over time

### Health Checks
- `/ingestion/status` endpoint
- Database connectivity check
- Graph statistics

## Extension Points

The architecture supports easy extension:

1. **New Graph Operations**: Add methods to `IngestionService`
2. **New Endpoints**: Add routes to `src/api/routes/ingestion.py`
3. **New Providers**: Extend `GraphitiClient` configuration
4. **Custom Processing**: Override `ingest_documents()` method
5. **Progress Tracking**: Use `progress_callback` parameter

## Related Documentation

- [Ingestion README](../src/ingestion/README.md)
- [API Summary](../INGESTION_API_SUMMARY.md)
- [Main API Docs](http://localhost:8000/docs)
