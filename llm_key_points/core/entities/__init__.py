"""
Core domain entities for the LLM Key Points Dataset Generator.
"""

from .dataset import Dataset
from .dataset_entry import DatasetEntry, VerificationResult, VerificationResults

__all__ = ["Dataset", "DatasetEntry", "VerificationResult", "VerificationResults"]
