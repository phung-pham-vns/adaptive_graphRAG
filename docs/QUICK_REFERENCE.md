# Adaptive RAG - Quick Reference Card

## 🚀 Quick Start

### Basic Request (All defaults)
```json
POST /workflow/run
{
    "question": "What causes durian leaf curl?"
}
```

### Custom Configuration
```json
{
    "question": "What causes durian leaf curl?",
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

## 🎛️ Configuration Options

### Retrieval Settings
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `n_retrieved_documents` | 3 | 1-10 | Number of KG documents |
| `n_web_searches` | 3 | 1-10 | Number of web results |
| `node_retrieval` | true | bool | Entity nodes |
| `edge_retrieval` | true | bool | Relationships |
| `episode_retrieval` | false | bool | Temporal sequences |
| `community_retrieval` | false | bool | Summaries |

### Quality Control
| Parameter | Default | Impact | Time Cost |
|-----------|---------|--------|-----------|
| `enable_retrieved_documents_grading` | true | Filter irrelevant docs | ~2s |
| `enable_hallucination_checking` | true | Prevent fabrication | ~1-2s |
| `enable_answer_quality_checking` | true | Ensure relevance | ~2-3s |

## ⚡ Performance Presets

### 🏆 Maximum Quality (Production)
```json
{
    "enable_retrieved_documents_grading": true,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": true
}
```
- **Time**: ~15-20s
- **Accuracy**: ⭐⭐⭐⭐⭐

### ⚖️ Balanced (Recommended)
```json
{
    "enable_retrieved_documents_grading": true,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": false
}
```
- **Time**: ~10-12s
- **Accuracy**: ⭐⭐⭐⭐

### 🚄 Maximum Speed (Development)
```json
{
    "enable_retrieved_documents_grading": false,
    "enable_hallucination_checking": false,
    "enable_answer_quality_checking": false
}
```
- **Time**: ~5-7s
- **Accuracy**: ⭐⭐

### 🎯 Fast + Accurate
```json
{
    "enable_retrieved_documents_grading": false,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": false
}
```
- **Time**: ~8-10s
- **Accuracy**: ⭐⭐⭐

## 🔄 Workflow Decision Points

### 1️⃣ Route Question
- **KG**: Domain-specific questions
- **Web**: Latest information
- **LLM**: Out-of-domain questions

### 2️⃣ Document Grading (optional)
- Filters irrelevant documents
- Retries: 3 max → web search fallback

### 3️⃣ Hallucination Check (optional)
- Verifies answer grounding
- Action: Regenerate if not grounded

### 4️⃣ Quality Check (optional)
- Validates answer relevance
- Retries: 3 max → best-effort answer

## 📊 Response Metadata

```json
{
    "metadata": {
        "total_processing_time": 12.456,
        "total_steps": 6,
        "total_citations": 5,
        "document_grading_enabled": true,
        "hallucination_checking_enabled": true,
        "answer_quality_checking_enabled": true,
        "node_retrieval": true,
        "edge_retrieval": true,
        "episode_retrieval": false,
        "community_retrieval": false
    }
}
```

## 🔍 Common Use Cases

### Production API
```json
{
    "n_retrieved_documents": 3,
    "n_web_searches": 3,
    "enable_retrieved_documents_grading": true,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": true
}
```

### Real-time Chat
```json
{
    "n_retrieved_documents": 2,
    "n_web_searches": 2,
    "enable_retrieved_documents_grading": false,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": false
}
```

### Research/Analysis
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

### Testing/Development
```json
{
    "n_retrieved_documents": 2,
    "enable_retrieved_documents_grading": false,
    "enable_hallucination_checking": false,
    "enable_answer_quality_checking": false
}
```

## 🛠️ Debugging Tips

### Slow Response?
1. Disable quality checks: `-5s`
2. Reduce document count: `-2s`
3. Disable document grading: `-2s`

### Inaccurate Answers?
1. Enable hallucination checking ✅
2. Enable document grading ✅
3. Increase document count 📈

### Irrelevant Answers?
1. Enable quality checking ✅
2. Enable document grading ✅
3. Adjust retrieval types 🎛️

## 📚 Full Documentation

- [Configuration Guide](./CONFIGURATION_GUIDE.md) - Detailed explanations
- [Workflow Diagram](./WORKFLOW_DIAGRAM.md) - Visual flowcharts
- [API Documentation](../README.md) - Complete API reference

## 🔗 API Endpoints

- **POST** `/workflow/run` - Full workflow with details
- **POST** `/workflow/run-simple` - Simple Q&A only
- **GET** `/health` - Health check

## ⚠️ Important Notes

1. **Retry Limits**: All retries max at 3 to prevent infinite loops
2. **Independent Checks**: Hallucination and quality checks work independently
3. **Fallbacks**: System has built-in fallbacks for robustness
4. **Performance**: Disable checks you don't need for speed

## 💡 Best Practice Tips

✅ **DO:**
- Use hallucination checking in production
- Enable document grading for better results
- Start with balanced config and adjust
- Monitor metadata for optimization

❌ **DON'T:**
- Disable all checks in production
- Set n_documents too high (>5)
- Ignore retry limits
- Skip monitoring performance


