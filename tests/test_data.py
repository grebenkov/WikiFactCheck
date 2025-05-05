"""
Tests for the data loading module.
"""
import pytest
import os
import tempfile
from wikifactcheck.data import load_article, load_sources

def test_load_article():
    """Test that load_article correctly loads article text."""
    # Create a temporary article file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test article content.")
        temp_path = f.name
    
    try:
        # Load the article
        article_text = load_article(temp_path)
        assert article_text == "Test article content."
    finally:
        # Clean up
        os.unlink(temp_path)

def test_load_article_file_not_found():
    """Test that load_article raises FileNotFoundError for non-existent files."""
    with pytest.raises(FileNotFoundError):
        load_article("nonexistent_file.txt")

def test_load_sources(tmpdir):
    """Test that load_sources correctly loads all source files."""
    # Create temporary source files
    source1 = tmpdir.join("source1.txt")
    source1.write("Source 1 content")
    source2 = tmpdir.join("source2.txt")
    source2.write("Source 2 content")
    
    # Change to the temporary directory
    original_dir = os.getcwd()
    os.chdir(tmpdir)
    
    try:
        # Load sources
        sources = load_sources()
        
        # Verify sources were loaded correctly
        assert len(sources) == 2
        assert "source1.txt" in sources
        assert sources["source1.txt"] == "Source 1 content"
        assert "source2.txt" in sources
        assert sources["source2.txt"] == "Source 2 content"
    finally:
        # Restore original directory
        os.chdir(original_dir)
