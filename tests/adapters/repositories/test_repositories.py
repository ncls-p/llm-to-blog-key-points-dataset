"""
Tests for the repository adapters.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from llm_key_points.adapters.repositories import (
    BeautifulSoupWebRepository,
    JsonDatasetRepository,
)
from llm_key_points.core.entities.dataset import Dataset, DatasetEntry


def test_json_dataset_repository_load_nonexistent():
    """Test loading from a nonexistent file creates empty dataset."""
    repo = JsonDatasetRepository()
    dataset = repo.load(Path("nonexistent.json"))
    assert isinstance(dataset, Dataset)
    assert len(dataset.entries) == 0


def test_json_dataset_repository_save_and_load():
    """Test saving and loading dataset through repository."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        file_path = Path(tmp.name)

    try:
        # Create and save dataset
        dataset = Dataset()
        entry = DatasetEntry(input="Test", output="* Point")
        dataset.add_entry(entry)

        repo = JsonDatasetRepository()
        repo.save(dataset, file_path)

        # Load dataset
        loaded_dataset = repo.load(file_path)

        assert len(loaded_dataset.entries) == 1
        assert loaded_dataset.entries[0].input == "Test"
        assert loaded_dataset.entries[0].output == "* Point"

    finally:
        # Cleanup
        file_path.unlink()


def test_json_dataset_repository_backup():
    """Test backup functionality of repository."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        file_path = Path(tmp.name)

    try:
        # Create initial dataset
        dataset = Dataset()
        entry = DatasetEntry(input="Original", output="* Point")
        dataset.add_entry(entry)

        repo = JsonDatasetRepository()
        repo.save(dataset, file_path)

        # Create modified dataset and save with backup
        modified_dataset = Dataset()
        entry = DatasetEntry(input="Modified", output="* New Point")
        modified_dataset.add_entry(entry)

        repo.save(modified_dataset, file_path, backup=True)

        # Check backup exists and contains original data
        backup_path = file_path.with_suffix(".json.backup")
        assert backup_path.exists()

        with open(backup_path, "r") as f:
            backup_data = json.load(f)
            assert len(backup_data) == 1
            assert backup_data[0]["input"] == "Original"

    finally:
        # Cleanup
        file_path.unlink()
        backup_path = file_path.with_suffix(".json.backup")
        if backup_path.exists():
            backup_path.unlink()


def test_web_repository_extract_content_success():
    """Test successful web content extraction."""
    html_content = """
    <html>
        <body>
            <script>var x = 1;</script>
            <nav>Navigation</nav>
            <div>Article content</div>
            <footer>Footer</footer>
        </body>
    </html>
    """

    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = html_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        repo = BeautifulSoupWebRepository()
        content = repo.extract_content("https://example.com")

        assert content is not None
        assert "Article content" in content
        assert "Navigation" not in content
        assert "Footer" not in content
        assert "var x = 1" not in content


def test_web_repository_extract_content_failure():
    """Test web content extraction failure."""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("Failed to fetch")

        repo = BeautifulSoupWebRepository()
        content = repo.extract_content("https://example.com")

        assert content is None


def test_web_repository_request_timeout():
    """Test web repository handles timeouts."""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.Timeout("Request timed out")

        repo = BeautifulSoupWebRepository(request_timeout=1)
        content = repo.extract_content("https://example.com")

        assert content is None


def test_web_repository_removes_unwanted_elements():
    """Test that web repository removes unwanted HTML elements."""
    html_content = """
    <html>
        <body>
            <script>JavaScript code</script>
            <style>CSS styles</style>
            <nav>Navigation menu</nav>
            <article>
                Important content
                <iframe src="ad.html">Advertisement</iframe>
                More content
            </article>
            <footer>Footer content</footer>
        </body>
    </html>
    """

    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = html_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        repo = BeautifulSoupWebRepository()
        content = repo.extract_content("https://example.com")

        assert content is not None
        assert "Important content" in content
        assert "More content" in content
        assert "JavaScript code" not in content
        assert "CSS styles" not in content
        assert "Navigation menu" not in content
        assert "Advertisement" not in content
        assert "Footer content" not in content
