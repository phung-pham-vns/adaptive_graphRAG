from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def process_metadata(data_dir: Path) -> dict:
    metadata = {}
    for file in data_dir.glob("*.pdf_index.json"):
        try:
            with file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if data and isinstance(data, list) and data[0].get("document_id"):
                metadata[data[0]["document_id"]] = file.stem
                logging.info(f"Processed {file.name}")
            else:
                logging.warning(f"Skipping invalid file: {file}")
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error processing {file}: {e}")
    return metadata


def main():
    data_dir = Path("/Users/mac/Documents/PHUNGPX/adaptive_rag/data/pest_and_disease")
    output_file = Path(
        "/Users/mac/Documents/PHUNGPX/adaptive_rag/data/QA_17_pest_disease_document_metadata.json"
    )

    if not data_dir.exists():
        logging.error(f"Directory not found: {data_dir}")
        return

    metadata = process_metadata(data_dir)

    try:
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
        logging.info(f"Saved metadata to {output_file}")
    except IOError as e:
        logging.error(f"Failed to save metadata: {e}")


if __name__ == "__main__":
    main()
