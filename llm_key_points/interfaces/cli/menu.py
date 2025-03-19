"""
Interactive menu handling for the CLI interface.
"""

import csv
import os
from pathlib import Path
from typing import List

import questionary

from ..console.rich_presenter import RichPresenter
from .api_key_manager import get_api_key, manage_api_key
from .commands import (
    clean_dataset,
    convert_dataset,
    process_urls,
    validate_dataset,
    verify_dataset,
)

presenter = RichPresenter()


def validate_url(url: str) -> bool:
    """Validate URL format."""
    return url.startswith(("http://", "https://"))


def read_urls_from_csv(csv_path: Path) -> List[str]:
    """Read URLs from a CSV file.

    Args:
        csv_path: Path to the CSV file

    Returns:
        A list of URLs from the CSV file
    """
    urls = []

    # First check if file exists
    if not csv_path.exists():
        presenter.display_error_message(f"File not found: {csv_path}")
        return []

    # Check if file is readable
    if not csv_path.is_file() or not os.access(csv_path, os.R_OK):
        presenter.display_error_message(
            f"Cannot read file (check permissions): {csv_path}"
        )
        return []

    try:
        with open(csv_path, "r") as file:
            reader = csv.DictReader(file)
            # Check if the CSV has a column named 'urls' or 'url'
            fieldnames = reader.fieldnames
            url_column = None
            if fieldnames:
                if "urls" in fieldnames:
                    url_column = "urls"
                elif "url" in fieldnames:
                    url_column = "url"

            if url_column:
                for row in reader:
                    url = row[url_column].strip()
                    if url and validate_url(url):
                        urls.append(url)
            else:
                # If no header or specific column names found, try to read the first column
                with open(csv_path, "r") as file:
                    reader = csv.reader(file)
                    next(reader, None)  # Skip header row
                    for row in reader:
                        if row and row[0].strip() and validate_url(row[0].strip()):
                            urls.append(row[0].strip())

        return urls
    except Exception as e:
        presenter.display_error_message(f"Error reading CSV file: {str(e)}")
        return []


def get_urls() -> List[str]:
    """Get URLs from user input."""
    # First ask if the user wants to enter URLs manually or load from CSV
    source = questionary.select(
        "How would you like to provide URLs?",
        choices=[
            "Enter URLs manually",
            "Load from CSV file",
        ],
    ).ask()

    urls = []

    if source == "Load from CSV file":
        while True:
            csv_path = Path(
                questionary.path("Enter CSV file path:", default="./url.csv").ask()
            )

            if not csv_path.exists():
                presenter.display_error_message(f"File not found: {csv_path}")
                if questionary.confirm("Would you like to try another file?").ask():
                    continue
                else:
                    return (
                        get_urls_manually()
                        if questionary.confirm(
                            "Would you like to enter URLs manually instead?"
                        ).ask()
                        else []
                    )

            urls = read_urls_from_csv(csv_path)
            if urls:
                presenter.display_success_message(
                    f"Loaded {len(urls)} URLs from {csv_path}"
                )
                # Display some of the loaded URLs
                if len(urls) > 5:
                    for url in urls[:5]:
                        presenter.console.print(f"  - {url}", style="cyan")
                    presenter.console.print(
                        f"  - ... and {len(urls) - 5} more", style="cyan"
                    )
                else:
                    for url in urls:
                        presenter.console.print(f"  - {url}", style="cyan")
                break
            else:
                presenter.display_warning_message(f"No valid URLs found in {csv_path}")
                if questionary.confirm("Would you like to try another file?").ask():
                    continue
                elif questionary.confirm(
                    "Would you like to enter URLs manually instead?"
                ).ask():
                    return get_urls_manually()
                else:
                    return []
    else:
        urls = get_urls_manually()

    return urls


def get_urls_manually() -> List[str]:
    """Get URLs through manual input."""
    urls = []
    while True:
        url = questionary.text(
            "Enter URL (or press Enter to finish):",
            validate=lambda text: not text
            or validate_url(text)
            or "Invalid URL format",
        ).ask()

        if not url:
            if not urls:
                presenter.display_warning_message("Please enter at least one URL")
                continue
            break

        urls.append(url)
        presenter.display_success_message(f"Added URL: {url}")

        if len(urls) >= 1 and not questionary.confirm("Add another URL?").ask():
            break

    return urls


def handle_process_urls():
    """Handle the process URLs menu option."""
    dataset_path = Path(
        questionary.path("Enter dataset path:", default="./dataset.json").ask()
    )
    backup = questionary.confirm("Create backup before processing?", default=True).ask()
    verify_points = questionary.confirm(
        "Verify key points against original content?", default=False
    ).ask()

    urls = get_urls()
    if not urls:
        presenter.display_warning_message("No URLs provided. Operation cancelled.")
        return

    if not questionary.confirm("Process these URLs?").ask():
        presenter.display_warning_message("Operation cancelled")
        return

    api_key = get_api_key()
    process_urls(urls, dataset_path, backup, verify_points, api_key)


def handle_clean_dataset():
    """Handle the clean dataset menu option."""
    dataset_path = Path(
        questionary.path("Enter dataset path:", default="./dataset.json").ask()
    )
    backup = questionary.confirm("Create backup before cleaning?", default=True).ask()
    api_key = get_api_key()
    clean_dataset(dataset_path, backup, api_key)


def handle_verify_dataset():
    """Handle the verify dataset menu option."""
    input_dataset = Path(
        questionary.path("Enter input dataset path:", default="./dataset.json").ask()
    )
    output_dataset = questionary.path(
        "Enter output dataset path (leave empty for default):", default=""
    ).ask()
    backup = questionary.confirm("Create backup before processing?", default=True).ask()
    output_path = Path(output_dataset) if output_dataset else None
    verify_dataset(input_dataset, output_path, backup)


def handle_convert_dataset():
    """Handle the convert dataset menu option."""
    input_path = Path(
        questionary.path("Enter input dataset path:", default="./dataset.json").ask()
    )
    output_path = Path(
        questionary.path("Enter output path:", default="./dataset_sharegpt.json").ask()
    )
    convert_dataset(input_path, output_path)


def main_menu():
    """Display and handle main menu."""
    while True:
        presenter.display_welcome()

        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "🌐 Process URLs",
                "🧹 Clean Existing Dataset",
                "📊 View Dataset Info",
                "✅ Validate Dataset",
                "🔍 Verify Dataset Key Points",
                "🔄 Convert to ShareGPT Format",
                "🔑 Manage API Key",
                "❌ Exit",
            ],
        ).ask()

        if choice == "🌐 Process URLs":
            handle_process_urls()
        elif choice == "🧹 Clean Existing Dataset":
            handle_clean_dataset()
        elif choice == "📊 View Dataset Info":
            dataset_path = Path(
                questionary.path("Enter dataset path:", default="./dataset.json").ask()
            )
            validate_dataset(dataset_path)
        elif choice == "✅ Validate Dataset":
            dataset_path = Path(
                questionary.path("Enter dataset path:", default="./dataset.json").ask()
            )
            validate_dataset(dataset_path)
        elif choice == "🔍 Verify Dataset Key Points":
            handle_verify_dataset()
        elif choice == "🔄 Convert to ShareGPT Format":
            handle_convert_dataset()
        elif choice == "🔑 Manage API Key":
            manage_api_key()
        else:
            presenter.console.print("\n👋 Goodbye!", style="bold cyan")

            return
        input("\nPress Enter to continue...")
