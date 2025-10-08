# Intelligent Routing Guide for Durian Pest & Disease Queries

## Quick Reference

This guide helps you understand how the Adaptive RAG system routes different types of questions to the optimal data source.

---

## 🔀 Three Routing Paths

### 1. 📊 Knowledge Graph (kg_retrieval)
**When**: Domain-specific durian pest and disease questions

**Use Cases**:
- Symptom identification
- Pest/disease information
- Treatment methods
- Prevention strategies
- Diagnostic questions

**Example Questions**:
```
✓ "What causes durian leaf curl disease?"
✓ "How to identify Phytophthora palmivora?"
✓ "What are symptoms of stem borer infestation?"
✓ "Best treatment for root rot in durian?"
✓ "How to prevent fruit borer attacks?"
✓ "What does durian leaf spot disease look like?"
✓ "My leaves have brown spots—what disease is this?"
```

### 2. 🌐 Web Search (web_search)
**When**: Latest/recent information about durian pests and diseases

**Keywords That Trigger Web Search**:
- "latest", "recent", "new", "current", "today"
- "this year", "breaking", "news", "update"
- "2025", "2024" (recent years)

**Example Questions**:
```
✓ "What are the latest news about durian diseases?"
✓ "Recent research on Phytophthora control?"
✓ "New treatment methods for durian pests in 2025?"
✓ "Current durian pest outbreaks in Thailand?"
✓ "Breaking news about durian disease management?"
```

### 3. 🤖 LLM Internal (llm_internal)
**When**: Out-of-domain questions (not about durian/pests/diseases)

**Example Questions**:
```
✓ "Hello, how are you?"
✓ "What is the capital of Thailand?"
✓ "How do I cook rice?"
✓ "Explain machine learning"
✓ "What's the weather like today?"
```

---

## 🎯 Routing Decision Process

### Step 1: Domain Check
```
Is the question about durian, pests, or diseases?
├─ NO  → Route to LLM Internal
└─ YES → Go to Step 2
```

### Step 2: Time Sensitivity Check
```
Does the question ask for latest/recent/new information?
├─ YES → Route to Web Search
└─ NO  → Route to Knowledge Graph
```

---

## 📋 Detailed Examples

### Knowledge Graph Examples

#### ✅ Diagnostic Questions
```
"My durian leaves are curling and yellowing—what could be wrong?"
"There's white powder on the fruit—is this a fungal disease?"
"Trunk has holes with sawdust—what borer is this?"
```

#### ✅ Information Requests
```
"What is Lasiodiplodia theobromae?"
"Life cycle of durian fruit borer?"
"Symptoms of Phytophthora palmivora infection?"
```

#### ✅ Treatment Questions
```
"How to treat durian stem borers?"
"What fungicide works for durian leaf spot?"
"Prevention methods for root rot?"
```

#### ✅ Management Questions
```
"Integrated pest management for durian?"
"Cultural practices to prevent diseases?"
"Monitoring strategies for durian pests?"
```

---

### Web Search Examples

#### ✅ Time-Sensitive Queries
```
"Latest durian disease outbreaks in 2025?"
"Recent studies on durian pest control?"
"New pesticide approvals for durian this year?"
```

#### ✅ News Requests
```
"Breaking news about durian diseases?"
"Current research on durian pests?"
"Today's updates on durian agriculture?"
```

#### ✅ Trend Queries
```
"Emerging durian diseases in Southeast Asia?"
"New pest species affecting durian recently?"
"Recent climate impact on durian pests?"
```

---

### LLM Internal Examples

#### ✅ Greetings/Conversational
```
"Hello!"
"How are you?"
"Thank you for your help"
"Good morning"
```

#### ✅ General Knowledge
```
"What is photosynthesis?"
"How does the internet work?"
"Capital of Thailand?"
"Who invented the computer?"
```

#### ✅ Other Topics
```
"How to cook Thai food?"
"Best tourist destinations in Thailand?"
"Explain quantum physics"
"What is cryptocurrency?"
```

---

## 🎨 Routing Examples by Question Type

### Symptom-Based Questions
| Question | Route | Reason |
|----------|-------|--------|
| "Leaves are curling and brown" | Knowledge Graph | Symptom identification |
| "Latest symptoms of new durian disease" | Web Search | Contains "latest" + "new" |
| "What causes plant wilting?" | LLM Internal | Generic, not durian-specific |

### Treatment Questions
| Question | Route | Reason |
|----------|-------|--------|
| "How to treat stem borers?" | Knowledge Graph | Standard treatment info |
| "New treatment methods this year?" | Web Search | Contains "new" + time reference |
| "How to treat common cold?" | LLM Internal | Not durian-related |

### Pest/Disease Information
| Question | Route | Reason |
|----------|-------|--------|
| "What is Phytophthora palmivora?" | Knowledge Graph | Domain-specific entity |
| "Recent discovery about pest X?" | Web Search | Contains "recent" |
| "What are viruses?" | LLM Internal | Generic biology |

### Prevention Questions
| Question | Route | Reason |
|----------|-------|--------|
| "How to prevent root rot?" | Knowledge Graph | Prevention strategy |
| "Latest prevention techniques 2025?" | Web Search | Contains "latest" + year |
| "How to prevent getting sick?" | LLM Internal | General health |

---

## 🚫 Common Routing Mistakes to Avoid

### ❌ Wrong Route: Knowledge Graph
```
# These should go to Web Search:
"Latest news about durian diseases"  # Has "latest" keyword
"Recent research on pest control"    # Has "recent" keyword

# These should go to LLM Internal:
"How to grow vegetables?"            # Not durian-specific
"General plant diseases"             # Too generic
```

### ❌ Wrong Route: Web Search
```
# These should go to Knowledge Graph:
"What causes durian leaf curl?"      # Standard knowledge, no time keywords
"Treatment for Phytophthora"         # Domain knowledge, not time-sensitive
```

### ❌ Wrong Route: LLM Internal
```
# These should go to Knowledge Graph:
"durian stem borer symptoms"         # Durian-specific
"Phytophthora palmivora treatment"   # Domain-specific
```

---

## 🔍 How to Frame Questions for Best Results

### For Knowledge Graph Retrieval

#### ✅ Good Questions (Specific)
```
"What are symptoms of durian leaf spot caused by Phomopsis?"
"How to identify durian fruit borer damage?"
"Treatment protocol for Lasiodiplodia theobromae?"
```

#### ❌ Avoid (Too Generic)
```
"Tell me about pests"
"Diseases?"
"How to grow durian?"  # Too broad, not pest/disease specific
```

### For Web Search

#### ✅ Good Questions (Time-Specific)
```
"Latest durian disease research in 2025?"
"Recent pest control innovations?"
"New durian pest species discovered this year?"
```

#### ❌ Avoid (Missing Time Keywords)
```
"Durian disease research?"  # No time indicator
"Pest control methods?"     # Could be KG retrieval
```

---

## 📊 Routing Statistics Reference

### Typical Distribution
Based on expected usage patterns:

```
Knowledge Graph: 70-80%  ← Most queries (domain expertise)
Web Search:      10-15%  ← Time-sensitive queries
LLM Internal:     5-15%  ← Out-of-domain queries
```

### Health Check Questions
To verify routing is working correctly:

```python
# Test Knowledge Graph routing
questions_kg = [
    "What causes durian leaf curl?",
    "How to treat Phytophthora?",
    "Symptoms of stem borer?"
]

# Test Web Search routing
questions_web = [
    "Latest durian disease news 2025?",
    "Recent pest control research?",
    "New treatment methods this year?"
]

# Test LLM Internal routing
questions_llm = [
    "Hello, how are you?",
    "What is the capital of France?",
    "How to cook pasta?"
]
```

---

## 🛠️ Troubleshooting

### Question: "My domain query went to LLM Internal"
**Possible Causes**:
1. Question doesn't mention durian/pests/diseases explicitly
2. Question is too generic

**Solution**:
- Be more specific: Add "durian" to the question
- Example: "stem borers" → "durian stem borers"

### Question: "My time-sensitive query went to Knowledge Graph"
**Possible Causes**:
1. Missing time-indicating keywords

**Solution**:
- Add keywords: "latest", "recent", "new", "current"
- Example: "pest research" → "latest pest research"

### Question: "My general question went to Knowledge Graph"
**Possible Causes**:
1. Question contains durian-related keywords but is out of scope

**Solution**:
- This is expected behavior—anything durian-related goes to KG first
- If truly general, rephrase without durian context

---

## 💡 Tips for Optimal Results

### 1. Be Specific
```
Good: "What are symptoms of Phytophthora palmivora in durian?"
Bad:  "Tell me about diseases"
```

### 2. Include Context
```
Good: "My durian leaves are curling—what pest causes this?"
Bad:  "Leaves curling"
```

### 3. Use Domain Terms
```
Good: "Treatment for durian stem borer infestation?"
Bad:  "How to kill bugs in trees?"
```

### 4. Specify Time for Current Info
```
Good: "Latest research on durian diseases in 2025?"
Bad:  "Research on durian diseases"  # Will go to KG, not Web
```

### 5. Ask One Thing at a Time
```
Good: "What causes durian leaf curl?"
      "How to treat durian leaf curl?"  # Separate question
Bad:  "What causes leaf curl and how to treat it and prevent it and what pesticides work?"
```

---

## 📖 Query Templates

### Template 1: Symptom Identification
```
"What [pest/disease] causes [symptom] in durian?"

Examples:
- "What pest causes holes in durian leaves?"
- "What disease causes brown spots on durian fruit?"
```

### Template 2: Treatment Request
```
"How to treat [pest/disease] in durian?"

Examples:
- "How to treat stem borers in durian?"
- "How to treat root rot in durian trees?"
```

### Template 3: Prevention Strategy
```
"How to prevent [pest/disease] in durian?"

Examples:
- "How to prevent fruit borer attacks in durian?"
- "How to prevent Phytophthora infection?"
```

### Template 4: Latest Information
```
"What are the latest [information type] about [topic]?"

Examples:
- "What are the latest news about durian pests?"
- "What are the recent studies on disease control?"
```

---

## 🎓 Best Practices Summary

### ✅ DO
- Be specific about durian pests/diseases
- Use scientific names when known
- Add time keywords for current information
- Include symptoms/context for diagnostics
- Ask focused questions

### ❌ DON'T
- Ask extremely generic questions
- Combine multiple unrelated questions
- Omit "durian" from domain questions
- Use ambiguous terms without context
- Expect domain expertise for general topics

---

## 📞 Getting Help

If routing seems incorrect:
1. Check if question includes "durian", "pest", or "disease" keywords
2. Verify time-indicating keywords for web search
3. Review examples in this guide
4. Consult [Workflow Architecture](./WORKFLOW_ARCHITECTURE.md) documentation

---

**Last Updated**: 2025-10-06  
**Related Docs**: [Workflow Refinements](./WORKFLOW_REFINEMENTS.md), [Workflow Architecture](./WORKFLOW_ARCHITECTURE.md)
