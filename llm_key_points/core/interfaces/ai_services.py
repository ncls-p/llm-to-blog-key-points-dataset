"""
Interfaces for AI service integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from ..entities.dataset_entry import VerificationResults


class KeyPointsExtractor(ABC):
    """Interface for key points extraction service."""

    @abstractmethod
    def extract_key_points(self, content: str) -> Optional[str]:
        """
        Extract key points from the given content.

        Args:
            content: The article content to extract key points from

        Returns:
            A string containing the extracted key points or None if extraction failed
        """
        pass

    @abstractmethod
    def clean_references(self, text: str) -> str:
        """
        Remove reference artifacts from text.

        Args:
            text: The text to clean

        Returns:
            Cleaned text with references removed
        """
        pass


class FactChecker(ABC):
    """Interface for fact-checking service."""

    @abstractmethod
    def verify_key_point(self, content: str, key_point: str) -> Dict[str, Any]:
        """
        Verify a single key point against the original content.

        Args:
            content: The original article content
            key_point: The key point to verify

        Returns:
            A dictionary with verification result information
        """
        pass

    @abstractmethod
    def verify_key_points(self, content: str, key_points: str) -> VerificationResults:
        """
        Verify all key points against the original content.

        Args:
            content: The original article content
            key_points: The key points to verify, as a formatted string

        Returns:
            A VerificationResults object containing results for each point
        """
        pass
