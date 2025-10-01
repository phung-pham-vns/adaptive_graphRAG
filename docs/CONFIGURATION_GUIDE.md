# Adaptive RAG Configuration Guide

This guide explains all configuration options available in the Adaptive RAG system and their impact on performance and quality.

## Table of Contents
1. [API Request Parameters](#api-request-parameters)
2. [Configuration Options](#configuration-options)
3. [Workflow Combinations](#workflow-combinations)
4. [Performance vs Quality Trade-offs](#performance-vs-quality-trade-offs)
5. [Best Practices](#best-practices)

## API Request Parameters

### Complete API Request Structure

```json
{
    "question": "Your question here",
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

## Configuration Options

### 1. Retrieval Parameters

#### `n_retrieved_documents` (int, default: 3)
- **Range**: 1-10
- **Description**: Number of documents to retrieve from the knowledge graph
- **Impact**: More documents = more context but slower retrieval

#### `n_web_searches` (int, default: 3)
- **Range**: 1-10
- **Description**: Number of web search results to fetch
- **Impact**: More results = broader coverage but slower retrieval

### 2. Knowledge Graph Retrieval Types

#### `node_retrieval` (bool, default: true)
- **Description**: Retrieve individual entity nodes from the knowledge graph
- **When to use**: Always enabled for basic entity information

#### `edge_retrieval` (bool, default: true)
- **Description**: Retrieve relationships between entities
- **When to use**: When you need to understand connections between entities

#### `episode_retrieval` (bool, default: false)
- **Description**: Retrieve episodic memory/temporal sequences
- **When to use**: For time-series or sequential information

#### `community_retrieval` (bool, default: false)
- **Description**: Retrieve community-level summaries
- **When to use**: For high-level overviews and summaries

### 3. Quality Control Options

#### `enable_retrieved_documents_grading` (bool, default: true)
- **Description**: Grade retrieved documents for relevance before generating answer
- **Impact**: 
  - ✅ Filters out irrelevant documents
  - ✅ Improves answer quality
  - ❌ Adds ~2 seconds to processing time
- **Behavior when disabled**: Uses all retrieved documents without filtering

#### `enable_hallucination_checking` (bool, default: true)
- **Description**: Verify that generated answer is grounded in the retrieved context
- **Impact**:
  - ✅ Prevents hallucinations
  - ✅ Ensures factual accuracy
  - ❌ Adds ~1-2 seconds to processing time
- **Behavior when disabled**: Accepts first generated answer without grounding check
- **Fallback**: If answer is not grounded, regenerates answer

#### `enable_answer_quality_checking` (bool, default: true)
- **Description**: Verify that generated answer actually addresses the question
- **Impact**:
  - ✅ Ensures answer relevance
  - ✅ Triggers query transformation if needed
  - ❌ Adds ~2-3 seconds to processing time
- **Behavior when disabled**: Accepts answer even if it doesn't fully address question
- **Fallback**: If answer doesn't address question, transforms query and retries (up to 3 times)

## Workflow Combinations

### 1. Maximum Quality (Default)
```json
{
    "enable_retrieved_documents_grading": true,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": true
}
```
- **Processing Time**: ~15-20 seconds
- **Use Case**: Production, accuracy-critical applications
- **Workflow**: Retrieval → Document Grading → Answer → Hallucination Check → Quality Check

### 2. Balanced (Recommended for Most Cases)
```json
{
    "enable_retrieved_documents_grading": true,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": false
}
```
- **Processing Time**: ~10-12 seconds
- **Use Case**: General purpose with good accuracy
- **Workflow**: Retrieval → Document Grading → Answer → Hallucination Check

### 3. Fast with Grounding
```json
{
    "enable_retrieved_documents_grading": false,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": false
}
```
- **Processing Time**: ~8-10 seconds
- **Use Case**: Speed important but need factual accuracy
- **Workflow**: Retrieval → Answer → Hallucination Check

### 4. Maximum Speed
```json
{
    "enable_retrieved_documents_grading": false,
    "enable_hallucination_checking": false,
    "enable_answer_quality_checking": false
}
```
- **Processing Time**: ~5-7 seconds
- **Use Case**: Development, testing, speed-critical applications
- **Workflow**: Retrieval → Answer (direct)

### 5. Quality-Focused (No Document Filtering)
```json
{
    "enable_retrieved_documents_grading": false,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": true
}
```
- **Processing Time**: ~12-15 seconds
- **Use Case**: When documents are pre-filtered or high quality
- **Workflow**: Retrieval → Answer → Hallucination Check → Quality Check

### 6. Document Filtering Only
```json
{
    "enable_retrieved_documents_grading": true,
    "enable_hallucination_checking": false,
    "enable_answer_quality_checking": false
}
```
- **Processing Time**: ~7-9 seconds
- **Use Case**: When you trust the LLM but want relevant documents
- **Workflow**: Retrieval → Document Grading → Answer

## Performance vs Quality Trade-offs

| Configuration | Speed | Accuracy | Relevance | Use Case |
|--------------|-------|----------|-----------|----------|
| All enabled | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Production |
| Doc + Hallucination | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Recommended |
| Hallucination only | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Fast + Accurate |
| All disabled | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | Development |

## Best Practices

### Production Environments
```json
{
    "n_retrieved_documents": 3,
    "n_web_searches": 3,
    "node_retrieval": true,
    "edge_retrieval": true,
    "episode_retrieval": false,
    "community_retrieval": false,
    "enable_retrieved_documents_grading": true,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": true
}
```

### Development/Testing
```json
{
    "n_retrieved_documents": 2,
    "n_web_searches": 2,
    "node_retrieval": true,
    "edge_retrieval": false,
    "episode_retrieval": false,
    "community_retrieval": false,
    "enable_retrieved_documents_grading": false,
    "enable_hallucination_checking": false,
    "enable_answer_quality_checking": false
}
```

### Real-time Applications (Speed Critical)
```json
{
    "n_retrieved_documents": 2,
    "n_web_searches": 2,
    "node_retrieval": true,
    "edge_retrieval": true,
    "episode_retrieval": false,
    "community_retrieval": false,
    "enable_retrieved_documents_grading": false,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": false
}
```

### Research/Analysis (Quality Critical)
```json
{
    "n_retrieved_documents": 5,
    "n_web_searches": 5,
    "node_retrieval": true,
    "edge_retrieval": true,
    "episode_retrieval": true,
    "community_retrieval": true,
    "enable_retrieved_documents_grading": true,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": true
}
```

## Understanding the Workflow

### Question Routing
The first step routes questions to:
1. **Knowledge Graph**: Domain-specific questions (durian pests/diseases)
2. **Web Search**: Latest information or trending topics
3. **LLM Internal**: Out-of-domain questions (no retrieval needed)

### Document Grading (if enabled)
- Grades each retrieved document for relevance
- Filters out non-relevant documents
- If all documents irrelevant: transforms query and retries (up to 3 times)
- After max retries: falls back to web search

### Hallucination Checking (if enabled)
- Verifies answer is grounded in retrieved context
- If not grounded: regenerates answer
- Prevents fabricated information

### Answer Quality Checking (if enabled)
- Validates answer addresses the original question
- If doesn't address question: transforms query and retries (up to 3 times)
- After max retries: returns best-effort answer

## Retry Limits

All retry mechanisms have a maximum limit of **3 retries** to prevent infinite loops:
- Document grading retries → Falls back to web search
- Answer quality retries → Returns best-effort answer

## Environment Variables (Optional)

You can set defaults in your environment:
```bash
export ADAPTIVE_RAG_N_DOCUMENTS=3
export ADAPTIVE_RAG_N_WEB_SEARCHES=3
export ADAPTIVE_RAG_ENABLE_DOCUMENT_GRADING=true
export ADAPTIVE_RAG_ENABLE_HALLUCINATION_CHECK=true
export ADAPTIVE_RAG_ENABLE_QUALITY_CHECK=true
```

## Monitoring and Debugging

The API response includes metadata with timing information:
```json
{
    "metadata": {
        "total_processing_time": 12.456,
        "average_step_time": 2.076,
        "total_steps": 6,
        "document_grading_enabled": true,
        "hallucination_checking_enabled": true,
        "answer_quality_checking_enabled": true,
        "total_citations": 5
    }
}
```

Use this to:
- Monitor performance
- Identify bottlenecks
- Tune configuration based on actual usage patterns


