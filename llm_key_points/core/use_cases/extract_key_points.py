"""
Use cases for extracting key points from web content.
"""

from pathlib import Path
from typing import Optional

from ..entities.dataset import Dataset
from ..entities.dataset_entry import DatasetEntry
from ..interfaces.ai_services import ExtractorConfig, FactChecker, KeyPointsExtractor
from ..interfaces.repositories import DatasetRepository, WebContentRepository


class ExtractKeyPointsUseCase:
    """Use case for extracting key points from web content."""

    def __init__(
        self,
        extractor: KeyPointsExtractor,
        dataset_repository: DatasetRepository,
        web_content_repository: WebContentRepository,
        fact_checker: Optional[FactChecker] = None,
    ):
        """Initialize the use case.

        Args:
            extractor: Implementation of KeyPointsExtractor
            dataset_repository: Implementation of DatasetRepository
            web_content_repository: Implementation of WebContentRepository
            fact_checker: Optional implementation of FactChecker for verifying key points
        """
        self.extractor = extractor
        self.fact_checker = fact_checker
        self.dataset_repository = dataset_repository
        self.web_content_repository = web_content_repository

        # Safely inject fact_checker if the extractor implementation supports it
        if fact_checker is not None:
            try:
                # Try to set fact_checker if the extractor supports it
                if hasattr(extractor, "fact_checker"):
                    setattr(extractor, "fact_checker", fact_checker)
            except (AttributeError, TypeError):
                # Ignore if the extractor doesn't support this attribute
                pass

    def extract_key_points_from_urls(
        self,
        urls: list[str],
        auto_check: bool = False,
        max_regeneration_attempts: int = 2,
        file_path: Optional[Path] = None,
    ) -> Dataset:
        """Extract key points from a list of URLs.

        Args:
            urls: List of URLs to process
            auto_check: Whether to automatically verify and regenerate inaccurate key points
            max_regeneration_attempts: Maximum number of regeneration attempts for inaccurate points
            file_path: Optional file path to save the dataset
        """
        # Create extraction config
        config = ExtractorConfig(
            auto_check_enabled=auto_check,
            max_regeneration_attempts=max_regeneration_attempts,
        )

        dataset = Dataset()

        for url in urls:
            content = self.web_content_repository.extract_content(url)
            if not content:
                continue

            key_points = self.extractor.extract_key_points(content, config=config)
            if key_points:
                # Create a proper DatasetEntry object and add it to the dataset
                entry = DatasetEntry(
                    input=content,
                    output=key_points,
                    instruction="Extract key points from the article",
                )
                dataset.add_entry(entry)

        # Only save if file_path is provided
        if file_path:
            self.dataset_repository.save(dataset, file_path)

        return dataset
