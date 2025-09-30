# Workflow Retry Mechanism - Quick Reference

## 🎯 What Was Fixed
Prevented infinite loops in query transformation by adding a maximum retry counter (default: 3 attempts).

## 🔄 How It Works

### Loop Prevention Points

**1. Knowledge Graph Loop (decide_to_generate)**
```
No relevant docs found → Check retry count
├─ If retry < 3: Transform query and try again
└─ If retry ≥ 3: Fallback to web search ✅
```

**2. Answer Quality Loop (grade_generation_vs_context_and_question)**
```
Answer doesn't address question → Check retry count  
├─ If retry < 3: Transform query and try again
└─ If retry ≥ 3: Accept answer and end workflow ✅
```

## 📊 Example Flow

### Before (Infinite Loop Risk):
```
Question: "How to cure unknown disease X?"
→ KG search (no results)
→ Transform query
→ KG search (no results)
→ Transform query
→ KG search (no results)
→ Transform query
→ ... (INFINITE LOOP) ❌
```

### After (With Retry Limit):
```
Question: "How to cure unknown disease X?"
→ KG search (no results) [Retry 1/3]
→ Transform query
→ KG search (no results) [Retry 2/3]
→ Transform query
→ KG search (no results) [Retry 3/3]
→ MAX RETRIES REACHED
→ Fallback to web search ✅
→ Answer generated from web
→ END
```

## ⚙️ Configuration

**Adjust retry limit:**
```python
# In src/core/constants.py
class Defaults:
    MAX_RETRY_COUNT = 3  # Change this value
```

**Common settings:**
- `MAX_RETRY_COUNT = 1`: Fast failover (impatient)
- `MAX_RETRY_COUNT = 3`: Balanced (recommended) ⭐
- `MAX_RETRY_COUNT = 5`: More attempts (patient)

## 📝 Monitoring Logs

Watch for these messages:
```
---RETRY COUNT: 1/3---
---RETRY COUNT: 2/3---
---RETRY COUNT: 3/3---
---MAX RETRIES REACHED: 3/3. FALLING BACK TO WEB SEARCH---
```

## 🔍 Key Files Changed

| File | Changes |
|------|---------|
| `src/core/functions.py` | Added `retry_count` field, increment logic |
| `src/core/workflow.py` | Added retry checks in decision functions |
| `src/core/constants.py` | Added `MAX_RETRY_COUNT` constant |

## ✅ Benefits

- ✅ No more infinite loops
- ✅ Guaranteed workflow termination
- ✅ Fallback to alternative data sources
- ✅ Best-effort answers always returned
- ✅ Observable retry attempts via logs

## 🚀 Usage

No changes needed to your existing code! The retry mechanism works automatically:

```python
from src.core.workflow import run_workflow

# Just use as before - retry logic is built-in
await run_workflow(
    question="Your question here",
    n_documents=3
)
```

## 🐛 Troubleshooting

**Problem**: Workflow exits too quickly
- **Solution**: Increase `MAX_RETRY_COUNT` in constants.py

**Problem**: Want to see retry attempts
- **Solution**: Check console logs for "RETRY COUNT" messages

**Problem**: Want different behavior after max retries
- **Solution**: Modify fallback logic in `decide_to_generate()` or `grade_generation_vs_context_and_question()`
