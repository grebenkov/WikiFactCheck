"""
Shared test fixtures for the WikiFactCheck test suite.
"""
import pytest
import os
import json
from unittest.mock import MagicMock

from openai import OpenAI
from wikifactcheck.config import DEFAULT_MODEL

@pytest.fixture
def sample_article():
    """Return sample article text for testing."""
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_article.txt')
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return f.read()

@pytest.fixture
def sample_sources():
    """Return sample sources for testing."""
    sources = {}
    fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
    
    for source_file in ['source1.txt', 'source2.txt']:
        path = os.path.join(fixtures_dir, source_file)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                sources[source_file] = f.read()
    
    return sources

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    mock_client = MagicMock(spec=OpenAI)
    
    # Create the chat attribute and its nested structure
    mock_chat = MagicMock()
    mock_completions = MagicMock()
    mock_client.chat = mock_chat
    mock_chat.completions = mock_completions
    
    # Mock the chat.completions.create method
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=json.dumps({
            "probabilities": {
                "test": 0.9,
                "article": 0.8,
                "content": 0.7
            }
        })))
    ]
    
    mock_completions.create.return_value = mock_completion
    return mock_client
