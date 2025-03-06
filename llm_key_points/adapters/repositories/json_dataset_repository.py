"""
JSON file implementation of the dataset repository.
"""

from pathlib import Path

from ...core.entities.dataset import Dataset
from ...core.interfaces.repositories import DatasetRepository


class JsonDatasetRepository(DatasetRepository):
    """Implementation of DatasetRepository that uses JSON files for storage."""

    def load(self, file_path: Path) -> Dataset:
        """Load a dataset from a JSON file."""
        return Dataset.load_from_file(file_path)

    def save(self, dataset: Dataset, file_path: Path, backup: bool = True) -> None:
        """Save a dataset to a JSON file."""
        dataset.save_to_file(file_path, backup)
