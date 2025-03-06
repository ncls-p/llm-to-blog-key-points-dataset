"""
Implementation of web content repository using BeautifulSoup.
"""

import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from ...core.interfaces.repositories import WebContentRepository

# Set up logging
logger = logging.getLogger(__name__)


class BeautifulSoupWebRepository(WebContentRepository):
    """Implementation of WebContentRepository using BeautifulSoup."""

    def __init__(self, request_timeout: int = 30):
        self.request_timeout = request_timeout

    def extract_content(self, url: str) -> Optional[str]:
        """Extract readable content from a web URL."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=self.request_timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "iframe"]):
                element.decompose()

            # Get text content
            text = " ".join(soup.stripped_strings)
            return text
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
