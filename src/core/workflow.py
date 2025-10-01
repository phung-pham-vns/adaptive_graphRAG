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
            print(LogMessages.DECISION_NOT_GROUNDED)
            return RouteDecision.NOT_GROUNDED

        print(LogMessages.DECISION_GROUNDED)
        return RouteDecision.GROUNDED

    except Exception as e:
        print(LogMessages.ERROR_IN.format("HALLUCINATION GRADING", e))
        return RouteDecision.NOT_GROUNDED


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
        current_retry = state.get("retry_count", 0)
        if current_retry >= Defaults.MAX_RETRY_COUNT:
            print(
                LogMessages.MAX_RETRIES_REACHED.format(
                    current_retry, Defaults.MAX_RETRY_COUNT, "END (BEST EFFORT)"
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

        workflow.add_node("answer_quality_check", answer_quality_check)

        # First check: Is generation grounded in context?
        workflow.add_conditional_edges(
            "answer_generation",
            grade_generation_and_context,
            {
                RouteDecision.NOT_GROUNDED: "answer_generation",  # Retry generation if hallucinating
                RouteDecision.GROUNDED: "answer_quality_check",  # Check answer quality if grounded
            },
        )

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
        workflow.add_conditional_edges(
            "answer_generation",
            grade_generation_and_context,
            {
                RouteDecision.NOT_GROUNDED: "answer_generation",  # Retry generation if hallucinating
                RouteDecision.GROUNDED: END,  # End if grounded
            },
        )
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
        "citations": [],
        "retry_count": 0,
    }
    try:
        async for output in workflow.astream(inputs):
            for key, value in output.items():
                pprint(f"Node '{key.upper()}'")

        pprint(f"Final Answer: {value.get('generation', 'No final answer generated.')}")
        pprint(f"Citations: {value.get('citations', 'No citations.')}")

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
    asyncio.run(
        run_workflow(
            question,
            n_retrieved_documents=Defaults.N_RETRIEVED_DOCUMENTS,
            n_web_searches=Defaults.N_WEB_SEARCHES,
            node_retrieval=Defaults.NODE_RETRIEVAL,
            edge_retrieval=Defaults.EDGE_RETRIEVAL,
            episode_retrieval=Defaults.EPISODE_RETRIEVAL,
            community_retrieval=Defaults.COMMUNITY_RETRIEVAL,
            enable_retrieved_document_grading=Defaults.ENABLE_RETRIEVED_DOCUMENTS_GRADING,
            enable_hallucination_checking=Defaults.ENABLE_HALLUCINATION_CHECKING,
            enable_answer_quality_checking=Defaults.ENABLE_ANSWER_QUALITY_CHECKING,
        )
    )
