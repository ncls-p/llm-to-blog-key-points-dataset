"""
Tests for the key points verification use case.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from llm_key_points.core.use_cases.verify_key_points import VerifyDatasetUseCase
from llm_key_points.core.entities.dataset import Dataset
from llm_key_points.core.entities.dataset_entry import DatasetEntry, VerificationResults


def test_verify_dataset():
    """Test verifying a dataset."""
    # Create test data
    dataset = Dataset()
    dataset.add_entry(DatasetEntry(input="Test content 1", output="* Key point 1"))
    dataset.add_entry(DatasetEntry(input="Test content 2", output="* Key point 2"))

    # Create mock dependencies
    dataset_repo = Mock()
    dataset_repo.load.return_value = dataset

    fact_checker = Mock()
    verification_results = VerificationResults()
    verification_results.accurate.append({"point": "Key point", "verification": {}})
    fact_checker.verify_key_points.return_value = verification_results

    # Create use case
    use_case = VerifyDatasetUseCase(
        dataset_repository=dataset_repo, fact_checker=fact_checker
    )

    # Test verification
    result = use_case.verify_dataset(Path("input.json"))

    assert len(result.entries) == 2
    for entry in result.entries:
        assert entry.verification_results is not None
        assert len(entry.verification_results.accurate) == 1

    # Verify save was called
    dataset_repo.save.assert_called_once()


def test_verify_dataset_custom_output():
    """Test verifying a dataset with custom output path."""
    dataset = Dataset()
    dataset.add_entry(DatasetEntry(input="Test content", output="* Key point"))

    dataset_repo = Mock()
    dataset_repo.load.return_value = dataset

    fact_checker = Mock()
    verification_results = VerificationResults()
    verification_results.accurate.append({"point": "Key point", "verification": {}})
    fact_checker.verify_key_points.return_value = verification_results

    use_case = VerifyDatasetUseCase(
        dataset_repository=dataset_repo, fact_checker=fact_checker
    )

    output_path = Path("custom_output.json")
    result = use_case.verify_dataset(Path("input.json"), output_path=output_path)

    # Verify save was called with custom output path
    dataset_repo.save.assert_called_once_with(result, output_path, True)


def test_verify_dataset_skip_invalid_entries():
    """Test that verification skips entries without input or output."""
    dataset = Dataset()
    # Add invalid entry (missing output)
    dataset.add_entry(DatasetEntry(input="Test content"))
    # Add valid entry
    dataset.add_entry(DatasetEntry(input="Test content", output="* Key point"))

    dataset_repo = Mock()
    dataset_repo.load.return_value = dataset

    fact_checker = Mock()
    verification_results = VerificationResults()
    verification_results.accurate.append({"point": "Key point", "verification": {}})
    fact_checker.verify_key_points.return_value = verification_results

    use_case = VerifyDatasetUseCase(
        dataset_repository=dataset_repo, fact_checker=fact_checker
    )

    result = use_case.verify_dataset(Path("input.json"))

    # Verify that fact checker was only called for valid entry
    assert fact_checker.verify_key_points.call_count == 1

    # First entry should still have no verification results
    assert result.entries[0].verification_results is None
    # Second entry should have verification results
    assert result.entries[1].verification_results is not None


def test_get_verification_stats():
    """Test getting verification statistics."""
    # Create dataset with mixed verification results
    dataset = Dataset()

    # Entry with no verification
    dataset.add_entry(DatasetEntry(input="Test 1", output="* Point 1"))

    # Entry with verification (all accurate)
    entry2 = DatasetEntry(input="Test 2", output="* Point 2\n* Point 3")
    entry2.verification_results = VerificationResults()
    entry2.verification_results.accurate.extend(
        [
            {"point": "Point 2", "verification": {}},
            {"point": "Point 3", "verification": {}},
        ]
    )
    dataset.add_entry(entry2)

    # Entry with mixed results
    entry3 = DatasetEntry(input="Test 3", output="* Point 4\n* Point 5\n* Point 6")
    entry3.verification_results = VerificationResults()
    entry3.verification_results.accurate.append(
        {"point": "Point 4", "verification": {}}
    )
    entry3.verification_results.inaccurate.append(
        {"point": "Point 5", "verification": {}}
    )
    entry3.verification_results.uncertain.append(
        {"point": "Point 6", "verification": {}}
    )
    dataset.add_entry(entry3)

    # Get stats
    use_case = VerifyDatasetUseCase(dataset_repository=Mock(), fact_checker=Mock())
    stats = use_case.get_verification_stats(dataset)

    # Verify stats
    assert stats["total_entries"] == 3
    assert stats["verified_entries"] == 2
    assert stats["total_verified_points"] == 5
    assert stats["accurate_points"] == 3
    assert stats["inaccurate_points"] == 1
    assert stats["uncertain_points"] == 1
