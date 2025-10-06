import asyncio
from typing import Optional, TypedDict

from langchain_tavily.tavily_search import TavilySearch

from graphiti_core.search.search_config_recipes import (
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
)
from graphiti_core.search.search_config import (
    CommunityReranker,
    CommunitySearchConfig,
    CommunitySearchMethod,
    EdgeReranker,
    EdgeSearchConfig,
    EdgeSearchMethod,
    EpisodeReranker,
    EpisodeSearchConfig,
    EpisodeSearchMethod,
    NodeReranker,
    NodeSearchConfig,
    NodeSearchMethod,
    SearchConfig,
    SearchResults,
)
from src.core.graphiti import GraphitiClient

from src.core.chains import (
    answer_generator,
    llm_internal_answer_generator,
    question_rewriter,
    question_router,
    retrieval_grader,
    hallucination_grader,
    answer_grader,
)
from src.core.constants import (
    BinaryScore,
    LogMessages,
    Defaults,
    DOCUMENT_ID_TO_DOCUMENT_NAME,
)


class GraphState(TypedDict):
    question: str
    generation: Optional[str]
    node_contents: list[str]
    edge_contents: list[str]
    web_contents: list[str]
    node_retrieval: bool
    edge_retrieval: bool
    episode_retrieval: bool
    community_retrieval: bool
    node_citations: list[dict[str, str]]
    edge_citations: list[dict[str, str]]
    web_citations: list[dict[str, str]]
    n_retrieved_documents: int
    n_web_searches: int
    citations: list[dict[str, str]]
    query_transformation_retry_count: int
    hallucination_retry_count: int


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
    question: str,
    limit: int = Defaults.N_RETRIEVED_DOCUMENTS,
    node_retrieval: bool = Defaults.NODE_RETRIEVAL,
    edge_retrieval: bool = Defaults.EDGE_RETRIEVAL,
    episode_retrieval: bool = Defaults.EPISODE_RETRIEVAL,
    community_retrieval: bool = Defaults.COMMUNITY_RETRIEVAL,
    search_methods_override: Optional[dict] = None,
) -> tuple[list[str], list[str], list[dict[str, str]], list[dict[str, str]]]:
    """Search knowledge graph for durian pest and disease information.

    This function performs hybrid search across multiple graph components:
    - Nodes (entities like pests, diseases, symptoms)
    - Edges (relationships between entities)
    - Episodes (text chunks from documents)
    - Communities (clustered knowledge)

    The search uses multiple methods (BM25, cosine similarity, BFS) and
    reranks results using a cross-encoder for optimal relevance.

    Args:
        question: Search query (e.g., "What causes durian leaf curl?")
        limit: Maximum number of results per component
        node_retrieval: Enable node/entity retrieval
        edge_retrieval: Enable edge/relationship retrieval
        episode_retrieval: Enable episode/text chunk retrieval
        community_retrieval: Enable community retrieval
        search_methods_override: Optional custom search methods configuration

    Returns:
        Tuple of (node_contents, edge_contents, node_citations, edge_citations)

    Example:
        >>> node_contents, edge_contents, node_cites, edge_cites = await search_durian_pest_and_disease_knowledge(
        ...     question="What causes leaf curl?",
        ...     limit=5,
        ...     node_retrieval=True,
        ...     edge_retrieval=True
        ... )
        >>> print(f"Found {len(node_contents)} nodes, {len(edge_contents)} edges")

    Performance:
        - Uses cached Graphiti client for efficient connection reuse
        - Hybrid search methods for comprehensive results
        - Cross-encoder reranking for relevance optimization
        - Typical latency: 1-3 seconds depending on result count
    """
    try:
        # Use cached client for efficient retrieval (singleton pattern)
        from src.core.graphiti import get_graphiti_client

        graphiti = await get_graphiti_client()

        # Build search configuration based on enabled retrievals
        search_config = _build_search_config(
            limit=limit,
            node_retrieval=node_retrieval,
            edge_retrieval=edge_retrieval,
            episode_retrieval=episode_retrieval,
            community_retrieval=community_retrieval,
            search_methods_override=search_methods_override,
        )

        # Perform search
        results = await graphiti.search_(query=question, config=search_config)

        # Extract contents
        node_contents, edge_contents = await get_node_and_edge_contents(results)

        # Extract citations with deduplication
        node_citations = _extract_citations(results.nodes, DOCUMENT_ID_TO_DOCUMENT_NAME)
        edge_citations = _extract_citations(results.edges, DOCUMENT_ID_TO_DOCUMENT_NAME)

        return node_contents, edge_contents, node_citations, edge_citations

    except Exception as e:
        print(LogMessages.ERROR_IN.format("KNOWLEDGE GRAPH SEARCH", str(e)))
        return [], [], [], []


def _build_search_config(
    limit: int,
    node_retrieval: bool,
    edge_retrieval: bool,
    episode_retrieval: bool,
    community_retrieval: bool,
    search_methods_override: Optional[dict] = None,
) -> SearchConfig:
    """Build search configuration based on enabled retrievals.

    This helper function constructs the SearchConfig with optimal settings
    for the durian pest and disease domain.

    Args:
        limit: Maximum results per component
        node_retrieval: Enable node retrieval
        edge_retrieval: Enable edge retrieval
        episode_retrieval: Enable episode retrieval
        community_retrieval: Enable community retrieval
        search_methods_override: Optional custom search methods

    Returns:
        Configured SearchConfig instance

    Note:
        Default search methods are optimized for durian domain:
        - Nodes/Edges: BM25 + Cosine Similarity + BFS (comprehensive)
        - Episodes/Communities: BM25 only (faster, good for text)
        - All use cross-encoder reranking for quality
    """
    # Get search methods from override or use defaults
    methods = search_methods_override or {}

    # Configure node search (entities: pests, diseases, symptoms, etc.)
    node_config = None
    if node_retrieval:
        node_config = NodeSearchConfig(
            search_methods=methods.get(
                "node_methods",
                [
                    NodeSearchMethod.bm25,  # Keyword matching
                    NodeSearchMethod.cosine_similarity,  # Semantic similarity
                    NodeSearchMethod.bfs,  # Graph traversal
                ],
            ),
            reranker=NodeReranker.cross_encoder,  # Refine results
        )

    # Configure edge search (relationships: causes, treats, symptoms_of, etc.)
    edge_config = None
    if edge_retrieval:
        edge_config = EdgeSearchConfig(
            search_methods=methods.get(
                "edge_methods",
                [
                    EdgeSearchMethod.bm25,
                    EdgeSearchMethod.cosine_similarity,
                    EdgeSearchMethod.bfs,
                ],
            ),
            reranker=EdgeReranker.cross_encoder,
        )

    # Configure episode search (text chunks from source documents)
    episode_config = None
    if episode_retrieval:
        episode_config = EpisodeSearchConfig(
            search_methods=methods.get(
                "episode_methods",
                [
                    EpisodeSearchMethod.bm25,  # BM25 is fast and effective for text
                ],
            ),
            reranker=EpisodeReranker.cross_encoder,
        )

    # Configure community search (clustered knowledge summaries)
    community_config = None
    if community_retrieval:
        community_config = CommunitySearchConfig(
            search_methods=methods.get(
                "community_methods",
                [
                    CommunitySearchMethod.bm25,
                ],
            ),
            reranker=CommunityReranker.cross_encoder,
        )

    return SearchConfig(
        node_config=node_config,
        edge_config=edge_config,
        episode_config=episode_config,
        community_config=community_config,
        limit=limit,
    )


def _extract_citations(
    items: list,
    document_mapping: dict[str, str],
) -> list[dict[str, str]]:
    """Extract unique citations from search results.

    Args:
        items: List of nodes or edges from search results
        document_mapping: Mapping of document IDs to document names

    Returns:
        List of citation dictionaries with unique titles

    Note:
        Duplicates are automatically removed to avoid redundant citations.
    """
    citations = []
    seen_titles = set()

    for item in items:
        document_id = getattr(item, "group_id", None)
        if document_id:
            document_name = document_mapping.get(document_id, None)
            if document_name and document_name not in seen_titles:
                citations.append({"title": document_name})
                seen_titles.add(document_name)

    return citations


def format_context(
    node_contents: list[str],
    edge_contents: list[str],
    web_contents: list[str],
    node_citations: list[dict[str, str]],
    edge_citations: list[dict[str, str]],
    web_citations: list[dict[str, str]],
) -> str:
    """Format node, edge, web contents, and citations into a well-structured context string.

    This function creates a hierarchical, easy-to-parse context for the LLM with clear sections
    for entities, relationships, and web information.
    """
    context_parts = []

    # Format entities (nodes) - these are key concepts, pests, diseases, symptoms, etc.
    if node_contents:
        context_parts.append("=" * 60)
        context_parts.append("KNOWLEDGE GRAPH ENTITIES (Key Concepts)")
        context_parts.append("=" * 60)
        for i, content in enumerate(node_contents, 1):
            context_parts.append(f"\n[Entity {i}]")
            context_parts.append(content)
            # Add citation inline if available
            if i - 1 < len(node_citations) and node_citations[i - 1].get("title"):
                context_parts.append(f"  Source: {node_citations[i - 1]['title']}")
        context_parts.append("")  # Blank line separator

    # Format relationships (edges) - these show connections between entities
    if edge_contents:
        context_parts.append("=" * 60)
        context_parts.append("KNOWLEDGE GRAPH RELATIONSHIPS (Connections)")
        context_parts.append("=" * 60)
        for i, content in enumerate(edge_contents, 1):
            context_parts.append(f"\n[Relationship {i}]")
            context_parts.append(content)
            # Add citation inline if available
            if i - 1 < len(edge_citations) and edge_citations[i - 1].get("title"):
                context_parts.append(f"  Source: {edge_citations[i - 1]['title']}")
        context_parts.append("")  # Blank line separator

    # Format web search results - for latest/current information
    if web_contents:
        context_parts.append("=" * 60)
        context_parts.append("WEB SEARCH RESULTS (Recent Information)")
        context_parts.append("=" * 60)
        for i, content in enumerate(web_contents, 1):
            context_parts.append(f"\n[Web Result {i}]")
            context_parts.append(content)
            # Add URL inline if available
            if i - 1 < len(web_citations):
                citation = web_citations[i - 1]
                if citation.get("title"):
                    context_parts.append(f"  Title: {citation['title']}")
                if citation.get("url"):
                    context_parts.append(f"  URL: {citation['url']}")
        context_parts.append("")  # Blank line separator

    # If no context is available
    if not context_parts:
        return "No relevant context found in knowledge base or web search."

    return "\n".join(context_parts)


async def knowledge_graph_retrieval(state: GraphState) -> dict:
    """Retrieve nodes and edges from the knowledge graph."""
    print(LogMessages.KNOWLEDGE_GRAPH_RETRIEVAL)
    node_contents, edge_contents, node_citations, edge_citations = (
        await search_durian_pest_and_disease_knowledge(
            question=state["question"],
            node_retrieval=state.get("node_retrieval", Defaults.NODE_RETRIEVAL),
            edge_retrieval=state.get("edge_retrieval", Defaults.EDGE_RETRIEVAL),
            episode_retrieval=state.get(
                "episode_retrieval", Defaults.EPISODE_RETRIEVAL
            ),
            community_retrieval=state.get(
                "community_retrieval", Defaults.COMMUNITY_RETRIEVAL
            ),
            limit=state.get("n_retrieved_documents", Defaults.N_RETRIEVED_DOCUMENTS),
        )
    )

    # Log retrieval statistics
    print(
        LogMessages.KNOWLEDGE_GRAPH_STATS.format(len(node_contents), len(edge_contents))
    )

    return {
        "node_contents": node_contents,
        "edge_contents": edge_contents,
        "node_citations": node_citations,
        "edge_citations": edge_citations,
    }


async def answer_generation(state: GraphState) -> dict:
    """Generate an answer using context if available, otherwise use LLM internal knowledge."""
    node_contents = state.get("node_contents", [])
    edge_contents = state.get("edge_contents", [])
    web_contents = state.get("web_contents", [])
    node_citations = state.get("node_citations", [])
    edge_citations = state.get("edge_citations", [])
    web_citations = state.get("web_citations", [])

    # Check if any context is available
    has_context = bool(node_contents or edge_contents or web_contents)

    if has_context:
        # Generate answer with context
        print(LogMessages.ANSWER_GENERATION)
        print(
            LogMessages.ANSWER_GENERATION_WITH_CONTEXT.format(
                len(node_contents), len(edge_contents), len(web_contents)
            )
        )
        context = format_context(
            node_contents,
            edge_contents,
            web_contents,
            node_citations,
            edge_citations,
            web_citations,
        )

        citations = []
        for citation in node_citations:
            if citation not in citations:
                citations.append(citation)

        for citation in edge_citations:
            if citation not in citations:
                citations.append(citation)

        for citation in web_citations:
            if citation not in citations:
                citations.append(citation)

        try:
            generation = await answer_generator.ainvoke(
                {"context": context, "question": state["question"]}
            )
            # Reset hallucination retry count on successful generation
            return {
                "generation": generation.answer,
                "citations": citations,
                "hallucination_retry_count": 0,
            }
        except Exception as e:
            print(LogMessages.ERROR_IN.format("ANSWER GENERATION", e))
            return {"generation": "", "citations": citations}
    else:
        # Generate answer using LLM internal knowledge (for out-of-domain questions)
        print(LogMessages.LLM_INTERNAL_ANSWER)
        try:
            generation = await llm_internal_answer_generator.ainvoke(
                {"question": state["question"]}
            )
            return {"generation": generation.answer, "hallucination_retry_count": 0}
        except Exception as e:
            print(LogMessages.ERROR_IN.format("LLM INTERNAL ANSWER", e))
            return {
                "generation": "I apologize, but I'm unable to answer that question at the moment."
            }


async def retrieved_documents_grading(state: GraphState) -> dict:
    """Grade the relevance of node and edge contents."""
    print(LogMessages.CHECK_DOCUMENT_RELEVANCE)
    question = state["question"]
    edge_citations = state.get("edge_citations", [])
    node_citations = state.get("node_citations", [])

    # Track statistics for better observability
    original_node_count = len(state.get("node_contents", []))
    original_edge_count = len(state.get("edge_contents", []))

    async def filter_contents_and_citations(
        contents: list[str], citations: list[dict[str, str]], content_type: str
    ) -> tuple[list[str], list[dict[str, str]]]:
        if not contents:
            return [], []

        tasks = [
            retrieval_grader.ainvoke({"question": question, "document": content})
            for content in contents
        ]
        scores = await asyncio.gather(*tasks, return_exceptions=True)
        filtered_contents = []
        filtered_citations = []
        for i, (content, score) in enumerate(zip(contents, scores)):
            if isinstance(score, Exception):
                print(LogMessages.ERROR_GRADING.format(content_type, score))
                continue
            grade = score.binary_score
            if grade == BinaryScore.YES:
                print(LogMessages.GRADE_RELEVANT.format(content_type))
                filtered_contents.append(content)
                filtered_citations.append(citations[i])
            else:
                print(LogMessages.GRADE_NOT_RELEVANT.format(content_type))
        return filtered_contents, filtered_citations

    node_contents, node_citations = await filter_contents_and_citations(
        state["node_contents"], state.get("node_citations", []), "NODE"
    )
    edge_contents, edge_citations = await filter_contents_and_citations(
        state["edge_contents"], state.get("edge_citations", []), "EDGE"
    )

    # Log grading summary
    filtered_node_count = len(node_contents)
    filtered_edge_count = len(edge_contents)
    total_original = original_node_count + original_edge_count
    total_filtered = filtered_node_count + filtered_edge_count
    print(LogMessages.GRADING_SUMMARY.format(total_filtered, total_original))

    return {
        "node_contents": node_contents,
        "edge_contents": edge_contents,
        "edge_citations": edge_citations,
        "node_citations": node_citations,
    }


async def query_transformation(state: GraphState) -> dict:
    """Transform the query for better retrieval."""
    print(LogMessages.QUERY_TRANSFORMATION)
    current_retry = state.get("query_transformation_retry_count", 0)
    print(
        LogMessages.RETRY_COUNT_INFO.format(
            current_retry + 1, Defaults.MAX_QUERY_TRANSFORMATION_RETRIES
        )
    )
    try:
        original_question = state["question"]
        refined = await question_rewriter.ainvoke({"question": original_question})
        refined_question = refined.refined_question

        # Log the transformation for observability
        print(
            LogMessages.QUERY_TRANSFORMATION_RESULT.format(
                (
                    original_question[:60] + "..."
                    if len(original_question) > 60
                    else original_question
                ),
                (
                    refined_question[:60] + "..."
                    if len(refined_question) > 60
                    else refined_question
                ),
            )
        )

        return {
            "question": refined_question,
            "query_transformation_retry_count": current_retry + 1,
        }
    except Exception as e:
        print(LogMessages.ERROR_IN.format("QUERY TRANSFORMATION", str(e)))
        return {
            "question": state["question"],
            "query_transformation_retry_count": current_retry + 1,
        }


async def web_search(state: GraphState) -> dict:
    """Perform a web search to gather relevant content."""
    print(LogMessages.WEB_SEARCH)
    web_search_tool = TavilySearch(
        max_results=state.get("n_web_searches", Defaults.N_WEB_SEARCHES)
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
