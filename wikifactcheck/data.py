"""
Data loading functionality for the WikiFactCheck application.
"""
import glob
import logging
from typing import Dict

logger = logging.getLogger(__name__)

def load_article(file_path: str) -> str:
    """
    Load article text from file.
    
    Args:
        file_path: Path to the article file
        
    Returns:
        Article text content
        
    Raises:
        FileNotFoundError: If article file doesn't exist
        IOError: If there's an error reading the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"Article file not found: {file_path}")
        raise
    except IOError as e:
        logger.error(f"Error reading article file: {e}")
        raise

def load_sources() -> Dict[str, str]:
    """
    Load all source files with pattern source*.txt.
    
    Returns:
        Dictionary mapping source filenames to their content
        
    Raises:
        IOError: If there's an error reading any source file
    """
    sources = {}
    try:
        for source_file in sorted(glob.glob("source*.txt")):
            with open(source_file, 'r', encoding='utf-8') as file:
                sources[source_file] = file.read()
                logger.info(f"Loaded source: {source_file}")
        
        if not sources:
            logger.warning("No source files found matching pattern 'source*.txt'")
            
        return sources
    except IOError as e:
        logger.error(f"Error loading source files: {e}")
        raise
