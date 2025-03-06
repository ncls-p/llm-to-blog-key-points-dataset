"""
Command line interface for the LLM Key Points Dataset Generator.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from .api_key_manager import get_api_key
from .commands import (
    process_urls,
    clean_dataset,
    validate_dataset,
    verify_dataset,
    convert_dataset,
)
from .menu import main_menu, get_urls
from ..console.rich_presenter import RichPresenter

# Load environment variables
load_dotenv()

# Create Typer app
app = typer.Typer(help="🚀 LLM Key Points Dataset Generator")

# Create presenter
presenter = RichPresenter()


@app.command()
def process(
    dataset_path: Path = typer.Option(
        "./dataset.json", "--dataset", "-d", help="Path to the dataset file"
    ),
    backup: bool = typer.Option(
        True, "--backup/--no-backup", help="Create backup before processing"
    ),
    verify_points: bool = typer.Option(
        False,
        "--verify-points",
        help="Verify key points against original content using Ollama",
    ),
):
    """Process URLs and enhance your dataset with OpenAI compatible API."""
    urls = get_urls()
    api_key = get_api_key()
    process_urls(urls, dataset_path, backup, verify_points, api_key)


@app.command()
def clean(
    dataset_path: Path = typer.Argument(
        "./dataset.json", help="Path to the dataset file"
    ),
    backup: bool = typer.Option(
        True, "--backup/--no-backup", help="Create backup before cleaning"
    ),
):
    """Clean references from existing dataset entries."""
    api_key = get_api_key()
    clean_dataset(dataset_path, backup, api_key)


@app.command()
def validate(
    dataset_path: Path = typer.Argument(
        "./dataset.json", help="Path to the dataset file"
    ),
):
    """Validate the dataset file format."""
    validate_dataset(dataset_path)


@app.command()
def verify(
    input_dataset: Path = typer.Argument(..., help="Path to the input dataset file"),
    output_dataset: Optional[Path] = typer.Argument(
        None,
        help="Path to save the verified dataset (defaults to input_dataset_verified.json)",
    ),
    backup: bool = typer.Option(
        True, "--backup/--no-backup", help="Create backup before processing"
    ),
):
    """Verify key points in an existing dataset against their original content."""
    verify_dataset(input_dataset, output_dataset, backup)


@app.command()
def convert(
    input_path: Path = typer.Argument(
        "./dataset.json", help="Path to the input dataset file"
    ),
    output_path: Path = typer.Argument(
        "./dataset_sharegpt.json", help="Path to save the converted dataset"
    ),
):
    """Convert dataset to ShareGPT format for fine-tuning."""
    convert_dataset(input_path, output_path)


def run():
    """Run the CLI application."""
    if len(sys.argv) > 1:
        app()
    else:
        main_menu()


if __name__ == "__main__":
    run()
