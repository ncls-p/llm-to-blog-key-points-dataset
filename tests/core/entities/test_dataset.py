"""
Tests for the Dataset and DatasetEntry entities.
"""

import json
import tempfile
from pathlib import Path

from llm_key_points.core.entities.dataset import Dataset
from llm_key_points.core.entities.dataset_entry import DatasetEntry, VerificationResults


def test_dataset_entry_creation():
    """Test creating a dataset entry."""
    entry = DatasetEntry(
        input="Test content",
        output="* Test key point",
        instruction="Extract key points",
    )

    assert entry.input == "Test content"
    assert entry.output == "* Test key point"
    assert entry.instruction == "Extract key points"
    assert entry.verification_results is None


def test_dataset_entry_to_dict():
    """Test converting a dataset entry to dictionary."""
    entry = DatasetEntry(
        input="Test content",
        output="* Test key point",
        instruction="Extract key points",
    )

    entry_dict = entry.to_dict()
    assert entry_dict["input"] == "Test content"
    assert entry_dict["output"] == "* Test key point"
    assert entry_dict["instruction"] == "Extract key points"
    assert "verification_results" not in entry_dict


def test_dataset_entry_from_dict():
    """Test creating a dataset entry from dictionary."""
    data = {
        "input": "Test content",
        "output": "* Test key point",
        "instruction": "Extract key points",
        "verification_results": {
            "accurate": [
                {"point": "Test point", "verification": {"is_accurate": True}}
            ],
            "inaccurate": [],
            "uncertain": [],
        },
    }

    entry = DatasetEntry.from_dict(data)
    assert entry.input == "Test content"
    assert entry.output == "* Test key point"
    assert entry.instruction == "Extract key points"
    assert entry.verification_results is not None
    assert len(entry.verification_results.accurate) == 1


def test_dataset_creation():
    """Test creating a dataset."""
    dataset = Dataset()
    assert len(dataset.entries) == 0


def test_dataset_add_entry():
    """Test adding entries to a dataset."""
    dataset = Dataset()
    entry = DatasetEntry(input="Test", output="* Point")

    dataset.add_entry(entry)
    assert len(dataset.entries) == 1
    assert dataset.entries[0].input == "Test"


def test_dataset_save_and_load():
    """Test saving and loading a dataset."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        file_path = Path(tmp.name)

    try:
        # Create and save dataset
        dataset = Dataset()
        entry = DatasetEntry(input="Test", output="* Point")
        dataset.add_entry(entry)

        dataset.save_to_file(file_path)

        # Load dataset
        loaded_dataset = Dataset.load_from_file(file_path)

        assert len(loaded_dataset.entries) == 1
        assert loaded_dataset.entries[0].input == "Test"
        assert loaded_dataset.entries[0].output == "* Point"

    finally:
        # Cleanup
        file_path.unlink()


def test_dataset_backup_creation():
    """Test that backup files are created when saving."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        file_path = Path(tmp.name)

    try:
        # Create and save initial dataset
        dataset = Dataset()
        entry = DatasetEntry(input="Original", output="* Point")
        dataset.add_entry(entry)
        dataset.save_to_file(file_path)

        # Modify and save with backup
        entry = DatasetEntry(input="Modified", output="* New point")
        dataset.add_entry(entry)
        dataset.save_to_file(file_path, backup=True)

        # Check backup file exists and contains original data
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


def test_dataset_sharegpt_conversion():
    """Test converting dataset to ShareGPT format."""
    dataset = Dataset()
    entry = DatasetEntry(
        input="Test content",
        output="* Test key point",
        instruction="Extract key points",
    )
    dataset.add_entry(entry)

    sharegpt_data = dataset.convert_to_sharegpt_format()

    assert len(sharegpt_data) == 1
    assert len(sharegpt_data[0]["conversations"]) == 3  # instruction + input + output
    assert sharegpt_data[0]["conversations"][0]["from"] == "human"
    assert sharegpt_data[0]["conversations"][0]["value"] == "Extract key points"
    assert sharegpt_data[0]["conversations"][1]["value"] == "Test content"
    assert sharegpt_data[0]["conversations"][2]["value"] == "* Test key point"


def test_dataset_stats():
    """Test getting dataset statistics."""
    dataset = Dataset()

    # Add an entry without verification
    entry1 = DatasetEntry(input="Test 1", output="* Point 1")
    dataset.add_entry(entry1)

    # Add an entry with verification results
    entry2 = DatasetEntry(input="Test 2", output="* Point 2")
    entry2.verification_results = VerificationResults()
    entry2.verification_results.accurate.append(
        {"point": "Point 2", "verification": {}}
    )
    dataset.add_entry(entry2)

    stats = dataset.get_stats()

    assert stats["total_entries"] == 2
    assert stats["verified_entries"] == 1
    assert stats["total_verified_points"] == 1
    assert stats["accurate_points"] == 1
    assert stats["inaccurate_points"] == 0
    assert stats["uncertain_points"] == 0
