import json
import logging
import re
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv

import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class OpenAICompatibleEnhancer:
    def __init__(self, api_key: str, max_retries: int = 3, retry_delay: int = 5):
        self.api_key = api_key
        # Get base URL from environment variable, with a default fallback
        base_api_url = os.getenv("OPENAI_COMPATIBLE_API_URL", "https://api.openai.com")
        self.api_url = f"{base_api_url}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.max_retries = max_retries
        self.retry_delay = retry_delay

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

    def extract_webpage_content(self, url: str) -> Optional[str]:
        """Extract readable content from webpage, removing scripts, styles, etc."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
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

    def get_key_points(self, content: str) -> Optional[str]:
        """Get key points from OpenAI compatible API with retry mechanism"""
        messages = [
            {
                "role": "system",
                "content": "Extract and list only the key points from the given article in a precise manner. Format the response as a bullet point list starting with 'Here are the key points of the article:'. Each point should start with an asterisk (*). Make it concise and focused on the main information. Do not include any references, citations, or source markers.",
            },
            {"role": "user", "content": content},
        ]

        payload = {
            "model": os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-3.5-turbo"),
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

    def process_single_url(self, url: str) -> Optional[Dict]:
        """Process a single URL and return article data"""
        content = self.extract_webpage_content(url)
        if not content:
            return None

        key_points = self.get_key_points(content)
        if not key_points:
            return None

        return {"instruction": "", "input": content, "output": key_points}

    def update_dataset(
        self,
        file_path: Union[str, Path],
        urls: Union[str, List[str]],
        backup: bool = True,
    ):
        """Update existing dataset with new entries from URLs"""
        # Load existing dataset
        file_path = Path(file_path)
        if not file_path.exists():
            logger.info(f"Creating new dataset file: {file_path}")
            dataset = []
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    dataset = json.load(f)
                if backup:
                    backup_path = file_path.with_suffix(".json.backup")
                    with open(backup_path, "w", encoding="utf-8") as f:
                        json.dump(dataset, f, ensure_ascii=False, indent=2)
                    logger.info(f"Created backup at: {backup_path}")
            except json.JSONDecodeError:
                logger.error(f"Error reading {file_path}. Invalid JSON.")
                return
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                return

        # Convert single URL to list
        if isinstance(urls, str):
            urls = [urls]

        # Process URLs
        for url in urls:
            logger.info(f"Processing URL: {url}")
            result = self.process_single_url(url)
            if result:
                dataset.append(result)
                logger.info(f"Successfully processed: {url}")
            time.sleep(2)  # Rate limiting between requests

        # Save updated dataset
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully updated dataset at: {file_path}")
        except Exception as e:
            logger.error(f"Error saving dataset: {e}")


def main():
    # Initialize enhancer with your API key from environment variable
    api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY")
    if not api_key:
        logger.error("API key not found in environment variables")
        return

    enhancer = OpenAICompatibleEnhancer(api_key)

    # Example usage - replace with your URLs
    urls = ["https://example.com/article1", "https://example.com/article2"]

    # Update the dataset with new URLs
    enhancer.update_dataset("./dataset.json", urls)


if __name__ == "__main__":
    main()
