"""
Tests for the OpenAI API integration module.
"""
import pytest
import json
from unittest.mock import patch
from wikifactcheck.api import OpenAIClient

def test_query_for_fact_check(mock_openai_client):
    """Test that query_for_fact_check correctly processes API responses."""
    client = OpenAIClient(mock_openai_client, "gpt-4.1-nano", api_delay=0)
    
    # Test with sample text
    article_block = "This is a test article."
    source_text = "This is a source that mentions test articles."
    
    # Query API
    with patch('time.sleep'):  # Patch sleep to avoid delays in tests
        result = client.query_for_fact_check(article_block, source_text)
    
    # Verify result
    assert "probabilities" in result
    assert result["probabilities"]["test"] == 0.9
    assert result["probabilities"]["article"] == 0.8

def test_build_prompt():
    """Test that _build_prompt correctly formats the prompt."""
    client = OpenAIClient(None, "model")
    
    article_block = "Test article."
    source_text = "Test source."
    
    prompt = client._build_prompt(article_block, source_text)
    
    # Verify prompt contains necessary components
    assert "ARTICLE TEXT" in prompt
    assert "SOURCE TEXT" in prompt
    assert article_block in prompt
    assert source_text in prompt

def test_parse_response_valid_json():
    """Test that _parse_response correctly handles valid JSON."""
    client = OpenAIClient(None, "model")
    
    response_text = '{"probabilities": {"test": 0.9}}'
    result = client._parse_response(response_text)
    
    assert result == {"probabilities": {"test": 0.9}}

def test_parse_response_embedded_json():
    """Test that _parse_response extracts JSON from text."""
    client = OpenAIClient(None, "model")
    
    response_text = 'Here is the result: {"probabilities": {"test": 0.9}} and some more text.'
    result = client._parse_response(response_text)
    
    assert result == {"probabilities": {"test": 0.9}}

def test_parse_response_invalid_json():
    """Test that _parse_response handles invalid JSON gracefully."""
    client = OpenAIClient(None, "model")
    
    response_text = 'Invalid JSON'
    result = client._parse_response(response_text)
    
    assert result == {"probabilities": {}}
