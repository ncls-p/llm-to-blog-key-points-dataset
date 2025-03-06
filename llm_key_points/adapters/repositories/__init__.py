"""
Repository implementations for data storage and retrieval.
"""

from .json_dataset_repository import JsonDatasetRepository
from .web_content_repository import BeautifulSoupWebRepository

__all__ = ["JsonDatasetRepository", "BeautifulSoupWebRepository"]
