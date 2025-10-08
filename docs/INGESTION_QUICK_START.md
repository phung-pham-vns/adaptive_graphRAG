# Ingestion API - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites

- Python 3.10+
- Neo4j database running
- Environment configured (`.env` file)

### 1. Start the API Server

```bash
# Development mode with auto-reload
uvicorn src.api.main:app --reload

# Production mode
python -m src.api.main
```

Server runs at: **http://localhost:8000**

### 2. Check API Documentation

Open in browser:
- **Interactive Docs**: http://localhost:8000/docs
- **API Reference**: http://localhost:8000/redoc

### 3. Quick Health Check

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ingestion/status
```

## 📋 Common Tasks

### Ingest Documents from Directory

```bash
curl -X POST "http://localhost:8000/ingestion/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "data_dir": "/path/to/your/data",
    "max_coroutines": 3
  }'
```

### Upload Files Directly

```bash
curl -X POST "http://localhost:8000/ingestion/ingest-files" \
  -F "files=@document1.json" \
  -F "files=@document2.json" \
  -F "max_coroutines=3"
```

### Get Graph Statistics

```bash
curl "http://localhost:8000/ingestion/statistics"
```

### View Sample Nodes

```bash
# All nodes
curl "http://localhost:8000/ingestion/nodes?limit=10"

# Only entities
curl "http://localhost:8000/ingestion/nodes?limit=10&node_type=Entity"
```

### View Sample Edges

```bash
curl "http://localhost:8000/ingestion/edges?limit=10"
```

## 🔧 Using the CLI

### Basic Ingestion

```bash
python -m src.ingestion.constructor --data-dir /path/to/data
```

### With Options

```bash
python -m src.ingestion.constructor \
  --data-dir /path/to/data \
  --max-coroutines 3 \
  --clear-existing-graphdb-data \
  --add-communities
```

## 📝 JSON Data Format

Your JSON files should follow this structure:

```json
[
  {
    "id": "chunk_001",
    "document_id": "doc_001",
    "text": {
      "content": "Your text content here",
      "text_translated": "Optional translated text"
    },
    "image": {
      "image_caption": "Optional image caption"
    },
    "table": {
      "content": "Optional table content as text"
    }
  }
]
```

## 🐍 Python Code Example

```python
from pathlib import Path
from src.ingestion import IngestionService
import asyncio

async def main():
    service = IngestionService()
    
    # Initialize
    await service.initialize_client(max_coroutines=3)
    
    # Load documents
    data_dir = Path("/path/to/data")
    json_files = list(data_dir.glob("*.json"))
    documents = service.load_documents(json_files)
    
    # Ingest
    result = await service.ingest_documents(documents)
    print(f"Success rate: {result['success_rate']}%")
    
    # Get stats
    stats = await service.get_graph_statistics()
    print(f"Total nodes: {stats['total_nodes']}")
    print(f"Total edges: {stats['total_edges']}")
    
    # Cleanup
    await service.close_client()

asyncio.run(main())
```

## ⚙️ Configuration Options

### Environment Variables

Create a `.env` file:

```bash
# LLM Settings
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-pro
LLM_API_KEY=your_api_key

# Embedding Settings
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=embedding-001
EMBEDDING_API_KEY=your_api_key

# Graph Database
GRAPH_DB_PROVIDER=neo4j
GRAPH_DB_URL=bolt://localhost:7687
GRAPH_DB_USERNAME=neo4j
GRAPH_DB_PASSWORD=your_password
```

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data_dir` | string | - | Path to data directory (required) |
| `clear_existing_data` | boolean | false | Clear graph before ingestion |
| `max_coroutines` | integer | 1 | Concurrent processing (1-10) |
| `add_communities` | boolean | false | Build communities |

## 📊 Response Format

### Successful Ingestion

```json
{
  "success": true,
  "message": "Successfully processed 5 documents",
  "total_documents": 5,
  "total_chunks": 750,
  "successful_chunks": 742,
  "failed_chunks": 8,
  "success_rate": 98.93,
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
  ]
}
```

## 🎯 Performance Tips

### 1. Concurrent Processing
Use multiple coroutines for faster processing:
```json
{"max_coroutines": 5}
```

### 2. Batch Large Datasets
Process in smaller batches:
```bash
# Batch 1
curl -X POST ".../ingest" -d '{"data_dir": "/data/batch1"}'

# Batch 2
curl -X POST ".../ingest" -d '{"data_dir": "/data/batch2"}'
```

### 3. Separate Community Building
Build communities after all ingestion:
```bash
# 1. Ingest all documents
curl -X POST ".../ingest" -d '{"data_dir": "/data", "add_communities": false}'

# 2. Build communities once
# (Can be done via GraphitiClient directly or in next ingestion with empty dir)
```

### 4. Clear Data Carefully
Only use `clear_existing_data: true` when starting fresh:
```json
{"data_dir": "/data", "clear_existing_data": true}
```

## 🔍 Troubleshooting

### Connection Refused
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Check API server is running
curl http://localhost:8000/health
```

### No Files Found
```bash
# Verify directory path
ls /path/to/data/*.json

# Check absolute vs relative paths
pwd
```

### Import Errors
```bash
# Install dependencies
pip install -r requirements.txt

# Check Python path
python -c "import src.ingestion; print('OK')"
```

### Slow Processing
- Increase `max_coroutines` (e.g., 5)
- Check Neo4j performance
- Monitor network latency
- Verify LLM API rate limits

## 📚 Next Steps

1. **Read Full Documentation**
   - [Ingestion README](../src/ingestion/README.md)
   - [Architecture Guide](./INGESTION_ARCHITECTURE.md)
   - [API Summary](../INGESTION_API_SUMMARY.md)

2. **Explore API**
   - Visit http://localhost:8000/docs
   - Try different endpoints
   - Inspect graph statistics

3. **Customize**
   - Modify `IngestionService` for your needs
   - Add custom processing logic
   - Create new endpoints

4. **Monitor**
   - Check logs for errors
   - Track success rates
   - Monitor graph growth

## 🆘 Getting Help

- **API Docs**: http://localhost:8000/docs
- **Check Logs**: Watch console output for errors
- **GitHub Issues**: Report bugs or request features
- **Code Examples**: See `src/ingestion/README.md`

## ✅ Checklist

Before ingestion:
- [ ] Neo4j running and accessible
- [ ] Environment variables configured
- [ ] API server started
- [ ] Data directory contains valid JSON files
- [ ] Sufficient disk space available

After ingestion:
- [ ] Check success rate in response
- [ ] Verify graph statistics
- [ ] Sample nodes/edges to verify data
- [ ] Review logs for any warnings

---

**Ready to start?** Run this command:

```bash
# Start API server
uvicorn src.api.main:app --reload

# In another terminal, test ingestion
curl -X POST "http://localhost:8000/ingestion/ingest" \
  -H "Content-Type: application/json" \
  -d '{"data_dir": "/path/to/your/data"}'
```

🎉 You're all set!
