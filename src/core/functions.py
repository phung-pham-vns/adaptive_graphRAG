import asyncio
from typing import Optional, TypedDict

from langchain_tavily.tavily_search import TavilySearch

from graphiti_core.search.search_config_recipes import (
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
)
from graphiti_core.search.search_config import SearchResults
from src.core.graphiti import GraphitiClient

from src.core.chains import (
    answer_generator,
    question_rewriter,
    question_router,
    retrieval_grader,
    hallucination_grader,
    answer_grader,
)
from src.core.constants import BinaryScore, LogMessages, Defaults


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
    retry_count: int


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
    question: str, limit: int = Defaults.N_DOCUMENTS
) -> tuple[list[str], list[str]]:
    """Search knowledge graph for durian pest and disease information."""
    try:
        graphiti = await GraphitiClient().create_client(
            clear_existing_graphdb_data=False,
            max_coroutines=Defaults.MAX_COROUTINES,
        )
        search_type = COMBINED_HYBRID_SEARCH_CROSS_ENCODER.model_copy(deep=True)
        search_type.limit = limit
        results = await graphiti.search_(query=question, config=search_type)
        return await get_node_and_edge_contents(results)
    except Exception as e:
        print(LogMessages.ERROR_IN.format("KNOWLEDGE GRAPH SEARCH", e))
        return [], []


def format_context(
    node_contents: list[str],
    edge_contents: list[str],
    web_contents: list[str],
    web_citations: list[dict[str, str]],
) -> str:
    """Format node, edge, web contents, and citations into a single context string."""
    context_parts = []

    def _format_list(items: list, title: str) -> str:
        """Helper to format a list of items with numbering."""
        formatted = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))
        return f"{title}:\n{formatted}\n"

    if node_contents:
        context_parts.append(_format_list(node_contents, "Node Information"))

    if edge_contents:
        context_parts.append(_format_list(edge_contents, "Relationship Information"))

    if web_contents:
        context_parts.append(_format_list(web_contents, "Web Information"))

    if web_citations:
        context_parts.append(_format_list(web_citations, "Web Citations"))

    return "".join(context_parts)


async def knowledge_graph_retrieval(state: GraphState) -> dict:
    """Retrieve nodes and edges from the knowledge graph."""
    print(LogMessages.KNOWLEDGE_GRAPH_RETRIEVAL)
    node_contents, edge_contents = await search_durian_pest_and_disease_knowledge(
        question=state["question"], limit=state.get("n_documents", Defaults.N_DOCUMENTS)
    )
    return {"node_contents": node_contents, "edge_contents": edge_contents}


async def answer_generation(state: GraphState) -> dict:
    """Generate an answer using the provided context and question."""
    print(LogMessages.ANSWER_GENERATION)
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
        print(LogMessages.ERROR_IN.format("ANSWER GENERATION", e))
        return {"generation": "", "web_citations": web_citations}


async def nodes_and_edges_grading(state: GraphState) -> dict:
    """Grade the relevance of node and edge contents."""
    print(LogMessages.CHECK_DOCUMENT_RELEVANCE)
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
                print(LogMessages.ERROR_GRADING.format(content_type.upper(), score))
                continue
            grade = score.binary_score
            if grade == BinaryScore.YES:
                print(LogMessages.GRADE_RELEVANT.format(content_type.upper()))
                filtered.append(content)
            else:
                print(LogMessages.GRADE_NOT_RELEVANT.format(content_type.upper()))
        return filtered

    node_contents = await filter_contents(state["node_contents"], "NODE")
    edge_contents = await filter_contents(state["edge_contents"], "EDGE")

    return {"node_contents": node_contents, "edge_contents": edge_contents}


async def query_transformation(state: GraphState) -> dict:
    """Transform the query for better retrieval."""
    print(LogMessages.QUERY_TRANSFORMATION)
    current_retry = state.get("retry_count", 0)
    print(
        LogMessages.RETRY_COUNT_INFO.format(current_retry + 1, Defaults.MAX_RETRY_COUNT)
    )
    try:
        refined = await question_rewriter.ainvoke({"question": state["question"]})
        return {"question": refined.refined_question, "retry_count": current_retry + 1}
    except Exception as e:
        print(LogMessages.ERROR_IN.format("QUERY TRANSFORMATION", e))
        return {"question": state["question"], "retry_count": current_retry + 1}


async def web_search(state: GraphState) -> dict:
    """Perform a web search to gather relevant content."""
    print(LogMessages.WEB_SEARCH)
    web_search_tool = TavilySearch(
        max_results=state.get("n_requests", Defaults.N_REQUESTS)
    )
    try:
        search_results = await web_search_tool.ainvoke({"query": state["question"]})
        search_contents = [result["content"] for result in search_results["results"]]
        search_citations = [
            {"title": result["title"], "url": result["url"]}
            for result in search_results["results"]
        ]
        return {"web_contents": search_contents, "web_citations": search_citations}
    except Exception as e:
        print(LogMessages.ERROR_IN.format("WEB SEARCH", e))
        return {"web_contents": [], "web_citations": []}
