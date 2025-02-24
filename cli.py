import typer
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.table import Table
from rich.text import Text
from rich import print as rprint
from pathlib import Path
from typing import List, Optional
import json
from enhance_dataset import PerplexityEnhancer
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

app = typer.Typer(help="🚀 Enhance your dataset with Perplexity AI")
console = Console()


def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    return api_key.startswith("pplx-") and len(api_key) > 20


def get_api_key() -> str:
    """Get API key from environment or user input."""
    api_key = os.getenv("PERPLEXITY_API_KEY")

    if api_key and validate_api_key(api_key):
        return api_key

    console.print("\n⚠️  API key not found in environment or invalid.", style="yellow")
    api_key = questionary.text(
        "Please enter your Perplexity API key:",
        validate=lambda text: validate_api_key(text) or "Invalid API key format",
    ).ask()

    # Ask if user wants to save to .env
    if questionary.confirm("Would you like to save this API key to .env file?").ask():
        with open(".env", "w") as f:
            f.write(f"PERPLEXITY_API_KEY={api_key}")
        console.print("✅ API key saved to .env file", style="green")

    return api_key


def display_welcome():
    """Display welcome message."""
    welcome_text = Text()
    welcome_text.append("🎉 Welcome to ", style="bold cyan")
    welcome_text.append("Dataset Enhancer", style="bold magenta")
    welcome_text.append(" powered by ", style="bold cyan")
    welcome_text.append("Perplexity AI", style="bold green")

    panel = Panel(
        welcome_text,
        subtitle="[cyan]Created with ❤️  by Ncls-p[/cyan]",
        border_style="bright_blue",
    )
    console.print(panel)


def create_url_table(urls: List[str]) -> Table:
    """Create a table to display URLs."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim")
    table.add_column("URL", style="cyan")

    for idx, url in enumerate(urls, 1):
        table.add_row(str(idx), url)

    return table


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
                console.print("⚠️  Please enter at least one URL", style="yellow")
                continue
            break

        urls.append(url)
        console.print(f"✅ Added URL: {url}", style="green")

        if len(urls) >= 1 and not questionary.confirm("Add another URL?").ask():
            break

    return urls


def show_dataset_info(dataset_path: Path):
    """Show information about the dataset."""
    try:
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        stats_table = Table(show_header=True, header_style="bold magenta")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")

        stats_table.add_row("Total entries", str(len(dataset)))
        stats_table.add_row(
            "File size", f"{os.path.getsize(dataset_path) / 1024:.2f} KB"
        )
        stats_table.add_row("Last modified", str(Path(dataset_path).stat().st_mtime))

        console.print("\n📊 Dataset Information:", style="bold cyan")
        console.print(stats_table)
    except Exception as e:
        console.print(f"\n⚠️  Could not load dataset: {e}", style="yellow")


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
            api_key = os.getenv("PERPLEXITY_API_KEY")
            if api_key:
                console.print(
                    f"\n🔑 Current API key: {api_key[:8]}...{api_key[-4:]}",
                    style="green",
                )
            else:
                console.print("\n⚠️  No API key found", style="yellow")

        elif choice == "Update API key":
            api_key = get_api_key()
            console.print("\n✅ API key updated", style="green")

        elif choice == "Remove API key":
            if os.path.exists(".env"):
                os.remove(".env")
                console.print("\n✅ API key removed", style="green")
            else:
                console.print("\n⚠️  No .env file found", style="yellow")

        else:
            break


def clean_existing_dataset(dataset_path: Path, backup: bool = True):
    """Clean references from existing dataset entries."""
    try:
        # Load dataset
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        if backup:
            backup_path = dataset_path.with_suffix(".json.backup")
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)
            console.print(f"\n✅ Created backup at: {backup_path}", style="green")

        # Initialize enhancer for cleaning
        api_key = get_api_key()
        enhancer = PerplexityEnhancer(api_key)

        # Clean each entry
        total_entries = len(dataset)
        cleaned_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Cleaning dataset...", total=total_entries)

            for entry in dataset:
                if "output" in entry:
                    entry["output"] = enhancer.clean_references(entry["output"])
                    cleaned_count += 1
                progress.advance(task)

        # Save cleaned dataset
        with open(dataset_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        # Show results
        console.print("\n✨ Dataset cleaning complete!", style="bold green")

        stats_table = Table(show_header=True, header_style="bold magenta")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")

        stats_table.add_row("Total entries", str(total_entries))
        stats_table.add_row("Cleaned entries", str(cleaned_count))

        console.print("\n📊 Cleaning Statistics:", style="bold cyan")
        console.print(stats_table)

    except Exception as e:
        console.print(f"\n❌ Error cleaning dataset: {e}", style="bold red")


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
    clean_existing_dataset(dataset_path, backup)


def main_menu():
    """Display and handle main menu."""
    while True:
        display_welcome()

        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "🌐 Process URLs",
                "🧹 Clean Existing Dataset",
                "📊 View Dataset Info",
                "✅ Validate Dataset",
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
            process(dataset_path=Path(dataset_path), backup=backup)

        elif choice == "🧹 Clean Existing Dataset":
            dataset_path = questionary.path(
                "Enter dataset path:", default="./dataset.json"
            ).ask()
            backup = questionary.confirm(
                "Create backup before cleaning?", default=True
            ).ask()
            clean_existing_dataset(Path(dataset_path), backup)

        elif choice == "📊 View Dataset Info":
            dataset_path = questionary.path(
                "Enter dataset path:", default="./dataset.json"
            ).ask()
            show_dataset_info(Path(dataset_path))

        elif choice == "✅ Validate Dataset":
            dataset_path = questionary.path(
                "Enter dataset path:", default="./dataset.json"
            ).ask()
            validate(Path(dataset_path))

        elif choice == "🔑 Manage API Key":
            manage_api_key()

        else:
            console.print("\n👋 Goodbye!", style="bold cyan")
            sys.exit(0)

        # Pause before showing menu again
        input("\nPress Enter to continue...")


@app.command()
def process(
    dataset_path: Path = typer.Option(
        "./dataset.json", "--dataset", "-d", help="Path to the dataset file"
    ),
    backup: bool = typer.Option(
        True, "--backup/--no-backup", help="Create backup before processing"
    ),
):
    """Process URLs and enhance your dataset with Perplexity AI."""
    # Get URLs interactively
    urls = get_urls()

    # Display URLs to process
    console.print("\n📋 URLs to process:", style="bold cyan")
    console.print(create_url_table(urls))

    # Confirm processing
    if not questionary.confirm("Process these URLs?").ask():
        console.print("\n❌ Operation cancelled", style="yellow")
        raise typer.Exit()

    # Get API key
    api_key = get_api_key()

    # Initialize enhancer
    enhancer = PerplexityEnhancer(api_key)

    # Process URLs with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing URLs...", total=len(urls))

        def progress_callback(url: str):
            progress.advance(task)
            console.print(f"✅ Processed: {url}", style="green")

        # Add progress callback to enhancer
        original_update = enhancer.update_dataset

        def update_with_progress(*args, **kwargs):
            result = original_update(*args, **kwargs)
            progress_callback(args[1] if isinstance(args[1], str) else "batch")
            return result

        enhancer.update_dataset = update_with_progress

        # Process URLs
        enhancer.update_dataset(dataset_path, urls, backup=backup)

    # Show completion message
    console.print("\n🎉 Processing complete!", style="bold green")

    # Show dataset statistics
    show_dataset_info(dataset_path)


@app.command()
def validate(
    dataset_path: Path = typer.Argument(
        "./dataset.json", help="Path to the dataset file"
    ),
):
    """Validate the dataset file format."""
    try:
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        valid_entries = 0
        invalid_entries = 0

        for entry in dataset:
            if all(k in entry for k in ["instruction", "input", "output"]):
                valid_entries += 1
            else:
                invalid_entries += 1

        stats_table = Table(show_header=True, header_style="bold magenta")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")

        stats_table.add_row("Total entries", str(len(dataset)))
        stats_table.add_row("Valid entries", str(valid_entries))
        stats_table.add_row("Invalid entries", str(invalid_entries))

        console.print("\n📊 Validation Results:", style="bold cyan")
        console.print(stats_table)

        if invalid_entries == 0:
            console.print("\n✅ Dataset is valid!", style="bold green")
        else:
            console.print("\n⚠️  Dataset contains invalid entries!", style="bold yellow")

    except Exception as e:
        console.print(f"\n❌ Error validating dataset: {e}", style="bold red")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        app()
    else:
        main_menu()
