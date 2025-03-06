"""
Command line interface for the LLM Key Points Dataset Generator.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

import typer
import questionary
from dotenv import load_dotenv

from ..console.rich_presenter import RichPresenter
from ...adapters.repositories.json_dataset_repository import JsonDatasetRepository
from ...adapters.repositories.web_content_repository import BeautifulSoupWebRepository
from ...adapters.api.openai_compatible_extractor import OpenAICompatibleExtractor
from ...adapters.verification.ollama_fact_checker import OllamaFactChecker
from ...core.use_cases.extract_key_points import ExtractKeyPointsUseCase
from ...core.use_cases.verify_key_points import VerifyDatasetUseCase
from ...core.entities.dataset import Dataset

# Load environment variables
load_dotenv()

# Create Typer app
app = typer.Typer(help="🚀 LLM Key Points Dataset Generator")

# Create presenter
presenter = RichPresenter()


def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    # More generic validation that works with various API providers
    return len(api_key) > 20


def get_api_key() -> str:
    """Get API key from environment or user input."""
    api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY")

    if api_key and validate_api_key(api_key):
        return api_key

    presenter.display_warning_message("API key not found in environment or invalid.")

    api_key = questionary.text(
        "Please enter your OpenAI compatible API key:",
        validate=lambda text: validate_api_key(text) or "Invalid API key format",
    ).ask()

    # Ask if user wants to save to .env
    if questionary.confirm("Would you like to save this API key to .env file?").ask():
        # Check if .env exists and update it
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                env_content = f.read()

            if "OPENAI_COMPATIBLE_API_KEY=" in env_content:
                # Replace existing key
                env_content = re.sub(
                    r"OPENAI_COMPATIBLE_API_KEY=.*",
                    f"OPENAI_COMPATIBLE_API_KEY={api_key}",
                    env_content,
                )
            else:
                # Add new key
                env_content += f"\nOPENAI_COMPATIBLE_API_KEY={api_key}"

            with open(".env", "w") as f:
                f.write(env_content)
        else:
            # Create new .env file
            with open(".env", "w") as f:
                f.write(f"OPENAI_COMPATIBLE_API_KEY={api_key}")

        presenter.display_success_message("API key saved to .env file")

    return api_key


def validate_url(url: str) -> bool:
    """Validate URL format."""
    return url.startswith(("http://", "https://"))


def get_urls() -> List[str]:
    """Get URLs from user input."""
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


def manage_api_key():
    """Manage API key settings."""
    while True:
        choice = questionary.select(
            "API Key Management:",
            choices=[
                "View current API key",
                "Update API key",
                "Remove API key",
                "Back to main menu",
            ],
        ).ask()

        if choice == "View current API key":
            api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY")
            if api_key:
                presenter.console.print(
                    f"\n🔑 Current API key: {api_key[:8]}...{api_key[-4:]}",
                    style="green",
                )
            else:
                presenter.display_warning_message("No API key found")
        elif choice == "Update API key":
            api_key = get_api_key()
            presenter.display_success_message("API key updated")
        elif choice == "Remove API key":
            if os.path.exists(".env"):
                os.remove(".env")
                presenter.display_success_message("API key removed")
            else:
                presenter.display_warning_message("No .env file found")
        else:
            break


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
        help="Verify key points against original content using Bespoke-MiniCheck",
    ),
):
    """Process URLs and enhance your dataset with OpenAI compatible API."""
    # Get URLs interactively
    urls = get_urls()

    # Display URLs to process
    presenter.console.print("\n📋 URLs to process:", style="bold cyan")
    presenter.console.print(presenter.create_url_table(urls))

    # Confirm processing
    if not questionary.confirm("Process these URLs?").ask():
        presenter.display_warning_message("Operation cancelled")
        raise typer.Exit()

    # Get API key
    api_key = get_api_key()

    # Set up components
    web_repo = BeautifulSoupWebRepository()
    dataset_repo = JsonDatasetRepository()
    extractor = OpenAICompatibleExtractor(api_key)

    # Set up fact checker if verification is requested
    fact_checker = None
    if verify_points:
        fact_checker = OllamaFactChecker()

    # Create use case
    use_case = ExtractKeyPointsUseCase(
        web_repository=web_repo,
        dataset_repository=dataset_repo,
        key_points_extractor=extractor,
        fact_checker=fact_checker,
    )

    # Process URLs with progress bar
    with presenter.create_progress("Processing URLs...") as progress:
        task = progress.add_task("Processing URLs...", total=len(urls))

        for i, url in enumerate(urls):
            progress_message = f"Processing: {url}"
            if verify_points:
                progress_message += " (with verification)"

            progress.update(task, description=progress_message)

            # Process the URL
            try:
                entry = use_case.extract_from_url(url, verify_points)
                if entry:
                    # Load current dataset
                    dataset = dataset_repo.load(dataset_path)

                    # Add the new entry
                    dataset.add_entry(entry)

                    # Save the updated dataset
                    dataset_repo.save(dataset, dataset_path, backup=(i == 0 and backup))

                progress.advance(task)
            except Exception as e:
                presenter.display_error_message(f"Error processing {url}: {str(e)}")

    # Show completion message
    presenter.display_success_message(
        f"Processing complete! Dataset saved to {dataset_path}"
    )

    # If verification was enabled, show a summary
    if verify_points:
        # Load the dataset to get statistics
        dataset = dataset_repo.load(dataset_path)
        stats = dataset.get_stats()
        presenter.display_verification_stats(stats)


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
    # Set up components
    dataset_repo = JsonDatasetRepository()

    try:
        # Load the dataset
        dataset = dataset_repo.load(dataset_path)

        # Get API key (we need it for the extractor)
        api_key = get_api_key()
        extractor = OpenAICompatibleExtractor(api_key)

        # Clean each entry with progress bar
        with presenter.create_progress("Cleaning dataset...") as progress:
            task = progress.add_task("Cleaning dataset...", total=len(dataset.entries))

            cleaned_count = 0
            for entry in dataset.entries:
                if entry.output:
                    entry.output = extractor.clean_references(entry.output)
                    cleaned_count += 1
                progress.advance(task)

        # Save the cleaned dataset
        dataset_repo.save(dataset, dataset_path, backup)

        # Show results
        presenter.display_success_message("Dataset cleaning complete!")

        stats = {
            "Total entries": len(dataset.entries),
            "Cleaned entries": cleaned_count,
        }

        stats_table = presenter.console.Table(
            show_header=True, header_style="bold magenta"
        )
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")

        for key, value in stats.items():
            stats_table.add_row(key, str(value))

        presenter.console.print("\n📊 Cleaning Statistics:", style="bold cyan")
        presenter.console.print(stats_table)

    except Exception as e:
        presenter.display_error_message(f"Error cleaning dataset: {str(e)}")


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
    """Verify key points in an existing dataset against their original content using Bespoke-MiniCheck."""
    # Check if input dataset exists
    if not input_dataset.exists():
        presenter.display_error_message(f"Dataset file not found: {input_dataset}")
        raise typer.Exit(1)

    # Get API key
    api_key = get_api_key()

    # Set up components
    dataset_repo = JsonDatasetRepository()
    fact_checker = OllamaFactChecker()

    # Check if Ollama is available
    try:
        ollama_url = os.getenv(
            "OLLAMA_API_URL", "http://localhost:11434/v1/chat/completions"
        )
        base_url = ollama_url.replace("/v1/chat/completions", "/api/tags")

        import requests

        response = requests.get(base_url)

        if response.status_code != 200:
            presenter.display_warning_message(
                "Could not connect to Ollama API. Make sure Ollama is running."
            )
            if not questionary.confirm("Continue anyway?").ask():
                presenter.display_warning_message("Operation cancelled")
                raise typer.Exit()
    except Exception:
        presenter.display_warning_message(
            "Could not connect to Ollama API. Make sure Ollama is running."
        )
        if not questionary.confirm("Continue anyway?").ask():
            presenter.display_warning_message("Operation cancelled")
            raise typer.Exit()

    # Create use case
    verify_use_case = VerifyDatasetUseCase(
        dataset_repository=dataset_repo, fact_checker=fact_checker
    )

    # Confirm verification
    presenter.console.print(
        f"\n🔍 Verifying dataset: {input_dataset}", style="bold cyan"
    )
    if not questionary.confirm(
        "This may take a while depending on the dataset size. Continue?"
    ).ask():
        presenter.display_warning_message("Operation cancelled")
        raise typer.Exit()

    try:
        # Load the dataset to get the entry count
        dataset = dataset_repo.load(input_dataset)
        total_entries = len(dataset.entries)

        # Set up our own verification loop with progress bar
        with presenter.create_progress("Verifying dataset entries...") as progress:
            task = progress.add_task(
                "Verifying dataset entries...", total=total_entries
            )

            verified_count = 0
            skipped_count = 0

            # Process all entries
            for i, entry in enumerate(dataset.entries):
                progress.update(
                    task, description=f"Verifying entry {i + 1}/{total_entries}"
                )

                if entry.input and entry.output:
                    # Verify this entry
                    results = fact_checker.verify_key_points(entry.input, entry.output)
                    entry.verification_results = results
                    verified_count += 1
                else:
                    skipped_count += 1

                # Save intermediate results every 5 entries
                if (i + 1) % 5 == 0 or i == total_entries - 1:
                    dataset_repo.save(
                        dataset,
                        output_dataset
                        or input_dataset.with_stem(f"{input_dataset.stem}_verified"),
                        backup=(i == 0 and backup),
                    )

                progress.advance(task)

        # Final save
        output_path = output_dataset or input_dataset.with_stem(
            f"{input_dataset.stem}_verified"
        )
        dataset_repo.save(dataset, output_path, backup=False)  # Already backed up above

        # Show completion message
        presenter.display_success_message(f"Verification complete!")
        presenter.console.print(
            f"  - Verified dataset saved to: {output_path}", style="cyan"
        )

        # Show verification statistics
        presenter.display_verification_stats(dataset.get_stats())

    except Exception as e:
        presenter.display_error_message(f"Error verifying dataset: {str(e)}")
        raise typer.Exit(1)


@app.command()
def validate(
    dataset_path: Path = typer.Argument(
        "./dataset.json", help="Path to the dataset file"
    ),
):
    """Validate the dataset file format."""
    try:
        # Set up components
        dataset_repo = JsonDatasetRepository()

        # Load the dataset
        dataset = dataset_repo.load(dataset_path)

        # Count valid entries (those with all required fields)
        valid_entries = 0
        invalid_entries = 0

        for entry in dataset.entries:
            if entry.input and entry.output:
                valid_entries += 1
            else:
                invalid_entries += 1

        # Show results
        stats = {
            "Total entries": len(dataset.entries),
            "Valid entries": valid_entries,
            "Invalid entries": invalid_entries,
        }

        presenter.display_dataset_stats(stats)

        if invalid_entries == 0:
            presenter.display_success_message("Dataset is valid!")
        else:
            presenter.display_warning_message("Dataset contains invalid entries!")

    except Exception as e:
        presenter.display_error_message(f"Error validating dataset: {str(e)}")


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
    try:
        if not input_path.exists():
            presenter.display_error_message(f"Input file {input_path} does not exist")
            raise typer.Exit(1)

        presenter.console.print(
            f"\n🔄 Converting dataset to ShareGPT format...", style="bold cyan"
        )

        # Set up components
        dataset_repo = JsonDatasetRepository()

        # Load the dataset
        dataset = dataset_repo.load(input_path)

        # Convert to ShareGPT format
        sharegpt_data = dataset.convert_to_sharegpt_format()

        # Save the converted dataset
        with open(output_path, "w", encoding="utf-8") as f:
            import json

            json.dump(sharegpt_data, f, ensure_ascii=False, indent=2)

        # Show success message
        presenter.display_success_message(
            "Successfully converted dataset to ShareGPT format!"
        )
        presenter.console.print(f"   Output saved to: {output_path}", style="green")

        # Show file size
        if output_path.exists():
            size_kb = output_path.stat().st_size / 1024
            presenter.console.print(f"   File size: {size_kb:.2f} KB", style="green")

    except Exception as e:
        presenter.display_error_message(f"Error converting dataset: {str(e)}")
        raise typer.Exit(1)


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
            dataset_path = questionary.path(
                "Enter dataset path:", default="./dataset.json"
            ).ask()
            backup = questionary.confirm(
                "Create backup before processing?", default=True
            ).ask()
            verify_points = questionary.confirm(
                "Verify key points against original content?", default=False
            ).ask()
            process(
                dataset_path=Path(dataset_path),
                backup=backup,
                verify_points=verify_points,
            )
        elif choice == "🧹 Clean Existing Dataset":
            dataset_path = questionary.path(
                "Enter dataset path:", default="./dataset.json"
            ).ask()
            backup = questionary.confirm(
                "Create backup before cleaning?", default=True
            ).ask()
            clean(Path(dataset_path), backup)
        elif choice == "📊 View Dataset Info":
            dataset_path = questionary.path(
                "Enter dataset path:", default="./dataset.json"
            ).ask()
            validate(Path(dataset_path))
        elif choice == "✅ Validate Dataset":
            dataset_path = questionary.path(
                "Enter dataset path:", default="./dataset.json"
            ).ask()
            validate(Path(dataset_path))
        elif choice == "🔍 Verify Dataset Key Points":
            input_dataset = questionary.path(
                "Enter input dataset path:", default="./dataset.json"
            ).ask()
            output_dataset = questionary.path(
                "Enter output dataset path (leave empty for default):", default=""
            ).ask()
            backup = questionary.confirm(
                "Create backup before processing?", default=True
            ).ask()
            # Handle empty output path
            output_path = Path(output_dataset) if output_dataset else None
            verify(
                input_dataset=Path(input_dataset),
                output_dataset=output_path,
                backup=backup,
            )
        elif choice == "🔄 Convert to ShareGPT Format":
            input_path = questionary.path(
                "Enter input dataset path:", default="./dataset.json"
            ).ask()
            output_path = questionary.path(
                "Enter output path:", default="./dataset_sharegpt.json"
            ).ask()
            convert(input_path=Path(input_path), output_path=Path(output_path))
        elif choice == "🔑 Manage API Key":
            manage_api_key()
        else:
            presenter.console.print("\n👋 Goodbye!", style="bold cyan")
            sys.exit(0)

        # Pause before showing menu again
        input("\nPress Enter to continue...")


def run():
    """Run the CLI application."""
    if len(sys.argv) > 1:
        app()
    else:
        main_menu()


if __name__ == "__main__":
    run()
