# Knowledge Graph Ingestion

This module provides functionality for ingesting documents into the knowledge graph, both via CLI and REST API.

## Overview

The ingestion system has been refactored into:
- **`service.py`**: Core ingestion service with reusable business logic
- **`models.py`**: Pydantic models for API requests/responses
- **`constructor.py`**: CLI script for command-line ingestion
- **API routes** (`src/api/routes/ingestion.py`): REST API endpoints

## Features

✅ **Document Ingestion**
- Upload JSON files directly via API
- Load JSON files from directory via CLI
- Process text, image captions, and table content
- Track processing statistics

✅ **Knowledge Graph Inspection**
- Get graph statistics (node/edge counts)
- Sample nodes and edges
- Filter by node type

✅ **Flexible Configuration**
- Concurrent processing with configurable coroutines
- Optional community building
- Clear existing data option

## Usage

### 1. CLI Usage

Ingest documents from command line:

```bash
# Basic ingestion
python -m src.ingestion.constructor \
    --data-dir /path/to/data

# Advanced options
python -m src.ingestion.constructor \
    --data-dir /path/to/data \
    --clear-existing-graphdb-data \
    --max-coroutines 3 \
    --add-communities
```

**CLI Arguments:**
- `--data-dir`: Directory containing JSON files (required)
- `--clear-existing-graphdb-data`: Clear existing graph data before ingestion
- `--max-coroutines`: Maximum concurrent coroutines (default: 1)
- `--add-communities`: Build communities after ingestion

### 2. API Usage

Start the API server:

```bash
python -m src.api.main
# or
uvicorn src.api.main:app --reload
```

#### Upload and Ingest Files

```bash
curl -X POST "http://localhost:8000/ingestion/ingest" \
  -F "files=@document1.json" \
  -F "files=@document2.json" \
  -F "clear_existing_data=false" \
  -F "max_coroutines=3" \
  -F "add_communities=false"
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully processed 5 documents",
  "total_documents": 5,
  "processed_documents": [
    {
      "document_id": "doc_001",
      "document_name": "document1.json",
      "total_chunks": 150,
      "successful_chunks": 148,
      "failed_chunks": 2,
      "text_chunks": 120,
      "image_chunks": 20,
      "table_chunks": 10
    }
  ],
  "total_chunks": 750,
  "successful_chunks": 742,
  "failed_chunks": 8,
  "success_rate": 98.93
}
```

#### Using Python requests

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
response = requests.post(
    'http://localhost:8000/ingestion/ingest',
    files=files,
    data=data
)
print(response.json())
```

#### Check Ingestion Status

```bash
curl "http://localhost:8000/ingestion/status"
```

**Response:**
```json
{
  "success": true,
  "message": "Knowledge graph is initialized and accessible",
  "graph_initialized": true,
  "statistics": {
    "total_nodes": 1250,
    "total_edges": 3420,
    "entity_nodes": 845,
    "episode_nodes": 350,
    "community_nodes": 55
  }
}
```

#### Get Graph Statistics

```bash
curl "http://localhost:8000/ingestion/statistics"
```

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_nodes": 1250,
    "total_edges": 3420,
    "entity_nodes": 845,
    "episode_nodes": 350,
    "community_nodes": 55
  }
}
```

#### Get Sample Nodes

```bash
# Get 10 nodes of any type
curl "http://localhost:8000/ingestion/nodes?limit=10"

# Get entity nodes only
curl "http://localhost:8000/ingestion/nodes?limit=20&node_type=Entity"

# Get episode nodes
curl "http://localhost:8000/ingestion/nodes?limit=5&node_type=Episode"
```

**Response:**
```json
{
  "success": true,
  "nodes": [
    {
      "id": "uuid-123",
      "name": "Durian Leaf Curl",
      "labels": ["Entity"],
      "properties": {
        "uuid": "uuid-123",
        "name": "Durian Leaf Curl",
        "created_at": "2025-10-06T10:30:00"
      }
    }
  ],
  "count": 10
}
```

#### Get Sample Edges

```bash
curl "http://localhost:8000/ingestion/edges?limit=10"
```

**Response:**
```json
{
  "success": true,
  "edges": [
    {
      "source": "Durian Leaf Curl",
      "target": "Phytoplasma",
      "relationship_type": "CAUSED_BY",
      "properties": {
        "created_at": "2025-10-06T10:30:00",
        "fact": "Durian leaf curl is caused by Phytoplasma"
      }
    }
  ],
  "count": 10
}
```

### 3. Programmatic Usage

Use the service directly in Python:

```python
from pathlib import Path
from src.ingestion.service import IngestionService

async def ingest_data():
    service = IngestionService()
    
    try:
        # Initialize client
        await service.initialize_client(
            clear_existing_graphdb_data=False,
            max_coroutines=3
        )
        
        # Load documents
        data_dir = Path("/path/to/data")
        json_paths = list(data_dir.glob("*.json"))
        documents = service.load_documents(json_paths)
        
        # Ingest documents
        result = await service.ingest_documents(
            documents=documents,
            add_communities=False
        )
        
        print(f"Processed {result['total_documents']} documents")
        print(f"Success rate: {result['success_rate']}%")
        
        # Get statistics
        stats = await service.get_graph_statistics()
        print(f"Total nodes: {stats['total_nodes']}")
        print(f"Total edges: {stats['total_edges']}")
        
    finally:
        await service.close_client()

# Run the function
import asyncio
asyncio.run(ingest_data())
```

## API Endpoints

All ingestion endpoints are under the `/ingestion` prefix:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingestion/ingest` | Upload and ingest JSON files |
| GET | `/ingestion/status` | Check ingestion system status |
| GET | `/ingestion/statistics` | Get detailed graph statistics |
| GET | `/ingestion/nodes` | Get sample nodes (with filters) |
| GET | `/ingestion/edges` | Get sample edges |

## Input Data Format

Documents should be in JSON format with the following structure:

```json
[
  {
    "id": "chunk_001",
    "document_id": "doc_001",
    "text": {
      "content": "Original text content",
      "text_translated": "Translated text (optional)"
    },
    "image": {
      "image_caption": "Caption for image (optional)"
    },
    "table": {
      "content": "Table content as text (optional)"
    }
  }
]
```

The service will process:
- **Text chunks**: From `text.text_translated` or `text.content`
- **Image chunks**: From `image.image_caption`
- **Table chunks**: From `table.content`

## Performance Tips

1. **Concurrent Processing**: Use `max_coroutines > 1` for faster processing
   ```json
   {"max_coroutines": 5}
   ```

2. **Community Building**: Build communities separately after all ingestion
   ```bash
   # First: ingest all documents without communities
   curl -X POST "http://localhost:8000/ingestion/ingest" \
     -d '{"data_dir": "/data", "add_communities": false}'
   
   # Then: build communities once
   curl -X POST "http://localhost:8000/ingestion/ingest" \
     -d '{"data_dir": "/empty", "add_communities": true}'
   ```

3. **Batch Processing**: Process large datasets in smaller batches

4. **Clear Data**: Only use `clear_existing_data=true` when starting fresh

## Error Handling

The service includes comprehensive error handling:
- Failed chunks are logged but don't stop processing
- Connection errors are caught and reported
- Invalid JSON files are skipped with warnings
- Statistics include success/failure counts

## Interactive API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive documentation where you can:
- Test all endpoints
- See request/response schemas
- View example payloads
- Execute requests directly

## Architecture

```
src/ingestion/
├── service.py          # Core business logic
├── models.py           # Pydantic models
├── constructor.py      # CLI script
└── README.md          # This file

src/api/routes/
└── ingestion.py       # REST API routes
```

**Key Classes:**
- `IngestionService`: Main service for document ingestion and graph operations
- `GraphitiClient`: Knowledge graph client wrapper
- API Models: Request/response validation with Pydantic

## Related Documentation

- Main API docs: http://localhost:8000/docs
- Workflow API: See `src/api/routes/workflow.py`
- GraphitiClient: See `src/core/graphiti.py`
- Settings: See `src/settings.py`
