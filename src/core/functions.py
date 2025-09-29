import asyncio
from typing import Optional, TypedDict

from langchain_tavily.tavily_search import TavilySearch

from graphiti_core.search.search_config_recipes import (
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
)
from graphiti_core.search.search_config import SearchResults
from src.core.graphiti_client import GraphitiClient

from src.core.chains import (
    answer_generator,
    question_rewriter,
    question_router,
    retrieval_grader,
    hallucination_grader,
    answer_grader,
)


class GraphState(TypedDict):
    question: str
    generation: Optional[str]
    node_contents: list[str]
    edge_contents: list[str]
    web_contents: list[str]
    n_documents: int
    n_requests: int
    web_citations: list[dict[str, str]]
    kg_citations: list[dict[str, str]]


async def get_node_and_edge_contents(
    result: SearchResults,
) -> tuple[list[str], list[str]]:
    """Extract node and edge contents from search results."""
    node_contents = [
        node.summary
        for node in getattr(result, "nodes", [])
        if hasattr(node, "summary")
    ]
    edge_contents = [
        edge.fact for edge in getattr(result, "edges", []) if hasattr(edge, "fact")
    ]
    return node_contents, edge_contents


async def search_durian_pest_and_disease_knowledge(
    question: str, limit: int = 3
) -> tuple[list[str], list[str]]:
    """Search knowledge graph for durian pest and disease information."""
    try:
        graphiti = await GraphitiClient().create_client(
            clear_existing_graphdb_data=False,
            max_coroutines=1,
        )
        search_type = COMBINED_HYBRID_SEARCH_CROSS_ENCODER.model_copy(deep=True)
        search_type.limit = limit
        results = await graphiti.search_(query=question, config=search_type)
        return await get_node_and_edge_contents(results)
    except Exception as e:
        print(f"---ERROR IN KNOWLEDGE GRAPH SEARCH: {e}---")
        return [], []


def format_context(
    node_contents: list[str],
    edge_contents: list[str],
    web_contents: list[str],
    web_citations: list[dict[str, str]],
) -> str:
    """Format node and edge contents into a single string."""
    context = ""
    if node_contents:
        nodes_content = "\n".join(
            f"{i + 1}. {node}" for i, node in enumerate(node_contents)
        )
        context += f"Node Information:\n{nodes_content}\n"

    if edge_contents:
        edges_content = "\n".join(
            f"{i + 1}. {edge}" for i, edge in enumerate(edge_contents)
        )
        context += f"Relationship Information:\n{edges_content}\n"

    if web_contents:
        web_content = "\n".join(
            f"{i + 1}. {content}" for i, content in enumerate(web_contents)
        )
        context += f"Web Information:\n{web_content}\n"

    if web_citations:
        web_citations = "\n".join(
            f"{i + 1}. {citation}" for i, citation in enumerate(web_citations)
        )
        context += f"Web Citations:\n{web_citations}\n"

    return context


async def knowledge_graph_retrieval(state: GraphState) -> dict:
    """Retrieve nodes and edges from the knowledge graph."""
    print("---KNOWLEDGE GRAPH RETRIEVAL---")
    node_contents, edge_contents = await search_durian_pest_and_disease_knowledge(
        question=state["question"], limit=state.get("n_documents", 3)
    )
    return {"node_contents": node_contents, "edge_contents": edge_contents}


async def answer_generation(state: GraphState) -> dict:
    """Generate an answer using the provided context and question."""
    print("---ANSWER GENERATION---")
    node_contents = state.get("node_contents", None)
    edge_contents = state.get("edge_contents", None)
    web_contents = state.get("web_contents", None)
    web_citations = state.get("web_citations", None)
    context = format_context(node_contents, edge_contents, web_contents, web_citations)
    try:
        generation = await answer_generator.ainvoke(
            {"context": context, "question": state["question"]}
        )
        return {"generation": generation.answer, "web_citations": web_citations}
    except Exception as e:
        print(f"---ERROR IN ANSWER GENERATION: {e}---")
        return {"generation": "", "web_citations": web_citations}


async def nodes_and_edges_grading(state: GraphState) -> dict:
    """Grade the relevance of node and edge contents."""
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]

    async def filter_contents(contents: list[str], content_type: str) -> list[str]:
        tasks = [
            retrieval_grader.ainvoke({"question": question, "document": content})
            for content in contents
        ]
        scores = await asyncio.gather(*tasks, return_exceptions=True)
        filtered = []
        for content, score in zip(contents, scores):
            if isinstance(score, Exception):
                print(f"---ERROR GRADING {content_type.upper()} CONTENT: {score}---")
                continue
            grade = score.binary_score
            print(
                f"---GRADE: {content_type.upper()} CONTENT {'RELEVANT' if grade == 'yes' else 'NOT RELEVANT'}---"
            )
            if grade == "yes":
                filtered.append(content)
        return filtered

    node_contents = await filter_contents(state["node_contents"], "NODE")
    edge_contents = await filter_contents(state["edge_contents"], "EDGE")

    return {"node_contents": node_contents, "edge_contents": edge_contents}


async def query_transformation(state: GraphState) -> dict:
    """Transform the query for better retrieval."""
    print("---QUERY TRANSFORMATION---")
    try:
        refined = await question_rewriter.ainvoke({"question": state["question"]})
        return {"question": refined.refined_question}
    except Exception as e:
        print(f"---ERROR IN QUERY TRANSFORMATION: {e}---")
        return {"question": state["question"]}


async def web_search(state: GraphState) -> dict:
    """Perform a web search to gather relevant content."""
    print("---WEB SEARCH---")
    web_search_tool = TavilySearch(max_results=state.get("n_requests", 3))
    try:
        import pdb

        pdb.set_trace()
        search_results = await web_search_tool.ainvoke({"query": state["question"]})
        search_contents = [result["content"] for result in search_results["results"]]
        search_citations = [
            {"title": result["title"], "url": result["url"]}
            for result in search_results["results"]
        ]
        return {"web_contents": search_contents, "web_citations": search_citations}
    except Exception as e:
        print(f"---ERROR IN WEB SEARCH: {e}---")
        return {"web_contents": [], "web_citations": []}
