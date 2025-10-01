"""Streamlit application for Adaptive RAG with workflow visualization and citations."""

import asyncio
from typing import Any, Dict, List
from datetime import datetime
import warnings

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

# Fix for event loop issues with Python 3.13 + gRPC + LangChain
import nest_asyncio

nest_asyncio.apply()

# Suppress gRPC warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="grpc")

from src.core.workflow import build_workflow
from src.core.constants import Defaults


# Page configuration
st.set_page_config(
    page_title="Adaptive RAG Chat",
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
    .workflow-step {
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
        background-color: #f0f2f6;
        border-radius: 0.3rem;
    }
    .step-name {
        font-weight: bold;
        color: #1f77b4;
    }
    .citation-box {
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
        border-left: 4px solid #28a745;
        border-radius: 0.3rem;
    }
    .retry-warning {
        padding: 0.5rem;
        margin: 0.5rem 0;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        border-radius: 0.3rem;
    }
    .error-box {
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        border-radius: 0.3rem;
    }
    .stTextInput > div > div > input {
        font-size: 1.1rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# Initialize session state
if "current_question" not in st.session_state:
    st.session_state.current_question = None

if "current_answer" not in st.session_state:
    st.session_state.current_answer = None

if "workflow_steps" not in st.session_state:
    st.session_state.workflow_steps = []

if "citations" not in st.session_state:
    st.session_state.citations = []

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False


def add_workflow_step(step_name: str, details: Dict[str, Any] = None):
    """Add a workflow step to the session state."""
    step = {
        "name": step_name,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "details": details or {},
    }
    st.session_state.workflow_steps.append(step)


def display_workflow_steps(container: DeltaGenerator):
    """Display workflow steps in a container."""
    if not st.session_state.workflow_steps:
        return

    with container:
        st.markdown("### 🔄 Workflow Steps")
        for i, step in enumerate(st.session_state.workflow_steps, 1):
            step_name = step["name"]
            timestamp = step["timestamp"]
            details = step["details"]

            # Format step name for display
            display_name = step_name.replace("_", " ").title()

            st.markdown(
                f"""<div class="workflow-step">
                    <span class="step-name">{i}. {display_name}</span> 
                    <span style="color: #6c757d; font-size: 0.9rem;">({timestamp})</span>
                </div>""",
                unsafe_allow_html=True,
            )

            # Show retry count if present
            if "retry_count" in details:
                retry_count = details["retry_count"]
                if retry_count > 0:
                    st.markdown(
                        f"""<div class="retry-warning">
                            ⚠️ Retry attempt: {retry_count}/{Defaults.MAX_RETRY_COUNT}
                        </div>""",
                        unsafe_allow_html=True,
                    )


def display_citations(container: DeltaGenerator):
    """Display citations in a container."""
    if not st.session_state.citations:
        return

    with container:
        st.markdown("### 📚 Sources & Citations")

        # Web citations
        web_citations = [
            c for c in st.session_state.citations if c.get("type") == "web"
        ]
        if web_citations:
            st.markdown("**Web Sources:**")
            for i, citation in enumerate(web_citations, 1):
                title = citation.get("title", "Untitled")
                url = citation.get("url", "#")
                st.markdown(
                    f"""<div class="citation-box">
                        {i}. <strong>{title}</strong><br>
                        <a href="{url}" target="_blank">🔗 {url}</a>
                    </div>""",
                    unsafe_allow_html=True,
                )

        # Knowledge graph citations (if any)
        kg_citations = [c for c in st.session_state.citations if c.get("type") == "kg"]
        if kg_citations:
            st.markdown("**Knowledge Graph:**")
            for i, citation in enumerate(kg_citations, 1):
                content = citation.get("content", "")
                st.markdown(
                    f"""<div class="citation-box">
                        {i}. {content}
                    </div>""",
                    unsafe_allow_html=True,
                )


async def run_adaptive_rag(
    question: str,
    n_documents: int = Defaults.N_DOCUMENTS,
    n_requests: int = Defaults.N_REQUESTS,
    enable_document_grading: bool = Defaults.ENABLE_DOCUMENT_GRADING,
    enable_generation_grading: bool = Defaults.ENABLE_GENERATION_GRADING,
) -> Dict[str, Any]:
    """Run the adaptive RAG workflow and track steps."""
    # Clear previous workflow steps and citations
    st.session_state.workflow_steps = []
    st.session_state.citations = []

    workflow = (
        await build_workflow(
            enable_document_grading=enable_document_grading,
            enable_generation_grading=enable_generation_grading,
        )
    ).compile()
    inputs = {
        "question": question,
        "n_documents": n_documents,
        "n_requests": n_requests,
        "node_contents": [],
        "edge_contents": [],
        "web_contents": [],
        "web_citations": [],
        "retry_count": 0,
    }

    final_state = None

    try:
        async for output in workflow.astream(inputs):
            for node_name, state in output.items():
                # Add workflow step
                add_workflow_step(
                    node_name,
                    details={
                        "retry_count": state.get("retry_count", 0),
                        "has_node_contents": bool(state.get("node_contents")),
                        "has_edge_contents": bool(state.get("edge_contents")),
                        "has_web_contents": bool(state.get("web_contents")),
                    },
                )
                final_state = state

        # Ensure all async tasks complete
        await asyncio.sleep(0.1)

        # Extract citations
        if final_state:
            web_citations = final_state.get("web_citations", [])
            for citation in web_citations:
                st.session_state.citations.append(
                    {
                        "type": "web",
                        "title": citation.get("title", ""),
                        "url": citation.get("url", ""),
                    }
                )

            # Add KG citations if available
            kg_citations = final_state.get("kg_citations", [])
            for citation in kg_citations:
                st.session_state.citations.append({"type": "kg", "content": citation})

        return {
            "success": True,
            "answer": (
                final_state.get("generation", "No answer generated.")
                if final_state
                else "No answer generated."
            ),
            "state": final_state,
        }

    except Exception as e:
        add_workflow_step("error", details={"error": str(e)})
        return {"success": False, "answer": f"Error: {str(e)}", "state": None}

    finally:
        # Clean up any pending async tasks
        await asyncio.sleep(0.1)


def main():
    """Main Streamlit application."""
    # Header
    st.markdown(
        '<h1 class="main-header">🌿 Adaptive RAG Chat Assistant</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #6c757d;'>Ask questions about durian pests and diseases</p>",
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Retrieval settings
        st.markdown("#### 📊 Retrieval Settings")
        n_documents = st.slider(
            "Number of documents to retrieve",
            min_value=1,
            max_value=10,
            value=Defaults.N_DOCUMENTS,
            help="Number of documents to retrieve from knowledge graph",
        )

        n_requests = st.slider(
            "Number of web search results",
            min_value=1,
            max_value=10,
            value=Defaults.N_REQUESTS,
            help="Number of results from web search",
        )

        st.markdown("---")

        # Workflow optimization settings
        st.markdown("#### ⚡ Workflow Optimization")
        st.markdown(
            "<small>Toggle these to speed up processing</small>",
            unsafe_allow_html=True,
        )

        enable_document_grading = st.checkbox(
            "✅ Document Grading",
            value=Defaults.ENABLE_DOCUMENT_GRADING,
            help="Grade retrieved documents for relevance. Disable for faster processing.",
        )

        enable_generation_grading = st.checkbox(
            "✅ Answer Quality Check",
            value=Defaults.ENABLE_GENERATION_GRADING,
            help="Check generated answers for hallucinations and quality. Disable for faster responses.",
        )

        st.markdown("---")

        # Info display
        st.markdown("### 📊 Current Configuration")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", n_documents)
            st.metric("Web Results", n_requests)
        with col2:
            st.metric("Max Retries", Defaults.MAX_RETRY_COUNT)

        # Optimization status
        optimization_status = []
        if not enable_document_grading:
            optimization_status.append("⚡ Fast mode: Doc grading OFF")
        if not enable_generation_grading:
            optimization_status.append("⚡ Fast mode: Quality check OFF")

        if optimization_status:
            st.warning("\n".join(optimization_status))
        else:
            st.success("🔍 Full quality mode enabled")

        st.markdown("---")

        if st.button("🔄 New Question", use_container_width=True):
            st.session_state.current_question = None
            st.session_state.current_answer = None
            st.session_state.workflow_steps = []
            st.session_state.citations = []
            st.session_state.is_processing = False
            st.rerun()

        st.markdown("---")

        st.markdown("### 💡 Example Questions")
        example_questions = [
            "My young durian leaves are curling and look scorched at the edges, could that be leafhopper damage?",
            "If I only see a few durian scales on some twigs, should I spray the whole block?",
            "What's a good rule for rotating insecticides when dealing with psyllids?",
            "Leaves show powdery white patches—what durian disease could this be?",
            "Which longhorn borer treatments are suitable for large limbs?",
        ]

        for i, example in enumerate(example_questions):
            if st.button(f"Q{i+1}", key=f"example_{i}", help=example):
                st.session_state.example_question = example

    # Main Q&A area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 💬 Question & Answer")

        # Handle example question
        if "example_question" in st.session_state:
            question = st.session_state.example_question
            del st.session_state.example_question
            st.session_state.is_processing = True
        else:
            question = None

        # Display current question if exists
        if st.session_state.current_question:
            st.markdown("#### 🙋 Question:")
            st.info(st.session_state.current_question)

        # Display current answer if exists
        if st.session_state.current_answer:
            st.markdown("#### 🤖 Answer:")
            if isinstance(st.session_state.current_answer, dict):
                if st.session_state.current_answer.get("success"):
                    st.success(st.session_state.current_answer["answer"])
                else:
                    st.error(st.session_state.current_answer["answer"])
            else:
                st.markdown(st.session_state.current_answer)

        # Show input form
        with st.form(key="question_form", clear_on_submit=True):
            user_question = st.text_area(
                "Ask a question about durian pests and diseases:",
                height=100,
                placeholder="e.g., What causes durian leaf curl?",
                disabled=st.session_state.is_processing,
            )
            submit_button = st.form_submit_button(
                "🔍 Get Answer",
                use_container_width=True,
                disabled=st.session_state.is_processing,
            )

            if submit_button and user_question:
                question = user_question
                st.session_state.is_processing = True

        # Process question if we have one
        if question and st.session_state.is_processing:
            # Store the question
            st.session_state.current_question = question

            # Show processing status
            with st.spinner("🤔 Thinking and searching..."):
                # Run workflow with proper error handling
                try:
                    result = asyncio.run(
                        run_adaptive_rag(
                            question=question,
                            n_documents=n_documents,
                            n_requests=n_requests,
                            enable_document_grading=enable_document_grading,
                            enable_generation_grading=enable_generation_grading,
                        )
                    )
                except Exception as e:
                    result = {
                        "success": False,
                        "answer": f"Error executing workflow: {str(e)}",
                        "state": None,
                    }

            # Store the answer
            st.session_state.current_answer = result
            st.session_state.is_processing = False

            # Force rerun to display results
            st.rerun()

    with col2:
        # Create containers for workflow steps and citations
        workflow_container = st.container()
        citation_container = st.container()

        # Display workflow steps
        display_workflow_steps(workflow_container)

        # Display citations
        display_citations(citation_container)


if __name__ == "__main__":
    main()
