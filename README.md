Langgraph Studio

```bash
langgraph dev --allow-blocking
```

APIs

```bash
uvicorn src.api.main:app --reload
```

Python

```bash
python -m src.core.workflow --question "Is algal leaf spot listed for durian and what does that tell me?" --n-retrieved-documents 3 --edge-retrieval
```
