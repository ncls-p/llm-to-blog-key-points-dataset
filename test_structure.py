#!/usr/bin/env python
"""
Simple test script to verify that our clean architecture implementation works correctly.
This script imports and initializes key components from each layer to ensure the structure is sound.
"""

import logging

from llm_key_points.adapters.repositories import (
    BeautifulSoupWebRepository,
    JsonDatasetRepository,
)
from llm_key_points.core.entities import Dataset, DatasetEntry

# Interface layer imports
from llm_key_points.interfaces.console import RichPresenter

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logger.info("Testing clean architecture imports...")

logger.info("All imports successful!")

# Try initializing some components
logger.info("Initializing components...")

# Initialize repositories
dataset_repo = JsonDatasetRepository()
web_repo = BeautifulSoupWebRepository()

# Initialize presenter
presenter = RichPresenter()

# Create a simple dataset
dataset = Dataset()
entry = DatasetEntry(
    input="This is a test input.",
    output="* This is a test key point.",
    instruction="Extract key points",
)
dataset.add_entry(entry)

logger.info(f"Dataset created with {len(dataset.entries)} entries")

# Display some info using the presenter
presenter.display_success_message("Clean architecture test completed successfully!")
logger.info(
    "Test completed without errors. The clean architecture structure is working correctly!"
)

if __name__ == "__main__":
    # This script is just for testing the imports and basic structure
    pass
