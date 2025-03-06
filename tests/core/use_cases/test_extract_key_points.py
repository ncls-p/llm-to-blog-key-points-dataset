"""
Tests for the key points extraction use case.
"""

from pathlib import Path
from unittest.mock import Mock

from llm_key_points.core.entities.dataset import Dataset
from llm_key_points.core.entities.dataset_entry import VerificationResults
from llm_key_points.core.use_cases.extract_key_points import ExtractKeyPointsUseCase


def test_extract_from_url_success():
    """Test successful extraction of key points from a URL."""
    # Create mock dependencies
    web_repo = Mock()
    web_repo.extract_content.return_value = "Test article content"

    dataset_repo = Mock()

    key_points_extractor = Mock()
    key_points_extractor.extract_key_points.return_value = (
        "* Key point 1\n* Key point 2"
    )

    # Create use case
    use_case = ExtractKeyPointsUseCase(
        web_repository=web_repo,
        dataset_repository=dataset_repo,
        key_points_extractor=key_points_extractor,
    )

    # Test extraction
    entry = use_case.extract_from_url("https://example.com")

    assert entry is not None
    assert entry.input == "Test article content"
    assert entry.output == "* Key point 1\n* Key point 2"
    assert entry.verification_results is None

    # Verify calls
    web_repo.extract_content.assert_called_once_with("https://example.com")
    key_points_extractor.extract_key_points.assert_called_once_with(
        "Test article content"
    )


def test_extract_from_url_with_verification():
    """Test key points extraction with verification."""
    # Create mock dependencies
    web_repo = Mock()
    web_repo.extract_content.return_value = "Test article content"

    dataset_repo = Mock()

    key_points_extractor = Mock()
    key_points_extractor.extract_key_points.return_value = (
        "* Key point 1\n* Key point 2"
    )

    fact_checker = Mock()
    verification_results = VerificationResults()
    verification_results.accurate.append({"point": "Key point 1", "verification": {}})
    fact_checker.verify_key_points.return_value = verification_results

    # Create use case
    use_case = ExtractKeyPointsUseCase(
        web_repository=web_repo,
        dataset_repository=dataset_repo,
        key_points_extractor=key_points_extractor,
        fact_checker=fact_checker,
    )

    # Test extraction with verification
    entry = use_case.extract_from_url("https://example.com", verify_points=True)

    assert entry is not None
    assert entry.verification_results is not None
    assert len(entry.verification_results.accurate) == 1

    # Verify calls
    fact_checker.verify_key_points.assert_called_once_with(
        "Test article content", "* Key point 1\n* Key point 2"
    )


def test_extract_from_url_content_failure():
    """Test handling of web content extraction failure."""
    web_repo = Mock()
    web_repo.extract_content.return_value = None  # Extraction failed

    use_case = ExtractKeyPointsUseCase(
        web_repository=web_repo, dataset_repository=Mock(), key_points_extractor=Mock()
    )

    entry = use_case.extract_from_url("https://example.com")
    assert entry is None


def test_extract_from_url_key_points_failure():
    """Test handling of key points extraction failure."""
    web_repo = Mock()
    web_repo.extract_content.return_value = "Test content"

    key_points_extractor = Mock()
    key_points_extractor.extract_key_points.return_value = None  # Extraction failed

    use_case = ExtractKeyPointsUseCase(
        web_repository=web_repo,
        dataset_repository=Mock(),
        key_points_extractor=key_points_extractor,
    )

    entry = use_case.extract_from_url("https://example.com")
    assert entry is None


def test_process_urls():
    """Test processing multiple URLs."""
    # Create mock dependencies
    web_repo = Mock()
    web_repo.extract_content.return_value = "Test content"

    dataset_repo = Mock()
    dataset = Dataset()
    dataset_repo.load.return_value = dataset

    key_points_extractor = Mock()
    key_points_extractor.extract_key_points.return_value = "* Key point"

    # Create use case
    use_case = ExtractKeyPointsUseCase(
        web_repository=web_repo,
        dataset_repository=dataset_repo,
        key_points_extractor=key_points_extractor,
    )

    # Test processing multiple URLs
    urls = ["https://example1.com", "https://example2.com"]
    result = use_case.process_urls(urls, Path("dataset.json"))

    assert len(result.entries) == 2
    assert dataset_repo.save.call_count == 2  # Saved after each URL

    # Verify that backup was only created for first save
    first_save = dataset_repo.save.call_args_list[0]
    second_save = dataset_repo.save.call_args_list[1]
    assert first_save[1]["backup"] is True
    assert second_save[1]["backup"] is False


def test_process_urls_with_verification():
    """Test processing URLs with verification enabled."""
    # Create mock dependencies
    web_repo = Mock()
    web_repo.extract_content.return_value = "Test content"

    dataset_repo = Mock()
    dataset = Dataset()
    dataset_repo.load.return_value = dataset

    key_points_extractor = Mock()
    key_points_extractor.extract_key_points.return_value = "* Key point"

    fact_checker = Mock()
    verification_results = VerificationResults()
    verification_results.accurate.append({"point": "Key point", "verification": {}})
    fact_checker.verify_key_points.return_value = verification_results

    # Create use case
    use_case = ExtractKeyPointsUseCase(
        web_repository=web_repo,
        dataset_repository=dataset_repo,
        key_points_extractor=key_points_extractor,
        fact_checker=fact_checker,
    )

    # Test processing with verification
    urls = ["https://example.com"]
    result = use_case.process_urls(urls, Path("dataset.json"), verify_points=True)

    assert len(result.entries) == 1
    assert result.entries[0].verification_results is not None
    assert len(result.entries[0].verification_results.accurate) == 1
