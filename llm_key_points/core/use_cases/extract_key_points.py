"""
Use cases for extracting key points from web content.
"""

from pathlib import Path
from typing import List, Optional

from ..entities.dataset import Dataset
from ..entities.dataset_entry import DatasetEntry
from ..interfaces.repositories import DatasetRepository, WebContentRepository
from ..interfaces.ai_services import KeyPointsExtractor, FactChecker


class ExtractKeyPointsUseCase:
    """Use case for extracting key points from web content."""

    def __init__(
        self,
        web_repository: WebContentRepository,
        dataset_repository: DatasetRepository,
        key_points_extractor: KeyPointsExtractor,
        fact_checker: Optional[FactChecker] = None,
    ):
        self.web_repository = web_repository
        self.dataset_repository = dataset_repository
        self.key_points_extractor = key_points_extractor
        self.fact_checker = fact_checker

    def extract_from_url(
        self, url: str, verify_points: bool = False
    ) -> Optional[DatasetEntry]:
        """Extract key points from a URL."""
        # Extract content
        content = self.web_repository.extract_content(url)
        if not content:
            return None

        # Extract key points
        key_points = self.key_points_extractor.extract_key_points(content)
        if not key_points:
            return None

        # Create entry
        entry = DatasetEntry(input=content, output=key_points)

        # Verify if requested and fact checker is available
        if verify_points and self.fact_checker:
            verification_results = self.fact_checker.verify_key_points(
                content, key_points
            )
            entry.verification_results = verification_results

        return entry

    def process_urls(
        self,
        urls: List[str],
        dataset_path: Path,
        verify_points: bool = False,
        backup: bool = True,
    ) -> Dataset:
        """Process multiple URLs and update dataset."""
        # Load existing dataset
        dataset = self.dataset_repository.load(dataset_path)

        # Process each URL
        for i, url in enumerate(urls):
            entry = self.extract_from_url(url, verify_points)
            if entry:
                dataset.add_entry(entry)
                # Only save immediately if it's the first URL (with backup) or last URL
                if i == 0 and backup:
                    self.dataset_repository.save(dataset, dataset_path, backup=True)
                elif i == len(urls) - 1:
                    self.dataset_repository.save(dataset, dataset_path, backup=False)

        return dataset
