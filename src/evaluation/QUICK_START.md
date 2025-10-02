# 🚀 Quick Start Guide - LangSmith Evaluation

## TL;DR - Get Started in 3 Steps

### 1️⃣ Setup Environment
```bash
# Make sure you have these in your .env file
LANGSMITH_API_KEY=your_key_here
llm_api_key=your_gemini_key_here
```

### 2️⃣ Upload Data
```bash
# Upload first 10 samples for testing
python -m src.evaluation.ingest_langsmith --num-samples 10 --overwrite
```

### 3️⃣ Run Evaluation
```bash
# Quick test (fast)
python -m src.evaluation.evaluate_langsmith --config quick

# Or use the shell script
./scripts/evaluate.sh quick
```

---

## Common Commands Cheat Sheet

### 📊 Data Ingestion

```bash
# Upload all samples
python -m src.evaluation.ingest_langsmith

# Upload first 50 samples
python -m src.evaluation.ingest_langsmith --num-samples 50

# Upload only multi-hop questions
python -m src.evaluation.ingest_langsmith --type multi-hop

# Upload only batch "a"
python -m src.evaluation.ingest_langsmith --batch a

# Overwrite existing dataset
python -m src.evaluation.ingest_langsmith --overwrite
```

### 🎯 Run Evaluation

```bash
# Quick test (3 docs, 1 web search, no checks) - ~10s per question
python -m src.evaluation.evaluate_langsmith --config quick

# Balanced (5 docs, 3 web searches, all checks) - ~25s per question
python -m src.evaluation.evaluate_langsmith --config balanced

# Accuracy-focused (10 docs, 5 web, all features) - ~50s per question
python -m src.evaluation.evaluate_langsmith --config accuracy
```

### 🔧 Configuration

```bash
# List all available configs
python -m src.evaluation.evaluate_langsmith --list-configs

# Compare configurations
python -m src.evaluation.evaluate_langsmith --compare-configs

# Custom configuration
python -m src.evaluation.evaluate_langsmith \
  --config balanced \
  --dataset-name "My Test Dataset" \
  --experiment-prefix "my-experiment"
```

### 🛠️ Shell Script (Easiest!)

```bash
# Make executable (first time only)
chmod +x scripts/evaluate.sh

# Quick test
./scripts/evaluate.sh quick

# Full evaluation
./scripts/evaluate.sh full

# Accuracy-focused
./scripts/evaluate.sh accuracy

# Upload data
./scripts/evaluate.sh ingest --num-samples 50

# Show help
./scripts/evaluate.sh help
```

---

## Configuration Presets

| Config | Speed | Thoroughness | Use When |
|--------|-------|--------------|----------|
| `quick` | ⚡⚡⚡ | ⭐ | Testing, debugging |
| `balanced` | ⚡⚡ | ⭐⭐⭐ | Standard evaluation |
| `accuracy` | ⚡ | ⭐⭐⭐⭐⭐ | Final evaluation |
| `minimal` | ⚡⚡⚡ | ⭐⭐ | Testing retrieval |
| `graph-only` | ⚡⚡ | ⭐⭐⭐ | Testing KG only |

---

## Evaluation Metrics

Your evaluation will produce 4 scores:

| Metric | What it Measures | Target Score |
|--------|------------------|--------------|
| **Correctness** | Answer matches reference | > 0.80 |
| **Concision** | Answer not too long | > 0.70 |
| **Relevance** | Addresses the question | > 0.90 |
| **Faithfulness** | No hallucinations | > 0.85 |

---

## Typical Workflow

### First Time Setup
```bash
# 1. Test with small dataset
python -m src.evaluation.ingest_langsmith --num-samples 10 --overwrite

# 2. Quick test evaluation
./scripts/evaluate.sh quick

# 3. Check results in LangSmith UI
# Go to https://smith.langchain.com
```

### Regular Evaluation
```bash
# 1. Upload full dataset (if not already done)
python -m src.evaluation.ingest_langsmith

# 2. Run balanced evaluation
./scripts/evaluate.sh full

# 3. Review results and iterate
```

### Before Production
```bash
# 1. Ensure you have comprehensive dataset
python -m src.evaluation.ingest_langsmith --overwrite

# 2. Run thorough evaluation
./scripts/evaluate.sh accuracy

# 3. Analyze all metrics carefully
```

---

## Viewing Results

### LangSmith UI

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Navigate to your project (default: "durian-pest-disease-eval")
3. Find experiment by prefix (e.g., "quick-test-...")
4. View:
   - Overall metrics (average scores)
   - Individual question results
   - Detailed traces
   - Evaluator comments

### What to Look For

✅ **Good Signs:**
- Correctness > 0.80
- Relevance > 0.90
- Faithfulness > 0.85
- Low variance in scores

⚠️ **Warning Signs:**
- Correctness < 0.70
- High variance (inconsistent performance)
- Low faithfulness (hallucinations)
- Poor concision (too verbose)

---

## Troubleshooting

### Problem: Import errors
```bash
# Solution: Install dependencies
pip install langsmith openai nest-asyncio python-dotenv
```

### Problem: API key errors
```bash
# Solution: Check .env file
cat .env | grep -E "LANGSMITH|llm_api_key"
```

### Problem: Rate limit errors
```bash
# Solution: Use slower config or reduce concurrency
# Already set to max_concurrency=1 by default
```

### Problem: Async errors
```bash
# Solution: Already handled with nest_asyncio
# If issues persist, run in fresh Python process
```

---

## Examples

### Example 1: Quick Test of 5 Questions
```bash
# Step 1: Upload 5 samples
python -m src.evaluation.ingest_langsmith \
  --num-samples 5 \
  --dataset-name "Quick Test" \
  --overwrite

# Step 2: Run quick evaluation
python -m src.evaluation.evaluate_langsmith \
  --config quick \
  --dataset-name "Quick Test" \
  --experiment-prefix "quick-test"

# Step 3: Check results in LangSmith UI
```

### Example 2: Evaluate Multi-Hop Questions Only
```bash
# Step 1: Upload multi-hop questions
python -m src.evaluation.ingest_langsmith \
  --type multi-hop \
  --dataset-name "Multi-Hop Test" \
  --overwrite

# Step 2: Run balanced evaluation
python -m src.evaluation.evaluate_langsmith \
  --config balanced \
  --dataset-name "Multi-Hop Test" \
  --experiment-prefix "multi-hop-balanced"
```

### Example 3: Compare Configurations
```bash
# Run same dataset with different configs
./scripts/evaluate.sh quick
./scripts/evaluate.sh full
./scripts/evaluate.sh accuracy

# Compare results in LangSmith UI
```

---

## Next Steps

📖 **Full Documentation**: See [README.md](README.md) for comprehensive guide

🔧 **Configuration Details**: See [config.py](config.py) for all presets

📊 **Change Log**: See [CHANGELOG.md](CHANGELOG.md) for what's new

🎯 **Advanced Usage**: See README.md sections on:
- Custom evaluators
- CI/CD integration
- Result analysis
- Workflow customization

---

## Quick Tips

💡 **Tip 1**: Start with `--num-samples 5` for quick testing

💡 **Tip 2**: Use `quick` config for iteration, `accuracy` for final eval

💡 **Tip 3**: Check LangSmith traces if scores are unexpected

💡 **Tip 4**: Use `--overwrite` to replace test datasets

💡 **Tip 5**: Shell script is fastest for common tasks: `./scripts/evaluate.sh`

---

## Help & Support

```bash
# Show help for ingestion
python -m src.evaluation.ingest_langsmith --help

# Show help for evaluation
python -m src.evaluation.evaluate_langsmith --help

# Show shell script help
./scripts/evaluate.sh help
```

---

**Happy Evaluating! 🎉**

