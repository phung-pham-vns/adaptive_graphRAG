# Adaptive RAG Workflow Diagrams

## Overview

The Adaptive RAG system supports flexible configuration with independent control over:
1. **Document Grading**: Filter retrieved documents for relevance
2. **Hallucination Checking**: Verify answer is grounded in context
3. **Answer Quality Checking**: Ensure answer addresses the question

## Full Workflow (All Checks Enabled)

```mermaid
flowchart TD
    START([START]) --> RouteQuestion{Route Question}
    
    RouteQuestion -->|web_search| WebSearch[Web Search]
    RouteQuestion -->|kg_retrieval| KGRetrieval[Knowledge Graph Retrieval]
    RouteQuestion -->|llm_internal| AnswerGen[Answer Generation]
    
    WebSearch --> AnswerGen
    
    KGRetrieval --> DocGrading[Retrieved Documents Grading]
    DocGrading --> DecideGenerate{Decide to Generate}
    
    DecideGenerate -->|All docs irrelevant<br/>retry < 3| QueryTransform[Query Transformation]
    DecideGenerate -->|All docs irrelevant<br/>retry >= 3| WebSearch
    DecideGenerate -->|Has relevant docs| AnswerGen
    
    QueryTransform --> KGRetrieval
    
    AnswerGen --> HallucinationCheck{Hallucination Check<br/>Grounded?}
    
    HallucinationCheck -->|Not Grounded| AnswerGen
    HallucinationCheck -->|Grounded| QualityNode[Answer Quality Check Node]
    
    QualityNode --> QualityCheck{Answer Quality Check<br/>Addresses Question?}
    
    QualityCheck -->|Not Useful<br/>retry < 3| QueryTransform
    QualityCheck -->|Not Useful<br/>retry >= 3| END([END])
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

**Configuration:**
```json
{
    "enable_retrieved_documents_grading": true,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": true
}
```

## Hallucination Check Only

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
    HallucinationCheck -->|Grounded| END([END])
    
    style START fill:#90EE90
    style END fill:#FFB6C1
    style RouteQuestion fill:#FFE4B5
    style HallucinationCheck fill:#FFE4B5
    style WebSearch fill:#87CEEB
    style KGRetrieval fill:#87CEEB
    style AnswerGen fill:#F0E68C
```

**Configuration:**
```json
{
    "enable_retrieved_documents_grading": false,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": false
}
```

## Answer Quality Check Only

```mermaid
flowchart TD
    START([START]) --> RouteQuestion{Route Question}
    
    RouteQuestion -->|web_search| WebSearch[Web Search]
    RouteQuestion -->|kg_retrieval| KGRetrieval[Knowledge Graph Retrieval]
    RouteQuestion -->|llm_internal| AnswerGen[Answer Generation]
    
    WebSearch --> AnswerGen
    KGRetrieval --> AnswerGen
    
    AnswerGen --> QualityCheck{Answer Quality Check<br/>Addresses Question?}
    
    QualityCheck -->|Not Useful<br/>retry < 3| QueryTransform[Query Transformation]
    QualityCheck -->|Not Useful<br/>retry >= 3| END([END])
    QualityCheck -->|Useful| END
    
    QueryTransform --> KGRetrieval
    
    style START fill:#90EE90
    style END fill:#FFB6C1
    style RouteQuestion fill:#FFE4B5
    style QualityCheck fill:#FFE4B5
    style WebSearch fill:#87CEEB
    style KGRetrieval fill:#87CEEB
    style AnswerGen fill:#F0E68C
    style QueryTransform fill:#FFA07A
```

**Configuration:**
```json
{
    "enable_retrieved_documents_grading": false,
    "enable_hallucination_checking": false,
    "enable_answer_quality_checking": true
}
```

## Document Grading + Hallucination Check (Recommended)

```mermaid
flowchart TD
    START([START]) --> RouteQuestion{Route Question}
    
    RouteQuestion -->|web_search| WebSearch[Web Search]
    RouteQuestion -->|kg_retrieval| KGRetrieval[Knowledge Graph Retrieval]
    RouteQuestion -->|llm_internal| AnswerGen[Answer Generation]
    
    WebSearch --> AnswerGen
    
    KGRetrieval --> DocGrading[Retrieved Documents Grading]
    DocGrading --> DecideGenerate{Decide to Generate}
    
    DecideGenerate -->|All docs irrelevant<br/>retry < 3| QueryTransform[Query Transformation]
    DecideGenerate -->|All docs irrelevant<br/>retry >= 3| WebSearch
    DecideGenerate -->|Has relevant docs| AnswerGen
    
    QueryTransform --> KGRetrieval
    
    AnswerGen --> HallucinationCheck{Hallucination Check<br/>Grounded?}
    
    HallucinationCheck -->|Not Grounded| AnswerGen
    HallucinationCheck -->|Grounded| END([END])
    
    style START fill:#90EE90
    style END fill:#FFB6C1
    style RouteQuestion fill:#FFE4B5
    style DecideGenerate fill:#FFE4B5
    style HallucinationCheck fill:#FFE4B5
    style WebSearch fill:#87CEEB
    style KGRetrieval fill:#87CEEB
    style DocGrading fill:#DDA0DD
    style AnswerGen fill:#F0E68C
    style QueryTransform fill:#FFA07A
```

**Configuration:**
```json
{
    "enable_retrieved_documents_grading": true,
    "enable_hallucination_checking": true,
    "enable_answer_quality_checking": false
}
```

## Minimal Workflow (Maximum Speed)

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

**Configuration:**
```json
{
    "enable_retrieved_documents_grading": false,
    "enable_hallucination_checking": false,
    "enable_answer_quality_checking": false
}
```

## Legend

### Node Types
- 🟢 **Green (Light)**: Start/End nodes
- 🔵 **Blue (Light)**: Data retrieval nodes (Web Search, KG Retrieval)
- 🟡 **Yellow (Light)**: Processing nodes (Answer Generation)
- 🟠 **Orange (Light)**: Query Transformation
- 🟣 **Purple (Light)**: Grading/checking nodes
- 💠 **Diamond (Orange)**: Decision points

### Decision Points

#### 1. Route Question
Routes based on question type:
- **web_search**: Latest information needed
- **kg_retrieval**: Domain-specific knowledge needed  
- **llm_internal**: Out-of-domain questions

#### 2. Decide to Generate (Document Grading)
- Checks if any documents are relevant
- Falls back to web search after 3 retries
- Otherwise transforms query and retries

#### 3. Hallucination Check
- Verifies answer is grounded in context
- Regenerates if not grounded
- No retry limit (regenerates until grounded or timeout)

#### 4. Answer Quality Check
- Validates answer addresses question
- Transforms query if not useful (max 3 retries)
- Returns best-effort answer after max retries

## Performance Comparison

| Configuration | Processing Time | Accuracy | Use Case |
|--------------|----------------|----------|----------|
| All enabled | ~15-20s | ⭐⭐⭐⭐⭐ | Production |
| Doc + Hallucination | ~10-12s | ⭐⭐⭐⭐ | Recommended |
| Hallucination only | ~8-10s | ⭐⭐⭐ | Fast + Accurate |
| Quality only | ~10-12s | ⭐⭐⭐⭐ | Pre-filtered docs |
| Doc only | ~7-9s | ⭐⭐⭐ | Trust LLM |
| All disabled | ~5-7s | ⭐⭐ | Development |

## Configuration Matrix

| Doc Grading | Hallucination | Quality | Speed | Quality | Best For |
|-------------|---------------|---------|-------|---------|----------|
| ✅ | ✅ | ✅ | ⭐ | ⭐⭐⭐⭐⭐ | Production |
| ✅ | ✅ | ❌ | ⭐⭐ | ⭐⭐⭐⭐ | Recommended |
| ✅ | ❌ | ✅ | ⭐⭐ | ⭐⭐⭐⭐ | Quality focus |
| ✅ | ❌ | ❌ | ⭐⭐⭐ | ⭐⭐⭐ | Doc filtering |
| ❌ | ✅ | ✅ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Pre-filtered |
| ❌ | ✅ | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Fast accurate |
| ❌ | ❌ | ✅ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Relevance focus |
| ❌ | ❌ | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐ | Development |

## Knowledge Graph Retrieval Types

The system supports 4 types of KG retrieval (all can be toggled independently):

```mermaid
graph LR
    KG[Knowledge Graph] --> Node[Node Retrieval<br/>Entities]
    KG --> Edge[Edge Retrieval<br/>Relationships]
    KG --> Episode[Episode Retrieval<br/>Temporal Sequences]
    KG --> Community[Community Retrieval<br/>High-level Summaries]
    
    style KG fill:#87CEEB
    style Node fill:#90EE90
    style Edge fill:#90EE90
    style Episode fill:#FFE4B5
    style Community fill:#FFE4B5
```

**Defaults:**
- `node_retrieval`: **true** (always recommended)
- `edge_retrieval`: **true** (recommended for understanding relationships)
- `episode_retrieval`: **false** (enable for temporal/sequential info)
- `community_retrieval`: **false** (enable for high-level overviews)

## API Endpoints

### POST `/workflow/run`
Full workflow with detailed steps and citations.

### POST `/workflow/run-simple`
Simplified endpoint returning only question and answer.

Both endpoints accept the same request parameters and configuration options.
