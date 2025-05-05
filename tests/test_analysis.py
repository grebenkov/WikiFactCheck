"""
Tests for the article analysis module.
"""
import pytest
from wikifactcheck.analysis import ArticleAnalyzer

def test_analyze_article_processes_all_blocks(mock_openai_client, sample_article, sample_sources):
    """Test that analyze_article processes all blocks of the article."""
    # Initialize analyzer with mock client
    analyzer = ArticleAnalyzer(mock_openai_client, "gpt-4.1-nano")
    
    # Split article into small blocks for testing
    article_blocks = ["Block 1 test content.", "Block 2 more test content."]
    
    # Run analysis
    result = analyzer.analyze_article(article_blocks, sample_sources)
    
    # Verify each source has results
    for source_name in sample_sources.keys():
        assert source_name in result
        
    # Verify API was called for each block and each source
    expected_calls = len(article_blocks) * len(sample_sources)
    assert mock_openai_client.chat.completions.create.call_count == expected_calls

def test_process_probabilities():
    """Test that _process_probabilities correctly handles word probabilities."""
    analyzer = ArticleAnalyzer(None, "model")  # Client not needed for this test
    
    # Test data
    probabilities = {"test": 0.9, "article": 0.8}
    words_in_block = ["Test", "article", "unknown"]
    source_probabilities = {}
    warned_words = set()
    
    # Process probabilities
    analyzer._process_probabilities(
        probabilities, words_in_block, source_probabilities, warned_words
    )
    
    # Verify results
    assert "test" in source_probabilities
    assert source_probabilities["test"] == [0.9]
    assert "article" in source_probabilities
    assert source_probabilities["article"] == [0.8]
    assert "unknown" in source_probabilities
    assert source_probabilities["unknown"] == [0.0]
    assert "unknown" in warned_words

def test_normalize_probabilities():
    """Test that _normalize_probabilities handles word variations correctly."""
    analyzer = ArticleAnalyzer(None, "model")
    
    # Test data with variations
    probabilities = {
        "Test": 0.9,
        "article,": 0.8,
        "word's": 0.7
    }
    
    normalized = analyzer._normalize_probabilities(probabilities)
    
    # Verify results
    assert "test" in normalized
    assert normalized["test"] == 0.9
    assert "article" in normalized
    assert normalized["article"] == 0.8
    assert "word" in normalized
    assert normalized["word"] == 0.7
