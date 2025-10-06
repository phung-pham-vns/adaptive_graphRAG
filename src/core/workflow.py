from typing import Literal
from pprint import pprint

from langgraph.graph import END, StateGraph, START

from src.core.functions import (
    GraphState,
    format_context,
    web_search,
    knowledge_graph_retrieval,
    retrieved_documents_grading,
    query_transformation,
    answer_generation,
)
from src.core.chains import (
    question_router,
    answer_grader,
    hallucination_grader,
)
from src.core.constants import BinaryScore, LogMessages, RouteDecision, Defaults


async def route_question(
    state: GraphState,
) -> Literal["web_search", "kg_retrieval", "answer_generation"]:
    """Route the question to the appropriate data source."""
    print(LogMessages.ROUTE_QUESTION)
    try:
        source = await question_router.ainvoke({"question": state["question"]})
        route = source.data_source
        print(LogMessages.ROUTE_TO.format(route.upper()))
        # If llm_internal, route directly to answer_generation (with no context)
        if route == RouteDecision.LLM_INTERNAL:
            return RouteDecision.ANSWER_GENERATION
        return route
    except Exception as e:
        print(
            LogMessages.ERROR_IN.format(
                "ROUTING", f"{e}, DEFAULTING TO ANSWER GENERATION"
            )
        )
        return RouteDecision.ANSWER_GENERATION


async def decide_to_generate(
    state: GraphState,
) -> Literal["query_transformation", "answer_generation", "web_search"]:
    """Decide whether to generate an answer, transform the query, or fallback to web search."""
    print(LogMessages.ASSESS_GRADED_DOCUMENTS)

    # Check if we have relevant documents
    if not state["node_contents"] and not state["edge_contents"]:
        print(LogMessages.DECISION_ALL_DOCUMENTS_NOT_RELEVANT)

        # Check retry count to prevent infinite loops
        current_retry = state.get("query_transformation_retry_count", 0)
        if current_retry >= Defaults.MAX_QUERY_TRANSFORMATION_RETRIES:
            print(
                LogMessages.MAX_RETRIES_REACHED.format(
                    current_retry,
                    Defaults.MAX_QUERY_TRANSFORMATION_RETRIES,
                    "WEB SEARCH",
                )
            )
            return RouteDecision.WEB_SEARCH

        return RouteDecision.QUERY_TRANSFORMATION

    print(LogMessages.DECISION_GENERATE)
    return RouteDecision.ANSWER_GENERATION


async def grade_generation_and_context(
    state: GraphState,
) -> Literal["not_grounded", "grounded"]:
    """Check if the generated answer is grounded in the context.

    Performs hallucination check: Is answer grounded in context?
    """
    print(LogMessages.CHECK_HALLUCINATIONS)
    try:
        node_contents = state.get("node_contents", None)
        edge_contents = state.get("edge_contents", None)
        web_contents = state.get("web_contents", None)
        node_citations = state.get("node_citations", None)
        edge_citations = state.get("edge_citations", None)
        web_citations = state.get("web_citations", None)
        context = format_context(
            node_contents,
            edge_contents,
            web_contents,
            node_citations,
            edge_citations,
            web_citations,
        )
        hallucination_score = await hallucination_grader.ainvoke(
            {"documents": context, "generation": state["generation"]}
        )

        if hallucination_score.binary_score != BinaryScore.YES:
            # Check retry count to prevent infinite loops
            current_hallucination_retry = state.get("hallucination_retry_count", 0)
            if current_hallucination_retry >= Defaults.MAX_HALLUCINATION_RETRIES:
                print(
                    LogMessages.MAX_RETRIES_REACHED.format(
                        current_hallucination_retry,
                        Defaults.MAX_HALLUCINATION_RETRIES,
                        "GROUNDED (BEST EFFORT)",
                    )
                )
                # Return as grounded to end workflow with best effort answer
                return RouteDecision.GROUNDED

            print(
                LogMessages.RETRY_COUNT_INFO.format(
                    current_hallucination_retry + 1, Defaults.MAX_HALLUCINATION_RETRIES
                )
            )
            print(LogMessages.DECISION_NOT_GROUNDED)
            return RouteDecision.NOT_GROUNDED

        print(LogMessages.DECISION_GROUNDED)
        return RouteDecision.GROUNDED

    except Exception as e:
        print(LogMessages.ERROR_IN.format("HALLUCINATION GRADING", e))
        # On error, return grounded to end workflow with best effort answer
        return RouteDecision.GROUNDED


async def grade_generation_and_question(
    state: GraphState,
) -> Literal["incorrect", "correct"]:
    """Check if the generated answer addresses the question.

    Performs answer quality check: Does answer address the question?
    """
    print(LogMessages.CHECK_ANSWER_QUALITY)
    try:
        answer_score = await answer_grader.ainvoke(
            {
                "question": state["question"],
                "generation": state["generation"],
            }
        )

        if answer_score.binary_score == BinaryScore.YES:
            print(LogMessages.DECISION_ADDRESSES_QUESTION)
            return RouteDecision.CORRECT

        # Check retry count before looping back to query_transformation
        current_retry = state.get("query_transformation_retry_count", 0)
        if current_retry >= Defaults.MAX_QUERY_TRANSFORMATION_RETRIES:
            print(
                LogMessages.MAX_RETRIES_REACHED.format(
                    current_retry,
                    Defaults.MAX_QUERY_TRANSFORMATION_RETRIES,
                    "END (BEST EFFORT)",
                )
            )
            # Return as corect to end workflow with best effort answer
            return RouteDecision.CORRECT

        print(LogMessages.DECISION_NOT_ADDRESSES_QUESTION)
        return RouteDecision.INCORRECT

    except Exception as e:
        print(LogMessages.ERROR_IN.format("ANSWER QUALITY GRADING", e))
        # On error, return corect to end workflow with best effort answer
        return RouteDecision.CORRECT


async def build_workflow(
    enable_retrieved_document_grading: bool = Defaults.ENABLE_RETRIEVED_DOCUMENTS_GRADING,
    enable_hallucination_checking: bool = Defaults.ENABLE_HALLUCINATION_CHECKING,
    enable_answer_quality_checking: bool = Defaults.ENABLE_ANSWER_QUALITY_CHECKING,
) -> StateGraph[GraphState]:
    """Build and configure the LangGraph workflow with optional optimization flags.

    Args:
        enable_retrieved_document_grading: If True, grade retrieved documents for relevance
        enable_hallucination_checking: If True, check if generated answer is grounded in context
        enable_answer_quality_checking: If True, check if generated answer addresses the question
    """
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("web_search", web_search)
    workflow.add_node("knowledge_graph_retrieval", knowledge_graph_retrieval)
    workflow.add_node("answer_generation", answer_generation)
    workflow.add_node("query_transformation", query_transformation)

    # Conditionally add grading nodes
    if enable_retrieved_document_grading:
        workflow.add_node("retrieved_documents_grading", retrieved_documents_grading)

    # Define edges
    workflow.add_conditional_edges(
        START,
        route_question,
        {
            RouteDecision.WEB_SEARCH: "web_search",
            RouteDecision.KG_RETRIEVAL: "knowledge_graph_retrieval",
            RouteDecision.ANSWER_GENERATION: "answer_generation",  # LLM internal routes here with no context
        },
    )
    workflow.add_edge("web_search", "answer_generation")

    # Configure KG retrieval flow based on document grading flag
    if enable_retrieved_document_grading:
        # With grading: KG → grading → decide → answer/transform
        workflow.add_edge("knowledge_graph_retrieval", "retrieved_documents_grading")
        workflow.add_conditional_edges(
            "retrieved_documents_grading",
            decide_to_generate,
            {
                RouteDecision.QUERY_TRANSFORMATION: "query_transformation",
                RouteDecision.ANSWER_GENERATION: "answer_generation",
                RouteDecision.WEB_SEARCH: "web_search",
            },
        )
    else:
        # Without grading: KG → answer directly
        workflow.add_edge("knowledge_graph_retrieval", "answer_generation")

    workflow.add_edge("query_transformation", "knowledge_graph_retrieval")

    # Configure answer generation flow based on grading flags
    # We need to handle 4 cases:
    # 1. Both enabled: hallucination → quality → end
    # 2. Only hallucination: hallucination → end
    # 3. Only quality: quality → end
    # 4. Neither: direct → end

    if enable_hallucination_checking and enable_answer_quality_checking:
        # Both checks enabled: chain them together
        async def answer_quality_check(state: GraphState) -> GraphState:
            """Passthrough node for answer quality checking routing."""
            return state

        async def increment_hallucination_retry(state: GraphState) -> GraphState:
            """Increment hallucination retry count before regenerating."""
            current_retry = state.get("hallucination_retry_count", 0)
            return {"hallucination_retry_count": current_retry + 1}

        workflow.add_node("answer_quality_check", answer_quality_check)
        workflow.add_node(
            "increment_hallucination_retry", increment_hallucination_retry
        )

        # First check: Is generation grounded in context?
        workflow.add_conditional_edges(
            "answer_generation",
            grade_generation_and_context,
            {
                RouteDecision.NOT_GROUNDED: "increment_hallucination_retry",  # Increment retry count
                RouteDecision.GROUNDED: "answer_quality_check",  # Check answer quality if grounded
            },
        )

        # After incrementing retry count, regenerate answer
        workflow.add_edge("increment_hallucination_retry", "answer_generation")

        # Second check: Does generation address the question?
        workflow.add_conditional_edges(
            "answer_quality_check",
            grade_generation_and_question,
            {
                RouteDecision.INCORRECT: "query_transformation",  # Transform query if not useful
                RouteDecision.CORRECT: END,  # End if useful
            },
        )
    elif enable_hallucination_checking:
        # Only hallucination check enabled
        async def increment_hallucination_retry(state: GraphState) -> GraphState:
            """Increment hallucination retry count before regenerating."""
            current_retry = state.get("hallucination_retry_count", 0)
            return {"hallucination_retry_count": current_retry + 1}

        workflow.add_node(
            "increment_hallucination_retry", increment_hallucination_retry
        )

        workflow.add_conditional_edges(
            "answer_generation",
            grade_generation_and_context,
            {
                RouteDecision.NOT_GROUNDED: "increment_hallucination_retry",  # Increment retry count
                RouteDecision.GROUNDED: END,  # End if grounded
            },
        )

        # After incrementing retry count, regenerate answer
        workflow.add_edge("increment_hallucination_retry", "answer_generation")
    elif enable_answer_quality_checking:
        # Only answer quality check enabled
        workflow.add_conditional_edges(
            "answer_generation",
            grade_generation_and_question,
            {
                RouteDecision.INCORRECT: "query_transformation",  # Transform query if not useful
                RouteDecision.CORRECT: END,  # End if useful
            },
        )
    else:
        # Neither check enabled: answer directly ends workflow
        workflow.add_edge("answer_generation", END)

    return workflow


async def run_workflow(
    question: str,
    n_retrieved_documents: int = Defaults.N_RETRIEVED_DOCUMENTS,
    n_web_searches: int = Defaults.N_WEB_SEARCHES,
    node_retrieval: bool = Defaults.NODE_RETRIEVAL,
    edge_retrieval: bool = Defaults.EDGE_RETRIEVAL,
    episode_retrieval: bool = Defaults.EPISODE_RETRIEVAL,
    community_retrieval: bool = Defaults.COMMUNITY_RETRIEVAL,
    enable_retrieved_document_grading: bool = Defaults.ENABLE_RETRIEVED_DOCUMENTS_GRADING,
    enable_hallucination_checking: bool = Defaults.ENABLE_HALLUCINATION_CHECKING,
    enable_answer_quality_checking: bool = Defaults.ENABLE_ANSWER_QUALITY_CHECKING,
) -> None:
    """Run the workflow with the given question and configuration options."""
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
    try:
        async for output in workflow.astream(inputs):
            for key, value in output.items():
                print(f"Node '{key.upper()}'")
        answer = value.get("generation", "No final answer generated.")
        citations = value.get("citations", [])

        return {"answer": answer, "citations": citations}

    except Exception as e:
        print(f"Error during workflow execution: {e}")
        return {"answer": "No final answer generated.", "citations": []}


# Example usage
if __name__ == "__main__":
    import asyncio
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the Adaptive RAG workflow with custom configuration"
    )

    # Required argument
    parser.add_argument(
        "-q",
        "--question",
        type=str,
        required=True,
        help="The question to ask the adaptive RAG system",
    )

    # Retrieval parameters
    parser.add_argument(
        "--n-retrieved-documents",
        type=int,
        default=Defaults.N_RETRIEVED_DOCUMENTS,
        help=f"Number of documents to retrieve from knowledge graph (default: {Defaults.N_RETRIEVED_DOCUMENTS})",
    )
    parser.add_argument(
        "--n-web-searches",
        type=int,
        default=Defaults.N_WEB_SEARCHES,
        help=f"Number of web search results to fetch (default: {Defaults.N_WEB_SEARCHES})",
    )

    # Knowledge graph retrieval types
    parser.add_argument(
        "--node-retrieval",
        action="store_true",
        default=Defaults.NODE_RETRIEVAL,
        help="Enable node retrieval from knowledge graph",
    )
    parser.add_argument(
        "--no-node-retrieval",
        dest="node_retrieval",
        action="store_false",
        help="Disable node retrieval from knowledge graph",
    )
    parser.add_argument(
        "--edge-retrieval",
        action="store_true",
        default=Defaults.EDGE_RETRIEVAL,
        help="Enable edge retrieval from knowledge graph",
    )
    parser.add_argument(
        "--no-edge-retrieval",
        dest="edge_retrieval",
        action="store_false",
        help="Disable edge retrieval from knowledge graph",
    )
    parser.add_argument(
        "--episode-retrieval",
        action="store_true",
        default=Defaults.EPISODE_RETRIEVAL,
        help="Enable episode retrieval from knowledge graph",
    )
    parser.add_argument(
        "--no-episode-retrieval",
        dest="episode_retrieval",
        action="store_false",
        help="Disable episode retrieval from knowledge graph",
    )
    parser.add_argument(
        "--community-retrieval",
        action="store_true",
        default=Defaults.COMMUNITY_RETRIEVAL,
        help="Enable community retrieval from knowledge graph",
    )
    parser.add_argument(
        "--no-community-retrieval",
        dest="community_retrieval",
        action="store_false",
        help="Disable community retrieval from knowledge graph",
    )

    # Quality control options
    parser.add_argument(
        "--enable-document-grading",
        dest="enable_retrieved_document_grading",
        action="store_true",
        default=Defaults.ENABLE_RETRIEVED_DOCUMENTS_GRADING,
        help="Enable retrieved documents grading for relevance",
    )
    parser.add_argument(
        "--no-document-grading",
        dest="enable_retrieved_document_grading",
        action="store_false",
        help="Disable retrieved documents grading",
    )
    parser.add_argument(
        "--enable-hallucination-check",
        dest="enable_hallucination_checking",
        action="store_true",
        default=Defaults.ENABLE_HALLUCINATION_CHECKING,
        help="Enable hallucination checking to verify answer is grounded in context",
    )
    parser.add_argument(
        "--no-hallucination-check",
        dest="enable_hallucination_checking",
        action="store_false",
        help="Disable hallucination checking",
    )
    parser.add_argument(
        "--enable-quality-check",
        dest="enable_answer_quality_checking",
        action="store_true",
        default=Defaults.ENABLE_ANSWER_QUALITY_CHECKING,
        help="Enable answer quality checking to verify answer addresses the question",
    )
    parser.add_argument(
        "--no-quality-check",
        dest="enable_answer_quality_checking",
        action="store_false",
        help="Disable answer quality checking",
    )

    # Parse arguments
    args = parser.parse_args()

    # Print configuration
    print("=" * 80)
    print("ADAPTIVE RAG WORKFLOW")
    print("=" * 80)
    print(f"Question: {args.question}")
    print(f"\nRetrieval Configuration:")
    print(f"  - Documents to retrieve: {args.n_retrieved_documents}")
    print(f"  - Web searches: {args.n_web_searches}")
    print(f"  - Node retrieval: {args.node_retrieval}")
    print(f"  - Edge retrieval: {args.edge_retrieval}")
    print(f"  - Episode retrieval: {args.episode_retrieval}")
    print(f"  - Community retrieval: {args.community_retrieval}")
    print(f"\nQuality Control:")
    print(f"  - Document grading: {args.enable_retrieved_document_grading}")
    print(f"  - Hallucination checking: {args.enable_hallucination_checking}")
    print(f"  - Answer quality checking: {args.enable_answer_quality_checking}")
    print("=" * 80)
    print()

    # Run workflow
    response = asyncio.run(
        run_workflow(
            question=args.question,
            n_retrieved_documents=args.n_retrieved_documents,
            n_web_searches=args.n_web_searches,
            node_retrieval=args.node_retrieval,
            edge_retrieval=args.edge_retrieval,
            episode_retrieval=args.episode_retrieval,
            community_retrieval=args.community_retrieval,
            enable_retrieved_document_grading=args.enable_retrieved_document_grading,
            enable_hallucination_checking=args.enable_hallucination_checking,
            enable_answer_quality_checking=args.enable_answer_quality_checking,
        )
    )

    print("=" * 80)
    print(f"Final Answer: {response['answer']}")
    print(f"Citations:")
    citations = response["citations"]
    for citation in citations:
        print(f"  - Title: {citation.get('title')}")
        print(f"  - URL: {citation.get('url', None)}")
    print("=" * 80)
    print()
