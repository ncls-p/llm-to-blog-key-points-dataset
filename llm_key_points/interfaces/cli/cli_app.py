"""
Command line interface for the LLM Key Points Dataset Generator.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from ..console.rich_presenter import RichPresenter
from .api_key_manager import get_api_key
from .commands import (
    clean_dataset,
    convert_dataset,
    process_urls,
    validate_dataset,
    verify_dataset,
)
from .menu import get_urls, main_menu, read_urls_from_csv

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
    auto_check: bool = typer.Option(
        False,
        "--auto-check",
        "-a",
        help="Automatically verify and regenerate inaccurate key points",
    ),
    max_attempts: int = typer.Option(
        2,
        "--max-attempts",
        "-m",
        help="Maximum number of regeneration attempts when auto-checking",
    ),
    csv_file: Optional[Path] = typer.Option(
        None, "--csv", "-c", help="Path to a CSV file containing URLs to process"
    ),
):
    """Process URLs and enhance your dataset with OpenAI compatible API."""
    urls = []

    if csv_file:
        if not csv_file.exists():
            presenter.display_error_message(f"CSV file not found: {csv_file}")
            raise typer.Exit(1)

        urls = read_urls_from_csv(csv_file)
        if not urls:
            presenter.display_error_message(f"No valid URLs found in {csv_file}")
            raise typer.Exit(1)

        presenter.display_success_message(f"Loaded {len(urls)} URLs from {csv_file}")
    else:
        urls = get_urls()

    if not urls:
        presenter.display_warning_message("No URLs provided. Operation cancelled.")
        return

    api_key = get_api_key()
    process_urls(
        urls, dataset_path, backup, verify_points, api_key, auto_check, max_attempts
    )


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
