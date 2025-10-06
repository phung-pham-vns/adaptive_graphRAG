"""CLI script for ingesting documents into knowledge graph.

This script has been refactored to use the IngestionService.
For API-based ingestion, see src/api/routes/ingestion.py
"""

import asyncio
import argparse
from pathlib import Path

from src.ingestion.service import IngestionService
from src.logger import setup_logging


logger = setup_logging()


async def main(
    data_dir: Path,
    clear_existing_graphdb_data: bool = False,
    max_coroutines: int = 1,
    add_communities: bool = False,
):
    """
    Main function to ingest documents from command line.

    Args:
        data_dir: Directory containing JSON files
        clear_existing_graphdb_data: Whether to clear existing graph data
        max_coroutines: Maximum number of concurrent coroutines
        add_communities: Whether to build communities after ingestion
    """
    service = IngestionService()

    try:
        # Find JSON files
        json_paths = list(data_dir.glob("*.json"))

        if not json_paths:
            logger.warning("No JSON files found in %s", data_dir)
            return

        logger.info("Found %d JSON files in %s", len(json_paths), data_dir)

        # Initialize client
        await service.initialize_client(
            clear_existing_graphdb_data=clear_existing_graphdb_data,
            max_coroutines=max_coroutines,
        )

        # Load documents
        documents = service.load_documents(json_paths)

        if not documents:
            logger.warning("No valid documents found to process")
            return

        # Ingest documents
        result = await service.ingest_documents(
            documents=documents, add_communities=add_communities
        )

        logger.info("=== Final Summary ===")
        logger.info("Total documents: %d", result["total_documents"])
        logger.info("Total chunks: %d", result["total_chunks"])
        logger.info("Successful chunks: %d", result["successful_chunks"])
        logger.info("Failed chunks: %d", result["failed_chunks"])
        logger.info("Success rate: %.2f%%", result["success_rate"])

    finally:
        await service.close_client()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest documents into knowledge graph from command line"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Directory containing JSON files to ingest",
    )
    parser.add_argument(
        "--clear-existing-graphdb-data",
        action="store_true",
        help="Clear existing graph data before ingestion",
    )
    parser.add_argument(
        "--max-coroutines",
        type=int,
        default=1,
        help="Maximum number of concurrent coroutines (default: 1)",
    )
    parser.add_argument(
        "--add-communities",
        action="store_true",
        help="Build communities after ingestion",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    asyncio.run(
        main(
            data_dir=data_dir,
            clear_existing_graphdb_data=args.clear_existing_graphdb_data,
            max_coroutines=args.max_coroutines,
            add_communities=args.add_communities,
        )
    )
