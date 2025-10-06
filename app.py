"""Interactive Streamlit app for Adaptive RAG with conversation, workflow investigation, and KG exploration."""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import warnings
import json

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

# Fix for event loop issues with Python 3.13 + gRPC + LangChain
import nest_asyncio
nest_asyncio.apply()

# Suppress gRPC warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="grpc")

from src.core.workflow import build_workflow
from src.core.constants import Defaults
from src.core.graphiti import get_graphiti_client, get_graph_info


# Create a single global loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Page configuration
st.set_page_config(
    page_title="Durian Pest & Disease Chat",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better UI
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f1f8e9;
        border-left: 4px solid #8bc34a;
    }
    .workflow-step {
        padding: 0.5rem;
        margin: 0.3rem 0;
        border-left: 3px solid #1f77b4;
        background-color: #f0f2f6;
        border-radius: 0.3rem;
        font-size: 0.9rem;
    }
    .step-name {
        font-weight: bold;
        color: #1f77b4;
    }
    .step-details {
        font-size: 0.85rem;
        color: #6c757d;
        margin-top: 0.3rem;
    }
    .citation-box {
        padding: 0.8rem;
        margin: 0.3rem 0;
        background-color: #f8f9fa;
        border-left: 3px solid #28a745;
        border-radius: 0.3rem;
        font-size: 0.9rem;
    }
    .retry-warning {
        padding: 0.5rem;
        margin: 0.3rem 0;
        background-color: #fff3cd;
        border-left: 3px solid #ffc107;
        border-radius: 0.3rem;
        font-size: 0.85rem;
    }
    .kg-info-box {
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        border-radius: 0.3rem;
    }
    .context-box {
        padding: 0.8rem;
        margin: 0.5rem 0;
        background-color: #f5f5f5;
        border: 1px solid #ddd;
        border-radius: 0.3rem;
        font-size: 0.85rem;
        max-height: 200px;
        overflow-y: auto;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# Initialize session state
def init_session_state():
    """Initialize all session state variables."""
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    if "workflow_steps" not in st.session_state:
        st.session_state.workflow_steps = []
    
    if "citations" not in st.session_state:
        st.session_state.citations = []
    
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    
    if "current_step_details" not in st.session_state:
        st.session_state.current_step_details = {}
    
    if "kg_info" not in st.session_state:
        st.session_state.kg_info = None
    
    if "show_step_details" not in st.session_state:
        st.session_state.show_step_details = True
    
    if "show_context_info" not in st.session_state:
        st.session_state.show_context_info = False


init_session_state()


def add_message_to_conversation(role: str, content: str, metadata: Optional[Dict] = None):
    """Add a message to the conversation history."""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "metadata": metadata or {}
    }
    st.session_state.conversation_history.append(message)


def add_workflow_step(step_name: str, state: Dict[str, Any]):
    """Add a workflow step with detailed information."""
    step = {
        "name": step_name,
        "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "state": state,
    }
    st.session_state.workflow_steps.append(step)
    
    # Store current step details for investigation
    st.session_state.current_step_details[step_name] = {
        "timestamp": step["timestamp"],
        "question": state.get("question", ""),
        "node_contents": state.get("node_contents", []),
        "edge_contents": state.get("edge_contents", []),
        "web_contents": state.get("web_contents", []),
        "node_citations": state.get("node_citations", []),
        "edge_citations": state.get("edge_citations", []),
        "web_citations": state.get("web_citations", []),
        "generation": state.get("generation", ""),
        "query_transformation_retry_count": state.get("query_transformation_retry_count", 0),
        "hallucination_retry_count": state.get("hallucination_retry_count", 0),
    }


def display_conversation():
    """Display the conversation history."""
    st.markdown("### 💬 Conversation History")
    
    if not st.session_state.conversation_history:
        st.info("👋 Start a conversation by asking a question below!")
        return
    
    for msg in st.session_state.conversation_history:
        role = msg["role"]
        content = msg["content"]
        timestamp = msg["timestamp"]
        
        if role == "user":
            st.markdown(
                f"""<div class="chat-message user-message">
                    <strong>👤 You</strong> <span style="color: #6c757d; font-size: 0.85rem;">({timestamp})</span><br>
                    {content}
                </div>""",
                unsafe_allow_html=True,
            )
        else:  # assistant
            st.markdown(
                f"""<div class="chat-message assistant-message">
                    <strong>🤖 Assistant</strong> <span style="color: #6c757d; font-size: 0.85rem;">({timestamp})</span><br>
                    {content}
                </div>""",
                unsafe_allow_html=True,
            )


def display_workflow_investigation():
    """Display detailed workflow step investigation."""
    st.markdown("### 🔍 Workflow Investigation")
    
    if not st.session_state.workflow_steps:
        st.info("No workflow steps yet. Ask a question to see the workflow in action!")
        return
    
    # Workflow summary
    with st.expander("📊 Workflow Summary", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Steps", len(st.session_state.workflow_steps))
        with col2:
            retry_count = sum(
                step["state"].get("query_transformation_retry_count", 0)
                for step in st.session_state.workflow_steps
            )
            st.metric("Query Retries", retry_count)
        with col3:
            hallucination_count = sum(
                step["state"].get("hallucination_retry_count", 0)
                for step in st.session_state.workflow_steps
            )
            st.metric("Hallucination Checks", hallucination_count)
    
    # Detailed step investigation
    if st.session_state.show_step_details:
        with st.expander("🔬 Step-by-Step Details", expanded=False):
            for i, step in enumerate(st.session_state.workflow_steps, 1):
                step_name = step["name"]
                timestamp = step["timestamp"]
                state = step["state"]
                
                display_name = step_name.replace("_", " ").title()
                
                st.markdown(f"#### {i}. {display_name}")
                st.markdown(f"**Time:** {timestamp}")
                
                # Step-specific information
                col1, col2 = st.columns(2)
                
                with col1:
                    if state.get("node_contents"):
                        st.write(f"🔹 **Nodes Retrieved:** {len(state['node_contents'])}")
                    if state.get("edge_contents"):
                        st.write(f"🔸 **Edges Retrieved:** {len(state['edge_contents'])}")
                    if state.get("web_contents"):
                        st.write(f"🌐 **Web Results:** {len(state['web_contents'])}")
                
                with col2:
                    if state.get("query_transformation_retry_count", 0) > 0:
                        st.warning(f"⚠️ Query Retry: {state['query_transformation_retry_count']}")
                    if state.get("hallucination_retry_count", 0) > 0:
                        st.warning(f"⚠️ Hallucination Check: {state['hallucination_retry_count']}")
                    if state.get("generation"):
                        st.success("✅ Answer Generated")
                
                # Show retrieved context if available
                if st.session_state.show_context_info:
                    if state.get("node_contents"):
                        with st.expander(f"📄 Node Contents ({len(state['node_contents'])})", expanded=False):
                            for j, content in enumerate(state["node_contents"][:3], 1):  # Show first 3
                                st.markdown(f"**Entity {j}:**")
                                st.markdown(f'<div class="context-box">{content[:200]}...</div>', unsafe_allow_html=True)
                    
                    if state.get("edge_contents"):
                        with st.expander(f"🔗 Edge Contents ({len(state['edge_contents'])})", expanded=False):
                            for j, content in enumerate(state["edge_contents"][:3], 1):
                                st.markdown(f"**Relationship {j}:**")
                                st.markdown(f'<div class="context-box">{content}</div>', unsafe_allow_html=True)
                
                st.markdown("---")


def display_kg_exploration():
    """Display Knowledge Graph exploration interface."""
    st.markdown("### 🗺️ Knowledge Graph Explorer")
    
    # Load KG info if not already loaded
    if st.session_state.kg_info is None:
        with st.spinner("Loading KG information..."):
            try:
                kg_info = loop.run_until_complete(get_graph_info())
                st.session_state.kg_info = kg_info
            except Exception as e:
                st.error(f"Failed to load KG info: {e}")
                return
    
    kg_info = st.session_state.kg_info
    
    # Display KG statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Nodes", kg_info.get("node_count", 0), help="All nodes in the graph")
    with col2:
        st.metric("Total Edges", kg_info.get("edge_count", 0), help="All relationships")
    with col3:
        st.metric("Entities", kg_info.get("entity_count", 0), help="Entity nodes (pests, diseases, etc.)")
    with col4:
        if kg_info.get("is_empty"):
            st.warning("⚠️ Empty")
        else:
            st.success("✅ Active")
    
    # KG exploration options
    with st.expander("🔍 Search Knowledge Graph", expanded=False):
        st.markdown("**Quick KG Search** (separate from main workflow)")
        
        kg_query = st.text_input(
            "Enter search query:",
            placeholder="e.g., Phytophthora palmivora",
            key="kg_search_query"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            search_limit = st.slider("Results limit", 1, 10, 5, key="kg_search_limit")
        with col2:
            search_type = st.selectbox(
                "Search type",
                ["Nodes only", "Edges only", "Both"],
                index=2,
                key="kg_search_type"
            )
        
        if st.button("🔎 Search KG", key="kg_search_button"):
            if kg_query:
                with st.spinner("Searching Knowledge Graph..."):
                    try:
                        from src.core.functions import search_durian_pest_and_disease_knowledge
                        
                        node_ret = search_type in ["Nodes only", "Both"]
                        edge_ret = search_type in ["Edges only", "Both"]
                        
                        results = loop.run_until_complete(
                            search_durian_pest_and_disease_knowledge(
                                question=kg_query,
                                limit=search_limit,
                                node_retrieval=node_ret,
                                edge_retrieval=edge_ret,
                                episode_retrieval=False,
                                community_retrieval=False,
                            )
                        )
                        
                        node_contents, edge_contents, node_cites, edge_cites = results
                        
                        st.success(f"✅ Found {len(node_contents)} nodes, {len(edge_contents)} edges")
                        
                        if node_contents:
                            st.markdown("**📄 Nodes:**")
                            for i, content in enumerate(node_contents, 1):
                                with st.expander(f"Node {i}", expanded=i==1):
                                    st.markdown(content)
                                    if i-1 < len(node_cites) and node_cites[i-1].get("title"):
                                        st.caption(f"Source: {node_cites[i-1]['title']}")
                        
                        if edge_contents:
                            st.markdown("**🔗 Edges:**")
                            for i, content in enumerate(edge_contents, 1):
                                with st.expander(f"Edge {i}", expanded=i==1):
                                    st.markdown(content)
                                    if i-1 < len(edge_cites) and edge_cites[i-1].get("title"):
                                        st.caption(f"Source: {edge_cites[i-1]['title']}")
                        
                        if not node_contents and not edge_contents:
                            st.warning("No results found for this query.")
                    
                    except Exception as e:
                        st.error(f"Search failed: {e}")
            else:
                st.warning("Please enter a search query")


def display_citations():
    """Display citations from the workflow."""
    st.markdown("### 📚 Sources & Citations")
    
    if not st.session_state.citations:
        st.info("No citations yet")
        return
    
    # Separate citations by type
    kg_citations = [c for c in st.session_state.citations if c.get("type") == "kg"]
    web_citations = [c for c in st.session_state.citations if c.get("type") == "web"]
    
    if kg_citations:
        with st.expander(f"📖 Knowledge Graph Sources ({len(kg_citations)})", expanded=True):
            for i, citation in enumerate(kg_citations, 1):
                st.markdown(
                    f'<div class="citation-box">{i}. {citation.get("content", "")}</div>',
                    unsafe_allow_html=True,
                )
    
    if web_citations:
        with st.expander(f"🌐 Web Sources ({len(web_citations)})", expanded=True):
            for i, citation in enumerate(web_citations, 1):
                title = citation.get("title", "Untitled")
                url = citation.get("url", "#")
                st.markdown(
                    f"""<div class="citation-box">
                        {i}. <strong>{title}</strong><br>
                        <a href="{url}" target="_blank" style="color: #2196f3;">🔗 {url}</a>
                    </div>""",
                    unsafe_allow_html=True,
                )


async def run_adaptive_rag_workflow(
    question: str,
    n_retrieved_documents: int,
    n_web_searches: int,
    node_retrieval: bool,
    edge_retrieval: bool,
    episode_retrieval: bool,
    community_retrieval: bool,
    enable_retrieved_document_grading: bool,
    enable_hallucination_checking: bool,
    enable_answer_quality_checking: bool,
) -> Dict[str, Any]:
    """Run the adaptive RAG workflow with step tracking."""
    # Clear previous workflow data for new question
    st.session_state.workflow_steps = []
    st.session_state.citations = []
    st.session_state.current_step_details = {}
    
    workflow = (
        await build_workflow(
            enable_retrieved_document_grading=enable_retrieved_document_grading,
            enable_hallucination_checking=enable_hallucination_checking,
            enable_answer_quality_checking=enable_answer_quality_checking,
        )
    ).compile()
    
    inputs = {
        "question": question,
        "n_retrieved_documents": n_retrieved_documents,
        "n_web_searches": n_web_searches,
        "node_retrieval": node_retrieval,
        "edge_retrieval": edge_retrieval,
        "episode_retrieval": episode_retrieval,
        "community_retrieval": community_retrieval,
        "node_contents": [],
        "edge_contents": [],
        "web_contents": [],
        "node_citations": [],
        "edge_citations": [],
        "web_citations": [],
        "citations": [],
        "query_transformation_retry_count": 0,
        "hallucination_retry_count": 0,
    }
    
    final_state = None
    
    try:
        async for output in workflow.astream(inputs):
            for node_name, state in output.items():
                add_workflow_step(node_name, state)
                final_state = state
        
        await asyncio.sleep(0.1)
        
        # Extract citations
        if final_state:
            citations = final_state.get("citations", [])
            for citation in citations:
                if citation.get("url"):
                    st.session_state.citations.append({
                        "type": "web",
                        "title": citation.get("title", ""),
                        "url": citation.get("url", ""),
                    })
                else:
                    st.session_state.citations.append({
                        "type": "kg",
                        "content": citation.get("title", ""),
                    })
        
        return {
            "success": True,
            "answer": final_state.get("generation", "No answer generated.") if final_state else "No answer generated.",
            "state": final_state,
        }
    
    except Exception as e:
        return {
            "success": False,
            "answer": f"Error: {str(e)}",
            "state": None,
        }
    
    finally:
        await asyncio.sleep(0.1)


def main():
    """Main Streamlit application."""
    # Header
    st.markdown(
        '<h1 class="main-header">🌿 Durian Pest & Disease Interactive Assistant</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #6c757d;'>Conversational AI with workflow investigation and KG exploration</p>",
        unsafe_allow_html=True,
    )
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Tab selection
        tab = st.radio(
            "Select Mode:",
            ["💬 Chat", "🔍 Investigation", "🗺️ KG Explorer"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Retrieval settings
        st.markdown("#### 📊 Retrieval Settings")
        n_retrieved_documents = st.slider(
            "KG documents",
            1, 10,
            Defaults.N_RETRIEVED_DOCUMENTS,
            help="Number of documents from knowledge graph"
        )
        
        n_web_searches = st.slider(
            "Web results",
            1, 10,
            Defaults.N_WEB_SEARCHES,
            help="Number of web search results"
        )
        
        # KG retrieval types
        st.markdown("#### 🔍 KG Components")
        node_retrieval = st.checkbox(
            "Nodes (Entities)",
            value=True,
            help="Retrieve entity nodes"
        )
        edge_retrieval = st.checkbox(
            "Edges (Relationships)",
            value=True,
            help="Retrieve relationships - RECOMMENDED for better answers"
        )
        episode_retrieval = st.checkbox(
            "Episodes (Text)",
            value=Defaults.EPISODE_RETRIEVAL,
            help="Retrieve text chunks"
        )
        community_retrieval = st.checkbox(
            "Communities",
            value=Defaults.COMMUNITY_RETRIEVAL,
            help="Retrieve community summaries"
        )
        
        st.markdown("---")
        
        # Quality control
        st.markdown("#### ⚡ Quality Control")
        enable_retrieved_document_grading = st.checkbox(
            "Document Grading",
            value=Defaults.ENABLE_RETRIEVED_DOCUMENTS_GRADING,
            help="Filter irrelevant documents (+1-2s)"
        )
        enable_hallucination_checking = st.checkbox(
            "Hallucination Check",
            value=Defaults.ENABLE_HALLUCINATION_CHECKING,
            help="Verify answer grounding (+1-2s)"
        )
        enable_answer_quality_checking = st.checkbox(
            "Quality Check",
            value=Defaults.ENABLE_ANSWER_QUALITY_CHECKING,
            help="Verify answer addresses question (+2-3s)"
        )
        
        st.markdown("---")
        
        # Display options
        st.markdown("#### 👁️ Display Options")
        st.session_state.show_step_details = st.checkbox(
            "Show step details",
            value=True,
            help="Show detailed workflow steps"
        )
        st.session_state.show_context_info = st.checkbox(
            "Show retrieved context",
            value=False,
            help="Show node/edge contents in investigation"
        )
        
        st.markdown("---")
        
        # Action buttons
        if st.button("🔄 Clear Conversation", use_container_width=True):
            st.session_state.conversation_history = []
            st.session_state.workflow_steps = []
            st.session_state.citations = []
            st.session_state.current_step_details = {}
            st.rerun()
        
        if st.button("🔄 Refresh KG Info", use_container_width=True):
            st.session_state.kg_info = None
            st.rerun()
        
        st.markdown("---")
        
        # Quick tips
        st.markdown("### 💡 Quick Tips")
        with st.expander("Usage Guide", expanded=False):
            st.markdown("""
            **💬 Chat Mode:**
            - Have conversations with the assistant
            - Ask follow-up questions
            - View conversation history
            
            **🔍 Investigation Mode:**
            - See each workflow step
            - Track retries and checks
            - View retrieved context
            
            **🗺️ KG Explorer:**
            - View graph statistics
            - Search knowledge graph directly
            - Explore entities and relationships
            """)
    
    # Main content area - tabs
    if tab == "💬 Chat":
        # Chat interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            display_conversation()
            
            # Chat input
            st.markdown("---")
            user_input = st.text_area(
                "Your question:",
                height=100,
                placeholder="Ask about durian pests and diseases...",
                disabled=st.session_state.is_processing,
                key="chat_input"
            )
            
            col_btn1, col_btn2 = st.columns([1, 4])
            with col_btn1:
                send_button = st.button(
                    "📤 Send",
                    use_container_width=True,
                    disabled=st.session_state.is_processing or not user_input
                )
            
            if send_button and user_input:
                # Add user message to conversation
                add_message_to_conversation("user", user_input)
                st.session_state.is_processing = True
                
                # Show processing
                with st.spinner("🤔 Processing your question..."):
                    try:
                        result = loop.run_until_complete(
                            run_adaptive_rag_workflow(
                                question=user_input,
                                n_retrieved_documents=n_retrieved_documents,
                                n_web_searches=n_web_searches,
                                node_retrieval=node_retrieval,
                                edge_retrieval=edge_retrieval,
                                episode_retrieval=episode_retrieval,
                                community_retrieval=community_retrieval,
                                enable_retrieved_document_grading=enable_retrieved_document_grading,
                                enable_hallucination_checking=enable_hallucination_checking,
                                enable_answer_quality_checking=enable_answer_quality_checking,
                            )
                        )
                        
                        # Add assistant response
                        answer = result["answer"]
                        add_message_to_conversation("assistant", answer, metadata={"result": result})
                        
                    except Exception as e:
                        add_message_to_conversation("assistant", f"❌ Error: {str(e)}")
                
                st.session_state.is_processing = False
                st.rerun()
        
        with col2:
            # Quick summary
            st.markdown("### 📊 Session Summary")
            st.metric("Messages", len(st.session_state.conversation_history))
            st.metric("Workflow Steps", len(st.session_state.workflow_steps))
            st.metric("Citations", len(st.session_state.citations))
            
            # Citations
            if st.session_state.citations:
                st.markdown("---")
                display_citations()
    
    elif tab == "🔍 Investigation":
        # Investigation interface
        display_workflow_investigation()
    
    else:  # KG Explorer
        # KG exploration interface
        display_kg_exploration()


if __name__ == "__main__":
    main()
