"""
Terminal visualization for the WikiFactCheck application.
"""
import colorama
from colorama import Fore, Style
from typing import Dict, List

from wikifactcheck.text_processing import tokenize_text
from wikifactcheck.config import HIGH_SUPPORT_THRESHOLD, PARTIAL_SUPPORT_THRESHOLD

# Initialize colorama for terminal coloring
colorama.init()

def colorize_article(text: str, word_probabilities: Dict[str, List[float]]) -> str:
    """
    Colorize the article text based on word probabilities for terminal output.
    
    Args:
        text: The article text to colorize
        word_probabilities: Dictionary mapping words to their probabilities
        
    Returns:
        Colorized article text ready for terminal display
    """
    tokens = tokenize_text(text)
    colored_text = []
    
    # Track occurrences of each word
    word_occurrences = {}
    
    for token, token_type in tokens:
        if token_type == "word":
            # Try to find probability for this word
            word_lower = token.lower()
            
            # Track occurrence count
            if word_lower not in word_occurrences:
                word_occurrences[word_lower] = 0
            else:
                word_occurrences[word_lower] += 1
            
            current_occurrence = word_occurrences[word_lower]
            
            # Check if word exists and we have data for this occurrence
            if (word_lower in word_probabilities and 
                current_occurrence < len(word_probabilities[word_lower])):
                prob = word_probabilities[word_lower][current_occurrence]
                
                if prob > HIGH_SUPPORT_THRESHOLD:
                    colored_text.append(f"{Fore.GREEN}{token}{Style.RESET_ALL}")
                elif prob > PARTIAL_SUPPORT_THRESHOLD:
                    colored_text.append(f"{Fore.YELLOW}{token}{Style.RESET_ALL}")
                else:
                    colored_text.append(f"{Fore.RED}{token}{Style.RESET_ALL}")
            else:
                # No probability or occurrence data, use red
                colored_text.append(f"{Fore.RED}{token}{Style.RESET_ALL}")
        else:
            # Punctuation and spaces remain uncolored
            colored_text.append(token)
    
    return ''.join(colored_text)