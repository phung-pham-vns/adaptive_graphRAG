from typing import Literal
from pprint import pprint

from langgraph.graph import END, StateGraph, START
from langgraph.graph.state import CompiledStateGraph

from src.core.functions import (
    GraphState,
    format_context,
    web_search,
    knowledge_graph_retrieval,
    nodes_and_edges_grading,
    query_transformation,
    answer_generation,
)
from src.core.chains import (
    question_router,
    answer_grader,
    hallucination_grader,
)
from src.core.constants import BinaryScore, LogMessages, RouteDecision, Defaults


async def route_question(state: GraphState) -> Literal["web_search", "kg_retrieval"]:
    """Route the question to the appropriate data source."""
    print(LogMessages.ROUTE_QUESTION)
    try:
        source = await question_router.ainvoke({"question": state["question"]})
        route = source.data_source
        print(LogMessages.ROUTE_TO.format(route.upper()))
        return route
    except Exception as e:
        print(LogMessages.ERROR_IN.format("ROUTING", f"{e}, DEFAULTING TO WEB SEARCH"))
        return RouteDecision.WEB_SEARCH


async def decide_to_generate(
    state: GraphState,
) -> Literal["query_transformation", "answer_generation", "web_search"]:
    """Decide whether to generate an answer, transform the query, or fallback to web search."""
    print(LogMessages.ASSESS_GRADED_DOCUMENTS)

    # Check if we have relevant documents
    if not state["node_contents"] and not state["edge_contents"]:
        print(LogMessages.DECISION_ALL_DOCUMENTS_NOT_RELEVANT)

        # Check retry count to prevent infinite loops
        current_retry = state.get("retry_count", 0)
        if current_retry >= Defaults.MAX_RETRY_COUNT:
            print(
                LogMessages.MAX_RETRIES_REACHED.format(
                    current_retry, Defaults.MAX_RETRY_COUNT, "WEB SEARCH"
                )
            )
            return RouteDecision.WEB_SEARCH

        return RouteDecision.QUERY_TRANSFORMATION

    print(LogMessages.DECISION_GENERATE)
    return RouteDecision.ANSWER_GENERATION


async def grade_generation_vs_context_and_question(
    state: GraphState,
) -> Literal["not_supported", "not_useful", "useful"]:
    """Check if the generated answer is grounded and addresses the question."""
    print(LogMessages.CHECK_HALLUCINATIONS)
    try:
        node_contents = state.get("node_contents", None)
        edge_contents = state.get("edge_contents", None)
        web_contents = state.get("web_contents", None)
        web_citations = state.get("web_citations", None)
        context = format_context(
            node_contents, edge_contents, web_contents, web_citations
        )
        score = await hallucination_grader.ainvoke(
            {"documents": context, "generation": state["generation"]}
        )
        if score.binary_score == BinaryScore.YES:
            print(LogMessages.DECISION_GROUNDED)
            score = await answer_grader.ainvoke(
                {
                    "question": state["question"],
                    "generation": state["generation"],
                }
            )
            if score.binary_score == BinaryScore.YES:
                print(LogMessages.DECISION_ADDRESSES_QUESTION)
                return RouteDecision.USEFUL

            # Check retry count before looping back to query_transformation
            current_retry = state.get("retry_count", 0)
            if current_retry >= Defaults.MAX_RETRY_COUNT:
                print(
                    LogMessages.MAX_RETRIES_REACHED.format(
                        current_retry, Defaults.MAX_RETRY_COUNT, "END (BEST EFFORT)"
                    )
                )
                # Return as useful to end workflow with best effort answer
                return RouteDecision.USEFUL

            print(LogMessages.DECISION_NOT_ADDRESSES_QUESTION)
            return RouteDecision.NOT_USEFUL
        print(LogMessages.DECISION_NOT_GROUNDED)
        return RouteDecision.NOT_SUPPORTED
    except Exception as e:
        print(LogMessages.ERROR_IN.format("GENERATION GRADING", e))
        return RouteDecision.NOT_SUPPORTED


async def build_workflow(
    enable_document_grading: bool = Defaults.ENABLE_DOCUMENT_GRADING,
    enable_generation_grading: bool = Defaults.ENABLE_GENERATION_GRADING,
) -> StateGraph[GraphState]:
    """Build and configure the LangGraph workflow with optional optimization flags.

    Args:
        enable_document_grading: If True, grade retrieved documents for relevance
        enable_generation_grading: If True, check generated answers for hallucinations and quality
    """
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("web_search", web_search)
    workflow.add_node("knowledge_graph_retrieval", knowledge_graph_retrieval)
    workflow.add_node("answer_generation", answer_generation)
    workflow.add_node("query_transformation", query_transformation)

    # Conditionally add grading nodes
    if enable_document_grading:
        workflow.add_node("nodes_and_edges_grading", nodes_and_edges_grading)

    # Define edges
    workflow.add_conditional_edges(
        START,
        route_question,
        {
            RouteDecision.WEB_SEARCH: "web_search",
            RouteDecision.KG_RETRIEVAL: "knowledge_graph_retrieval",
        },
    )
    workflow.add_edge("web_search", "answer_generation")

    # Configure KG retrieval flow based on document grading flag
    if enable_document_grading:
        # With grading: KG → grading → decide → answer/transform
        workflow.add_edge("knowledge_graph_retrieval", "nodes_and_edges_grading")
        workflow.add_conditional_edges(
            "nodes_and_edges_grading",
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

    # Configure answer generation flow based on generation grading flag
    if enable_generation_grading:
        # With grading: check quality and retry if needed
        workflow.add_conditional_edges(
            "answer_generation",
            grade_generation_vs_context_and_question,
            {
                RouteDecision.NOT_SUPPORTED: "answer_generation",
                RouteDecision.NOT_USEFUL: "query_transformation",
                RouteDecision.USEFUL: END,
            },
        )
    else:
        # Without grading: answer directly ends workflow
        workflow.add_edge("answer_generation", END)

    return workflow


async def run_workflow(
    question: str,
    n_documents: int = Defaults.N_DOCUMENTS,
    n_requests: int = Defaults.N_REQUESTS,
    enable_document_grading: bool = Defaults.ENABLE_DOCUMENT_GRADING,
    enable_generation_grading: bool = Defaults.ENABLE_GENERATION_GRADING,
) -> None:
    """Run the workflow with the given question and configuration options."""
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
    try:
        async for output in workflow.astream(inputs):
            for key, value in output.items():
                pprint(f"Node '{key.upper()}'")
        if "generation" in value:
            pprint(f"Final Answer: {value['generation']}")
        else:
            pprint("No final answer generated.")

        if "web_citations" in value:
            pprint(f"Web Citations: {value['web_citations']}")
        else:
            pprint("No web citations.")

    except Exception as e:
        pprint(f"Error during workflow execution: {e}")


# Example usage
if __name__ == "__main__":
    import asyncio

    # question = "My young durian leaves are curling and look scorched at the edges, could that be leafhopper damage and what should I do first?"
    # question = "Where can I buy durian in Thailand?"
    # question = "If I only see a few durian scales on some twigs, should I spray the whole block?"
    # question = "What’s a good rule for rotating insecticides when dealing with psyllids or leafhoppers?"
    # question = "Leaves show powdery white patches—what durian disease could this be?"
    question = "Which longhorn borer treatments are suitable for large limbs and trunk?"
    asyncio.run(run_workflow(question, n_documents=Defaults.N_DOCUMENTS))
