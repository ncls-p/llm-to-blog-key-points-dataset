import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import re
import requests

import questionary
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table
from rich.text import Text

from enhance_dataset import OpenAICompatibleEnhancer, logger
from convert_to_sharegpt import convert_dataset

# Load environment variables
load_dotenv()

app = typer.Typer(help="🚀 Enhance your dataset with OpenAI compatible API")
console = Console()


def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    # More generic validation that works with various API providers
    return len(api_key) > 20


def get_api_key() -> str:
    """Get API key from environment or user input."""
    api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY")

    if api_key and validate_api_key(api_key):
        return api_key

    console.print("\n⚠️  API key not found in environment or invalid.", style="yellow")
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

        console.print("✅ API key saved to .env file", style="green")

    return api_key


def display_welcome():
    """Display welcome message."""
    welcome_text = Text()
    welcome_text.append("🎉 Welcome to ", style="bold cyan")
    welcome_text.append("Dataset Enhancer", style="bold magenta")
    welcome_text.append(" powered by ", style="bold cyan")
    welcome_text.append("OpenAI compatible API", style="bold green")

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
            api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY")
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
        enhancer = OpenAICompatibleEnhancer(api_key)

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
            validate(dataset_path=Path(dataset_path))

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
            verify_dataset(
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
            convert_to_sharegpt(
                input_path=Path(input_path), output_path=Path(output_path)
            )

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
    console.print("\n📋 URLs to process:", style="bold cyan")
    console.print(create_url_table(urls))

    # Confirm processing
    if not questionary.confirm("Process these URLs?").ask():
        console.print("\n❌ Operation cancelled", style="yellow")
        raise typer.Exit()

    # Get API key
    api_key = get_api_key()

    # Initialize enhancer
    enhancer = OpenAICompatibleEnhancer(api_key)

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
            progress.update(task, advance=1, description=f"Processed: {url}")

        # Process each URL
        for url in urls:
            progress_message = f"Processing: {url}"
            if verify_points:
                progress_message += " (with fact-checking)"
            progress.update(task, description=progress_message)

            try:
                enhancer.update_dataset(
                    dataset_path, url, backup=backup, verify_points=verify_points
                )
                progress_callback(url)
            except Exception as e:
                console.print(f"\n❌ Error processing {url}: {e}", style="red")

    # Show completion message
    console.print(
        f"\n✅ Processing complete! Dataset saved to {dataset_path}", style="green"
    )

    # If verification was enabled, show a summary
    if verify_points:
        console.print("\n🔍 Fact-checking summary:", style="bold cyan")
        console.print(
            "Key points were verified against the original content using Bespoke-MiniCheck.",
            style="cyan",
        )

        # Calculate verification statistics
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                dataset = json.load(f)

            # Calculate total points across all entries
            total_accurate = 0
            total_inaccurate = 0
            total_uncertain = 0
            entries_with_verification = 0

            for entry in dataset:
                if "verification_results" in entry:
                    entries_with_verification += 1
                    total_accurate += len(
                        entry["verification_results"].get("accurate", [])
                    )
                    total_inaccurate += len(
                        entry["verification_results"].get("inaccurate", [])
                    )
                    total_uncertain += len(
                        entry["verification_results"].get("uncertain", [])
                    )

            total_all_points = total_accurate + total_inaccurate + total_uncertain

            if total_all_points > 0:
                console.print("\n📊 Verification Statistics:", style="bold cyan")
                console.print(
                    f"  - Entries with verification: {entries_with_verification}/{len(dataset)}",
                    style="cyan",
                )
                console.print(
                    f"  - Total key points verified: {total_all_points}", style="cyan"
                )
                console.print(
                    f"  - Accurate: {total_accurate} ({total_accurate / total_all_points * 100:.1f}%)",
                    style="green",
                )
                console.print(
                    f"  - Inaccurate: {total_inaccurate} ({total_inaccurate / total_all_points * 100:.1f}%)",
                    style="red",
                )
                console.print(
                    f"  - Uncertain: {total_uncertain} ({total_uncertain / total_all_points * 100:.1f}%)",
                    style="yellow",
                )
        except Exception as e:
            console.print(
                f"Could not calculate detailed statistics: {e}", style="yellow"
            )

        console.print(
            "\nTo view the verification results in the dataset, you can use:",
            style="cyan",
        )
        console.print(
            f"  - python -m json.tool {dataset_path} | grep -A 20 verification_results",
            style="yellow",
        )


@app.command()
def verify_dataset(
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
        console.print(f"\n❌ Dataset file not found: {input_dataset}", style="red")
        raise typer.Exit(1)

    # Get API key
    api_key = get_api_key()

    # Initialize enhancer
    enhancer = OpenAICompatibleEnhancer(api_key)

    # Check if Ollama is available
    try:
        ollama_url = os.getenv(
            "OLLAMA_API_URL", "http://localhost:11434/v1/chat/completions"
        )
        response = requests.get(ollama_url.replace("/v1/chat/completions", "/api/tags"))
        if response.status_code != 200:
            console.print(
                "\n⚠️ Warning: Could not connect to Ollama API. Make sure Ollama is running.",
                style="yellow",
            )
            if not questionary.confirm("Continue anyway?").ask():
                console.print("\n❌ Operation cancelled", style="yellow")
                raise typer.Exit()
    except Exception:
        console.print(
            "\n⚠️ Warning: Could not connect to Ollama API. Make sure Ollama is running.",
            style="yellow",
        )
        if not questionary.confirm("Continue anyway?").ask():
            console.print("\n❌ Operation cancelled", style="yellow")
            raise typer.Exit()

    # Confirm verification
    console.print(f"\n🔍 Verifying dataset: {input_dataset}", style="bold cyan")
    if not questionary.confirm(
        "This may take a while depending on the dataset size. Continue?"
    ).ask():
        console.print("\n❌ Operation cancelled", style="yellow")
        raise typer.Exit()

    # Load dataset to get total entries for progress bar
    try:
        with open(input_dataset, "r", encoding="utf-8") as f:
            dataset = json.load(f)
        total_entries = len(dataset)
    except Exception as e:
        console.print(f"\n❌ Error loading dataset: {e}", style="red")
        raise typer.Exit(1)

    # Create a custom enhancer class that updates the progress bar
    class ProgressEnhancer(OpenAICompatibleEnhancer):
        def verify_existing_dataset(
            self, file_path, output_file_path=None, backup=True
        ):
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"Dataset file not found: {file_path}")
                return

            # Set default output path if not provided
            if output_file_path is None:
                output_file_path = file_path.with_stem(f"{file_path.stem}_verified")
            else:
                output_file_path = Path(output_file_path)

            # Load dataset
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    dataset = json.load(f)

                if backup:
                    backup_path = file_path.with_suffix(".json.backup")
                    with open(backup_path, "w", encoding="utf-8") as f:
                        json.dump(dataset, f, ensure_ascii=False, indent=2)
                    logger.info(f"Created backup at: {backup_path}")
            except json.JSONDecodeError:
                logger.error(f"Error reading {file_path}. Invalid JSON.")
                return
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                return

            # Process each entry with progress bar
            total_entries = len(dataset)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "Verifying dataset entries...", total=total_entries
                )

                verified_count = 0
                skipped_count = 0

                for i, entry in enumerate(dataset):
                    progress.update(
                        task, description=f"Verifying entry {i + 1}/{total_entries}"
                    )

                    content = entry.get("input")
                    key_points = entry.get("output")

                    if not content or not key_points:
                        logger.warning(
                            f"Entry {i + 1} is missing content or key points, skipping"
                        )
                        skipped_count += 1
                        progress.update(task, advance=1)
                        continue

                    verification_results = self.test_key_points(content, key_points)
                    # Ensure entry is treated as a dictionary with string keys and any values
                    entry_dict: Dict[str, Any] = entry
                    entry_dict["verification_results"] = verification_results

                    # Log verification summary
                    accurate_count = len(verification_results["accurate"])
                    inaccurate_count = len(verification_results["inaccurate"])
                    uncertain_count = len(verification_results["uncertain"])
                    total_points = accurate_count + inaccurate_count + uncertain_count

                    if total_points > 0:
                        verified_count += 1
                        logger.info(
                            f"  - Accurate: {accurate_count}/{total_points} ({accurate_count / total_points * 100:.1f}%)"
                        )
                        logger.info(
                            f"  - Inaccurate: {inaccurate_count}/{total_points} ({inaccurate_count / total_points * 100:.1f}%)"
                        )
                        logger.info(
                            f"  - Uncertain: {uncertain_count}/{total_points} ({uncertain_count / total_points * 100:.1f}%)"
                        )
                    else:
                        skipped_count += 1
                        logger.warning(f"  - No points were extracted for verification")

                    # Save intermediate results every 5 entries
                    if (i + 1) % 5 == 0 or i == total_entries - 1:
                        try:
                            with open(output_file_path, "w", encoding="utf-8") as f:
                                json.dump(dataset, f, ensure_ascii=False, indent=2)
                            logger.info(
                                f"Saved intermediate results to {output_file_path}"
                            )
                        except Exception as e:
                            logger.error(f"Error saving intermediate results: {e}")

                    progress.update(task, advance=1)

            # Final save
            try:
                with open(output_file_path, "w", encoding="utf-8") as f:
                    json.dump(dataset, f, ensure_ascii=False, indent=2)
                logger.info(
                    f"Successfully saved verified dataset to: {output_file_path}"
                )

                # Show summary
                console.print(f"\n✅ Verification complete!", style="bold green")
                console.print(f"  - Total entries: {total_entries}", style="cyan")
                console.print(
                    f"  - Successfully verified: {verified_count}", style="green"
                )
                console.print(
                    f"  - Skipped (no points to verify): {skipped_count}",
                    style="yellow",
                )
                console.print(
                    f"  - Verified dataset saved to: {output_file_path}", style="cyan"
                )

                # Add detailed verification statistics
                if verified_count > 0:
                    # Calculate total points across all entries
                    total_accurate = 0
                    total_inaccurate = 0
                    total_uncertain = 0
                    total_all_points = 0

                    for entry in dataset:
                        if "verification_results" in entry:
                            total_accurate += len(
                                entry["verification_results"].get("accurate", [])
                            )
                            total_inaccurate += len(
                                entry["verification_results"].get("inaccurate", [])
                            )
                            total_uncertain += len(
                                entry["verification_results"].get("uncertain", [])
                            )

                    total_all_points = (
                        total_accurate + total_inaccurate + total_uncertain
                    )

                    if total_all_points > 0:
                        console.print(
                            "\n📊 Verification Statistics:", style="bold cyan"
                        )
                        console.print(
                            f"  - Total key points verified: {total_all_points}",
                            style="cyan",
                        )
                        console.print(
                            f"  - Accurate: {total_accurate} ({total_accurate / total_all_points * 100:.1f}%)",
                            style="green",
                        )
                        console.print(
                            f"  - Inaccurate: {total_inaccurate} ({total_inaccurate / total_all_points * 100:.1f}%)",
                            style="red",
                        )
                        console.print(
                            f"  - Uncertain: {total_uncertain} ({total_uncertain / total_all_points * 100:.1f}%)",
                            style="yellow",
                        )

                        console.print(
                            "\n💡 Fact-checking performed using Bespoke-MiniCheck model",
                            style="cyan",
                        )
                        console.print(
                            "   For more details on each entry, examine the verification_results field in the dataset",
                            style="cyan",
                        )

            except Exception as e:
                logger.error(f"Error saving verified dataset: {e}")

    # Verify dataset with progress bar
    try:
        progress_enhancer = ProgressEnhancer(api_key)
        progress_enhancer.verify_existing_dataset(
            input_dataset, output_dataset, backup=backup
        )
    except Exception as e:
        console.print(f"\n❌ Error verifying dataset: {e}", style="red")
        raise typer.Exit(1)


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


@app.command()
def convert_to_sharegpt(
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
            console.print(
                f"\n❌ Input file {input_path} does not exist", style="bold red"
            )
            raise typer.Exit(1)

        console.print(
            f"\n🔄 Converting dataset to ShareGPT format...", style="bold cyan"
        )

        # Create a progress spinner
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Converting...", total=None)

            # Perform the conversion
            convert_dataset(input_path, output_path)

        # Show success message
        console.print(
            f"\n✅ Successfully converted dataset to ShareGPT format!",
            style="bold green",
        )
        console.print(f"   Output saved to: {output_path}", style="green")

        # Show file size
        if output_path.exists():
            size_kb = output_path.stat().st_size / 1024
            console.print(f"   File size: {size_kb:.2f} KB", style="green")

    except Exception as e:
        console.print(f"\n❌ Error converting dataset: {e}", style="bold red")
        raise typer.Exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        app()
    else:
        main_menu()
