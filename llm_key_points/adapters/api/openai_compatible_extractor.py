"""
Implementation of key points extractor using an OpenAI-compatible API.
"""

import logging
import os
import re
import time
from typing import Optional

import requests

from ...core.interfaces.ai_services import KeyPointsExtractor

# Set up logging
logger = logging.getLogger(__name__)


class OpenAICompatibleExtractor(KeyPointsExtractor):
    """Implementation of KeyPointsExtractor using an OpenAI-compatible API."""

    DEFAULT_MODEL = "gpt-3.5-turbo"

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        """Initialize the extractor.

        Args:
            api_key: The API key for authentication
            model: Optional model name, defaults to DEFAULT_MODEL if not provided
            max_retries: Number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.api_key = api_key
        self.model = (
            model
            if model is not None
            else os.getenv("OPENAI_COMPATIBLE_MODEL", self.DEFAULT_MODEL)
        )
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Set up API URL
        base_api_url = os.getenv("OPENAI_COMPATIBLE_API_URL", "https://api.openai.com")
        self.api_url = (
            f"{base_api_url}/v1/chat/completions"  # Fixed API path to include v1
        )

        # Set up headers
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def extract_key_points(self, content: str) -> Optional[str]:
        """Extract key points from the given content using the OpenAI API."""
        messages = [
            {
                "role": "system",
                "content": "Extract and list only the key points from the given article in a precise manner. Format the response as a bullet point list starting with 'Here are the key points of the article:'. Each point should start with an asterisk (*). Make it concise and focused on the main information. Do not include any references, citations, or source markers.",
            },
            {"role": "user", "content": content},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "top_p": 0.9,
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url, headers=self.headers, json=payload, timeout=30
                )
                response.raise_for_status()
                output = response.json()["choices"][0]["message"]["content"]

                # Clean any remaining references from the output
                cleaned_output = self.clean_references(output)
                return cleaned_output
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Max retries reached")
                    return None

    def clean_references(self, text: str) -> str:
        """Remove reference artifacts from text."""
        # Remove [X] style references
        text = re.sub(r"\[\d+\]", "", text)

        # Remove (Source: X) style references
        text = re.sub(r"\(Source:.*?\)", "", text)

        # Remove [Source: X] style references
        text = re.sub(r"\[Source:.*?\]", "", text)

        # Remove any remaining citation markers
        text = re.sub(r"\[\w+\s*\d*\]", "", text)

        # Clean up any double spaces created by removals
        text = re.sub(r"\s+", " ", text)

        # Clean up any empty bullet points
        text = re.sub(r"\*\s*\n", "", text)

        # Clean up multiple newlines
        text = re.sub(r"\n\s*\n", "\n", text)

        return text.strip()
