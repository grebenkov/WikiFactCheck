"""
GUI visualization for the WikiFactCheck application.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, List

from wikifactcheck.text_processing import tokenize_text
from wikifactcheck.config import HIGH_SUPPORT_THRESHOLD, PARTIAL_SUPPORT_THRESHOLD

class WikiFactCheckGUI:
    """GUI for WikiFactCheck application."""
    
    def __init__(self, root, article_text, sources_data, word_probabilities):
        """
        Initialize the GUI application.
        
        Args:
            root: Tkinter root window
            article_text: Full article text
            sources_data: Dictionary of source names to source texts
            word_probabilities: Dictionary of word probabilities by source
        """
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
        """
        Display article with color-coding based on selected source.
        
        Args:
            source_name: Name of the selected source
        """
        # Clear current content
        self.text_display.delete(1.0, tk.END)
        
        # Configure text tags for coloring
        self.text_display.tag_configure("green", foreground="green")
        self.text_display.tag_configure("yellow", foreground="orange")
        self.text_display.tag_configure("red", foreground="red")
        
        # Get tokens from the article
        tokens = tokenize_text(self.article_text)
        
        # Track occurrences of each word
        word_occurrences = {}
        
        # Insert tokens with appropriate coloring
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
                source_probs = self.word_probabilities[source_name]
                if (word_lower in source_probs and 
                    current_occurrence < len(source_probs[word_lower])):
                    prob = source_probs[word_lower][current_occurrence]
                    
                    if prob > HIGH_SUPPORT_THRESHOLD:
                        self.text_display.insert(tk.END, token, "green")
                    elif prob > PARTIAL_SUPPORT_THRESHOLD:
                        self.text_display.insert(tk.END, token, "yellow")
                    else:
                        self.text_display.insert(tk.END, token, "red")
                else:
                    # No probability or occurrence data, use red
                    self.text_display.insert(tk.END, token, "red")
            else:
                # For punctuation and spaces
                self.text_display.insert(tk.END, token)
