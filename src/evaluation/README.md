# LangSmith Evaluation Module

This module provides tools for evaluating the Durian Pest and Disease RAG system using LangSmith and Gemini.

## Overview

The evaluation module consists of three main components:

1. **Data Ingestion** (`ingest_langsmith.py`) - Upload evaluation datasets to LangSmith
2. **Evaluation** (`evaluate_langsmith.py`) - Run evaluations using Gemini-based evaluators
3. **RAGAS Integration** (`ragas.py`) - Advanced RAG metrics evaluation

## Features

### Gemini-Powered Evaluation
- ✅ Uses Gemini 2.5 Pro for generating responses
- ✅ Uses Gemini Flash for fast evaluation
- ✅ OpenAI-compatible API for easy integration
- ✅ Multiple evaluators: correctness, concision, relevance, faithfulness

### Enhanced Data Management
- Filter by question type (1-hop, multi-hop)
- Filter by batch identifier
- Sample size control
- Dataset versioning and overwrite options

### Comprehensive Metrics
- **Correctness**: Does the answer match the reference?
- **Concision**: Is the answer appropriately sized?
- **Relevance**: Does the answer address the question?
- **Faithfulness**: Is the answer grounded in context?

## Setup

### Prerequisites

```bash
# Install required dependencies
pip install langsmith openai nest-asyncio python-dotenv
```

### Environment Variables

Add the following to your `.env` file:

```bash
# LangSmith Configuration
LANGSMITH_API_KEY=your_langsmith_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_PROJECT=durian-pest-disease-eval

# Gemini Configuration (already in settings)
llm_api_key=your_gemini_api_key
llm_base_url=https://generativelanguage.googleapis.com/v1beta/openai/
llm_model=gemini-2.5-pro
```

## Usage

### 1. Ingest Data to LangSmith

#### Basic Usage

```bash
# Upload all samples
python -m src.evaluation.ingest_langsmith
```

#### Advanced Options

```bash
# Upload first 50 samples
python -m src.evaluation.ingest_langsmith --num-samples 50

# Upload only multi-hop questions
python -m src.evaluation.ingest_langsmith --type multi-hop

# Upload only batch "a" questions
python -m src.evaluation.ingest_langsmith --batch a

# Upload with custom dataset name
python -m src.evaluation.ingest_langsmith \
  --dataset-name "Durian Pest Disease - Test Set" \
  --description "Test evaluation dataset"

# Overwrite existing dataset
python -m src.evaluation.ingest_langsmith --overwrite

# Combine filters
python -m src.evaluation.ingest_langsmith \
  --type multi-hop \
  --batch a \
  --num-samples 20
```

#### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--data-file` | Path to JSON data file | `data/QA_17_pest_disease.json` |
| `--source` | Source identifier for metadata | `17-document-durian-pest-and-disease` |
| `--dataset-name` | Name of the LangSmith dataset | `Durian Pest and Disease` |
| `--description` | Dataset description | Auto-generated |
| `--type` | Filter by question type (`1-hop`, `multi-hop`) | None (all types) |
| `--batch` | Filter by batch identifier | None (all batches) |
| `--num-samples` | Maximum number of samples to upload | None (all samples) |
| `--overwrite` | Overwrite existing dataset | False |

### 2. Run Evaluation

#### Basic Usage

```bash
# Run evaluation with default settings
python -m src.evaluation.evaluate_langsmith
```

#### Customization

You can customize the evaluation by modifying the configuration in `evaluate_langsmith.py`:

```python
# Workflow configuration
DEFAULT_WORKFLOW_CONFIG = {
    "n_retrieved_documents": 5,         # Number of documents to retrieve
    "n_web_searches": 3,                # Number of web searches
    "node_retrieval": True,             # Enable node retrieval
    "edge_retrieval": True,             # Enable edge retrieval
    "episode_retrieval": False,         # Disable episode retrieval
    "community_retrieval": False,       # Disable community retrieval
    "enable_retrieved_document_grading": True,
    "enable_hallucination_checking": True,
    "enable_answer_quality_checking": True,
}

# Evaluation settings
DATASET_NAME = "Durian Pest and Disease"
EXPERIMENT_PREFIX = "gemini-2.5-pro"
GEMINI_MODEL = "gemini-2.5-pro"              # Model for generation
GEMINI_EVAL_MODEL = "gemini-2.5-flash-lite-preview-06-17"  # Model for evaluation
```

### 3. View Results

After running the evaluation, view results in the LangSmith UI:

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Navigate to your project (e.g., "durian-pest-disease-eval")
3. Click on the experiment with your prefix (e.g., "gemini-2.5-pro-...")
4. View detailed metrics, traces, and individual evaluations

## Evaluators

### 1. Correctness Evaluator

Compares predicted answers against reference answers using Gemini.

**Criteria:**
- Factual accuracy of pest/disease identification
- Correctness of recommended treatments
- Accuracy of timing and application methods
- Overall alignment with reference

**Output:** Binary score (0 or 1) + reasoning

### 2. Concision Evaluator

Checks if the answer is appropriately sized (not more than 2x reference length).

**Criteria:**
- Response length vs reference length ratio

**Output:** Binary score (0 or 1) + length ratio

### 3. Relevance Evaluator

Evaluates if the answer directly addresses the question.

**Criteria:**
- Does the answer address the question?
- Is information relevant to durian pest/disease management?
- Does it cover specific aspects asked?

**Output:** Binary score (0 or 1) + reasoning

### 4. Faithfulness Evaluator

Checks for hallucinations and grounding in context.

**Criteria:**
- No fabricated facts
- Information supported by references/citations
- Grounded in provided context

**Output:** Binary score (0 or 1) + reasoning

## Example Workflow

Here's a complete workflow for evaluating your RAG system:

```bash
# Step 1: Prepare a test subset (first 10 multi-hop questions)
python -m src.evaluation.ingest_langsmith \
  --dataset-name "Durian Test - Multi-Hop" \
  --type multi-hop \
  --num-samples 10 \
  --overwrite

# Step 2: Update dataset name in evaluate_langsmith.py
# Edit: DATASET_NAME = "Durian Test - Multi-Hop"

# Step 3: Run evaluation
python -m src.evaluation.evaluate_langsmith

# Step 4: Review results in LangSmith UI
# Navigate to your project and review metrics
```

## Advanced Configuration

### Custom Evaluators

You can add custom evaluators by following this template:

```python
def custom_evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """
    Custom evaluator template.
    
    Args:
        inputs: Input question and context
        outputs: Model outputs (response, citations)
        reference_outputs: Ground truth (answer, citations)
        
    Returns:
        dict with 'key', 'score', and 'comment'
    """
    # Your evaluation logic here
    score = 1  # or 0
    
    return {
        "key": "custom_metric",
        "score": score,
        "comment": "Explanation of the score"
    }

# Add to evaluators list in run_evaluation()
evaluators=[
    correctness_evaluator,
    concision_evaluator,
    relevance_evaluator,
    faithfulness_evaluator,
    custom_evaluator,  # Add your evaluator
]
```

### Workflow Configuration

Customize retrieval and quality checking behavior:

```python
config = {
    # Retrieval settings
    "n_retrieved_documents": 10,      # Increase for more context
    "n_web_searches": 5,              # Increase for web fallback
    
    # Knowledge graph settings
    "node_retrieval": True,           # Entity-level retrieval
    "edge_retrieval": True,           # Relationship retrieval
    "episode_retrieval": True,        # Enable episode memory
    "community_retrieval": True,      # Enable community detection
    
    # Quality control
    "enable_retrieved_document_grading": True,  # Grade relevance
    "enable_hallucination_checking": True,      # Check grounding
    "enable_answer_quality_checking": True,     # Check usefulness
}
```

## Troubleshooting

### Common Issues

#### 1. `nest_asyncio` Import Error

```bash
pip install nest-asyncio
```

#### 2. LangSmith API Key Not Found

Ensure `LANGSMITH_API_KEY` is set in your `.env` file.

#### 3. Gemini API Rate Limits

Reduce `max_concurrency` in `run_evaluation()`:

```python
experiment_results = langsmith_client.evaluate(
    ls_target,
    data=dataset_name,
    evaluators=[...],
    max_concurrency=1,  # Lower value = slower but safer
)
```

#### 4. Async Event Loop Issues

If you encounter event loop errors, the script automatically handles them using `nest_asyncio`.

## Performance Tips

1. **Start Small**: Test with 5-10 samples first before full evaluation
2. **Use Flash for Evaluation**: Keep `GEMINI_EVAL_MODEL` as Flash for speed
3. **Monitor Rate Limits**: Keep `max_concurrency=1` for Gemini API
4. **Filter Strategically**: Use `--type` and `--batch` to focus on specific question types

## Metrics Interpretation

### Good Performance Thresholds

- **Correctness**: > 0.8 (80% correct)
- **Concision**: > 0.7 (70% appropriately sized)
- **Relevance**: > 0.9 (90% relevant)
- **Faithfulness**: > 0.85 (85% grounded)

### Score Analysis

```python
# Example results analysis
correctness_avg = 0.82  # Good
concision_avg = 0.65    # Could be improved (too verbose)
relevance_avg = 0.91    # Excellent
faithfulness_avg = 0.88 # Good

# Action: Work on making responses more concise
```

## Integration with CI/CD

You can integrate evaluation into your CI/CD pipeline:

```bash
# .github/workflows/evaluate.yml
name: Evaluate RAG System

on:
  pull_request:
    branches: [main]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run evaluation
        env:
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
          llm_api_key: ${{ secrets.GEMINI_API_KEY }}
        run: python -m src.evaluation.evaluate_langsmith
```

## Next Steps

1. **Baseline Evaluation**: Run initial evaluation to establish baseline metrics
2. **Iterative Improvement**: Modify prompts, retrieval settings, and re-evaluate
3. **A/B Testing**: Compare different models or configurations
4. **Production Monitoring**: Set up continuous evaluation on production data

## Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [RAG Evaluation Best Practices](https://docs.smith.langchain.com/evaluation)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review LangSmith traces for detailed error information
3. Consult project documentation in `/docs`

