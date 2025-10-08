# Interactive Streamlit App Guide

## Overview

The Interactive Streamlit App provides a comprehensive interface for conversational AI, workflow investigation, and knowledge graph exploration for the durian pest and disease domain.

**Launch**: `streamlit run app.py`

---

## 🎯 Three Modes of Operation

### 1. 💬 Chat Mode (Conversation Interface)

**Purpose**: Natural conversation with the AI assistant

**Features**:
- **Conversation History**: See all your messages and responses
- **Context Awareness**: Ask follow-up questions
- **Real-time Processing**: Watch the assistant think
- **Citations**: View sources for each answer

**Usage**:
```
You: What causes durian leaf curl?
Assistant: Durian leaf curl is primarily caused by Phytoplasma pathogens...

You: How do I treat it?
Assistant: Treatment for Phytoplasma-induced leaf curl involves...
```

**Best For**:
- General Q&A
- Learning about pests/diseases
- Getting quick answers
- Building on previous questions

---

### 2. 🔍 Investigation Mode (Workflow Deep Dive)

**Purpose**: Understand exactly how the system processes your question

**Features**:
- **Step-by-Step Breakdown**: See each workflow node
- **Timing Information**: When each step executed
- **Retrieved Context**: View actual nodes/edges retrieved
- **Retry Tracking**: See query transformations and quality checks
- **Statistics**: Workflow summary metrics

**Workflow Steps You'll See**:
1. **route_question**: Determines if query goes to KG/Web/LLM
2. **knowledge_graph_retrieval**: Searches the KG
3. **retrieved_documents_grading** (optional): Filters relevance
4. **answer_generation**: Creates the response
5. **Quality checks** (optional): Validates answer

**Usage**:
1. Ask a question in Chat mode
2. Switch to Investigation mode
3. Expand "Step-by-Step Details"
4. Review each step's:
   - Timestamp
   - Retrieved content counts
   - Retry attempts
   - Generated answer

**Example Investigation**:
```
Workflow Summary:
├─ Total Steps: 4
├─ Query Retries: 0
└─ Hallucination Checks: 0

Step 1: Route Question
  Time: 14:32:10.523
  ✓ Routed to: KG_RETRIEVAL

Step 2: Knowledge Graph Retrieval
  Time: 14:32:12.341
  🔹 Nodes Retrieved: 3
  🔸 Edges Retrieved: 2
  
Step 3: Answer Generation
  Time: 14:32:14.156
  ✅ Answer Generated
```

**Best For**:
- Understanding workflow decisions
- Debugging unexpected answers
- Learning how the system works
- Optimizing configurations

---

### 3. 🗺️ KG Explorer Mode (Knowledge Graph Investigation)

**Purpose**: Direct exploration of the knowledge graph

**Features**:
- **Graph Statistics**: Total nodes, edges, entities
- **Direct Search**: Query KG without full workflow
- **Component Selection**: Search only nodes or edges
- **Result Browsing**: Expand and read full content
- **Source Attribution**: See which documents contributed

**KG Statistics Display**:
```
Total Nodes: 1,234
Total Edges: 2,456
Entities: 567
Status: ✅ Active
```

**Direct Search**:
```
Search Query: "Phytophthora palmivora"
Results Limit: 5
Search Type: Both (nodes + edges)

Results:
📄 Nodes:
  1. Phytophthora palmivora is a pathogen causing root rot...
     Source: PL-DR-DP-ED-01.pdf
  
  2. Symptoms include wilting leaves and brown lesions...
     Source: DR-DP-ED-03.pdf

🔗 Edges:
  1. Phytophthora palmivora CAUSES root rot in durian
  2. Phytophthora palmivora TREATED_WITH metalaxyl fungicide
```

**Best For**:
- Exploring specific entities
- Finding relationships between concepts
- Verifying knowledge base content
- Research and learning

---

## ⚙️ Configuration Panel

### Retrieval Settings

**KG Documents (1-10)**:
- How many documents to retrieve from knowledge graph
- **Recommended**: 3-5 for speed, 7-10 for quality
- More documents = more comprehensive but slower

**Web Results (1-10)**:
- Number of web search results (if query requires latest info)
- **Recommended**: 3 for most cases
- Only used when routing determines web search needed

### KG Components

**Nodes (Entities)** ✅:
- Individual entities: pests, diseases, symptoms, treatments
- **Always recommended**: Core knowledge

**Edges (Relationships)** ✅:
- Connections: "X causes Y", "A treats B"
- **Highly recommended**: Provides crucial context
- Adds ~0.5-1s but significantly improves answers

**Episodes (Text)** ⚪:
- Direct text chunks from source documents
- Use when: Need verbatim quotes or detailed passages
- Adds ~1-2s

**Communities** ⚪:
- Clustered knowledge summaries
- Use when: Need broader topic understanding
- Adds ~1-2s

### Quality Control

**Document Grading** ⚪:
- Filters out irrelevant retrieved documents
- **When to enable**: Queries returning off-topic results
- Trade-off: +1-2s per query

**Hallucination Check** ⚪:
- Verifies answer is grounded in retrieved context
- **When to enable**: High-stakes decisions
- Trade-off: +1-2s per query

**Quality Check** ⚪:
- Verifies answer actually addresses the question
- **When to enable**: Answer quality issues
- Trade-off: +2-3s per query

### Recommended Configurations

#### Speed Mode (Default)
```
KG Documents: 3
Nodes: ✅
Edges: ✅
Episodes: ⚪
Communities: ⚪
Document Grading: ⚪
Hallucination Check: ⚪
Quality Check: ⚪

Expected Time: ~2-4 seconds
Quality: Good (80-85%)
```

#### Balanced Mode
```
KG Documents: 5
Nodes: ✅
Edges: ✅
Episodes: ⚪
Communities: ⚪
Document Grading: ✅
Hallucination Check: ⚪
Quality Check: ⚪

Expected Time: ~4-7 seconds
Quality: Better (85-90%)
```

#### Quality Mode
```
KG Documents: 7
Nodes: ✅
Edges: ✅
Episodes: ✅
Communities: ⚪
Document Grading: ✅
Hallucination Check: ✅
Quality Check: ✅

Expected Time: ~10-15 seconds
Quality: Excellent (90-95%)
```

---

## 💡 Usage Examples

### Example 1: Quick Q&A

**Goal**: Get fast answer to simple question

**Steps**:
1. Select "💬 Chat" mode
2. Use Speed Mode configuration
3. Ask: "What causes durian leaf curl?"
4. Get answer in ~3 seconds

---

### Example 2: Deep Investigation

**Goal**: Understand how system arrived at answer

**Steps**:
1. Ask question in Chat mode
2. Switch to "🔍 Investigation" mode
3. Review workflow summary:
   - Which route was taken?
   - How many documents retrieved?
   - Were there any retries?
4. Enable "Show retrieved context"
5. Examine actual node/edge contents
6. Understand decision-making process

---

### Example 3: Knowledge Discovery

**Goal**: Explore what the KG knows about a specific topic

**Steps**:
1. Switch to "🗺️ KG Explorer" mode
2. Enter search query: "stem borers"
3. Set results limit: 10
4. Choose "Both" (nodes + edges)
5. Click "🔎 Search KG"
6. Browse results:
   - Read entity descriptions
   - View relationships
   - Check source documents

---

### Example 4: Conversational Learning

**Goal**: Learn about topic through multi-turn conversation

**Steps**:
1. Chat mode, ask: "What are common durian pests?"
2. Follow up: "Tell me more about the first one"
3. Follow up: "How do I identify it?"
4. Follow up: "What's the best treatment?"
5. Review conversation history
6. Check citations for all answers

---

## 🎨 UI Features

### Chat Messages

**User Messages** (Blue):
```
┌────────────────────────────────┐
│ 👤 You (14:32:10)              │
│                                │
│ What causes durian leaf curl?  │
└────────────────────────────────┘
```

**Assistant Messages** (Green):
```
┌────────────────────────────────┐
│ 🤖 Assistant (14:32:15)        │
│                                │
│ Durian leaf curl is primarily  │
│ caused by Phytophthora...      │
└────────────────────────────────┘
```

### Workflow Steps

```
┌─────────────────────────────────┐
│ 1. Route Question (14:32:10)   │
│    ✓ Routed to KG_RETRIEVAL    │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 2. Knowledge Graph Retrieval    │
│    (14:32:12)                   │
│    🔹 Nodes Retrieved: 3        │
│    🔸 Edges Retrieved: 2        │
└─────────────────────────────────┘
```

### Citations

**Knowledge Graph Sources**:
```
┌────────────────────────────────┐
│ 📖 Knowledge Graph Sources (3) │
├────────────────────────────────┤
│ 1. PL-DR-DP-ED-06-เพลี้ยหอย.pdf │
│ 2. DR-DP-ED-03-โรคของทุเรียน.pdf │
│ 3. PL-DR-DP-THE-03-โรคกิ่งแห้ง... │
└────────────────────────────────┘
```

**Web Sources**:
```
┌────────────────────────────────┐
│ 🌐 Web Sources (2)             │
├────────────────────────────────┤
│ 1. Latest Durian Disease News  │
│    🔗 https://example.com/...   │
│                                │
│ 2. Pest Management Guide       │
│    🔗 https://example.com/...   │
└────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### Issue: "No answer generated"

**Possible causes**:
- No relevant documents found
- Network/API issues
- KG not accessible

**Solutions**:
1. Check KG Explorer - is graph active?
2. Try simpler, more specific question
3. Enable document grading to filter better
4. Check Investigation mode for error details

---

### Issue: "Answer seems off-topic"

**Possible causes**:
- Query misrouted
- Retrieved irrelevant documents
- LLM hallucination

**Solutions**:
1. Check Investigation mode:
   - Was it routed correctly?
   - What documents were retrieved?
2. Enable document grading
3. Enable hallucination checking
4. Rephrase question more specifically

---

### Issue: "Slow performance"

**Possible causes**:
- Too many quality checks enabled
- High retrieval limits
- Episodes/communities enabled

**Solutions**:
1. Use Speed Mode configuration
2. Reduce KG documents to 3
3. Disable episodes and communities
4. Disable quality checks unless needed
5. Keep only Nodes + Edges enabled

---

### Issue: "Can't see workflow steps"

**Solutions**:
1. Make sure you asked a question first
2. Switch to Investigation mode
3. Enable "Show step details" in sidebar
4. Expand "Step-by-Step Details" section

---

## 📊 Metrics & Monitoring

### Session Summary

Track your session statistics:
- **Messages**: Total conversation exchanges
- **Workflow Steps**: Steps executed across all queries
- **Citations**: Total sources used

### Workflow Summary

For each query, track:
- **Total Steps**: How many nodes executed
- **Query Retries**: Query transformations attempted
- **Hallucination Checks**: How many regenerations

### KG Statistics

Monitor graph health:
- **Total Nodes**: All nodes in graph
- **Total Edges**: All relationships
- **Entities**: Entity nodes count
- **Status**: Active/Empty indicator

---

## 💡 Tips & Best Practices

### For Better Answers

1. **Be Specific**:
   - ❌ "Tell me about pests"
   - ✅ "What are symptoms of durian stem borers?"

2. **Enable Edge Retrieval**:
   - Always keep this on for relationship context

3. **Use Follow-ups**:
   - Build on previous answers in chat mode

4. **Check Citations**:
   - Verify source quality and relevance

### For Investigation

1. **Enable Step Details**:
   - See what system is doing

2. **Review Retrieved Content**:
   - Understand what influenced answer

3. **Track Retries**:
   - If many retries, question may be unclear

4. **Compare Configurations**:
   - Try same question with different settings

### For KG Exploration

1. **Start Broad**:
   - Search general terms first
   - Then narrow down

2. **Use Both Modes**:
   - Search nodes for entities
   - Search edges for relationships

3. **Check Sources**:
   - See which documents contributed knowledge

4. **Explore Related**:
   - Use found entities for new searches

---

## 🚀 Keyboard Shortcuts & Tips

- **Enter** in text area: New line (Shift+Enter to send would be nice but not available)
- **Clear Conversation**: Start fresh without restarting app
- **Refresh KG Info**: Update graph statistics
- **Mode Switching**: Instantly switch between Chat/Investigation/Explorer

---

## 📱 Responsive Design

The app adapts to different screen sizes:
- **Wide screens**: Side-by-side layout
- **Medium screens**: Stacked layout with good spacing
- **Mobile**: Vertical layout (best viewed on tablet or desktop)

---

## 🔄 Data Flow

```
User Question
    ↓
Chat Interface
    ↓
Workflow Execution
    ├─→ Route Question
    ├─→ Retrieve from KG/Web
    ├─→ Grade Documents (optional)
    ├─→ Generate Answer
    ├─→ Quality Checks (optional)
    └─→ Return Answer
    ↓
Display in Chat
    ↓
Store in History
    ↓
Investigation Mode Shows:
    ├─ Each step
    ├─ Retrieved content
    ├─ Retry attempts
    └─ Final answer
```

---

## 📚 Related Documentation

- [Workflow Architecture](./WORKFLOW_ARCHITECTURE.md) - System design
- [Workflow Refinements](./WORKFLOW_REFINEMENTS.md) - Recent improvements
- [Routing Guide](./ROUTING_GUIDE.md) - How routing works
- [Graphiti Refinements](./GRAPHITI_REFINEMENTS.md) - KG optimizations

---

## 🎓 Learning Path

### Beginner
1. Start with Chat mode
2. Ask simple questions
3. Review answers and citations
4. Try different question types

### Intermediate
1. Explore Investigation mode
2. Understand workflow steps
3. Experiment with configurations
4. Compare speed vs quality modes

### Advanced
1. Use KG Explorer for research
2. Analyze retrieved context
3. Optimize configuration for your use case
4. Understand retry patterns and edge cases

---

**Last Updated**: 2025-10-06  
**Launch Command**: `streamlit run app.py`  
**Status**: ✅ Ready for Use
