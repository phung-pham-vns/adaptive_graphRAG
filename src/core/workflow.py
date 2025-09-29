from langgraph.graph import END, StateGraph, START

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


async def route_question(state: GraphState) -> str:
    """Route the question to the appropriate data source."""
    print("---ROUTE QUESTION---")
    try:
        source = await question_router.ainvoke({"question": state["question"]})
        route = source.data_source
        print(f"---ROUTE QUESTION TO {route.upper()}---")
        return route
    except Exception as e:
        print(f"---ERROR IN ROUTING: {e}, DEFAULTING TO WEB SEARCH---")
        return "web_search"


async def decide_to_generate(state: GraphState) -> str:
    """Decide whether to generate an answer or transform the query."""
    print("---ASSESS GRADED DOCUMENTS---")
    if not state["node_contents"] and not state["edge_contents"]:
        print("---DECISION: ALL DOCUMENTS ARE NOT RELEVANT, TRANSFORM QUERY---")
        return "query_transformation"
    print("---DECISION: GENERATE---")
    return "answer_generation"


async def grade_generation_vs_context_and_question(state: GraphState) -> str:
    """Check if the generated answer is grounded and addresses the question."""
    print("---CHECK HALLUCINATIONS---")
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
        if score.binary_score == "yes":
            print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
            score = await answer_grader.ainvoke(
                {
                    "question": state["question"],
                    "generation": state["generation"],
                }
            )
            if score.binary_score == "yes":
                print("---DECISION: GENERATION ADDRESSES QUESTION---")
                return "useful"
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not_useful"
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not_supported"
    except Exception as e:
        print(f"---ERROR IN GENERATION GRADING: {e}---")
        return "not_supported"


async def build_workflow() -> StateGraph:
    """Build and configure the LangGraph workflow."""
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("web_search", web_search)
    workflow.add_node("knowledge_graph_retrieval", knowledge_graph_retrieval)
    workflow.add_node("nodes_and_edges_grading", nodes_and_edges_grading)
    workflow.add_node("answer_generation", answer_generation)
    workflow.add_node("query_transformation", query_transformation)

    # Define edges
    workflow.add_conditional_edges(
        START,
        route_question,
        {
            "web_search": "web_search",
            "kg_retrieval": "knowledge_graph_retrieval",
        },
    )
    workflow.add_edge("web_search", "answer_generation")
    workflow.add_edge("knowledge_graph_retrieval", "nodes_and_edges_grading")
    workflow.add_conditional_edges(
        "nodes_and_edges_grading",
        decide_to_generate,
        {
            "query_transformation": "query_transformation",
            "answer_generation": "answer_generation",
        },
    )
    workflow.add_edge("query_transformation", "knowledge_graph_retrieval")
    workflow.add_conditional_edges(
        "answer_generation",
        grade_generation_vs_context_and_question,
        {
            "not_supported": "answer_generation",
            "not_useful": "query_transformation",
            "useful": END,
        },
    )

    return workflow


async def run_workflow(
    question: str,
    n_documents: int = 3,
    n_requests: int = 3,
) -> None:
    """Run the workflow with the given question and document limit."""
    workflow = (await build_workflow()).compile()
    inputs = {
        "question": question,
        "n_documents": n_documents,
        "n_requests": n_requests,
        "node_contents": [],
        "edge_contents": [],
        "web_contents": [],
        "web_citations": [],
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
    from pprint import pprint

    # question = "My young durian leaves are curling and look scorched at the edges, could that be leafhopper damage and what should I do first?"
    question = "Where can I buy durian in Thailand?"
    asyncio.run(run_workflow(question, n_documents=3))
