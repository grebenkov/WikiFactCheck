"""
Tests for the text processing module.
"""
import pytest
from wikifactcheck.text_processing import tokenize_text, split_into_blocks

def test_tokenize_text():
    """Test that tokenize_text correctly identifies words, spaces, and punctuation."""
    text = "Hello, world! This is a test."
    tokens = tokenize_text(text)
    
    expected = [
        ("Hello", "word"), (",", "punctuation"), (" ", "space"),
        ("world", "word"), ("!", "punctuation"), (" ", "space"),
        ("This", "word"), (" ", "space"), ("is", "word"), (" ", "space"),
        ("a", "word"), (" ", "space"), ("test", "word"), (".", "punctuation")
    ]
    
    assert tokens == expected

def test_split_into_blocks_respects_target_size():
    """Test that split_into_blocks creates blocks of approximately the target size."""
    # Create a text with 100 words (10 sentences of 10 words each)
    sentences = []
    for i in range(10):
        words = ' '.join([f"word{j}" for j in range(10)])
        sentences.append(f"{words}.")
    
    text = ' '.join(sentences)
    
    # Split with target size of 25 words
    blocks = split_into_blocks(text, 25)
    
    # Should create approximately 4 blocks
    assert 3 <= len(blocks) <= 5
    
    # Each block should contain approximately 25 words
    for block in blocks:
        word_count = len(block.split())
        # Allow some flexibility due to sentence boundaries
        assert 10 <= word_count <= 40

def test_split_into_blocks_preserves_sentences():
    """Test that split_into_blocks preserves complete sentences."""
    text = "First sentence. Second sentence. Third sentence."
    blocks = split_into_blocks(text, 2)
    
    # Should split into 3 blocks (one for each sentence)
    assert len(blocks) == 3
    
    # Each block should end with a period
    for block in blocks:
        assert block.endswith('.')
    
    # Verify content of blocks
    assert blocks[0] == "First sentence."
    assert blocks[1] == "Second sentence."
    assert blocks[2] == "Third sentence."

