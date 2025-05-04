import os
import re
import json
import glob
import time
import argparse
from typing import List, Dict, Any
import openai
from openai import OpenAI
import colorama
from colorama import Fore, Style
import logging

# Initialize colorama for terminal coloring
colorama.init()

def load_article(file_path: str) -> str:
    """Load article text from file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def load_sources() -> Dict[str, str]:
    """Load all source files with pattern source*.txt."""
    sources = {}
    for source_file in sorted(glob.glob("source*.txt")):
        with open(source_file, 'r', encoding='utf-8') as file:
            sources[source_file] = file.read()
            print(f"Loaded source: {source_file}")
    return sources

def split_into_blocks(text: str, target_size: int = 100) -> List[str]:
    """Split text into ~100-word blocks of complete sentences."""
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
    
    print(f"Split article into {len(blocks)} blocks")
    return blocks

def query_chatgpt(client: OpenAI, article_block: str, source_text: str, model_name: str) -> Dict[str, Any]:
    """Query ChatGPT to check article text against source."""
    # Improved prompt for better results
    json_structure = r"""
    {
        "probabilities": {
            "word1": 0.9,
            "word2": 0.5,
            "word3": 0.0,
            ...
        }
    }
    """
    
    prompt = f"""
    You are an expert Wikipedia article reviewer tasked with fact-checking. Compare the article text below against the provided source and verify its accuracy.

    For EACH WORD in the article text, assign a probability (0.0 to 1.0) that indicates how well it's supported by the source:
    - 1.0: Word is directly supported by information in the source
    - 0.7-0.9: Word is supported but with some minor context differences
    - 0.4-0.6: Word has partial support or is ambiguous
    - 0.1-0.3: Word has minimal support or is tangentially related
    - 0.0: Word contradicts the source or has no support

    Analyze EVERY SINGLE WORD, including articles (the, a, an), prepositions, and conjunctions.

    Return ONLY a valid JSON object with this structure:
    {json_structure}

    ========= ARTICLE TEXT =========
    {article_block}
    ========= SOURCE TEXT =========
    {source_text}
    """
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an expert fact-checker for Wikipedia articles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,  # Use deterministic responses
        )
        
        # Extract and parse JSON response
        response_text = response.choices[0].message.content
        
        try:
            # Parse the entire response as JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try extracting JSON with regex as fallback
            json_match = re.search(r'({.*})', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            else:
                print(f"Failed to parse JSON response: {response_text[:100]}...")
                return {"probabilities": {}}
    except Exception as e:
        print(f"Error querying ChatGPT: {e}")
        # Dump response
        with open("request.json", "w", encoding="utf-8") as f:
            f.write(response_text)
        return {"probabilities": {}}

def process_article_blocks(client: OpenAI, article_blocks: List[str], sources: Dict[str, str], model_name: str) -> Dict[str, List[float]]:
    """Process each article block against each source and collect word probabilities."""
    word_probabilities = {}
    
    for i, block in enumerate(article_blocks):
        print(f"Processing block {i+1}/{len(article_blocks)}...")
        
        for source_name, source_text in sources.items():
            print(f"  Checking against source: {source_name}")
            
            # Query ChatGPT
            response = query_chatgpt(client, block, source_text, model_name)
            
            # Update word probabilities
            if "probabilities" in response:
                for word, prob in response["probabilities"].items():
                    word_lower = word.lower()
                    if word_lower not in word_probabilities:
                        word_probabilities[word_lower] = []
                    
                    try:
                        prob_value = float(prob)
                        word_probabilities[word_lower].append(prob_value)
                    except (ValueError, TypeError):
                        print(f"Warning: Invalid probability for word '{word}': {prob}")
            
            # Add a small delay to avoid rate limits
            time.sleep(0.5)
    
    return word_probabilities

def tokenize_text(text: str) -> List[tuple]:
    """Tokenize text into words and non-words while preserving structure."""
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

def colorize_article(text: str, word_probabilities: Dict[str, List[float]]) -> str:
    """Colorize the article text based on word probabilities."""
    tokens = tokenize_text(text)
    colored_text = []
    
    for token, token_type in tokens:
        if token_type in ["word", "punctuation"] and token.lower() in word_probabilities:
            probs = word_probabilities[token.lower()]
            max_prob = max(probs) if probs else 0.0
            
            if max_prob > 0.7:
                colored_text.append(f"{Fore.GREEN}{token}{Style.RESET_ALL}")
            elif max_prob > 0.35:
                colored_text.append(f"{Fore.YELLOW}{token}{Style.RESET_ALL}")
            else:
                colored_text.append(f"{Fore.RED}{token}{Style.RESET_ALL}")
        else:
            # Other tokens (spaces or tokens without probabilities)
            colored_text.append(token)
    
    return ''.join(colored_text)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Fact-check an article against sources using OpenAI API.')
    parser.add_argument('--base_url', type=str, help='Base URL for OpenAI API')
    parser.add_argument('--model', type=str, default='gpt-4.1-nano', help='OpenAI model name (default: gpt-4.1-nano)')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Initialize OpenAI client
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: Please set the OPENAI_API_KEY environment variable")
        return
    
    # Set up client with base_url if provided
    client_kwargs = {"api_key": api_key}
    if args.base_url:
        client_kwargs["base_url"] = args.base_url
    
    client = OpenAI(**client_kwargs)
    
    # Load article and sources
    try:
        article_text = load_article("article.txt")
        sources = load_sources()
        
        if not sources:
            print("Error: No source files found (source*.txt)")
            return
        
        # Split article into blocks
        article_blocks = split_into_blocks(article_text)
        
        # Process article blocks
        word_probabilities = process_article_blocks(client, article_blocks, sources, args.model)
        
        # Colorize and print article
        colored_article = colorize_article(article_text, word_probabilities)
        print("\nColored Article Text:")
        print(colored_article)
        
    except Exception as e:
        logging.exception("An exception was thrown!")

if __name__ == "__main__":
    main()
