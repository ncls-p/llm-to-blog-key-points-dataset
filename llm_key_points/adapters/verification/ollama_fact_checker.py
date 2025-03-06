"""
Implementation of fact checker using Ollama API.
"""

import logging
import os
import re
import time
from typing import Any, Dict

import requests

from ...core.entities.dataset_entry import VerificationResults
from ...core.interfaces.ai_services import FactChecker

# Set up logging
logger = logging.getLogger(__name__)


class OllamaFactChecker(FactChecker):
    """Implementation of FactChecker using Ollama API."""

    def __init__(
        self,
        model: str = None,
        api_url: str = None,
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        self.model = model or os.getenv("FACT_CHECK_MODEL", "bespoke-minicheck")
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Set up API URL
        self.api_url = api_url or os.getenv(
            "OLLAMA_API_URL", "http://localhost:11434/chat/completions"
        )

        # Set up headers
        self.headers = {
            "Content-Type": "application/json",
        }

    def verify_key_point(self, content: str, key_point: str) -> Dict[str, Any]:
        """Verify a single key point against the original content."""
        # Truncate content if too long to fit in context window
        max_content_length = 6000  # Adjust based on model's context window
        if len(content) > max_content_length:
            truncated = content[: max_content_length - 3]  # Leave room for ...
            if not truncated.endswith("..."):
                truncated += "..."
            content = truncated

        # According to Bespoke-MiniCheck documentation, the model expects a simple format:
        # Document: {document}
        # Claim: {claim}
        messages = [
            {
                "role": "user",
                "content": f"Document: {content}\n\nClaim: {key_point}\n\nIs this claim consistent with the document?",
            },
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,  # Low temperature for more deterministic results
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60,
                )
                response.raise_for_status()
                result = response.json()["choices"][0]["message"]["content"]

                # Parse the result - Bespoke-MiniCheck responds with "Yes" or "No"
                is_accurate = None
                if result.lower().startswith("yes"):
                    is_accurate = True
                elif result.lower().startswith("no"):
                    is_accurate = False
                # Otherwise, leave as None (uncertain)

                return {
                    "is_accurate": is_accurate,
                    "explanation": result,
                    "raw_response": result,
                }
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Attempt {attempt + 1} failed when verifying point: {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Max retries reached during fact verification")
                    return {
                        "is_accurate": None,
                        "explanation": f"Error: {str(e)}",
                        "raw_response": None,
                    }

        # Ensure we always return a value even if the loop completes without returning
        return {
            "is_accurate": None,
            "explanation": "Failed to verify after maximum retries",
            "raw_response": None,
        }

    def verify_key_points(self, content: str, key_points: str) -> VerificationResults:
        """Verify all key points against the original content."""
        # Extract individual key points from the bullet list
        points = [
            p.strip().lstrip("*").strip()
            for p in key_points.split("\n")
            if p.strip() and not p.startswith("Here are the key points")
        ]

        # Check if we have any valid points to verify
        if not points:
            logger.warning(
                "No valid bullet points found in the key_points string. Expected format: '* Point 1\\n* Point 2'"
            )
            # Try a more lenient extraction - treat each sentence as a point
            sentences = [
                s.strip() for s in re.split(r"(?<=[.!?])\s+", key_points) if s.strip()
            ]
            if sentences:
                logger.info(
                    f"Extracted {len(sentences)} sentences to verify instead of bullet points"
                )
                points = sentences
            else:
                logger.warning(
                    "Could not extract any sentences either. Verification will be skipped."
                )

        results = VerificationResults()

        for point in points:
            if not point:  # Skip empty points
                continue

            verification = self.verify_key_point(content, point)

            if verification["is_accurate"]:
                results.accurate.append({"point": point, "verification": verification})
            elif verification["is_accurate"] is False:  # Explicitly False, not None
                results.inaccurate.append(
                    {"point": point, "verification": verification}
                )
            else:
                results.uncertain.append({"point": point, "verification": verification})

        return results
