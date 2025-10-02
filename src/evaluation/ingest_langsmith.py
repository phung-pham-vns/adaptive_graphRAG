"""
Enhanced LangSmith dataset ingestion script for Durian Pest and Disease dataset.

This script loads questions and answers from JSON files and uploads them to LangSmith
for evaluation. Supports filtering by question type and batch.
"""

import json
import argparse
from pathlib import Path
from typing import List, Optional
from langsmith import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# Default configuration
DEFAULT_SOURCE = "17-document-durian-pest-and-disease"
DEFAULT_DATA_FILE = "data/QA_17_pest_disease.json"
DEFAULT_DATASET_NAME = "Durian Pest and Disease"
DEFAULT_DATASET_DESC = (
    "Questions and answers about durian pests and diseases for RAG evaluation."
)


def load_samples(data_file: str) -> List[dict]:
    """
    Load samples from JSON file.

    Args:
        data_file: Path to JSON file containing samples

    Returns:
        List of sample dictionaries
    """
    data_path = Path(data_file)

    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")

    with open(data_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    print(f"Loaded {len(samples)} samples from {data_file}")
    return samples


def filter_samples(
    samples: List[dict],
    question_type: Optional[str] = None,
    batch: Optional[str] = None,
    num_samples: Optional[int] = None,
) -> List[dict]:
    """
    Filter samples based on criteria.

    Args:
        samples: List of sample dictionaries
        question_type: Filter by question type ("1-hop", "multi-hop", etc.)
        batch: Filter by batch ("a", "b", etc.)
        num_samples: Maximum number of samples to return

    Returns:
        Filtered list of samples
    """
    filtered = samples

    if question_type:
        filtered = [s for s in filtered if s.get("type") == question_type]
        print(f"Filtered to {len(filtered)} samples of type '{question_type}'")

    if batch:
        filtered = [s for s in filtered if s.get("batch") == batch]
        print(f"Filtered to {len(filtered)} samples in batch '{batch}'")

    if num_samples:
        filtered = filtered[:num_samples]
        print(f"Limited to {len(filtered)} samples")

    return filtered


def format_examples(samples: List[dict], source: str) -> List[dict]:
    """
    Format samples into LangSmith example format.

    Args:
        samples: List of sample dictionaries
        source: Source identifier for metadata

    Returns:
        List of formatted examples
    """
    examples = []

    for sample in samples:
        example = {
            "inputs": {"question": sample.get("question", "")},
            "outputs": {
                "answer": sample.get("answer", ""),
                "citation": sample.get("citation", []),
            },
            "metadata": {
                "source": source,
                "type": sample.get("type", "unknown"),
                "batch": sample.get("batch", "unknown"),
            },
        }
        examples.append(example)

    return examples


def create_or_update_dataset(
    client: Client,
    dataset_name: str,
    description: str,
    examples: List[dict],
    overwrite: bool = False,
) -> None:
    """
    Create or update a LangSmith dataset.

    Args:
        client: LangSmith client
        dataset_name: Name of the dataset
        description: Dataset description
        examples: List of examples to upload
        overwrite: If True, delete existing dataset before creating new one
    """
    try:
        # Check if dataset exists
        existing_datasets = list(client.list_datasets(dataset_name=dataset_name))

        if existing_datasets:
            if overwrite:
                print(f"Deleting existing dataset '{dataset_name}'...")
                for ds in existing_datasets:
                    client.delete_dataset(dataset_id=ds.id)
            else:
                print(f"Dataset '{dataset_name}' already exists.")
                dataset = existing_datasets[0]
                print(f"Adding {len(examples)} new examples...")
                client.create_examples(dataset_id=dataset.id, examples=examples)
                print(f"Successfully added examples to '{dataset_name}'")
                return

        # Create new dataset
        print(f"Creating new dataset '{dataset_name}'...")
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description=description,
        )

        # Upload examples
        print(f"Uploading {len(examples)} examples...")
        client.create_examples(dataset_id=dataset.id, examples=examples)

        print(
            f"✓ Successfully created dataset '{dataset_name}' with {len(examples)} examples"
        )

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        raise


def main():
    """Main function to run the ingestion script."""
    parser = argparse.ArgumentParser(
        description="Ingest Durian Pest and Disease data into LangSmith"
    )

    # Data source arguments
    parser.add_argument(
        "--data-file",
        type=str,
        default=DEFAULT_DATA_FILE,
        help=f"Path to JSON data file (default: {DEFAULT_DATA_FILE})",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=DEFAULT_SOURCE,
        help=f"Source identifier for metadata (default: {DEFAULT_SOURCE})",
    )

    # Dataset arguments
    parser.add_argument(
        "--dataset-name",
        type=str,
        default=DEFAULT_DATASET_NAME,
        help=f"Name of the LangSmith dataset (default: {DEFAULT_DATASET_NAME})",
    )
    parser.add_argument(
        "--description",
        type=str,
        default=DEFAULT_DATASET_DESC,
        help="Dataset description",
    )

    # Filtering arguments
    parser.add_argument(
        "--type",
        type=str,
        choices=["1-hop", "multi-hop"],
        help="Filter by question type",
    )
    parser.add_argument(
        "--batch",
        type=str,
        help="Filter by batch identifier",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        help="Maximum number of samples to upload",
    )

    # Options
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing dataset if it exists",
    )

    args = parser.parse_args()

    # Print configuration
    print("=" * 80)
    print("LangSmith Dataset Ingestion")
    print("=" * 80)
    print(f"Data file: {args.data_file}")
    print(f"Dataset name: {args.dataset_name}")
    print(f"Source: {args.source}")
    if args.type:
        print(f"Type filter: {args.type}")
    if args.batch:
        print(f"Batch filter: {args.batch}")
    if args.num_samples:
        print(f"Sample limit: {args.num_samples}")
    print(f"Overwrite: {args.overwrite}")
    print("=" * 80)
    print()

    # Load and filter samples
    samples = load_samples(args.data_file)
    filtered_samples = filter_samples(
        samples,
        question_type=args.type,
        batch=args.batch,
        num_samples=args.num_samples,
    )

    if not filtered_samples:
        print("No samples to upload after filtering!")
        return

    # Format examples
    examples = format_examples(filtered_samples, args.source)

    # Create/update dataset
    client = Client()
    create_or_update_dataset(
        client=client,
        dataset_name=args.dataset_name,
        description=args.description,
        examples=examples,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
