"""
Tests for the terminal visualization module.
"""
import pytest
from colorama import Fore, Style
from wikifactcheck.visualization.terminal import colorize_article

def test_colorize_article():
    """Test that colorize_article correctly applies color based on probabilities."""
    text = "This is a test."
    word_probabilities = {
        "this": [0.9],  # High support (green)
        "is": [0.5],    # Partial support (yellow)
        "a": [0.2],     # Low support (red)
        "test": [0.1]   # Low support (red)
    }
    
    colored_text = colorize_article(text, word_probabilities)
    
    # Verify colors were applied correctly
    assert f"{Fore.GREEN}This{Style.RESET_ALL}" in colored_text
    assert f"{Fore.YELLOW}is{Style.RESET_ALL}" in colored_text
    assert f"{Fore.RED}a{Style.RESET_ALL}" in colored_text
    assert f"{Fore.RED}test{Style.RESET_ALL}" in colored_text

def test_colorize_article_missing_word():
    """Test that colorize_article handles missing words correctly."""
    text = "This word is missing."
    word_probabilities = {
        "this": [0.9],
        "is": [0.5]
        # "word" and "missing" are not in the probabilities
    }
    
    colored_text = colorize_article(text, word_probabilities)
    
    # Verify colors were applied correctly for known words
    assert f"{Fore.GREEN}This{Style.RESET_ALL}" in colored_text
    assert f"{Fore.YELLOW}is{Style.RESET_ALL}" in colored_text
    
    # Verify missing words are colored red
    assert f"{Fore.RED}word{Style.RESET_ALL}" in colored_text
    assert f"{Fore.RED}missing{Style.RESET_ALL}" in colored_text
