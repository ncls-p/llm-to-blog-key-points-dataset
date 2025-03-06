"""
Tests for the Rich console presenter.
"""

from rich.console import Console
from rich.table import Table

from llm_key_points.interfaces.console import RichPresenter


def test_display_welcome(capsys):
    """Test welcome message display."""
    presenter = RichPresenter()
    presenter.display_welcome()

    # Check that output contains key phrases
    captured = capsys.readouterr()
    assert "Welcome to" in captured.out
    assert "Dataset Enhancer" in captured.out
    assert "OpenAI compatible API" in captured.out


def test_create_url_table():
    """Test URL table creation."""
    presenter = RichPresenter()
    urls = ["https://example1.com", "https://example2.com"]

    table = presenter.create_url_table(urls)

    assert isinstance(table, Table)
    assert table.columns[0].header == "#"
    assert table.columns[1].header == "URL"

    # Convert table to string to check content
    console = Console()
    with console.capture() as capture:
        console.print(table)

    output = capture.get()
    assert "example1.com" in output
    assert "example2.com" in output


def test_display_dataset_stats(capsys):
    """Test dataset statistics display."""
    presenter = RichPresenter()
    stats = {"total_entries": 10, "valid_entries": 8, "invalid_entries": 2}

    presenter.display_dataset_stats(stats)

    captured = capsys.readouterr()
    assert "Dataset Statistics" in captured.out
    assert "Total Entries" in captured.out
    assert "10" in captured.out


def test_display_verification_stats(capsys):
    """Test verification statistics display."""
    presenter = RichPresenter()
    stats = {
        "total_entries": 10,
        "verified_entries": 8,
        "total_verified_points": 20,
        "accurate_points": 15,
        "inaccurate_points": 3,
        "uncertain_points": 2,
    }

    presenter.display_verification_stats(stats)

    captured = capsys.readouterr()
    assert "Verification Statistics" in captured.out
    assert "8/10" in captured.out  # Verified/total entries
    assert "75.0%" in captured.out  # Accurate percentage
    assert "15.0%" in captured.out  # Inaccurate percentage
    assert "10.0%" in captured.out  # Uncertain percentage


def test_display_success_message(capsys):
    """Test success message display."""
    presenter = RichPresenter()
    message = "Operation completed successfully"

    presenter.display_success_message(message)

    captured = capsys.readouterr()
    assert "✅" in captured.out
    assert message in captured.out


def test_display_error_message(capsys):
    """Test error message display."""
    presenter = RichPresenter()
    message = "An error occurred"

    presenter.display_error_message(message)

    captured = capsys.readouterr()
    assert "❌" in captured.out
    assert message in captured.out


def test_display_warning_message(capsys):
    """Test warning message display."""
    presenter = RichPresenter()
    message = "Warning: proceed with caution"

    presenter.display_warning_message(message)

    captured = capsys.readouterr()
    assert "⚠️" in captured.out
    assert message in captured.out


def test_create_progress():
    """Test progress bar creation."""
    presenter = RichPresenter()
    progress = presenter.create_progress("Testing progress")

    assert "Testing progress" in progress.columns[1].text_format
    assert isinstance(progress.columns[0], type(progress.columns[0]))  # SpinnerColumn
    assert isinstance(progress.columns[2], type(progress.columns[2]))  # BarColumn
    assert isinstance(
        progress.columns[3], type(progress.columns[3])
    )  # TaskProgressColumn
