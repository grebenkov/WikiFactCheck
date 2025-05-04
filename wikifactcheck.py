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
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter import font as tkfont

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
        try:
            with open("request.json", "w", encoding="utf-8") as f:
                f.write(response_text)
        except:
            pass
        return {"probabilities": {}}

def process_article_blocks(client: OpenAI, article_blocks: List[str], sources: Dict[str, str], model_name: str) -> Dict[str, Dict[str, List[float]]]:
    """Process each article block against each source and collect word probabilities by source."""
    source_word_probabilities = {}
    
    # Initialize dict for each source
    for source_name in sources.keys():
        source_word_probabilities[source_name] = {}
        
    for i, block in enumerate(article_blocks):
        print(f"Processing block {i+1}/{len(article_blocks)}...")
        
        for source_name, source_text in sources.items():
            print(f"  Checking against source: {source_name}")
            
            # Query ChatGPT
            response = query_chatgpt(client, block, source_text, model_name)
            
            # Update word probabilities for this source
            if "probabilities" in response:
                for word, prob in response["probabilities"].items():
                    word_lower = word.lower()
                    if word_lower not in source_word_probabilities[source_name]:
                        source_word_probabilities[source_name][word_lower] = []
                    
                    try:
                        prob_value = float(prob)
                        source_word_probabilities[source_name][word_lower].append(prob_value)
                    except (ValueError, TypeError):
                        print(f"Warning: Invalid probability for word '{word}': {prob}")
            
            # Add a small delay to avoid rate limits
            time.sleep(0.5)
    
    return source_word_probabilities

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
    
    for i, (token, token_type) in enumerate(tokens):
        if token_type == "word":
            # Try to find probability for this word
            word_lower = token.lower()
            
            # Check if word exists in probabilities
            if word_lower in word_probabilities:
                probs = word_probabilities[word_lower]
            else:
                # Check if word with adjacent punctuation exists in probabilities
                # Look ahead for punctuation
                compound_word = word_lower
                next_index = i + 1
                while next_index < len(tokens) and tokens[next_index][1] == "punctuation":
                    compound_word += tokens[next_index][0].lower()
                    next_index += 1
                
                # Look behind for punctuation
                prev_compound_word = word_lower
                prev_index = i - 1
                while prev_index >= 0 and tokens[prev_index][1] == "punctuation":
                    prev_compound_word = tokens[prev_index][0].lower() + prev_compound_word
                    prev_index -= 1
                
                # Check compounds
                if compound_word in word_probabilities:
                    probs = word_probabilities[compound_word]
                elif prev_compound_word in word_probabilities:
                    probs = word_probabilities[prev_compound_word]
                else:
                    probs = []
            
            # Color based on probability
            max_prob = max(probs) if probs else 0.0
            
            if max_prob > 0.7:
                colored_text.append(f"{Fore.GREEN}{token}{Style.RESET_ALL}")
            elif max_prob > 0.35:
                colored_text.append(f"{Fore.YELLOW}{token}{Style.RESET_ALL}")
            else:
                colored_text.append(f"{Fore.RED}{token}{Style.RESET_ALL}")
        else:
            # Punctuation and spaces remain uncolored
            colored_text.append(token)
    
    return ''.join(colored_text)

class WikiFactCheckGUI:
    """GUI for WikiFactCheck application."""
    
    def __init__(self, root, article_text, sources_data, word_probabilities):
        self.root = root
        self.root.title("WikiFactCheck")
        self.root.geometry("1000x700")
        
        self.article_text = article_text
        self.sources_data = sources_data
        self.word_probabilities = word_probabilities
        
        # Create the main layout
        self.create_layout()
        
        # Display first source by default
        if self.sources_listbox.size() > 0:
            self.sources_listbox.selection_set(0)
            self.on_source_selected()
    
    def create_layout(self):
        """Create the GUI layout."""
        # Create main panel with padding
        main_panel = ttk.Frame(self.root, padding="10")
        main_panel.pack(fill=tk.BOTH, expand=True)
        
        # Create top panel for sources
        sources_panel = ttk.LabelFrame(main_panel, text="Sources", padding="5")
        sources_panel.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))
        
        # Add sources listbox
        self.sources_listbox = tk.Listbox(sources_panel, height=5)
        self.sources_listbox.pack(fill=tk.X, padx=5, pady=5)
        for source_name in self.sources_data.keys():
            self.sources_listbox.insert(tk.END, source_name)
        
        # Bind selection event
        self.sources_listbox.bind("<<ListboxSelect>>", lambda e: self.on_source_selected())
        
        # Create article display panel
        article_panel = ttk.LabelFrame(main_panel, text="Article", padding="5")
        article_panel.pack(fill=tk.BOTH, expand=True)
        
        # Add text display widget
        self.text_display = scrolledtext.ScrolledText(article_panel, wrap=tk.WORD)
        self.text_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create legend panel
        legend_panel = ttk.Frame(main_panel)
        legend_panel.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        # Add color legend
        ttk.Label(legend_panel, text="Legend:", font=("", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        green_label = ttk.Label(legend_panel, text="High support", foreground="green")
        green_label.pack(side=tk.LEFT, padx=(0, 15))
        
        yellow_label = ttk.Label(legend_panel, text="Partial support", foreground="orange")
        yellow_label.pack(side=tk.LEFT, padx=(0, 15))
        
        red_label = ttk.Label(legend_panel, text="Low/No support", foreground="red")
        red_label.pack(side=tk.LEFT)
        
        # Add exit button
        exit_button = ttk.Button(legend_panel, text="Exit", command=self.root.destroy)
        exit_button.pack(side=tk.RIGHT)
    
    def on_source_selected(self):
        """Handle source selection event."""
        if not self.sources_listbox.curselection():
            return
            
        # Get selected source
        selected_index = self.sources_listbox.curselection()[0]
        selected_source = self.sources_listbox.get(selected_index)
        
        # Update article display
        self.display_article_for_source(selected_source)
    
    def display_article_for_source(self, source_name):
        """Display article with color-coding based on selected source."""
        # Clear current content
        self.text_display.delete(1.0, tk.END)
        
        # Configure text tags for coloring
        self.text_display.tag_configure("green", foreground="green")
        self.text_display.tag_configure("yellow", foreground="orange")
        self.text_display.tag_configure("red", foreground="red")
        
        # Get tokens from the article
        tokens = tokenize_text(self.article_text)
        
        # Insert tokens with appropriate coloring
        for i, (token, token_type) in enumerate(tokens):
            if token_type == "word":
                # Try to find probability for this word
                word_lower = token.lower()
                
                # Check if word exists in probabilities
                if word_lower in self.word_probabilities[source_name]:
                    probs = self.word_probabilities[source_name][word_lower]
                else:
                    # Check if word with adjacent punctuation exists in probabilities
                    # Look ahead for punctuation
                    compound_word = word_lower
                    next_index = i + 1
                    while next_index < len(tokens) and tokens[next_index][1] == "punctuation":
                        compound_word += tokens[next_index][0].lower()
                        next_index += 1
                    
                    # Look behind for punctuation
                    prev_compound_word = word_lower
                    prev_index = i - 1
                    while prev_index >= 0 and tokens[prev_index][1] == "punctuation":
                        prev_compound_word = tokens[prev_index][0].lower() + prev_compound_word
                        prev_index -= 1
                    
                    # Check compounds
                    if compound_word in self.word_probabilities[source_name]:
                        probs = self.word_probabilities[source_name][compound_word]
                    elif prev_compound_word in self.word_probabilities[source_name]:
                        probs = self.word_probabilities[source_name][prev_compound_word]
                    else:
                        probs = []
                
                # Apply coloring based on probability
                max_prob = max(probs) if probs else 0.0
                
                if max_prob > 0.7:
                    self.text_display.insert(tk.END, token, "green")
                elif max_prob > 0.35:
                    self.text_display.insert(tk.END, token, "yellow")
                else:
                    self.text_display.insert(tk.END, token, "red")
            else:
                # For punctuation and spaces
                self.text_display.insert(tk.END, token)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Fact-check an article against sources using OpenAI API.')
    parser.add_argument('--base_url', type=str, help='Base URL for OpenAI API')
    parser.add_argument('--model', type=str, default='gpt-4.1-nano', help='OpenAI model name (default: gpt-4.1-nano)')
    parser.add_argument('--gui', action='store_true', help='Use GUI interface instead of terminal output')
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
        source_word_probabilities = process_article_blocks(client, article_blocks, sources, args.model)
        
        if args.gui:
            # Launch GUI
            root = tk.Tk()
            app = WikiFactCheckGUI(root, article_text, sources, source_word_probabilities)
            root.mainloop()
        else:
            # Terminal output - combine probabilities from all sources
            combined_probabilities = {}
            for source_probs in source_word_probabilities.values():
                for word, probs in source_probs.items():
                    if word not in combined_probabilities:
                        combined_probabilities[word] = []
                    combined_probabilities[word].extend(probs)
            
            # Colorize and print article
            colored_article = colorize_article(article_text, combined_probabilities)
            print("\nColored Article Text:")
            print(colored_article)
        
    except Exception as e:
        logging.exception("An exception was thrown!")

if __name__ == "__main__":
    main()
