"""
Repository interfaces for the dataset domain.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..entities.dataset import Dataset


class DatasetRepository(ABC):
    """Interface for dataset storage operations."""

    @abstractmethod
    def load(self, file_path: Path) -> Dataset:
        """Load a dataset from storage."""
        pass

    @abstractmethod
    def save(self, dataset: Dataset, file_path: Path, backup: bool = True) -> None:
        """Save a dataset to storage."""
        pass


class WebContentRepository(ABC):
    """Interface for retrieving web content."""

    @abstractmethod
    def extract_content(self, url: str) -> Optional[str]:
        """Extract readable content from a web URL."""
        pass
