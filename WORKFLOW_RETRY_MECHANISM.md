# Workflow Retry Mechanism - Implementation Guide

## Problem Statement
The adaptive RAG workflow had infinite loop vulnerabilities in two scenarios:
1. **KG Loop**: `query_transformation` → `knowledge_graph_retrieval` → `nodes_and_edges_grading` → `decide_to_generate` → `query_transformation` (repeats when documents are never relevant)
2. **Answer Loop**: `answer_generation` → `grade_generation_vs_context_and_question` → `query_transformation` → ... (repeats when answer never addresses the question)

## Solution Overview
Implemented a **maximum retry counter** mechanism that:
- Tracks the number of query transformation attempts
- Prevents infinite loops by enforcing a retry limit (default: 3)
- Provides fallback strategies when limit is reached

## Implementation Details

### 1. Added Retry Tracking to State
```python
class GraphState(TypedDict):
    # ... existing fields ...
    retry_count: int  # NEW: Tracks query transformation attempts
```

### 2. Added Configuration Constant
```python
class Defaults:
    MAX_RETRY_COUNT = 3  # Maximum number of query transformation retries
```

### 3. Updated Query Transformation
The `query_transformation` function now:
- Increments retry counter on each call
- Logs current retry count for monitoring

```python
async def query_transformation(state: GraphState) -> dict:
    current_retry = state.get("retry_count", 0)
    print(LogMessages.RETRY_COUNT_INFO.format(current_retry + 1, Defaults.MAX_RETRY_COUNT))
    # ... transform query ...
    return {"question": refined_question, "retry_count": current_retry + 1}
```

### 4. Enhanced Decision Logic

#### A. `decide_to_generate()` - Prevents KG Loop
**Before:**
```python
if not relevant_documents:
    return "query_transformation"  # Can loop forever!
```

**After:**
```python
if not relevant_documents:
    current_retry = state.get("retry_count", 0)
    if current_retry >= Defaults.MAX_RETRY_COUNT:
        # Fallback to web search as alternative data source
        return RouteDecision.WEB_SEARCH
    return RouteDecision.QUERY_TRANSFORMATION
```

#### B. `grade_generation_vs_context_and_question()` - Prevents Answer Loop
**Before:**
```python
if answer_not_useful:
    return "query_transformation"  # Can loop forever!
```

**After:**
```python
if answer_not_useful:
    current_retry = state.get("retry_count", 0)
    if current_retry >= Defaults.MAX_RETRY_COUNT:
        # Accept best-effort answer and end workflow
        return RouteDecision.USEFUL
    return RouteDecision.NOT_USEFUL
```

### 5. Updated Workflow Graph
Added new edge: `nodes_and_edges_grading` → `web_search` (fallback path)

```python
workflow.add_conditional_edges(
    "nodes_and_edges_grading",
    decide_to_generate,
    {
        RouteDecision.QUERY_TRANSFORMATION: "query_transformation",
        RouteDecision.ANSWER_GENERATION: "answer_generation",
        RouteDecision.WEB_SEARCH: "web_search",  # NEW: Fallback path
    },
)
```

## Workflow Diagram

### Before (Vulnerable to Infinite Loops):
```
START → route_question
         ├─→ web_search → answer_generation → END
         └─→ knowledge_graph_retrieval 
              ↓
             nodes_and_edges_grading
              ↓
             decide_to_generate
              ├─→ answer_generation → grade_generation
              │                        ├─→ END (useful)
              │                        ├─→ answer_generation (not_supported)
              │                        └─→ query_transformation (not_useful) ⚠️ LOOP!
              └─→ query_transformation ⚠️ LOOP!
                   ↓
                  (back to knowledge_graph_retrieval)
```

### After (With Retry Limits):
```
START → route_question
         ├─→ web_search → answer_generation → END
         └─→ knowledge_graph_retrieval 
              ↓
             nodes_and_edges_grading
              ↓
             decide_to_generate (checks retry_count)
              ├─→ answer_generation → grade_generation (checks retry_count)
              │                        ├─→ END (useful)
              │                        ├─→ answer_generation (not_supported)
              │                        ├─→ query_transformation (not_useful, retry < MAX) ✅
              │                        └─→ END (not_useful, retry >= MAX) ✅ EXITS
              ├─→ query_transformation (retry < MAX) ✅
              │    ↓ (increments retry_count)
              │   (back to knowledge_graph_retrieval)
              └─→ web_search (retry >= MAX) ✅ FALLBACK
```

## Retry Scenarios

### Scenario 1: Knowledge Graph Has No Relevant Documents
| Retry | Action | Result |
|-------|--------|--------|
| 1 | Transform query → Retrieve → Grade | No relevant docs |
| 2 | Transform query → Retrieve → Grade | No relevant docs |
| 3 | Transform query → Retrieve → Grade | No relevant docs |
| **MAX** | **Fallback to web search** | **Gets different data source** ✅ |

### Scenario 2: Answer Never Addresses Question
| Retry | Action | Result |
|-------|--------|--------|
| 1 | Generate → Grade | Not useful |
| 2 | Transform → Retrieve → Generate → Grade | Not useful |
| 3 | Transform → Retrieve → Generate → Grade | Not useful |
| **MAX** | **Accept best-effort answer** | **Workflow ends** ✅ |

## Configuration

### Adjusting Max Retries
Edit `src/core/constants.py`:
```python
class Defaults:
    MAX_RETRY_COUNT = 5  # Increase for more attempts
```

### Monitoring Retries
The workflow logs retry information:
```
---RETRY COUNT: 1/3---
---RETRY COUNT: 2/3---
---RETRY COUNT: 3/3---
---MAX RETRIES REACHED: 3/3. FALLING BACK TO WEB SEARCH---
```

## Benefits

✅ **No Infinite Loops**: Hard limit on retry attempts
✅ **Intelligent Fallbacks**: Web search as alternative when KG fails
✅ **Best-Effort Results**: Always returns an answer (even if imperfect)
✅ **Observable**: Clear logging of retry attempts
✅ **Configurable**: Easy to adjust retry limits
✅ **Backward Compatible**: Existing workflows work unchanged

## Files Modified

1. **`src/core/functions.py`**
   - Added `retry_count` to `GraphState`
   - Updated `query_transformation()` to increment counter

2. **`src/core/workflow.py`**
   - Enhanced `decide_to_generate()` with retry check
   - Enhanced `grade_generation_vs_context_and_question()` with retry check
   - Added web_search fallback edge
   - Initialize `retry_count: 0` in workflow inputs

3. **`src/core/constants.py`**
   - Added `MAX_RETRY_COUNT` constant
   - Added retry-related log messages

## Testing Recommendations

1. **Test infinite loop prevention:**
   ```python
   # Question that KG has no info about
   question = "What is the price of Bitcoin today?"
   # Should fallback to web search after 3 retries
   ```

2. **Test retry logging:**
   - Monitor logs to verify retry counts are displayed
   - Confirm MAX_RETRIES_REACHED message appears

3. **Test fallback mechanisms:**
   - Verify web search is triggered after max KG retries
   - Verify workflow ends with best-effort answer after max grade retries

## Future Enhancements (Optional)

1. **Exponential Backoff**: Add delays between retries
2. **Retry Strategies**: Different limits for different failure types
3. **Metrics Collection**: Track retry rates for monitoring
4. **Dynamic Limits**: Adjust MAX_RETRY_COUNT based on query complexity
