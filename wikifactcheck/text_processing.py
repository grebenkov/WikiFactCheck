"""
Text processing utilities for the WikiFactCheck application.
"""
import re
from typing import List, Tuple

def tokenize_text(text: str) -> List[Tuple[str, str]]:
    """
    Tokenize text into words, punctuation, and spaces while preserving structure.
    
    Args:
        text: The text to tokenize
        
    Returns:
        List of tuples (token, token_type) where token_type is one of:
        "word", "punctuation", or "space"
    """
    tokens = []
    pattern = r'(\b\w+\b)|([^\w\s])|(\s+)'
    
    for match in re.finditer(pattern, text):
        if match.group(1):  # Word
            tokens.append((match.group(1), "word"))
        elif match.group(2):  # Punctuation
            tokens.append((match.group(2), "punctuation"))
        elif match.group(3):  # Space
            tokens.append((match.group(3), "space"))
    
    return tokens

def split_into_blocks(text: str, target_size: int = 100) -> List[str]:
    """
    Split text into blocks of approximately target_size words, preserving complete sentences.
    
    Args:
        text: The text to split
        target_size: Target number of words per block
        
    Returns:
        List of text blocks
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    blocks = []
    current_block = []
    current_word_count = 0
    
    for sentence in sentences:
        words_in_sentence = len(re.findall(r'\b\w+\b', sentence))
        
        if current_word_count + words_in_sentence <= target_size:
            current_block.append(sentence)
            current_word_count += words_in_sentence
        else:
            if current_block:
                blocks.append(' '.join(current_block))
            current_block = [sentence]
            current_word_count = words_in_sentence
    
    # Add the last block if not empty
    if current_block:
        blocks.append(' '.join(current_block))
    
    return blocks
