"""
Command implementations for the CLI interface.
"""

from pathlib import Path
from typing import List, Optional

import typer

from ...adapters.api.openai_compatible_extractor import OpenAICompatibleExtractor
from ...adapters.repositories.json_dataset_repository import JsonDatasetRepository
from ...adapters.repositories.web_content_repository import BeautifulSoupWebRepository
from ...adapters.verification.ollama_fact_checker import OllamaFactChecker
from ...core.use_cases.extract_key_points import ExtractKeyPointsUseCase
from ..console.rich_presenter import RichPresenter

# Initialize shared components
presenter = RichPresenter()


def process_urls(
    urls: List[str], dataset_path: Path, backup: bool, verify_points: bool, api_key: str
):
    """Process URLs and enhance dataset."""
    # Display URLs to process
    presenter.console.print("\n📋 URLs to process:", style="bold cyan")
    presenter.console.print(presenter.create_url_table(urls))

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

    # Process URLs
    with presenter.create_progress("Processing URLs...") as progress:
        task = progress.add_task("Processing URLs...", total=len(urls))

        for i, url in enumerate(urls):
            progress_message = f"Processing: {url}"
            if verify_points:
                progress_message += " (with verification)"

            progress.update(task, description=progress_message)

            try:
                entry = use_case.extract_from_url(url, verify_points)
                if entry:
                    # Load current dataset
                    dataset = dataset_repo.load(dataset_path)
                    dataset.add_entry(entry)
                    dataset_repo.save(dataset, dataset_path, backup=(i == 0 and backup))

                progress.advance(task)
            except Exception as e:
                presenter.display_error_message(f"Error processing {url}: {str(e)}")

    presenter.display_success_message(
        f"Processing complete! Dataset saved to {dataset_path}"
    )


def clean_dataset(dataset_path: Path, backup: bool, api_key: str):
    """Clean references from existing dataset entries."""
    try:
        dataset_repo = JsonDatasetRepository()
        dataset = dataset_repo.load(dataset_path)
        extractor = OpenAICompatibleExtractor(api_key)

        with presenter.create_progress("Cleaning dataset...") as progress:
            task = progress.add_task("Cleaning dataset...", total=len(dataset.entries))

            cleaned_count = 0
            for entry in dataset.entries:
                if entry.output:
                    entry.output = extractor.clean_references(entry.output)
                    cleaned_count += 1
                progress.advance(task)

        dataset_repo.save(dataset, dataset_path, backup)

        presenter.display_success_message("Dataset cleaning complete!")
        stats = {
            "Total entries": len(dataset.entries),
            "Cleaned entries": cleaned_count,
        }
        presenter.display_dataset_stats(stats)

    except Exception as e:
        presenter.display_error_message(f"Error cleaning dataset: {str(e)}")
        raise typer.Exit(1)


def validate_dataset(dataset_path: Path):
    """Validate the dataset file format."""
    try:
        dataset_repo = JsonDatasetRepository()
        dataset = dataset_repo.load(dataset_path)

        valid_entries = sum(
            1 for entry in dataset.entries if entry.input and entry.output
        )
        invalid_entries = len(dataset.entries) - valid_entries

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


def verify_dataset(input_dataset: Path, output_dataset: Optional[Path], backup: bool):
    """Verify key points in dataset."""
    try:
        dataset_repo = JsonDatasetRepository()
        fact_checker = OllamaFactChecker()
        dataset = dataset_repo.load(input_dataset)
        final_output_path = output_dataset or input_dataset.with_stem(
            f"{input_dataset.stem}_verified"
        )

        with presenter.create_progress("Verifying dataset entries...") as progress:
            task = progress.add_task(
                "Verifying dataset entries...", total=len(dataset.entries)
            )

            for i, entry in enumerate(dataset.entries):
                progress.update(
                    task, description=f"Verifying entry {i + 1}/{len(dataset.entries)}"
                )

                if entry.input and entry.output:
                    results = fact_checker.verify_key_points(entry.input, entry.output)
                    entry.verification_results = results

                if (i + 1) % 5 == 0 or i == len(dataset.entries) - 1:
                    dataset_repo.save(
                        dataset, final_output_path, backup=(i == 0 and backup)
                    )

                progress.advance(task)

        presenter.display_success_message("Verification complete!")
        presenter.console.print(
            f"  - Verified dataset saved to: {final_output_path}", style="cyan"
        )
        presenter.display_verification_stats(dataset.get_stats())

    except Exception as e:
        presenter.display_error_message(f"Error verifying dataset: {str(e)}")
        raise typer.Exit(1)


def convert_dataset(input_path: Path, output_path: Path):
    """Convert dataset to ShareGPT format."""
    try:
        if not input_path.exists():
            presenter.display_error_message(f"Input file {input_path} does not exist")
            raise typer.Exit(1)

        presenter.console.print(
            "\n🔄 Converting dataset to ShareGPT format...", style="bold cyan"
        )

        dataset_repo = JsonDatasetRepository()
        dataset = dataset_repo.load(input_path)
        sharegpt_data = dataset.convert_to_sharegpt_format()

        with open(output_path, "w", encoding="utf-8") as f:
            import json

            json.dump(sharegpt_data, f, ensure_ascii=False, indent=2)

        presenter.display_success_message(
            "Successfully converted dataset to ShareGPT format!"
        )
        presenter.console.print(f"   Output saved to: {output_path}", style="green")

        if output_path.exists():
            size_kb = output_path.stat().st_size / 1024
            presenter.console.print(f"   File size: {size_kb:.2f} KB", style="green")

    except Exception as e:
        presenter.display_error_message(f"Error converting dataset: {str(e)}")
        raise typer.Exit(1)
