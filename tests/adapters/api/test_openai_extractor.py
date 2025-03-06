"""
Tests for the OpenAI-compatible key points extractor.
"""

import os
from unittest.mock import patch, MagicMock

import pytest
import requests

from llm_key_points.adapters.api import OpenAICompatibleExtractor


@pytest.fixture(autouse=True)
def setup_env():
    """Set up environment variables for all tests."""
    with patch.dict(os.environ, {"OPENAI_COMPATIBLE_MODEL": "gpt-3.5-turbo"}):
        yield


def test_extractor_initialization():
    """Test initializing the extractor with different configurations."""
    # Test with minimal configuration
    extractor = OpenAICompatibleExtractor("test-key")
    assert extractor.api_key == "test-key"
    assert extractor.model == "gpt-3.5-turbo"

    # Test with custom model
    extractor = OpenAICompatibleExtractor("test-key", model="gpt-4")
    assert extractor.model == "gpt-4"

    # Test with environment variable for API URL
    with patch.dict(
        os.environ, {"OPENAI_COMPATIBLE_API_URL": "https://custom-api.com"}
    ):
        extractor = OpenAICompatibleExtractor("test-key")
        assert "https://custom-api.com" in extractor.api_url


def test_clean_references():
    """Test reference cleaning functionality."""
    extractor = OpenAICompatibleExtractor("test-key")

    text = """
    Here are the key points:
    * First point [1]
    * Second point (Source: Website)
    * Third point [Source: Book]
    * Fourth point[citation1]
    * Fifth point with [multiple] [citations] [here]
    """

    cleaned = extractor.clean_references(text)

    assert "[1]" not in cleaned
    assert "(Source: Website)" not in cleaned
    assert "[Source: Book]" not in cleaned
    assert "[citation1]" not in cleaned
    assert "[multiple]" not in cleaned
    assert "[citations]" not in cleaned
    assert "[here]" not in cleaned
    assert "First point" in cleaned
    assert "Second point" in cleaned
    assert "Third point" in cleaned
    assert "Fourth point" in cleaned
    assert "Fifth point with" in cleaned


def test_extract_key_points_success():
    """Test successful key points extraction."""
    mock_response = {
        "choices": [
            {"message": {"content": "Here are the key points:\n* Point 1\n* Point 2"}}
        ]
    }

    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status.return_value = None

        extractor = OpenAICompatibleExtractor("test-key")
        result = extractor.extract_key_points("Test content")

        assert result is not None
        assert "Point 1" in result
        assert "Point 2" in result


def test_extract_key_points_retry():
    """Test retry mechanism for key points extraction."""
    success_response = {
        "choices": [{"message": {"content": "Here are the key points:\n* Point 1"}}]
    }

    with patch("requests.post") as mock_post:
        # First call fails, second succeeds
        mock_post.side_effect = [
            requests.RequestException("Network error"),
            MagicMock(json=lambda: success_response, raise_for_status=lambda: None),
        ]

        extractor = OpenAICompatibleExtractor(
            "test-key",
            max_retries=2,
            retry_delay=0,  # No delay for testing
        )
        result = extractor.extract_key_points("Test content")

        assert result is not None
        assert "Point 1" in result
        assert mock_post.call_count == 2


def test_extract_key_points_failure():
    """Test handling of repeated failures in key points extraction."""
    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.RequestException("Network error")

        extractor = OpenAICompatibleExtractor(
            "test-key",
            max_retries=2,
            retry_delay=0,  # No delay for testing
        )
        result = extractor.extract_key_points("Test content")

        assert result is None
        assert mock_post.call_count == 2  # Tried maximum number of times


def test_extract_key_points_api_error():
    """Test handling of API errors."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.raise_for_status.side_effect = requests.HTTPError(
            "API Error"
        )

        extractor = OpenAICompatibleExtractor("test-key", max_retries=1, retry_delay=0)
        result = extractor.extract_key_points("Test content")

        assert result is None


def test_extract_key_points_request_validation():
    """Test that the API request is properly formatted."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Here are the key points:\n* Point 1"}}]
        }
        mock_post.return_value.raise_for_status.return_value = None

        extractor = OpenAICompatibleExtractor("test-key")
        extractor.extract_key_points("Test content")

        # Check that the request was made with correct data
        called_with = mock_post.call_args[1]["json"]
        assert called_with["model"] == "gpt-3.5-turbo"
        assert called_with["temperature"] == 0.2
        assert called_with["top_p"] == 0.9
        assert len(called_with["messages"]) == 2
        assert called_with["messages"][0]["role"] == "system"
        assert called_with["messages"][1]["role"] == "user"
        assert called_with["messages"][1]["content"] == "Test content"
