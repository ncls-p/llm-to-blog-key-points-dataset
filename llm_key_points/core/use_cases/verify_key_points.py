"""
Use cases for verifying key points in existing datasets.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from ..entities.dataset import Dataset
from ..interfaces.ai_services import FactChecker
from ..interfaces.repositories import DatasetRepository


class VerifyDatasetUseCase:
    """
    Use case for verifying key points in an existing dataset.
    """

    def __init__(
        self, dataset_repository: DatasetRepository, fact_checker: FactChecker
    ):
        self.dataset_repository = dataset_repository
        self.fact_checker = fact_checker

    def verify_dataset(
        self, input_path: Path, output_path: Optional[Path] = None, backup: bool = True
    ) -> Dataset:
        """
        Verify all entries in a dataset.

        Args:
            input_path: Path to the input dataset file
            output_path: Path to save the verified dataset (defaults to input with _verified suffix)
            backup: Whether to create a backup of the input file

        Returns:
            The verified dataset
        """
        # Set default output path if not provided
        if output_path is None:
            output_path = input_path.with_stem(f"{input_path.stem}_verified")

        # Load the dataset
        dataset = self.dataset_repository.load(input_path)

        # Process each entry in the dataset
        for entry in dataset.entries:
            if entry.input and entry.output:
                # Verify the key points for this entry
                verification_results = self.fact_checker.verify_key_points(
                    entry.input, entry.output
                )
                entry.verification_results = verification_results

        # Save the verified dataset
        self.dataset_repository.save(dataset, output_path, backup)

        return dataset

    def get_verification_stats(self, dataset: Dataset) -> Dict[str, Any]:
        """
        Calculate verification statistics for a dataset.

        Args:
            dataset: The dataset to analyze

        Returns:
            A dictionary containing verification statistics
        """
        return dataset.get_stats()
