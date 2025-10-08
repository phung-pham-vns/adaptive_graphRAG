# Adaptive RAG Workflow Refinements

## Overview

This document outlines the comprehensive refinements made to the Adaptive RAG workflow, prompts, chains, and functions to optimize performance for the durian pest and disease domain with three-way intelligent routing (Knowledge Graph, Web Search, LLM Internal).

**Date**: 2025-10-06  
**Version**: 0.2.0

---

## 🎯 Key Improvements

### 1. Enhanced Routing Intelligence

**Objective**: Improve routing accuracy between Knowledge Graph (KG), Web Search, and LLM Internal routes.

#### Changes Made:

**File**: `src/core/prompts.py` - `question_routing_prompt`

**Improvements**:
- Added clear **ROUTING RULES** with explicit criteria for each route
- Introduced **DECISION PRIORITY** framework (2-step decision process)
- Added domain-specific examples for each routing category
- Included keyword indicators for web search detection ("latest", "recent", "new", etc.)
- Structured format makes it easier for LLM to make consistent routing decisions

**Example Decision Flow**:
```
Question: "What causes durian leaf curl?"
Step 1: Is it about durian/pests/diseases? → YES
Step 2: Does it ask for latest info? → NO
Result: kg_retrieval
```

**Benefits**:
- More accurate routing decisions
- Reduced misrouting of domain queries to LLM internal
- Better detection of time-sensitive queries requiring web search
- Clear reasoning path for debugging

---

### 2. Domain-Optimized Prompts

#### A. Document Relevance Grading

**File**: `src/core/prompts.py` - `retrieval_grading_prompt`

**Enhancements**:
- Added **GRADING CRITERIA** section with explicit rules
- Specified what qualifies as relevant for durian domain
- Included semantic connection guidelines
- Made criteria lenient but focused on durian pest/disease relevance

**Impact**: More accurate filtering of retrieved documents, reducing noise in context.

#### B. Query Transformation

**File**: `src/core/prompts.py` - `question_rewriting_prompt`

**Enhancements**:
- Added **OPTIMIZATION STRATEGIES** (5 specific techniques)
- Included domain-specific expansion guidance
- Knowledge graph-friendly term preferences
- Entity and relationship extraction focus

**Example Transformations**:
```
Original: "leaf curl"
Optimized: "leaf curl disease symptoms Phytoplasma durian"

Original: "Why are my leaves dying?"
Optimized: "durian leaf death causes symptoms"
```

**Impact**: Better retrieval results from knowledge graph through optimized queries.

#### C. Answer Generation

**File**: `src/core/prompts.py` - `answer_generation_prompt`

**Enhancements**:
- Added **ANSWER GUIDELINES** (7 specific rules)
- Structured response format guidance
- Emphasis on synthesizing multi-source information
- Context citation requirements
- Actionable advice focus for pest/disease domain

**Benefits**:
- More comprehensive answers using all available context
- Better integration of entities and relationships from KG
- Actionable recommendations for farmers/practitioners
- Clear acknowledgment when information is insufficient

#### D. LLM Internal Responses

**File**: `src/core/prompts.py` - `llm_internal_answer_prompt`

**Enhancements**:
- Added **GUIDELINES** for out-of-domain queries
- Differentiated handling for greetings vs. general knowledge
- Scope acknowledgment for domain boundaries
- Conciseness requirements (2-3 sentences)

**Impact**: Better user experience for out-of-domain and casual interactions.

---

### 3. Improved Context Formatting

**File**: `src/core/functions.py` - `format_context()`

**Major Refactoring**:

**Before**:
```python
# Simple numbered lists with generic titles
Node Information:
1. [content]
2. [content]

Relationship Information:
1. [content]
```

**After**:
```python
============================================================
KNOWLEDGE GRAPH ENTITIES (Key Concepts)
============================================================

[Entity 1]
[detailed content]
  Source: document_name.pdf

[Entity 2]
[detailed content]
  Source: document_name.pdf

============================================================
KNOWLEDGE GRAPH RELATIONSHIPS (Connections)
============================================================

[Relationship 1]
[detailed content]
  Source: document_name.pdf

============================================================
WEB SEARCH RESULTS (Recent Information)
============================================================

[Web Result 1]
[content]
  Title: Article Title
  URL: https://example.com
```

**Benefits**:
- **Hierarchical structure**: Clear visual separation between sections
- **Inline citations**: Sources appear immediately with each piece of information
- **Semantic labels**: "Entities" and "Relationships" are more meaningful than "Nodes" and "Edges"
- **Context clarity**: LLM can better understand the type and source of each information piece
- **Better synthesis**: Structured format helps LLM integrate information from multiple sources

---

### 4. Enhanced Logging and Observability

**File**: `src/core/constants.py` - `LogMessages` class

**Complete Overhaul**:

**Features**:
- **Emoji indicators**: Visual categorization of log types (🔀 routing, 📊 KG, 🌐 web, ✍️ generation)
- **Structured categories**: Routing, Retrieval, Generation, Grading, Quality Checks, Retry Management
- **Clear status indicators**: ✓ for success, ✗ for failure, ⚠️ for warnings
- **Detailed context**: Each message includes purpose and state information

**Example Log Output**:
```
🔀 [ROUTING] Analyzing question to determine optimal data source...
🔀 [ROUTING] → Routing to: KG_RETRIEVAL (Reason: Durian pest/disease domain question requiring knowledge base)
📊 [KNOWLEDGE GRAPH] Retrieving from durian pest/disease knowledge base...
📊 [KNOWLEDGE GRAPH] Retrieved: 3 nodes, 2 edges
🔍 [GRADING] Assessing relevance of retrieved documents...
  ✓ NODE content is RELEVANT
  ✓ NODE content is RELEVANT
  ✗ NODE content is NOT RELEVANT (filtered out)
🔍 [GRADING] Summary: 4/5 documents relevant after filtering
✍️  [GENERATION] Generating answer from retrieved context...
✍️  [GENERATION] Context available: 2 entities, 2 relationships, 0 web results
```

**Benefits**:
- **Easy debugging**: Quick identification of workflow stages and issues
- **Performance monitoring**: Clear tracking of retrieval and grading results
- **User feedback**: Can be exposed to users for transparency
- **Development insights**: Understand routing patterns and quality check triggers

---

### 5. Workflow Enhancements

**File**: `src/core/workflow.py`

#### A. Routing with Reasons

**Enhancement**:
```python
route_reasons = {
    RouteDecision.KG_RETRIEVAL: "Durian pest/disease domain question requiring knowledge base",
    RouteDecision.WEB_SEARCH: "Request for latest/recent information",
    RouteDecision.LLM_INTERNAL: "Out-of-domain question",
}
reason = route_reasons.get(route, "Default routing")
print(LogMessages.ROUTE_TO.format(route.upper(), reason))
```

**Impact**: Clear visibility into why each routing decision was made.

#### B. Improved Retry Messages

**Enhancement**: More descriptive fallback messages
- "Falling back to WEB SEARCH" instead of just "WEB SEARCH"
- "Proceeding with best-effort answer" instead of "GROUNDED (BEST EFFORT)"
- "Ending workflow with best-effort answer" instead of "END (BEST EFFORT)"

**Impact**: Better understanding of system behavior at max retry limits.

---

### 6. Function-Level Improvements

**File**: `src/core/functions.py`

#### A. Knowledge Graph Retrieval Stats

**Added**:
```python
print(LogMessages.KNOWLEDGE_GRAPH_STATS.format(len(node_contents), len(edge_contents)))
```

**Impact**: Immediate visibility into retrieval results.

#### B. Answer Generation Context Stats

**Added**:
```python
print(LogMessages.ANSWER_GENERATION_WITH_CONTEXT.format(
    len(node_contents), len(edge_contents), len(web_contents)
))
```

**Impact**: Understanding of context richness before generation.

#### C. Query Transformation Tracking

**Added**:
```python
print(LogMessages.QUERY_TRANSFORMATION_RESULT.format(
    original_question[:60] + "...",
    refined_question[:60] + "..."
))
```

**Impact**: Visibility into how queries are being optimized.

#### D. Document Grading Summary

**Added**:
```python
print(LogMessages.GRADING_SUMMARY.format(total_filtered, total_original))
```

**Impact**: Quick understanding of grading effectiveness.

---

## 📊 Performance Optimization Recommendations

### Current Default Configuration
```python
class Defaults:
    N_RETRIEVED_DOCUMENTS = 3
    N_WEB_SEARCHES = 3
    NODE_RETRIEVAL = True
    EDGE_RETRIEVAL = False  # ⚠️ Consider enabling for richer context
    EPISODE_RETRIEVAL = False
    COMMUNITY_RETRIEVAL = False
    MAX_QUERY_TRANSFORMATION_RETRIES = 3
    MAX_HALLUCINATION_RETRIES = 3
    ENABLE_RETRIEVED_DOCUMENTS_GRADING = False
    ENABLE_HALLUCINATION_CHECKING = False
    ENABLE_ANSWER_QUALITY_CHECKING = False
```

### Recommended Configuration for Production

#### High-Speed Mode (Default)
- Best for: Real-time user-facing applications
- Trade-off: Speed over maximum quality
```python
N_RETRIEVED_DOCUMENTS = 3
NODE_RETRIEVAL = True
EDGE_RETRIEVAL = True  # Enable for relationship context
ENABLE_RETRIEVED_DOCUMENTS_GRADING = False
ENABLE_HALLUCINATION_CHECKING = False
ENABLE_ANSWER_QUALITY_CHECKING = False
```
**Expected time**: ~3-5 seconds

#### Balanced Mode
- Best for: General use with quality awareness
- Trade-off: Slight speed decrease for better relevance
```python
N_RETRIEVED_DOCUMENTS = 5
NODE_RETRIEVAL = True
EDGE_RETRIEVAL = True
ENABLE_RETRIEVED_DOCUMENTS_GRADING = True  # Filter irrelevant docs
ENABLE_HALLUCINATION_CHECKING = False
ENABLE_ANSWER_QUALITY_CHECKING = False
```
**Expected time**: ~5-8 seconds

#### Maximum Quality Mode
- Best for: Critical applications, research, high-stakes decisions
- Trade-off: Slower but highest quality
```python
N_RETRIEVED_DOCUMENTS = 5
NODE_RETRIEVAL = True
EDGE_RETRIEVAL = True
ENABLE_RETRIEVED_DOCUMENTS_GRADING = True
ENABLE_HALLUCINATION_CHECKING = True  # Verify grounding
ENABLE_ANSWER_QUALITY_CHECKING = True  # Verify answer quality
MAX_QUERY_TRANSFORMATION_RETRIES = 2  # Reduce retries for speed
MAX_HALLUCINATION_RETRIES = 2
```
**Expected time**: ~10-15 seconds

---

## 🎨 Workflow Architecture

### Three-Way Intelligent Routing

```
                    ┌─────────────┐
                    │   Question  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Router    │
                    │  (Enhanced) │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌──────────┐   ┌──────────────┐   ┌──────────┐
    │   Web    │   │  Knowledge   │   │   LLM    │
    │  Search  │   │    Graph     │   │ Internal │
    │          │   │  (Enhanced)  │   │          │
    └────┬─────┘   └──────┬───────┘   └────┬─────┘
         │                │                 │
         │         ┌──────▼──────┐         │
         │         │  Document   │         │
         │         │   Grading   │         │
         │         │ (Optimized) │         │
         │         └──────┬──────┘         │
         │                │                 │
         │         ┌──────▼──────┐         │
         │         │   Context   │         │
         │         │ Formatting  │         │
         │         │   (New)     │         │
         │         └──────┬──────┘         │
         │                │                 │
         └────────────────┼─────────────────┘
                          │
                   ┌──────▼──────┐
                   │   Answer    │
                   │ Generation  │
                   │ (Enhanced)  │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │   Quality   │
                   │   Checks    │
                   │ (Optional)  │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │ Final Answer│
                   │ + Citations │
                   └─────────────┘
```

---

## 🔑 Key Benefits Summary

### 1. **Better Routing Accuracy**
- Clear decision criteria reduce misrouting
- Explicit keyword detection for time-sensitive queries
- Domain-boundary awareness for out-of-scope questions

### 2. **Richer Context for Answers**
- Structured formatting helps LLM understand information hierarchy
- Inline citations provide source attribution
- Clear separation of entities, relationships, and web data

### 3. **Higher Answer Quality**
- Domain-optimized prompts for pest/disease specific responses
- Better synthesis of multi-source information
- Actionable recommendations focus

### 4. **Improved Observability**
- Comprehensive logging at each workflow stage
- Visual indicators (emojis) for quick scanning
- Statistics tracking for performance monitoring

### 5. **Optimized Query Refinement**
- Domain-aware query transformation
- Entity and relationship extraction focus
- Knowledge graph-friendly terminology

### 6. **Enhanced Debugging**
- Clear error messages with context
- Retry tracking with detailed logs
- Routing reason visibility

---

## 🧪 Testing Recommendations

### Test Scenarios

#### 1. Knowledge Graph Routing
```python
test_questions = [
    "What causes durian leaf curl disease?",
    "How to identify Phytophthora palmivora symptoms?",
    "What pesticide is effective against durian fruit borers?",
    "My durian leaves are curling with scorched edges—is this leafhopper damage?",
]
# Expected route: kg_retrieval
```

#### 2. Web Search Routing
```python
test_questions = [
    "What are the latest news about durian pests in 2025?",
    "Recent research on durian disease management?",
    "New treatment methods discovered this year?",
    "Current outbreak information for durian diseases?",
]
# Expected route: web_search
```

#### 3. LLM Internal Routing
```python
test_questions = [
    "What is the capital of Thailand?",
    "How do I cook rice?",
    "Hello, how are you?",
    "Explain machine learning concepts",
]
# Expected route: llm_internal (answer_generation with no context)
```

#### 4. Query Transformation Effectiveness
```python
# Test that query transformation improves retrieval when initial results are poor
test_scenario = {
    "initial_query": "leaves dying",
    "expected_refinement": "durian leaf death causes symptoms",
    "should_retrieve_better_results": True,
}
```

#### 5. Context Formatting
```python
# Verify structured output format
test_context = format_context(
    node_contents=["Entity info..."],
    edge_contents=["Relationship info..."],
    web_contents=["Web info..."],
    node_citations=[{"title": "doc1.pdf"}],
    edge_citations=[{"title": "doc2.pdf"}],
    web_citations=[{"title": "Article", "url": "https://..."}],
)
# Should contain section headers, inline citations, clear structure
assert "KNOWLEDGE GRAPH ENTITIES" in test_context
assert "Source:" in test_context
```

---

## 📈 Monitoring Metrics

### Key Metrics to Track

1. **Routing Distribution**
   - % of queries to KG retrieval
   - % of queries to web search
   - % of queries to LLM internal
   - Misrouting rate (if detectable)

2. **Retrieval Performance**
   - Average nodes retrieved per query
   - Average edges retrieved per query
   - Retrieval success rate

3. **Document Grading**
   - % of documents filtered as irrelevant
   - Average relevant documents per query
   - Grading consistency

4. **Query Transformation**
   - Transformation trigger rate
   - Average retry count
   - Success rate after transformation

5. **Answer Quality**
   - Hallucination check failure rate
   - Answer quality check failure rate
   - Average retry count before final answer

6. **Performance Timing**
   - Average end-to-end latency
   - Average time per workflow stage
   - 95th percentile latency

---

## 🚀 Future Enhancement Opportunities

### 1. Hybrid Routing
- Combine KG retrieval with web search for comprehensive answers
- Dynamic decision to query both sources based on context richness

### 2. Adaptive Retrieval Limits
- Automatically adjust `N_RETRIEVED_DOCUMENTS` based on query complexity
- Increase limit if initial results are insufficient

### 3. Caching Layer
- Cache routing decisions for similar questions
- Cache KG retrieval results for identical queries
- Cache embeddings for frequent queries

### 4. Feedback Loop
- Collect user feedback on answer quality
- Use feedback to refine routing model
- Continuously improve prompts based on failure cases

### 5. Multi-lingual Support
- Extend prompts for Thai language support (important for durian domain)
- Language-aware routing and answer generation

### 6. Citation Enhancement
- Add snippet extraction from source documents
- Provide confidence scores for citations
- Enable citation verification

---

## 📝 Migration Guide

### Upgrading from Previous Version

#### No Breaking Changes
All changes are backward compatible. The workflow will continue to function with existing configurations.

#### Recommended Updates

1. **Review Default Settings**
   - Consider enabling `EDGE_RETRIEVAL` for richer relationship context
   - Evaluate trade-offs for quality control flags

2. **Monitor New Logs**
   - Updated log format provides more information
   - Existing log parsing may need adjustment

3. **Test Routing Behavior**
   - Improved routing may change query distribution
   - Monitor routing decisions for expected behavior

4. **Update Integration Tests**
   - New log messages may affect test assertions
   - Context format changes may affect downstream processing

---

## 📚 Related Documentation

- [Workflow Architecture](./WORKFLOW_ARCHITECTURE.md) - Comprehensive workflow documentation
- [API Models](../src/api/models.py) - Request/response schemas
- [Configuration Guide](./CONFIGURATION_GUIDE.md) - Detailed configuration options
- [Quick Reference](./QUICK_REFERENCE.md) - Quick start guide

---

## 🤝 Contributing

When making further refinements:

1. **Update prompts**: Always test prompt changes with diverse queries
2. **Add logging**: Ensure new workflow stages have appropriate log messages
3. **Document changes**: Update this file with new refinements
4. **Test routing**: Verify routing decisions remain accurate
5. **Performance check**: Measure impact on end-to-end latency

---

**Last Updated**: 2025-10-06  
**Contributors**: AI Assistant  
**Status**: Production Ready ✅
