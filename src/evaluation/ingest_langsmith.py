import json
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from langsmith import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")


@dataclass
class DatasetConfig:
    """Configuration for dataset ingestion."""

    name: str = "Durian Pest and Disease"
    description: str = (
        "Questions and answers about durian pests and diseases for RAG evaluation."
    )
    source: str = "17-document-durian-pest-and-disease"
    data_file: str = "data/QA_17_pest_disease.json"


class DatasetFilter:
    def __init__(
        self,
        question_type: Optional[str] = None,
        batch: Optional[str] = None,
        num_samples: Optional[int] = None,
    ):
        """
        Initialize the dataset filter.

        Args:
            question_type: Filter by question type ("1-hop", "multi-hop", etc.)
            batch: Filter by batch ("a", "b", etc.)
            num_samples: Maximum number of samples to return
        """
        self.question_type = question_type
        self.batch = batch
        self.num_samples = num_samples

    def apply(self, samples: List[dict]) -> List[dict]:
        """
        Apply filters to the samples.

        Args:
            samples: List of sample dictionaries

        Returns:
            Filtered list of samples
        """
        filtered = samples

        if self.question_type:
            filtered = [s for s in filtered if s.get("type") == self.question_type]
            print(f"Filtered to {len(filtered)} samples of type '{self.question_type}'")

        if self.batch:
            filtered = [s for s in filtered if s.get("batch") == self.batch]
            print(f"Filtered to {len(filtered)} samples in batch '{self.batch}'")

        if self.num_samples:
            filtered = filtered[: self.num_samples]
            print(f"Limited to {len(filtered)} samples")

        return filtered


class DatasetLoader:
    @staticmethod
    def load_samples(data_file: str) -> List[dict]:
        """
        Load samples from JSON file.

        Args:
            data_file: Path to JSON file containing samples

        Returns:
            List of sample dictionaries

        Raises:
            FileNotFoundError: If data file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        data_path = Path(data_file)

        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_file}")

        try:
            with open(data_path, "r", encoding="utf-8") as f:
                samples = json.load(f)

            if not isinstance(samples, list):
                raise ValueError("Data file must contain a JSON array")

            print(f"✓ Loaded {len(samples)} samples from {data_file}")
            return samples
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in {data_file}: {e.msg}", e.doc, e.pos
            )


class ExampleFormatter:
    def __init__(self, source: str):
        """
        Initialize the formatter.

        Args:
            source: Source identifier for metadata
        """
        self.source = source

    def format_samples(self, samples: List[dict]) -> List[Dict[str, Any]]:
        """
        Format samples into LangSmith example format.

        Args:
            samples: List of sample dictionaries

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
                    "source": self.source,
                    "type": sample.get("type", "unknown"),
                    "batch": sample.get("batch", "unknown"),
                },
            }
            examples.append(example)

        return examples


class LangSmithDatasetManager:
    def __init__(self, client: Optional[Client] = None):
        """
        Initialize the dataset manager.

        Args:
            client: Optional LangSmith client (creates one if not provided)
        """
        self.client = client or Client()

    def create_or_update_dataset(
        self,
        dataset_name: str,
        description: str,
        examples: List[Dict[str, Any]],
        overwrite: bool = False,
    ) -> None:
        """
        Create or update a LangSmith dataset.

        Args:
            dataset_name: Name of the dataset
            description: Dataset description
            examples: List of examples to upload
            overwrite: If True, delete existing dataset before creating new one

        Raises:
            Exception: If dataset operation fails
        """
        try:
            existing_datasets = list(
                self.client.list_datasets(dataset_name=dataset_name)
            )

            if existing_datasets:
                if overwrite:
                    print(f"⚠ Deleting existing dataset '{dataset_name}'...")
                    for ds in existing_datasets:
                        self.client.delete_dataset(dataset_id=ds.id)
                else:
                    print(f"ℹ Dataset '{dataset_name}' already exists.")
                    dataset = existing_datasets[0]
                    print(f"Adding {len(examples)} new examples...")
                    self.client.create_examples(
                        dataset_id=dataset.id,
                        examples=examples,
                    )
                    print(f"✓ Successfully added examples to '{dataset_name}'")
                    return

            # Create new dataset
            print(f"Creating new dataset '{dataset_name}'...")
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description=description,
            )

            # Upload examples
            print(f"Uploading {len(examples)} examples...")
            self.client.create_examples(
                dataset_id=dataset.id,
                examples=examples,
            )

            print(
                f"✓ Successfully created dataset '{dataset_name}' with {len(examples)} examples"
            )

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            raise


class DataIngestionPipeline:
    def __init__(self, config: DatasetConfig):
        """
        Initialize the ingestion pipeline.

        Args:
            config: Dataset configuration
        """
        self.config = config
        self.loader = DatasetLoader()
        self.formatter = ExampleFormatter(config.source)
        self.manager = LangSmithDatasetManager()

    def run(
        self,
        filter_config: Optional[DatasetFilter] = None,
        overwrite: bool = False,
    ) -> None:
        """
        Run the ingestion pipeline.

        Args:
            filter_config: Optional filter configuration
            overwrite: Whether to overwrite existing dataset
        """
        print("=" * 80)
        print("LangSmith Dataset Ingestion")
        print("=" * 80)
        print(f"Data file: {self.config.data_file}")
        print(f"Dataset name: {self.config.name}")
        print(f"Source: {self.config.source}")
        print(f"Overwrite: {overwrite}")
        print("=" * 80)
        print()

        # Load samples
        samples = self.loader.load_samples(self.config.data_file)

        # Apply filters if provided
        if filter_config:
            samples = filter_config.apply(samples)

        if not samples:
            print("⚠ No samples to upload after filtering!")
            return

        # Format examples
        examples = self.formatter.format_samples(samples)

        # Create/update dataset
        self.manager.create_or_update_dataset(
            dataset_name=self.config.name,
            description=self.config.description,
            examples=examples,
            overwrite=overwrite,
        )


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Ingest Durian Pest and Disease data into LangSmith"
    )

    # Data source arguments
    parser.add_argument(
        "--data-file",
        type=str,
        default="data/QA_17_pest_disease.json",
        help="Path to JSON data file",
    )
    parser.add_argument(
        "--source",
        type=str,
        default="17-document-durian-pest-and-disease",
        help="Source identifier for metadata",
    )

    # Dataset arguments
    parser.add_argument(
        "--dataset-name",
        type=str,
        default="Durian Pest and Disease",
        help="Name of the LangSmith dataset",
    )
    parser.add_argument(
        "--description",
        type=str,
        default="Questions and answers about durian pests and diseases for RAG evaluation.",
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

    return parser.parse_args()


def main():
    """Main entry point for ingestion script."""
    args = parse_arguments()

    # Create configuration
    config = DatasetConfig(
        name=args.dataset_name,
        description=args.description,
        source=args.source,
        data_file=args.data_file,
    )

    # Create filter if any filtering requested
    filter_config = None
    if args.type or args.batch or args.num_samples:
        filter_config = DatasetFilter(
            question_type=args.type,
            batch=args.batch,
            num_samples=args.num_samples,
        )

    # Run ingestion pipeline
    pipeline = DataIngestionPipeline(config)
    pipeline.run(filter_config=filter_config, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
