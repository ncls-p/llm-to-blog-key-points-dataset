"""
Tests for the Ollama fact checker.
"""

from unittest.mock import MagicMock, patch

import requests

from llm_key_points.adapters.verification import OllamaFactChecker
from llm_key_points.core.entities.dataset_entry import VerificationResults


def test_fact_checker_initialization():
    """Test initializing the fact checker with different configurations."""
    # Test with default configuration
    checker = OllamaFactChecker()
    assert checker.model == "bespoke-minicheck"
    assert "localhost" in checker.api_url

    # Test with custom model
    checker = OllamaFactChecker(model="custom-model")
    assert checker.model == "custom-model"

    # Test with custom API URL
    custom_url = "http://custom-ollama:11434/v1/chat/completions"
    checker = OllamaFactChecker(api_url=custom_url)
    assert checker.api_url == custom_url


def test_verify_key_point_accurate():
    """Test verification of an accurate key point."""
    mock_response = {
        "choices": [
            {"message": {"content": "Yes, this claim is consistent with the document."}}
        ]
    }

    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status.return_value = None

        checker = OllamaFactChecker()
        result = checker.verify_key_point(
            "The sky is blue.", "The sky has a blue color."
        )

        assert result["is_accurate"] is True
        assert "Yes" in result["explanation"]


def test_verify_key_point_inaccurate():
    """Test verification of an inaccurate key point."""
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": "No, this claim is not consistent with the document."
                }
            }
        ]
    }

    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status.return_value = None

        checker = OllamaFactChecker()
        result = checker.verify_key_point("The sky is blue.", "The sky is green.")

        assert result["is_accurate"] is False
        assert "No" in result["explanation"]


def test_verify_key_point_uncertain():
    """Test verification with uncertain response."""
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": "The document does not provide enough information to verify this claim."
                }
            }
        ]
    }

    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status.return_value = None

        checker = OllamaFactChecker()
        result = checker.verify_key_point(
            "The sky is blue.", "The sky has always been blue."
        )

        assert result["is_accurate"] is None


def test_verify_key_point_retry():
    """Test retry mechanism for verification."""
    success_response = {
        "choices": [
            {"message": {"content": "Yes, this claim is consistent with the document."}}
        ]
    }

    with patch("requests.post") as mock_post:
        # First call fails, second succeeds
        mock_post.side_effect = [
            requests.RequestException("Network error"),
            MagicMock(json=lambda: success_response, raise_for_status=lambda: None),
        ]

        checker = OllamaFactChecker(
            max_retries=2,
            retry_delay=0,  # No delay for testing
        )
        result = checker.verify_key_point(
            "The sky is blue.", "The sky has a blue color."
        )

        assert result["is_accurate"] is True
        assert mock_post.call_count == 2


def test_verify_key_points_multiple():
    """Test verification of multiple key points."""
    text = """
    The sky is blue during clear days.
    Clouds can make the sky appear white or gray.
    The sun appears yellow from Earth.
    """

    key_points = """
    * The sky appears blue on clear days
    * Clouds affect the sky's appearance
    * The sun looks yellow from our planet
    """

    mock_responses = [
        {"choices": [{"message": {"content": "Yes, this is accurate."}}]},
        {"choices": [{"message": {"content": "Yes, this matches the document."}}]},
        {"choices": [{"message": {"content": "Yes, this is consistent."}}]},
    ]

    with patch("requests.post") as mock_post:
        mock_post.return_value.raise_for_status.return_value = None
        mock_post.return_value.json.side_effect = mock_responses

        checker = OllamaFactChecker()
        results = checker.verify_key_points(text, key_points)

        assert isinstance(results, VerificationResults)
        assert len(results.accurate) == 3
        assert len(results.inaccurate) == 0
        assert len(results.uncertain) == 0


def test_verify_key_points_mixed_results():
    """Test verification with mixed response types."""
    text = "The sky is blue. The grass is green."
    key_points = """
    * The sky is blue
    * The grass is red
    * The clouds are purple
    """

    mock_responses = [
        {"choices": [{"message": {"content": "Yes, accurate."}}]},
        {"choices": [{"message": {"content": "No, this is incorrect."}}]},
        {"choices": [{"message": {"content": "Cannot determine from the text."}}]},
    ]

    with patch("requests.post") as mock_post:
        mock_post.return_value.raise_for_status.return_value = None
        mock_post.return_value.json.side_effect = mock_responses

        checker = OllamaFactChecker()
        results = checker.verify_key_points(text, key_points)

        assert len(results.accurate) == 1
        assert len(results.inaccurate) == 1
        assert len(results.uncertain) == 1


def test_verify_key_points_content_truncation():
    """Test that long content is properly truncated."""
    long_content = "A" * 7000  # Longer than max_content_length
    key_point = "This is a test point."

    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Yes"}}]
        }
        mock_post.return_value.raise_for_status.return_value = None

        checker = OllamaFactChecker()
        result = checker.verify_key_point(long_content, key_point)

        # Get the actual formatted content that was sent
        called_content = mock_post.call_args[1]["json"]["messages"][0]["content"]

        # Extract the document content between "Document:" and "Claim:"
        document_content = called_content.split("\n\nClaim:")[0].replace(
            "Document: ", ""
        )

        # Check truncation
        assert len(document_content) < 7000
        assert document_content.endswith("...")
