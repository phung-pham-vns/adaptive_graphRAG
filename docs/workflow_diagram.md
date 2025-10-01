# Adaptive RAG Workflow - Mermaid Diagram

## Full Workflow (All Grading Enabled)

```mermaid
flowchart TD
    START([START]) --> RouteQuestion{Route Question}
    
    RouteQuestion -->|web_search| WebSearch[Web Search]
    RouteQuestion -->|kg_retrieval| KGRetrieval[Knowledge Graph Retrieval]
    RouteQuestion -->|llm_internal| AnswerGen[Answer Generation]
    
    WebSearch --> AnswerGen
    
    KGRetrieval --> DocGrading[Retrieved Documents Grading]
    DocGrading --> DecideGenerate{Decide to Generate}
    
    DecideGenerate -->|All docs irrelevant<br/>retry < max| QueryTransform[Query Transformation]
    DecideGenerate -->|All docs irrelevant<br/>retry >= max| WebSearch
    DecideGenerate -->|Has relevant docs| AnswerGen
    
    QueryTransform --> KGRetrieval
    
    AnswerGen --> HallucinationCheck{Hallucination Check<br/>Grounded?}
    
    HallucinationCheck -->|Not Grounded| AnswerGen
    HallucinationCheck -->|Grounded| QualityNode[Answer Quality Check Node]
    
    QualityNode --> QualityCheck{Answer Quality Check<br/>Addresses Question?}
    
    QualityCheck -->|Not Useful<br/>retry < max| QueryTransform
    QualityCheck -->|Not Useful<br/>retry >= max| END([END])
    QualityCheck -->|Useful| END
    
    style START fill:#90EE90
    style END fill:#FFB6C1
    style RouteQuestion fill:#FFE4B5
    style DecideGenerate fill:#FFE4B5
    style HallucinationCheck fill:#FFE4B5
    style QualityCheck fill:#FFE4B5
    style WebSearch fill:#87CEEB
    style KGRetrieval fill:#87CEEB
    style DocGrading fill:#DDA0DD
    style AnswerGen fill:#F0E68C
    style QueryTransform fill:#FFA07A
    style QualityNode fill:#DDA0DD
```

## Simplified Workflow (Document Grading Disabled, Generation Grading Enabled)

```mermaid
flowchart TD
    START([START]) --> RouteQuestion{Route Question}
    
    RouteQuestion -->|web_search| WebSearch[Web Search]
    RouteQuestion -->|kg_retrieval| KGRetrieval[Knowledge Graph Retrieval]
    RouteQuestion -->|llm_internal| AnswerGen[Answer Generation]
    
    WebSearch --> AnswerGen
    KGRetrieval --> AnswerGen
    
    AnswerGen --> HallucinationCheck{Hallucination Check<br/>Grounded?}
    
    HallucinationCheck -->|Not Grounded| AnswerGen
    HallucinationCheck -->|Grounded| QualityNode[Answer Quality Check Node]
    
    QualityNode --> QualityCheck{Answer Quality Check<br/>Addresses Question?}
    
    QualityCheck -->|Not Useful<br/>retry < max| QueryTransform[Query Transformation]
    QualityCheck -->|Not Useful<br/>retry >= max| END([END])
    QualityCheck -->|Useful| END
    
    QueryTransform --> KGRetrieval
    
    style START fill:#90EE90
    style END fill:#FFB6C1
    style RouteQuestion fill:#FFE4B5
    style HallucinationCheck fill:#FFE4B5
    style QualityCheck fill:#FFE4B5
    style WebSearch fill:#87CEEB
    style KGRetrieval fill:#87CEEB
    style AnswerGen fill:#F0E68C
    style QueryTransform fill:#FFA07A
    style QualityNode fill:#DDA0DD
```

## Minimal Workflow (All Grading Disabled)

```mermaid
flowchart TD
    START([START]) --> RouteQuestion{Route Question}
    
    RouteQuestion -->|web_search| WebSearch[Web Search]
    RouteQuestion -->|kg_retrieval| KGRetrieval[Knowledge Graph Retrieval]
    RouteQuestion -->|llm_internal| AnswerGen[Answer Generation]
    
    WebSearch --> AnswerGen
    KGRetrieval --> AnswerGen
    
    AnswerGen --> END([END])
    
    style START fill:#90EE90
    style END fill:#FFB6C1
    style RouteQuestion fill:#FFE4B5
    style WebSearch fill:#87CEEB
    style KGRetrieval fill:#87CEEB
    style AnswerGen fill:#F0E68C
```

## Legend

- 🟢 **Green (Light)**: Start/End nodes
- 🟡 **Yellow (Light)**: Processing nodes (Web Search, KG Retrieval, Answer Generation)
- 🟠 **Orange (Light)**: Query Transformation
- 🔵 **Blue (Light)**: Data retrieval nodes
- 🟣 **Purple (Light)**: Grading/checking nodes
- 💠 **Diamond**: Decision points

## Workflow Configuration Options

### API Request Parameters

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
    "enable_generation_grading": true
}
```

### Decision Points

1. **Route Question**: Routes to one of three paths based on question type:
   - `web_search`: Latest information needed
   - `kg_retrieval`: Domain-specific knowledge needed
   - `llm_internal`: Out-of-domain questions (no retrieval)

2. **Decide to Generate** (only when document grading enabled):
   - Checks if retrieved documents are relevant
   - Falls back to web search after max retries
   - Otherwise transforms query and retries

3. **Hallucination Check** (only when generation grading enabled):
   - Verifies answer is grounded in retrieved context
   - Regenerates if not grounded

4. **Answer Quality Check** (only when generation grading enabled):
   - Validates answer addresses the question
   - Transforms query if not useful (with retry limit)

### Retry Logic

- Maximum retries: 3 (configurable via `Defaults.MAX_RETRY_COUNT`)
- After max retries in document grading: fallback to web search
- After max retries in quality check: return best-effort answer

### Performance Trade-offs

| Configuration | Speed | Quality | Use Case |
|--------------|-------|---------|----------|
| All grading enabled | Slowest (~15-20s) | Highest | Production, accuracy critical |
| Document grading only | Medium (~10-12s) | High | Balanced performance |
| Generation grading only | Medium (~12-15s) | High | When documents are pre-filtered |
| All grading disabled | Fastest (~5-7s) | Lower | Development, speed critical |

