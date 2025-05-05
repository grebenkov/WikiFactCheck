"""
Core analysis logic for the WikiFactCheck application.
"""
import logging
from typing import Dict, List, Any

from openai import OpenAI

from wikifactcheck.api import OpenAIClient
from wikifactcheck.text_processing import tokenize_text

logger = logging.getLogger(__name__)

class ArticleAnalyzer:
    """
    Analyzer for fact-checking article text against sources.
    """
    
    def __init__(self, client: OpenAI, model_name: str):
        """
        Initialize the article analyzer.
        
        Args:
            client: OpenAI client
            model_name: Model name to use for analysis
        """
        self.api_client = OpenAIClient(client, model_name)
    
    def analyze_article(self, article_blocks: List[str], 
                      sources: Dict[str, str]) -> Dict[str, Dict[str, List[float]]]:
        """
        Process each article block against each source and collect word probabilities.
        
        Args:
            article_blocks: List of article text blocks
            sources: Dictionary mapping source names to source texts
            
        Returns:
            Dictionary mapping source names to word probabilities
        """
        source_word_probabilities = {source_name: {} for source_name in sources.keys()}
        warned_words = set()  # Track words we've already warned about
            
        for i, block in enumerate(article_blocks):
            logger.info(f"Processing block {i+1}/{len(article_blocks)}...")
            
            # Tokenize the block to get words in order
            tokens = tokenize_text(block)
            words_in_block = [token[0] for token in tokens if token[1] == "word"]
            
            for source_name, source_text in sources.items():
                logger.info(f"Checking against source: {source_name}")
                
                # Query OpenAI
                response = self.api_client.query_for_fact_check(block, source_text)
                
                # Update word probabilities for this source
                if "probabilities" in response:
                    self._process_probabilities(
                        response["probabilities"], 
                        words_in_block, 
                        source_word_probabilities[source_name],
                        warned_words
                    )
        
        return source_word_probabilities
    
    def _process_probabilities(self, 
                             probabilities: Dict[str, float], 
                             words_in_block: List[str],
                             source_probabilities: Dict[str, List[float]],
                             warned_words: set) -> None:
        """
        Process probabilities for a block of text.
        
        Args:
            probabilities: Dictionary of word probabilities from API
            words_in_block: List of words in the block
            source_probabilities: Dictionary to update with probabilities
            warned_words: Set of words we've already warned about
        """
        # Create a normalized mapping of words to probabilities
        block_probs = self._normalize_probabilities(probabilities)
        
        # Assign probabilities to each word in the block in order
        for word in words_in_block:
            word_lower = word.lower()
            
            # Initialize the probabilities list if it doesn't exist
            if word_lower not in source_probabilities:
                source_probabilities[word_lower] = []
            
            # Find probability for this word in the block
            found_prob = False
            
            # First, try the word as is
            if word_lower in block_probs:
                source_probabilities[word_lower].append(block_probs[word_lower])
                found_prob = True
            else:
                # Try the word with punctuation stripped
                stripped_word = word_lower.strip('.,;:?!()[]{}"\'')
                if stripped_word in block_probs:
                    source_probabilities[word_lower].append(block_probs[stripped_word])
                    found_prob = True
            
            # If we still didn't find a probability
            if not found_prob:
                if word_lower not in warned_words:
                    logger.warning(f"No probability found for word '{word}'")
                    warned_words.add(word_lower)
                source_probabilities[word_lower].append(0.0)
    
    def _normalize_probabilities(self, probabilities: Dict[str, Any]) -> Dict[str, float]:
        """
        Normalize probabilities to handle variations of the same word.
        
        Args:
            probabilities: Raw probabilities from API response
            
        Returns:
            Normalized dictionary of word probabilities
        """
        normalized = {}
        
        for word, prob in probabilities.items():
            try:
                # Convert to float and add the original word
                normalized[word.lower()] = float(prob)
                
                # Also add a stripped version for robustness
                stripped_word = word.lower().strip('.,;:?!()[]{}"\'')
                if stripped_word and stripped_word != word.lower():
                    # If multiple versions map to the same stripped word, use the highest probability
                    if stripped_word in normalized:
                        normalized[stripped_word] = max(normalized[stripped_word], float(prob))
                    else:
                        normalized[stripped_word] = float(prob)
                        
                # Handle possessives
                if word.lower().endswith("'s"):
                    base_word = word.lower()[:-2]
                    if base_word not in normalized or float(prob) > normalized[base_word]:
                        normalized[base_word] = float(prob)
                        
            except (ValueError, TypeError):
                logger.warning(f"Invalid probability for word '{word}': {prob}")
        
        return normalized
