"""
Configuration settings for the WikiFactCheck application.
"""
import os
from typing import Dict, Any

# Application constants
DEFAULT_MODEL = "gpt-4.1-nano"
BLOCK_TARGET_SIZE = 100
API_DELAY = 0.5  # Delay between API calls to avoid rate limits

# Probability thresholds for coloring
HIGH_SUPPORT_THRESHOLD = 0.7
PARTIAL_SUPPORT_THRESHOLD = 0.35

# OpenAI API configuration
def get_openai_config() -> Dict[str, Any]:
    """
    Get OpenAI API configuration from environment variables.
    
    Returns:
        Dict containing API configuration parameters
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    
    config = {"api_key": api_key}
    return config

# JSON response structure for OpenAI API
JSON_STRUCTURE = r"""
{
    "probabilities": {
        "word1": 0.9,
        "word2": 0.5,
        "word3": 0.0,
        ...
    }
}
"""

# System prompt for OpenAI
SYSTEM_PROMPT = "You are an expert fact-checker for Wikipedia articles."
