"""Graphiti Knowledge Graph Client for Durian Pest & Disease Domain.

This module provides a centralized client for interacting with the Graphiti knowledge graph,
optimized for the durian pest and disease domain. It handles:
- LLM client configuration (Gemini/OpenAI)
- Embedder configuration for semantic search
- Cross-encoder (reranker) for result refinement
- Graph database driver (Neo4j)
- Connection pooling and reuse
- Singleton pattern for efficient resource management

Usage:
    # Ingestion (create new client each time)
    from src.core.graphiti import GraphitiClient
    
    client = GraphitiClient()
    graphiti = await client.create_client(clear_existing_graphdb_data=False)
    await graphiti.add_episode(...)
    await client.close()
    
    # Retrieval (use cached instance)
    from src.core.graphiti import get_graphiti_client
    
    graphiti = await get_graphiti_client()
    results = await graphiti.search_(query, config)
"""

import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.llm_client.openai_client import OpenAIClient

from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig

from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from graphiti_core.driver.neo4j_driver import Neo4jDriver

from graphiti_core.utils.maintenance.graph_data_operations import clear_data

from src.settings import settings
from src.models.providers import LLMProviders, GraphDBProviders, EmbeddingProviders
from src.deps.reranker.gemini import GeminiRerankerClient
from src.logger import setup_logging


logger = setup_logging()


# ============================================================================
# Global Cache for Retrieval Client (Singleton Pattern)
# ============================================================================

_cached_retrieval_graphiti: Optional[Graphiti] = None
_client_lock = asyncio.Lock()


# ============================================================================
# GraphitiClient Class
# ============================================================================

class GraphitiClient:
    """Configurable Graphiti client for knowledge graph operations.
    
    This client handles the initialization of all required components:
    - LLM client (for entity/relationship extraction)
    - Embedder (for semantic search)
    - Cross-encoder (for result reranking)
    - Graph database driver
    
    The client supports two usage patterns:
    1. **Ingestion**: Create fresh instances for each ingestion job
    2. **Retrieval**: Use cached singleton instance for efficient searching
    
    Attributes:
        llm_client: LLM client for graph construction
        embedder: Embedder for semantic search
        cross_encoder: Reranker for result refinement
        driver: Graph database driver
    """
    
    def __init__(self):
        """Initialize the Graphiti client with configured providers."""
        # Initialize LLM client
        self.llm_client = self._create_llm_client()
        
        # Initialize embedder
        self.embedder = self._create_embedder()
        
        # Initialize cross-encoder (reranker)
        self.cross_encoder = self._create_cross_encoder()
        
        # Initialize graph database driver
        self.driver = self._create_driver()
        
        logger.debug("GraphitiClient components initialized")
    
    def _create_llm_client(self):
        """Create LLM client based on configuration.
        
        Returns:
            Configured LLM client (GeminiClient or OpenAIClient)
            
        Raises:
            ValueError: If invalid provider is specified
        """
        provider = settings.llm_provider
        
        if provider == LLMProviders.Gemini.value:
            return GeminiClient(
                config=LLMConfig(
                    base_url=settings.llm_base_url,
                    api_key=settings.llm_api_key,
                    model=settings.llm_model,
                )
            )
        elif provider == LLMProviders.OpenAI.value:
            return OpenAIClient(
                config=LLMConfig(
                    api_key=settings.llm_api_key,
                    model=settings.llm_model,
                )
            )
        else:
            raise ValueError(
                f"Invalid LLM provider: {provider}. "
                f"Supported: {[p.value for p in LLMProviders]}"
            )
    
    def _create_embedder(self):
        """Create embedder based on configuration.
        
        Returns:
            Configured embedder (GeminiEmbedder or OpenAIEmbedder)
            
        Raises:
            ValueError: If invalid provider is specified
        """
        provider = settings.embedding.embedding_provider
        
        if provider == EmbeddingProviders.Gemini.value:
            return GeminiEmbedder(
                config=GeminiEmbedderConfig(
                    api_key=settings.embedding.embedding_api_key,
                    embedding_model=settings.embedding.embedding_model,
                    embedding_dim=settings.embedding.embedding_dimensions,
                )
            )
        elif provider == EmbeddingProviders.OpenAI.value:
            return OpenAIEmbedder(
                config=OpenAIEmbedderConfig(
                    api_key=settings.embedding.embedding_api_key,
                    embedding_model=settings.embedding.embedding_model,
                    embedding_dim=settings.embedding.embedding_dimensions,
                )
            )
        else:
            raise ValueError(
                f"Invalid embedding provider: {provider}. "
                f"Supported: {[p.value for p in EmbeddingProviders]}"
            )
    
    def _create_cross_encoder(self):
        """Create cross-encoder (reranker) based on configuration.
        
        Returns:
            Configured cross-encoder client
            
        Raises:
            ValueError: If invalid provider is specified
        """
        provider = settings.reranker.reranker_provider
        
        if provider == LLMProviders.Gemini.value:
            return GeminiRerankerClient(
                config=LLMConfig(
                    base_url=settings.reranker.reranker_base_url,
                    api_key=settings.reranker.reranker_api_key,
                    model=settings.reranker.reranker_model,
                )
            )
        elif provider == LLMProviders.OpenAI.value:
            return OpenAIRerankerClient(
                config=LLMConfig(
                    api_key=settings.reranker.reranker_api_key,
                    model=settings.reranker.reranker_model,
                )
            )
        else:
            raise ValueError(
                f"Invalid reranker provider: {provider}. "
                f"Supported: {[p.value for p in LLMProviders]}"
            )
    
    def _create_driver(self):
        """Create graph database driver based on configuration.
        
        Returns:
            Configured graph database driver
            
        Raises:
            ValueError: If invalid provider is specified
        """
        provider = settings.graph_db_provider
        
        if provider == GraphDBProviders.Neo4j.value:
            return Neo4jDriver(
                uri=settings.graph_db_url,
                user=settings.graph_db_username,
                password=settings.graph_db_password,
            )
        else:
            raise ValueError(
                f"Invalid graph database provider: {provider}. "
                f"Supported: {[p.value for p in GraphDBProviders]}"
            )
    
    async def create_client(
        self,
        clear_existing_graphdb_data: bool = False,
        max_coroutines: int = 1,
    ) -> Graphiti:
        """Create a Graphiti instance with all configured components.
        
        This method initializes the Graphiti graph with indices and constraints,
        and optionally clears existing data.
        
        Args:
            clear_existing_graphdb_data: If True, clear all existing graph data.
                                         **WARNING**: This is destructive!
            max_coroutines: Maximum number of concurrent coroutines for parallel
                           processing during ingestion. Higher values = faster
                           ingestion but more resource usage.
                           
        Returns:
            Configured Graphiti instance ready for use
            
        Example:
            # For ingestion with parallel processing
            client = GraphitiClient()
            graphiti = await client.create_client(
                clear_existing_graphdb_data=False,
                max_coroutines=5
            )
            
            # For retrieval (use get_graphiti_client() instead)
            graphiti = await get_graphiti_client()
        """
        logger.info("Creating Graphiti client instance")
        
        graphiti = Graphiti(
            graph_driver=self.driver,
            llm_client=self.llm_client,
            embedder=self.embedder,
            cross_encoder=self.cross_encoder,
            max_coroutines=max_coroutines,
        )
        
        # Initialize the graph database with graphiti's indices and constraints
        logger.debug("Building indices and constraints...")
        await graphiti.build_indices_and_constraints()
        logger.info("Graphiti indices and constraints ready")
        
        # Optionally clear existing data
        if clear_existing_graphdb_data:
            logger.warning("⚠️  Clearing existing graph data (destructive operation)...")
            await clear_data(graphiti.driver)
            logger.info("✓ Graph data cleared successfully")
        
        logger.info("✓ Graphiti client created successfully")
        return graphiti
    
    async def close(self):
        """Close the graph database driver connection.
        
        This should be called when the client is no longer needed to free resources.
        
        Example:
            client = GraphitiClient()
            graphiti = await client.create_client()
            # ... use graphiti ...
            await client.close()
        """
        try:
            if self.driver:
                await self.driver.close()
                logger.info("Graph database driver connection closed")
        except Exception as e:
            logger.exception(f"Error closing graph database driver: {e}")


# ============================================================================
# Singleton Pattern for Retrieval (Efficient Resource Reuse)
# ============================================================================

async def get_graphiti_client(
    force_recreate: bool = False,
) -> Graphiti:
    """Get cached Graphiti instance for efficient retrieval operations.
    
    This function implements a singleton pattern to reuse the same Graphiti
    instance across multiple retrieval operations, avoiding the overhead of
    creating new connections for each search.
    
    **Use this function for retrieval operations only.**
    For ingestion, create a new GraphitiClient instance.
    
    Args:
        force_recreate: If True, recreate the client even if cached.
                       Useful for testing or after configuration changes.
                       
    Returns:
        Cached or newly created Graphiti instance
        
    Example:
        # Efficient retrieval (reuses connection)
        from src.core.graphiti import get_graphiti_client
        
        graphiti = await get_graphiti_client()
        results = await graphiti.search_(query, config)
        # No need to close - connection is reused
        
        # Force recreation (e.g., after config change)
        graphiti = await get_graphiti_client(force_recreate=True)
    
    Note:
        The cached instance is thread-safe using asyncio.Lock.
        Connection is automatically reused across multiple calls.
    """
    global _cached_retrieval_graphiti
    
    async with _client_lock:
        if _cached_retrieval_graphiti is None or force_recreate:
            if force_recreate and _cached_retrieval_graphiti is not None:
                logger.info("Force recreating cached Graphiti client")
                try:
                    await _cached_retrieval_graphiti.driver.close()
                except Exception as e:
                    logger.warning(f"Error closing previous client: {e}")
            
            logger.info("Creating cached Graphiti instance for retrieval")
            client = GraphitiClient()
            _cached_retrieval_graphiti = await client.create_client(
                clear_existing_graphdb_data=False,
                max_coroutines=1,  # Retrieval typically doesn't need parallelism
            )
            logger.info("✓ Cached Graphiti instance created")
        else:
            logger.debug("Reusing cached Graphiti instance")
    
    return _cached_retrieval_graphiti


async def close_cached_client():
    """Close the cached Graphiti client and clear the cache.
    
    Call this during application shutdown or when you want to force
    recreation of the client (e.g., after configuration changes).
    
    Example:
        # During application shutdown
        from src.core.graphiti import close_cached_client
        
        await close_cached_client()
    """
    global _cached_retrieval_graphiti
    
    async with _client_lock:
        if _cached_retrieval_graphiti is not None:
            logger.info("Closing cached Graphiti client")
            try:
                await _cached_retrieval_graphiti.driver.close()
                logger.info("✓ Cached client closed successfully")
            except Exception as e:
                logger.error(f"Error closing cached client: {e}")
            finally:
                _cached_retrieval_graphiti = None


# ============================================================================
# Context Manager for Ingestion (Automatic Cleanup)
# ============================================================================

@asynccontextmanager
async def graphiti_ingestion_client(
    clear_existing_graphdb_data: bool = False,
    max_coroutines: int = 1,
):
    """Context manager for ingestion operations with automatic cleanup.
    
    This is the recommended way to use GraphitiClient for ingestion,
    as it automatically handles connection cleanup.
    
    Args:
        clear_existing_graphdb_data: If True, clear existing graph data
        max_coroutines: Maximum concurrent coroutines for parallel processing
        
    Yields:
        Configured Graphiti instance
        
    Example:
        from src.core.graphiti import graphiti_ingestion_client
        
        async with graphiti_ingestion_client(max_coroutines=5) as graphiti:
            await graphiti.add_episode(...)
            await graphiti.add_episode(...)
        # Connection automatically closed
    """
    client = GraphitiClient()
    graphiti = await client.create_client(
        clear_existing_graphdb_data=clear_existing_graphdb_data,
        max_coroutines=max_coroutines,
    )
    
    try:
        yield graphiti
    finally:
        await client.close()


# ============================================================================
# Utility Functions
# ============================================================================

async def test_connection() -> bool:
    """Test connection to the graph database.
    
    Returns:
        True if connection successful, False otherwise
        
    Example:
        from src.core.graphiti import test_connection
        
        if await test_connection():
            print("Graph database is accessible")
        else:
            print("Cannot connect to graph database")
    """
    try:
        logger.info("Testing graph database connection...")
        graphiti = await get_graphiti_client()
        
        # Simple query to test connection
        result = await graphiti.driver.execute_query("RETURN 1 as test")
        
        if result and result[0]["test"] == 1:
            logger.info("✓ Graph database connection successful")
            return True
        else:
            logger.warning("Graph database connection test returned unexpected result")
            return False
            
    except Exception as e:
        logger.error(f"Graph database connection test failed: {e}")
        return False


async def get_graph_info() -> dict:
    """Get basic information about the graph database.
    
    Returns:
        Dictionary with graph statistics
        
    Example:
        from src.core.graphiti import get_graph_info
        
        info = await get_graph_info()
        print(f"Nodes: {info['node_count']}, Edges: {info['edge_count']}")
    """
    try:
        graphiti = await get_graphiti_client()
        driver = graphiti.driver
        
        # Get node count
        node_result = await driver.execute_query("MATCH (n) RETURN count(n) as count")
        node_count = node_result[0]["count"] if node_result else 0
        
        # Get edge count
        edge_result = await driver.execute_query("MATCH ()-[r]->() RETURN count(r) as count")
        edge_count = edge_result[0]["count"] if edge_result else 0
        
        # Get entity count
        entity_result = await driver.execute_query("MATCH (n:Entity) RETURN count(n) as count")
        entity_count = entity_result[0]["count"] if entity_result else 0
        
        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "entity_count": entity_count,
            "is_empty": node_count == 0,
        }
        
    except Exception as e:
        logger.exception("Error getting graph info")
        return {
            "error": str(e),
            "node_count": 0,
            "edge_count": 0,
            "entity_count": 0,
            "is_empty": True,
        }


# ============================================================================
# Export Public API
# ============================================================================

__all__ = [
    # Main client class
    "GraphitiClient",
    # Singleton for retrieval
    "get_graphiti_client",
    "close_cached_client",
    # Context manager for ingestion
    "graphiti_ingestion_client",
    # Utilities
    "test_connection",
    "get_graph_info",
]
