import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from graphiti_core.nodes import EpisodeType

from src.core.graphiti import GraphitiClient
from src.logger import setup_logging


logger = setup_logging()


class IngestionService:
    def __init__(self):
        self.graphiti_client: Optional[Any] = None
        self._client_wrapper: Optional[Any] = None

    async def initialize_client(
        self,
        clear_existing_graphdb_data: bool = False,
        max_coroutines: int = 1,
    ) -> None:
        """
        Initialize the Graphiti client for ingestion.

        Args:
            clear_existing_graphdb_data: Whether to clear existing graph data
            max_coroutines: Maximum number of concurrent coroutines for parallel processing.
                           Higher values (3-10) significantly speed up ingestion but use more resources.

        Note:
            This creates a fresh GraphitiClient instance for ingestion operations.
            The client should be closed after use by calling close_client().
        """
        client = GraphitiClient()
        self.graphiti_client = await client.create_client(
            clear_existing_graphdb_data=clear_existing_graphdb_data,
            max_coroutines=max_coroutines,
        )
        # Store the client wrapper for cleanup
        self._client_wrapper = client
        logger.info("Graphiti client initialized successfully for ingestion")

    async def close_client(self) -> None:
        """Close the Graphiti client connection and free resources.

        This should always be called after ingestion operations are complete
        to properly clean up database connections.
        """
        if self._client_wrapper:
            try:
                await self._client_wrapper.close()
                logger.info("Graphiti client connection closed")
            except Exception:
                logger.exception("Error while closing the Graphiti client")

        self.graphiti_client = None
        self._client_wrapper = None

    def load_documents(self, file_paths: list[Path]) -> list[dict[str, any]]:
        """
        Load documents from JSON files.

        Args:
            file_paths: List of paths to JSON files

        Returns:
            List of processed documents with chunks
        """
        documents: list[dict[str, any]] = []

        for file_path in file_paths:
            file_name = file_path.name
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except Exception as e:
                logger.exception("Failed to read/parse JSON file: %s", file_path)
                continue

            count = len(data) if isinstance(data, list) else 0
            logger.info("Loading %s - %d items", file_path, count)

            document_id = data[0]["document_id"] if len(data) else None

            document = {
                "id": document_id,
                "name": file_name,
                "chunks": [],
                "total_chunk": 0,
                "text_chunk": 0,
                "image_chunk": 0,
                "table_chunk": 0,
            }

            if not isinstance(data, list):
                logger.warning(
                    "Expected a list in %s, got %s; skipping.",
                    file_path,
                    type(data).__name__,
                )
                continue

            for item in data:
                # Text
                if item.get("text") is not None:
                    content = (item["text"].get("text_translated") or "") or (
                        item["text"].get("content") or ""
                    )
                    if content:
                        document["chunks"].append({"id": item["id"], "text": content})
                        document["text_chunk"] += 1
                        document["total_chunk"] += 1

                # Image caption
                if item.get("image") is not None:
                    caption = item["image"].get("image_caption")
                    if caption:
                        document["chunks"].append({"id": item["id"], "text": caption})
                        document["image_chunk"] += 1
                        document["total_chunk"] += 1

                # Table
                if item.get("table") is not None:
                    table_txt = item["table"].get("content")
                    if table_txt:
                        document["chunks"].append({"id": item["id"], "text": table_txt})
                        document["table_chunk"] += 1
                        document["total_chunk"] += 1

            documents.append(document)

        return documents

    async def ingest_documents(
        self,
        documents: list[dict[str, any]],
        add_communities: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Ingest documents into the knowledge graph.

        Args:
            documents: List of documents to ingest
            add_communities: Whether to build communities
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with ingestion statistics
        """
        if not self.graphiti_client:
            raise RuntimeError(
                "Graphiti client not initialized. Call initialize_client() first."
            )

        if add_communities:
            await self.graphiti_client.build_communities(group_ids=None)

        successful_chunks = 0
        failed_chunks = 0
        processed_documents = []

        total_docs = len(documents)
        logger.info("Beginning processing of %d document(s)", total_docs)

        for i, document in enumerate(documents, start=1):
            file_name = document["name"]
            document_id = document["id"]
            chunks = document["chunks"]

            logger.info(
                "Processing document %d/%d - %s (%d chunks)",
                i,
                total_docs,
                file_name,
                len(chunks),
            )

            doc_successful = 0
            doc_failed = 0

            for j, chunk in enumerate(chunks, start=1):
                try:
                    await self.graphiti_client.add_episode(
                        name=document_id,
                        episode_body=chunk["text"],
                        source_description=chunk["id"],
                        reference_time=datetime.now(),
                        source=EpisodeType.text,
                        group_id=document_id,
                        update_communities=True if add_communities else False,
                    )
                    logger.info(
                        "Chunk %d/%d for %s processed successfully",
                        j,
                        len(chunks),
                        file_name,
                    )
                    successful_chunks += 1
                    doc_successful += 1

                    # Call progress callback if provided
                    if progress_callback:
                        await progress_callback(
                            current_doc=i,
                            total_docs=total_docs,
                            current_chunk=j,
                            total_chunks=len(chunks),
                            doc_name=file_name,
                        )

                except Exception as e:
                    logger.exception(
                        "Error processing chunk %d/%d for %s. Chunk ID: %s",
                        j,
                        len(chunks),
                        file_name,
                        chunk["id"],
                    )
                    failed_chunks += 1
                    doc_failed += 1
                    continue

            processed_documents.append(
                {
                    "document_id": document_id,
                    "document_name": file_name,
                    "total_chunks": len(chunks),
                    "successful_chunks": doc_successful,
                    "failed_chunks": doc_failed,
                    "text_chunks": document["text_chunk"],
                    "image_chunks": document["image_chunk"],
                    "table_chunks": document["table_chunk"],
                }
            )

        total = successful_chunks + failed_chunks
        success_rate = (successful_chunks / total * 100.0) if total else 0.0

        logger.info("=== Processing Summary ===")
        logger.info("Successful chunks: %d", successful_chunks)
        logger.info("Failed chunks: %d", failed_chunks)
        logger.info("Total chunks: %d", total)
        logger.info("Chunk success rate: %.2f%%", success_rate)

        return {
            "total_documents": total_docs,
            "processed_documents": processed_documents,
            "total_chunks": total,
            "successful_chunks": successful_chunks,
            "failed_chunks": failed_chunks,
            "success_rate": round(success_rate, 2),
        }

    async def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph.

        Returns:
            Dictionary with graph statistics
        """
        if not self.graphiti_client:
            raise RuntimeError(
                "Graphiti client not initialized. Call initialize_client() first."
            )

        try:
            driver = self.graphiti_client.driver

            # Get node count
            node_count_query = "MATCH (n) RETURN count(n) as count"
            node_result = await driver.execute_query(node_count_query)
            node_count = node_result[0]["count"] if node_result else 0

            # Get edge count
            edge_count_query = "MATCH ()-[r]->() RETURN count(r) as count"
            edge_result = await driver.execute_query(edge_count_query)
            edge_count = edge_result[0]["count"] if edge_result else 0

            # Get entity node count
            entity_count_query = "MATCH (n:Entity) RETURN count(n) as count"
            entity_result = await driver.execute_query(entity_count_query)
            entity_count = entity_result[0]["count"] if entity_result else 0

            # Get episode node count
            episode_count_query = "MATCH (n:Episode) RETURN count(n) as count"
            episode_result = await driver.execute_query(episode_count_query)
            episode_count = episode_result[0]["count"] if episode_result else 0

            # Get community count
            community_count_query = "MATCH (n:Community) RETURN count(n) as count"
            community_result = await driver.execute_query(community_count_query)
            community_count = community_result[0]["count"] if community_result else 0

            return {
                "total_nodes": node_count,
                "total_edges": edge_count,
                "entity_nodes": entity_count,
                "episode_nodes": episode_count,
                "community_nodes": community_count,
            }

        except Exception as e:
            logger.exception("Error getting graph statistics")
            raise

    async def get_sample_nodes(
        self, limit: int = 10, node_type: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Get sample nodes from the knowledge graph.

        Args:
            limit: Maximum number of nodes to return
            node_type: Optional node type filter (e.g., 'Entity', 'Episode', 'Community')

        Returns:
            List of node dictionaries
        """
        if not self.graphiti_client:
            raise RuntimeError(
                "Graphiti client not initialized. Call initialize_client() first."
            )

        try:
            driver = self.graphiti_client.driver

            if node_type:
                query = f"MATCH (n:{node_type}) RETURN n LIMIT $limit"
            else:
                query = "MATCH (n) RETURN n LIMIT $limit"

            results = await driver.execute_query(query, {"limit": limit})

            nodes = []
            for record in results:
                node = record["n"]
                nodes.append(
                    {
                        "id": node.get("uuid", ""),
                        "name": node.get("name", ""),
                        "labels": list(node.labels) if hasattr(node, "labels") else [],
                        "properties": dict(node) if hasattr(node, "__iter__") else {},
                    }
                )

            return nodes

        except Exception as e:
            logger.exception("Error getting sample nodes")
            raise

    async def get_sample_edges(self, limit: int = 10) -> list[Dict[str, Any]]:
        """
        Get sample edges from the knowledge graph.

        Args:
            limit: Maximum number of edges to return

        Returns:
            List of edge dictionaries
        """
        if not self.graphiti_client:
            raise RuntimeError(
                "Graphiti client not initialized. Call initialize_client() first."
            )

        try:
            driver = self.graphiti_client.driver

            query = """
            MATCH (source)-[r]->(target)
            RETURN source.name as source_name, 
                   type(r) as relationship_type, 
                   target.name as target_name,
                   r as relationship
            LIMIT $limit
            """

            results = await driver.execute_query(query, {"limit": limit})

            edges = []
            for record in results:
                edges.append(
                    {
                        "source": record["source_name"],
                        "target": record["target_name"],
                        "relationship_type": record["relationship_type"],
                        "properties": (
                            dict(record["relationship"])
                            if record["relationship"]
                            else {}
                        ),
                    }
                )

            return edges

        except Exception as e:
            logger.exception("Error getting sample edges")
            raise
