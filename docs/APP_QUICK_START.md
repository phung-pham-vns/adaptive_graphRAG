# Interactive App Quick Start

## 🚀 Launch the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 🎯 Three Modes at a Glance

### 💬 Chat Mode
**What**: Conversational interface  
**Use**: Ask questions, get answers  
**Best for**: Quick Q&A, learning

### 🔍 Investigation Mode
**What**: Workflow deep dive  
**Use**: See each processing step  
**Best for**: Understanding how answers are generated

### 🗺️ KG Explorer
**What**: Knowledge graph browser  
**Use**: Search graph directly  
**Best for**: Exploring entities and relationships

---

## ⚡ Quick Guide

### 1. Ask Your First Question

1. **Mode**: Select 💬 Chat
2. **Type**: "What causes durian leaf curl?"
3. **Click**: 📤 Send
4. **Wait**: ~3 seconds
5. **Read**: Answer + sources

### 2. Investigate the Answer

1. **Switch**: Click 🔍 Investigation
2. **View**: Workflow steps
3. **Expand**: "Step-by-Step Details"
4. **See**: What was retrieved and why

### 3. Explore the Knowledge Graph

1. **Switch**: Click 🗺️ KG Explorer
2. **Stats**: View graph statistics
3. **Search**: Enter "Phytophthora"
4. **Browse**: Nodes and edges

---

## ⚙️ Essential Settings

### For Speed (Default)
```
📊 Retrieval:
  • KG Documents: 3
  • Web Results: 3

🔍 KG Components:
  • Nodes: ✅
  • Edges: ✅
  • Episodes: ⚪
  • Communities: ⚪

⚡ Quality Control:
  • All disabled

Result: ~2-4 seconds per query
```

### For Quality
```
📊 Retrieval:
  • KG Documents: 7
  • Web Results: 3

🔍 KG Components:
  • Nodes: ✅
  • Edges: ✅
  • Episodes: ✅
  • Communities: ⚪

⚡ Quality Control:
  • All enabled ✅

Result: ~10-15 seconds per query
```

---

## 💡 Example Questions

### Identification
- "What pest causes holes in durian leaves?"
- "How to identify Phytophthora palmivora?"
- "What are symptoms of stem borers?"

### Treatment
- "How to treat durian leaf curl?"
- "What pesticide for fruit borers?"
- "Treatment for root rot?"

### Prevention
- "How to prevent durian diseases?"
- "Preventive measures for pests?"
- "IPM strategies for durian?"

### Latest Info
- "Latest news about durian diseases?"
- "Recent research on pest control?"
- "New treatment methods 2025?"

---

## 🎨 Understanding the Interface

### Chat Message Colors

🔵 **Blue Box** = Your question  
🟢 **Green Box** = AI answer

### Workflow Icons

- 🔀 Routing
- 📊 KG Retrieval
- 🌐 Web Search
- ✍️ Generation
- 🔍 Quality Check

### Citation Types

- 📖 Knowledge Graph Sources
- 🌐 Web Sources

---

## ⚡ Power Tips

### 1. Always Enable Edges
**Why**: Captures relationships like "X causes Y"  
**Impact**: Better, more complete answers  
**Cost**: +0.5s only

### 2. Use Chat for Conversations
**Example**:
```
You: What are common durian pests?
AI: [Lists 5 pests]
You: Tell me more about the first one
AI: [Details about first pest]
```

### 3. Check Investigation After Each Query
**Learn**: See exactly what the system retrieved  
**Improve**: Adjust settings based on results

### 4. Search KG Directly for Research
**Use Case**: Want to know everything about "Phytophthora"  
**Action**: Go to KG Explorer, search, browse all results

### 5. Clear Conversation to Start Fresh
**When**: Switching topics or testing  
**Action**: Click "🔄 Clear Conversation" in sidebar

---

## 🐛 Quick Fixes

### No Answer?
- ✅ Check KG Explorer - is graph active?
- ✅ Try simpler question
- ✅ Check Investigation mode for errors

### Off-topic Answer?
- ✅ Enable "Document Grading"
- ✅ Rephrase question more specifically
- ✅ Check Investigation - was routing correct?

### Too Slow?
- ✅ Reduce KG documents to 3
- ✅ Disable Episodes & Communities
- ✅ Disable quality checks
- ✅ Keep only Nodes + Edges

### Can't See Steps?
- ✅ Switch to Investigation mode
- ✅ Enable "Show step details" in sidebar
- ✅ Ask a question first!

---

## 📊 What to Monitor

### Session Summary (Chat Mode)
- **Messages**: Your conversation length
- **Workflow Steps**: Processing complexity
- **Citations**: Source count

### Workflow Summary (Investigation)
- **Total Steps**: Nodes executed
- **Query Retries**: Transformation attempts
- **Hallucination Checks**: Regenerations

### KG Stats (Explorer)
- **Total Nodes**: Graph size
- **Total Edges**: Relationships
- **Status**: Active or Empty

---

## 🎯 Common Workflows

### Workflow 1: Quick Answer
```
1. Chat mode
2. Ask question
3. Read answer
4. Check citations
```

### Workflow 2: Deep Research
```
1. Chat mode: Ask question
2. Investigation: Review workflow
3. KG Explorer: Search related topics
4. Chat: Ask follow-up questions
```

### Workflow 3: Knowledge Discovery
```
1. KG Explorer: Search broad term
2. Browse results
3. Find interesting entity
4. KG Explorer: Search that entity
5. Repeat to explore
```

### Workflow 4: Quality Debugging
```
1. Chat: Ask question
2. Get unexpected answer
3. Investigation: Check routing
4. Investigation: View retrieved docs
5. Adjust settings
6. Chat: Try again
```

---

## 🚦 Status Indicators

### Processing States

- 🤔 **"Thinking and searching..."** = Working on it
- ✅ **Green answer box** = Success
- ❌ **Red box** = Error occurred
- ⚠️ **Yellow warning** = Retry attempted

### Quality Checks

- ✅ **"Answer Generated"** = Step complete
- ⚠️ **"Query Retry: 1/3"** = Refining search
- ⚠️ **"Hallucination Check: 1/3"** = Verifying answer

---

## 📱 Best Practices

### Do's ✅
- ✅ Enable edge retrieval
- ✅ Start with speed mode
- ✅ Check citations
- ✅ Use investigation for learning
- ✅ Ask specific questions

### Don'ts ❌
- ❌ Enable all quality checks by default
- ❌ Set retrieval limits too high initially
- ❌ Ask extremely vague questions
- ❌ Forget to check KG Explorer
- ❌ Ignore workflow investigation insights

---

## 🔄 Iteration Tips

### Refining Questions
```
Vague: "Tell me about pests"
Better: "What are common durian pests?"
Best: "What pest causes brown spots on durian leaves?"
```

### Configuration Tuning
```
Try 1: Default settings → Answer OK but could be better
Try 2: Enable edge retrieval → Much better!
Try 3: Increase to 5 docs → More comprehensive
Try 4: Enable document grading → More relevant
```

### Investigation Learning
```
Step 1: See what was retrieved
Step 2: Understand routing decision
Step 3: Adjust configuration
Step 4: Retry query
Step 5: Compare results
```

---

## 🎓 5-Minute Tour

### Minute 1: First Question
- Open app
- Chat mode
- Ask: "What causes leaf curl?"
- Read answer

### Minute 2: Investigation
- Switch to Investigation
- Review workflow steps
- See retrieved documents

### Minute 3: Citations
- Scroll down in Chat
- Check citation sources
- Verify information quality

### Minute 4: KG Explorer
- Switch to KG Explorer
- View statistics
- Try quick search

### Minute 5: Configuration
- Open sidebar
- Try enabling edge retrieval
- Ask another question
- Compare results

---

## 📚 Next Steps

After this quick start:

1. **Read**: [Full App Guide](./INTERACTIVE_APP_GUIDE.md)
2. **Explore**: [Routing Guide](./ROUTING_GUIDE.md)
3. **Understand**: [Workflow Architecture](./WORKFLOW_ARCHITECTURE.md)
4. **Optimize**: [Optimization Recommendations](./OPTIMIZATION_RECOMMENDATIONS.md)

---

## 💬 Example Session

```
[Open app]

You: What causes durian leaf curl?
AI: Durian leaf curl is primarily caused by Phytoplasma pathogens...
    📖 Sources: 3 documents

[Switch to Investigation]
See: Routing → KG Retrieval → Generation
     Retrieved 3 nodes, 2 edges
     No retries needed

[Switch to KG Explorer]
Search: "Phytophthora palmivora"
Results: 5 nodes, 3 edges found
Browse: Symptoms, treatments, relationships

[Back to Chat]
You: How do I treat it?
AI: Treatment involves removing affected parts and applying...
    📖 Sources: 2 documents

Session Summary:
  Messages: 4
  Workflow Steps: 6
  Citations: 5
```

---

**Quick Help**: Press `?` in any mode for help (not implemented yet, but planned!)  
**Launch**: `streamlit run app.py`  
**Docs**: `/docs` folder  
**Last Updated**: 2025-10-06
