"""
Main application entry point for WikiFactCheck.
"""
import os
import argparse
import logging
import tkinter as tk
from typing import Dict, List

from openai import OpenAI

from wikifactcheck.config import DEFAULT_MODEL, BLOCK_TARGET_SIZE, get_openai_config
from wikifactcheck.data import load_article, load_sources
from wikifactcheck.text_processing import split_into_blocks
from wikifactcheck.analysis import ArticleAnalyzer
from wikifactcheck.visualization.terminal import colorize_article
from wikifactcheck.visualization.gui import WikiFactCheckGUI

# Initialize logger
logger = logging.getLogger(__name__)

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Fact-check an article against sources using OpenAI API.')
    parser.add_argument('--base_url', type=str, help='Base URL for OpenAI API')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL, 
                        help=f'OpenAI model name (default: {DEFAULT_MODEL})')
    parser.add_argument('--gui', action='store_true', help='Use GUI interface instead of terminal output')
    return parser.parse_args()

def combine_probabilities(source_word_probabilities: Dict[str, Dict[str, List[float]]]) -> Dict[str, List[float]]:
    """
    Combine probabilities from all sources.
    
    Args:
        source_word_probabilities: Dictionary of word probabilities by source
        
    Returns:
        Combined probabilities
    """
    combined_probabilities = {}
    for source_probs in source_word_probabilities.values():
        for word, probs in source_probs.items():
            if word not in combined_probabilities:
                combined_probabilities[word] = []
            combined_probabilities[word].extend(probs)
    
    return combined_probabilities

def main():
    """Main application entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Initialize logging
    logging.basicConfig(level=logging.INFO)

    # Get OpenAI configuration
    openai_config = get_openai_config()
    if not openai_config["api_key"]:
        logger.error("Please set the OPENAI_API_KEY environment variable")
        return
    
    # Set up client with base_url if provided
    if args.base_url:
        openai_config["base_url"] = args.base_url
    
    client = OpenAI(**openai_config)
    
    try:
        # Load article and sources
        article_text = load_article("article.txt")
        sources = load_sources()
        
        if not sources:
            logger.error("Error: No source files found (source*.txt)")
            return
        
        # Split article into blocks
        article_blocks = split_into_blocks(article_text, BLOCK_TARGET_SIZE)
        
        # Initialize analyzer and process article blocks
        analyzer = ArticleAnalyzer(client, args.model)
        source_word_probabilities = analyzer.analyze_article(article_blocks, sources)
        
        if args.gui:
            # Launch GUI
            root = tk.Tk()
            app = WikiFactCheckGUI(root, article_text, sources, source_word_probabilities)
            root.mainloop()
        else:
            # Terminal output - combine probabilities from all sources
            combined_probabilities = combine_probabilities(source_word_probabilities)
            
            # Colorize and print article
            colored_article = colorize_article(article_text, combined_probabilities)
            print("\nColored Article Text:")
            print(colored_article)
        
    except Exception as e:
        logger.exception(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
