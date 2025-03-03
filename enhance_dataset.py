import json
import logging
import re
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any
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

        # Ollama API settings for fact-checking
        self.ollama_api_url = os.getenv(
            "OLLAMA_API_URL", "http://localhost:11434/v1/chat/completions"
        )
        self.ollama_headers = {
            "Content-Type": "application/json",
        }
        self.fact_check_model = os.getenv("FACT_CHECK_MODEL", "bespoke-minicheck")

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

    def test_key_points(self, content: str, key_points: str) -> Dict[str, List[Dict]]:
        """
        Test each key point against the original content using the Bespoke-MiniCheck model.

        Args:
            content: The original article content
            key_points: The extracted key points as a string

        Returns:
            Dictionary with 'accurate' and 'inaccurate' lists of key points and their verification results
        """
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

        results = {"accurate": [], "inaccurate": [], "uncertain": []}

        for point in points:
            if not point:  # Skip empty points
                continue

            verification = self._verify_point_with_ollama(content, point)

            if verification["is_accurate"]:
                results["accurate"].append(
                    {"point": point, "verification": verification}
                )
            elif verification["is_accurate"] is False:  # Explicitly False, not None
                results["inaccurate"].append(
                    {"point": point, "verification": verification}
                )
            else:
                results["uncertain"].append(
                    {"point": point, "verification": verification}
                )

        return results

    def _verify_point_with_ollama(self, content: str, point: str) -> Dict:
        """
        Verify a single key point against the content using Ollama's Bespoke-MiniCheck model.

        Args:
            content: The original article content
            point: A single key point to verify

        Returns:
            Dictionary with verification results
        """
        # Truncate content if too long to fit in context window
        max_content_length = 6000  # Adjust based on model's context window
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."

        # According to Bespoke-MiniCheck documentation, the model expects a simple format:
        # Document: {document}
        # Claim: {claim}
        # And responds with "Yes" or "No"
        messages = [
            {
                "role": "user",
                "content": f"Document: {content}\n\nClaim: {point}\n\nIs this claim consistent with the document?",
            },
        ]

        payload = {
            "model": self.fact_check_model,
            "messages": messages,
            "temperature": 0.1,  # Low temperature for more deterministic results
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.ollama_api_url,
                    headers=self.ollama_headers,
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

    def process_single_url(
        self, url: str, verify_points: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Process a single URL and return article data with optional verification"""
        content = self.extract_webpage_content(url)
        if not content:
            return None

        key_points = self.get_key_points(content)
        if not key_points:
            return None

        result: Dict[str, Any] = {
            "instruction": "",
            "input": content,
            "output": key_points,
        }

        # If verification is requested, add verification results
        if verify_points:
            verification_results = self.test_key_points(content, key_points)
            # Store verification results as a separate field, not overwriting existing fields
            result["verification_results"] = verification_results

            # Log verification summary
            accurate_count = len(verification_results["accurate"])
            inaccurate_count = len(verification_results["inaccurate"])
            uncertain_count = len(verification_results["uncertain"])
            total_points = accurate_count + inaccurate_count + uncertain_count

            if total_points > 0:
                logger.info(f"Verification results for {url}:")
                logger.info(
                    f"  - Accurate: {accurate_count}/{total_points} ({accurate_count / total_points * 100:.1f}%)"
                )
                logger.info(
                    f"  - Inaccurate: {inaccurate_count}/{total_points} ({inaccurate_count / total_points * 100:.1f}%)"
                )
                logger.info(
                    f"  - Uncertain: {uncertain_count}/{total_points} ({uncertain_count / total_points * 100:.1f}%)"
                )

        return result

    def update_dataset(
        self,
        file_path: Union[str, Path],
        urls: Union[str, List[str]],
        backup: bool = True,
        verify_points: bool = False,
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
            result = self.process_single_url(url, verify_points=verify_points)
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

    def verify_existing_dataset(
        self,
        file_path: Union[str, Path],
        output_file_path: Optional[Union[str, Path]] = None,
        backup: bool = True,
    ):
        """
        Verify key points in an existing dataset against their original content.

        Args:
            file_path: Path to the dataset file
            output_file_path: Path to save the verified dataset (defaults to original with _verified suffix)
            backup: Whether to create a backup of the original file
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"Dataset file not found: {file_path}")
            return

        # Set default output path if not provided
        if output_file_path is None:
            output_file_path = file_path.with_stem(f"{file_path.stem}_verified")
        else:
            output_file_path = Path(output_file_path)

        # Load dataset
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

        # Process each entry
        total_entries = len(dataset)
        for i, entry in enumerate(dataset):
            logger.info(f"Verifying entry {i + 1}/{total_entries}")

            content = entry.get("input")
            key_points = entry.get("output")

            if not content or not key_points:
                logger.warning(
                    f"Entry {i + 1} is missing content or key points, skipping"
                )
                continue

            verification_results = self.test_key_points(content, key_points)
            # Ensure entry is treated as a dictionary with string keys and any values
            entry_dict: Dict[str, Any] = entry
            entry_dict["verification_results"] = verification_results

            # Log verification summary
            accurate_count = len(verification_results["accurate"])
            inaccurate_count = len(verification_results["inaccurate"])
            uncertain_count = len(verification_results["uncertain"])
            total_points = accurate_count + inaccurate_count + uncertain_count

            if total_points > 0:
                logger.info(
                    f"  - Accurate: {accurate_count}/{total_points} ({accurate_count / total_points * 100:.1f}%)"
                )
                logger.info(
                    f"  - Inaccurate: {inaccurate_count}/{total_points} ({inaccurate_count / total_points * 100:.1f}%)"
                )
                logger.info(
                    f"  - Uncertain: {uncertain_count}/{total_points} ({uncertain_count / total_points * 100:.1f}%)"
                )
            else:
                logger.warning(f"  - No points were extracted for verification")

            # Save intermediate results every 5 entries
            if (i + 1) % 5 == 0 or i == total_entries - 1:
                try:
                    with open(output_file_path, "w", encoding="utf-8") as f:
                        json.dump(dataset, f, ensure_ascii=False, indent=2)
                    logger.info(f"Saved intermediate results to {output_file_path}")
                except Exception as e:
                    logger.error(f"Error saving intermediate results: {e}")

        # Final save
        try:
            with open(output_file_path, "w", encoding="utf-8") as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully saved verified dataset to: {output_file_path}")
        except Exception as e:
            logger.error(f"Error saving verified dataset: {e}")


def main():
    # Initialize enhancer with your API key from environment variable
    api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY")
    if not api_key:
        logger.error("API key not found in environment variables")
        return

    enhancer = OpenAICompatibleEnhancer(api_key)

    # Example usage - replace with your URLs
    urls = ["https://example.com/article1", "https://example.com/article2"]

    # Update the dataset with new URLs and verify key points
    enhancer.update_dataset("./dataset.json", urls, verify_points=True)

    # Alternatively, verify an existing dataset
    # enhancer.verify_existing_dataset("./dataset.json")


if __name__ == "__main__":
    main()
