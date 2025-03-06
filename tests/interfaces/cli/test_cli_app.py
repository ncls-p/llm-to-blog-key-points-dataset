"""
Tests for the CLI application.
"""

import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import typer
from typer.testing import CliRunner

from llm_key_points.interfaces.cli.cli_app import app, validate_api_key, validate_url

runner = CliRunner()


@pytest.fixture(autouse=True)
def setup_env():
    """Set up environment variables for all tests."""
    with patch.dict(
        os.environ,
        {
            "OPENAI_COMPATIBLE_API_KEY": "test-api-key",
            "OPENAI_COMPATIBLE_MODEL": "gpt-3.5-turbo",
            "OLLAMA_API_URL": "http://localhost:11434",
        },
    ):
        yield


def test_validate_api_key():
    """Test API key validation."""
    assert validate_api_key("sk-1234567890abcdefghijklmn") is True
    assert validate_api_key("short-key") is False
    assert validate_api_key("") is False


def test_validate_url():
    """Test URL validation."""
    assert validate_url("https://example.com") is True
    assert validate_url("http://example.com") is True
    assert validate_url("ftp://example.com") is False
    assert validate_url("not-a-url") is False


@patch("llm_key_points.interfaces.cli.cli_app.BeautifulSoupWebRepository")
@patch("llm_key_points.interfaces.cli.cli_app.JsonDatasetRepository")
@patch("llm_key_points.interfaces.cli.cli_app.OpenAICompatibleExtractor")
@patch("llm_key_points.interfaces.cli.cli_app.RichPresenter")
@patch("llm_key_points.interfaces.cli.cli_app.ExtractKeyPointsUseCase")
@patch("llm_key_points.interfaces.cli.cli_app.get_api_key")
def test_process_command(
    mock_get_api_key,
    mock_use_case_class,
    mock_presenter_class,
    mock_extractor_class,
    mock_dataset_repo_class,
    mock_web_repo_class,
):
    """Test the process command."""
    # Mock API key
    mock_get_api_key.return_value = "test-api-key"

    # Set up mocks
    mock_web_repo = Mock()
    mock_web_repo.extract_content.return_value = "Test content"
    mock_web_repo_class.return_value = mock_web_repo

    mock_dataset = Mock()
    mock_dataset_repo = Mock()
    mock_dataset_repo.load.return_value = mock_dataset
    mock_dataset_repo_class.return_value = mock_dataset_repo

    mock_extractor = Mock()
    mock_extractor.extract_key_points.return_value = "* Test point"
    mock_extractor_class.return_value = mock_extractor

    # Mock the presenter with proper context manager for progress
    mock_progress = Mock()
    mock_progress_context = Mock()
    mock_progress_context.__enter__ = Mock(return_value=mock_progress)
    mock_progress_context.__exit__ = Mock(return_value=None)
    mock_presenter = Mock()
    mock_presenter.create_progress.return_value = mock_progress_context
    mock_presenter_class.return_value = mock_presenter

    # Mock the use case
    mock_use_case = Mock()
    mock_use_case.process_urls.return_value = mock_dataset
    # Set up extract_from_url to return a mock entry
    mock_entry = Mock()
    mock_use_case.extract_from_url.return_value = mock_entry
    mock_use_case_class.return_value = mock_use_case

    # Create a temporary dataset file
    with runner.isolated_filesystem():
        with open("dataset.json", "w") as f:
            f.write("[]")

        # Mock questionary to avoid interactive prompts
        with (
            patch("questionary.text") as mock_text,
            patch("questionary.confirm") as mock_confirm,
        ):
            mock_text.return_value.ask.return_value = "https://example.com"
            mock_confirm.return_value.ask.side_effect = [
                False,
                True,
            ]  # No more URLs, confirm processing

            # Test the command
            result = runner.invoke(
                app,
                ["process", "--dataset", "dataset.json"],
            )

        # Check that the command executed without errors
        if result.exit_code != 0:
            print(f"Command output: {result.stdout}")

        assert result.exit_code == 0
        # Check that extract_from_url was called
        mock_use_case.extract_from_url.assert_called_once()
        # Check that save was called at least once
        assert mock_dataset_repo.save.call_count >= 1


@patch("llm_key_points.interfaces.cli.cli_app.JsonDatasetRepository")
@patch("llm_key_points.interfaces.cli.cli_app.OpenAICompatibleExtractor")
@patch("llm_key_points.interfaces.cli.cli_app.get_api_key")
def test_clean_command(mock_get_api_key, mock_extractor_class, mock_dataset_repo_class):
    """Test the clean command."""
    # Mock API key
    mock_get_api_key.return_value = "test-api-key"

    # Set up mocks
    mock_dataset = Mock()
    # Create mock entries with references to be cleaned
    mock_entries = [
        Mock(spec=["input", "output"], input="Test content", output="* Point [1]")
    ]
    mock_dataset.entries = mock_entries

    # Mock the extractor
    mock_extractor = Mock()
    mock_extractor.clean_references.return_value = "* Point"
    mock_extractor_class.return_value = mock_extractor

    mock_dataset_repo = Mock()
    mock_dataset_repo.load.return_value = mock_dataset
    mock_dataset_repo_class.return_value = mock_dataset_repo

    # Create a temporary dataset file
    with runner.isolated_filesystem():
        with open("dataset.json", "w") as f:
            f.write("[]")

        # Mock presenter to avoid progress bar issues
        with patch(
            "llm_key_points.interfaces.cli.cli_app.RichPresenter"
        ) as mock_presenter_class:
            # Mock the presenter with proper context manager for progress
            mock_progress = Mock()
            mock_progress_context = Mock()
            mock_progress_context.__enter__ = Mock(return_value=mock_progress)
            mock_progress_context.__exit__ = Mock(return_value=None)
            mock_presenter = Mock()
            mock_presenter.create_progress.return_value = mock_progress_context
            mock_presenter_class.return_value = mock_presenter

            # Test the command
            result = runner.invoke(app, ["clean", "dataset.json"])

        # Check that the command executed without errors
        if result.exit_code != 0:
            print(f"Command output: {result.stdout}")

        assert result.exit_code == 0
        # Verify that save was called
        assert mock_dataset_repo.save.call_count >= 1


@patch("llm_key_points.interfaces.cli.cli_app.JsonDatasetRepository")
def test_validate_command(mock_dataset_repo_class):
    """Test the validate command."""
    # Set up mocks
    mock_dataset = Mock()
    mock_dataset.entries = [
        Mock(input="Test 1", output="Point 1"),
        Mock(input="Test 2", output=None),  # Invalid entry
    ]
    mock_dataset_repo = Mock()
    mock_dataset_repo.load.return_value = mock_dataset
    mock_dataset_repo_class.return_value = mock_dataset_repo

    # Create a temporary dataset file
    with runner.isolated_filesystem():
        with open("dataset.json", "w") as f:
            f.write("[]")

        # Test the command
        result = runner.invoke(app, ["validate", "dataset.json"])

    assert result.exit_code == 0
    assert "Dataset contains invalid entries!" in result.stdout


@patch("llm_key_points.interfaces.cli.cli_app.JsonDatasetRepository")
def test_convert_command(mock_dataset_repo_class):
    """Test the convert command."""
    # Set up mocks
    mock_dataset = Mock()
    mock_dataset.convert_to_sharegpt_format.return_value = [
        {"conversations": [{"from": "human", "value": "Test"}]}
    ]
    mock_dataset_repo = Mock()
    mock_dataset_repo.load.return_value = mock_dataset
    mock_dataset_repo_class.return_value = mock_dataset_repo

    # Create a temporary dataset file
    with runner.isolated_filesystem():
        with open("input.json", "w") as f:
            f.write("[]")

        # Test the command
        result = runner.invoke(app, ["convert", "input.json", "output.json"])

    assert result.exit_code == 0
    mock_dataset.convert_to_sharegpt_format.assert_called_once()


@patch("llm_key_points.interfaces.cli.cli_app.JsonDatasetRepository")
@patch("llm_key_points.interfaces.cli.cli_app.OllamaFactChecker")
@patch("llm_key_points.interfaces.cli.cli_app.RichPresenter")
@patch("llm_key_points.interfaces.cli.cli_app.VerifyDatasetUseCase")
@patch("requests.get")
@patch("llm_key_points.interfaces.cli.cli_app.get_api_key")
def test_verify_command(
    mock_get_api_key,
    mock_requests_get,
    mock_use_case_class,
    mock_presenter_class,
    mock_fact_checker_class,
    mock_dataset_repo_class,
):
    """Test the verify command."""
    # Mock API key
    mock_get_api_key.return_value = "test-api-key"

    # Set up mocks
    mock_dataset = Mock()
    mock_dataset.entries = [Mock(input="Test", output="* Point")]
    mock_dataset.get_stats = Mock(
        return_value={"accurate": 1, "inaccurate": 0, "uncertain": 0}
    )

    mock_dataset_repo = Mock()
    mock_dataset_repo.load.return_value = mock_dataset
    mock_dataset_repo_class.return_value = mock_dataset_repo

    mock_fact_checker = Mock()
    verification_results = Mock()
    verification_results.accurate = [{"point": "Point", "verification": {}}]
    mock_fact_checker.verify_key_points.return_value = verification_results
    mock_fact_checker_class.return_value = mock_fact_checker

    # Mock the use case
    mock_use_case = Mock()
    mock_use_case.verify_dataset.return_value = mock_dataset
    mock_use_case_class.return_value = mock_use_case

    # Mock the Ollama API health check
    mock_requests_get.return_value = Mock(status_code=200)

    # Mock the presenter with proper context manager for progress
    mock_progress = Mock()
    mock_progress_context = Mock()
    mock_progress_context.__enter__ = Mock(return_value=mock_progress)
    mock_progress_context.__exit__ = Mock(return_value=None)
    mock_presenter = Mock()
    mock_presenter.create_progress.return_value = mock_progress_context
    mock_presenter_class.return_value = mock_presenter

    # Create a temporary dataset file
    with runner.isolated_filesystem():
        with open("input.json", "w") as f:
            f.write("[]")

        with open("verified.json", "w") as f:
            f.write("[]")

        # Mock questionary to avoid interactive prompts
        with patch("questionary.confirm") as mock_confirm:
            mock_confirm.return_value.ask.return_value = True

            # Test the command with correct arguments
            result = runner.invoke(
                app,
                ["verify", "input.json", "verified.json"],
            )

        # Check that the command executed without errors
        if result.exit_code != 0:
            print(f"Command output: {result.stdout}")

        assert result.exit_code == 0
        # Check that the fact checker was used
        assert mock_fact_checker.verify_key_points.call_count >= 1
        # Check that save was called at least once
        assert mock_dataset_repo.save.call_count >= 1
