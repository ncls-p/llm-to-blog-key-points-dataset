#!/usr/bin/env python3
import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def convert_to_sharegpt_format(entry: Dict[str, str]) -> Dict[str, Any]:
    """
    Convert a single dataset entry to ShareGPT format.

    Input format:
    {
        "instruction": "",
        "input": "Full article content",
        "output": "Key points extracted by the AI"
    }

    Output format:
    {
        "conversations": [
            {"from": "human", "value": "Full article content"},
            {"from": "gpt", "value": "Key points extracted by the AI"}
        ],
        "source": "article-key-points"
    }
    """
    # Create the conversation list
    conversations = [
        {"from": "human", "value": entry.get("input", "")},
        {"from": "gpt", "value": entry.get("output", "")},
    ]

    # If there's an instruction, prepend it to the input or add it as a separate message
    if entry.get("instruction") and entry.get("instruction").strip():
        # Option 1: Add instruction as a separate message
        conversations.insert(
            0, {"from": "human", "value": entry.get("instruction", "")}
        )

        # Option 2 (alternative): Combine instruction with input
        # conversations[0]["value"] = f"{entry.get('instruction', '')}\n\n{entry.get('input', '')}"

    return {"conversations": conversations, "source": "article-key-points"}


def convert_dataset(input_path: Path, output_path: Path) -> None:
    """Convert the entire dataset to ShareGPT format."""
    try:
        # Load the input dataset
        with open(input_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        logger.info(f"Loaded {len(dataset)} entries from {input_path}")

        # Convert each entry
        sharegpt_dataset = []
        for entry in dataset:
            sharegpt_entry = convert_to_sharegpt_format(entry)
            sharegpt_dataset.append(sharegpt_entry)

        # Save the converted dataset
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sharegpt_dataset, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Successfully converted and saved {len(sharegpt_dataset)} entries to {output_path}"
        )

    except Exception as e:
        logger.error(f"Error converting dataset: {e}")


def main():
    parser = argparse.ArgumentParser(description="Convert dataset to ShareGPT format")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="./dataset.json",
        help="Path to the input dataset file",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="./dataset_sharegpt.json",
        help="Path to save the converted dataset",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file {input_path} does not exist")
        return

    convert_dataset(input_path, output_path)


if __name__ == "__main__":
    main()
