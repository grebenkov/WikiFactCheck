"""
OpenAI API integration for the WikiFactCheck application.
"""
import json
import re
import logging
import time
from typing import Dict, Any, Optional

from openai import OpenAI

from wikifactcheck.config import JSON_STRUCTURE, SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class OpenAIClient:
    """
    Client for interacting with the OpenAI API for fact-checking.
    """
    
    def __init__(self, client: OpenAI, model_name: str, api_delay: float = 0.5):
        """
        Initialize the OpenAI client.
        
        Args:
            client: Initialized OpenAI client
            model_name: Name of the model to use
            api_delay: Delay between API calls to avoid rate limits
        """
        self.client = client
        self.model_name = model_name
        self.api_delay = api_delay
    
    def query_for_fact_check(self, article_block: str, source_text: str) -> Dict[str, Any]:
        """
        Query OpenAI to check article text against source.
        
        Args:
            article_block: Block of article text to check
            source_text: Source text to check against
            
        Returns:
            Dictionary containing probabilities for each word
        """
        prompt = self._build_prompt(article_block, source_text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Use deterministic responses
            )
            
            # Extract and parse JSON response
            response_text = response.choices[0].message.content
            return self._parse_response(response_text)
            
        except Exception as e:
            logger.exception(f"Error querying OpenAI API: {e}")
            return {"probabilities": {}}
        finally:
            # Add delay to avoid rate limits
            time.sleep(self.api_delay)
    
    def _build_prompt(self, article_block: str, source_text: str) -> str:
        """
        Build the prompt for the OpenAI API.
        
        Args:
            article_block: Block of article text to check
            source_text: Source text to check against
            
        Returns:
            Formatted prompt string
        """
        return f"""
        You are an expert Wikipedia article reviewer tasked with fact-checking. Compare the article text below against the provided source and verify its accuracy.

        For EACH WORD in the article text, assign a probability (0.0 to 1.0) that indicates how well it's supported by the source:
        - 1.0: Word is directly supported by information in the source
        - 0.7-0.9: Word is supported but with some minor context differences
        - 0.4-0.6: Word has partial support or is ambiguous
        - 0.1-0.3: Word has minimal support or is tangentially related
        - 0.0: Word contradicts the source or has no support

        IMPORTANT: When analyzing words, ignore punctuation. For example:
        - For "Germany's" provide a probability for "Germany" (without apostrophe-s)
        - For "(USA)" provide a probability for "USA" (without parentheses)
        - For "Killer's" provide a probability for "Killer" (without apostrophe-s)

        Analyze EVERY SINGLE WORD, including articles (the, a, an), prepositions, and conjunctions.

        Return ONLY a valid JSON object with this structure:
        {JSON_STRUCTURE}

        ========= ARTICLE TEXT =========
        {article_block}
        ========= SOURCE TEXT =========
        {source_text}
        """
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the JSON response from the OpenAI API.
        
        Args:
            response_text: Text response from the API
            
        Returns:
            Parsed JSON object
        """
        try:
            # Parse the entire response as JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try extracting JSON with regex as fallback
            json_match = re.search(r'({.*})', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            else:
                logger.error(f"Failed to parse JSON response: {response_text[:100]}...")
                logger.debug(f"JSON: {response_text}")
                return {"probabilities": {}}
