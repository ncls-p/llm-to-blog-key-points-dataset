"""
Core entity representing a dataset entry with article content and key points.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class VerificationResult:
    """Represents the verification result of a single key point."""

    is_accurate: Optional[bool]
    explanation: str
    raw_response: Optional[str]


@dataclass
class VerificationResults:
    """Collection of verification results for key points."""

    accurate: List[Dict[str, Any]] = field(default_factory=list)
    inaccurate: List[Dict[str, Any]] = field(default_factory=list)
    uncertain: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DatasetEntry:
    """
    Represents an entry in the dataset with article content and key points.
    """

    input: str  # The original article content
    output: Optional[str] = None  # The extracted key points
    instruction: str = ""  # Optional instruction for the model
    verification_results: Optional[VerificationResults] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
        result = {
            "instruction": self.instruction,
            "input": self.input,
            "output": self.output,
        }

        if self.verification_results:
            result["verification_results"] = {
                "accurate": self.verification_results.accurate,
                "inaccurate": self.verification_results.inaccurate,
                "uncertain": self.verification_results.uncertain,
            }

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetEntry":
        """Create an instance from a dictionary."""
        verification_results = None
        if "verification_results" in data:
            verification_results = VerificationResults(
                accurate=data["verification_results"].get("accurate", []),
                inaccurate=data["verification_results"].get("inaccurate", []),
                uncertain=data["verification_results"].get("uncertain", []),
            )

        return cls(
            input=data.get("input", ""),
            output=data.get("output"),
            instruction=data.get("instruction", ""),
            verification_results=verification_results,
        )
