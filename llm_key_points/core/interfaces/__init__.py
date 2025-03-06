"""
Abstract interfaces that define how the layers interact in the application.
"""

from .ai_services import FactChecker, KeyPointsExtractor
from .repositories import DatasetRepository, WebContentRepository

__all__ = [
    "KeyPointsExtractor",
    "FactChecker",
    "DatasetRepository",
    "WebContentRepository",
]
