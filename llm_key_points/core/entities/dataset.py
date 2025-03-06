"""
Core entity representing a dataset of article key points.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from .dataset_entry import DatasetEntry


@dataclass
class Dataset:
    """
    Represents a collection of dataset entries with article content and key points.
    """

    entries: List[DatasetEntry] = field(default_factory=list)

    def add_entry(self, entry: DatasetEntry) -> None:
        """Add a new entry to the dataset."""
        self.entries.append(entry)

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert the dataset to a list of dictionaries for serialization."""
        return [entry.to_dict() for entry in self.entries]

    @classmethod
    def from_dict_list(cls, data: List[Dict[str, Any]]) -> "Dataset":
        """Create a dataset from a list of dictionaries."""
        entries = [DatasetEntry.from_dict(entry_data) for entry_data in data]
        return cls(entries=entries)

    @classmethod
    def load_from_file(cls, file_path: Path) -> "Dataset":
        """Load a dataset from a JSON file."""
        if not file_path.exists():
            return cls()

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_dict_list(data)

    def save_to_file(self, file_path: Path, backup: bool = True) -> None:
        """Save the dataset to a JSON file, optionally creating a backup."""
        if backup and file_path.exists():
            backup_path = file_path.with_suffix(".json.backup")
            with open(backup_path, "w", encoding="utf-8") as f:
                with open(file_path, "r", encoding="utf-8") as original:
                    f.write(original.read())

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict_list(), f, ensure_ascii=False, indent=2)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the dataset."""
        total_entries = len(self.entries)

        # Count entries with verification
        verified_entries = sum(
            1 for entry in self.entries if entry.verification_results is not None
        )

        # Count accurate, inaccurate, uncertain points
        accurate_points = 0
        inaccurate_points = 0
        uncertain_points = 0

        for entry in self.entries:
            if entry.verification_results:
                accurate_points += len(entry.verification_results.accurate)
                inaccurate_points += len(entry.verification_results.inaccurate)
                uncertain_points += len(entry.verification_results.uncertain)

        total_points = accurate_points + inaccurate_points + uncertain_points

        return {
            "total_entries": total_entries,
            "verified_entries": verified_entries,
            "total_verified_points": total_points,
            "accurate_points": accurate_points,
            "inaccurate_points": inaccurate_points,
            "uncertain_points": uncertain_points,
        }

    def convert_to_sharegpt_format(self) -> List[Dict[str, Any]]:
        """Convert the dataset to ShareGPT format for fine-tuning."""
        sharegpt_dataset = []

        for entry in self.entries:
            conversations = []

            # Add instruction as a separate message if it exists
            if entry.instruction.strip():
                conversations.append({"from": "human", "value": entry.instruction})

            # Add the main content and response
            conversations.append({"from": "human", "value": entry.input})

            conversations.append({"from": "gpt", "value": entry.output})

            sharegpt_dataset.append(
                {"conversations": conversations, "source": "article-key-points"}
            )

        return sharegpt_dataset
