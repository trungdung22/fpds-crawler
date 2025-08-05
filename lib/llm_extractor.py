"""
LLM Extractor Module
Phase 1: Bootstrap extraction via LLM to understand page structure
"""

import json
import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

try:
    import openai
    from openai import OpenAI
except ImportError:
    logger.warning("OpenAI not installed. LLM features will be disabled.")
    openai = None

class LLMExtractor:
    """
    LLM-based extractor for bootstrap extraction
    Analyzes page structure and generates reusable extraction configs
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None
        
        if self.api_key and openai:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info(f"LLM Extractor initialized with model: {model}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("No OpenAI API key provided. LLM extraction disabled.")
    
    def analyze_page_structure(self, html_content: str, target_fields: List[str] = None) -> Dict[str, Any]:
        """
        Analyze HTML page structure and generate extraction config
        
        Args:
            html_content: Raw HTML content
            target_fields: List of fields to extract (e.g., ['title', 'summary', 'date'])
            
        Returns:
            Dictionary containing extraction config and metadata
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized. Please provide valid API key.")
        
        # Default target fields if none provided
        if not target_fields:
            target_fields = ['title', 'summary', 'date', 'content', 'author']
        
        # Process HTML content
        processed_html = self._preprocess_html(html_content)
        
        # Create analysis prompt
        prompt = self._create_analysis_prompt(processed_html, target_fields)
        
        try:
            logger.info("Sending page structure analysis request to LLM...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert web scraping analyst. Your job is to analyze HTML structure and create precise BeautifulSoup extraction rules."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=2000
            )
            
            # Parse response
            result = self._parse_llm_response(response.choices[0].message.content)
            
            # Add metadata
            result['metadata'] = {
                'model': self.model,
                'target_fields': target_fields,
                'html_length': len(html_content),
                'processed_length': len(processed_html),
                'extraction_method': 'llm_bootstrap'
            }
            
            logger.info(f"Successfully generated extraction config for {len(result['selectors'])} fields")
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise
    
    def _preprocess_html(self, html_content: str, max_length: int = 8000) -> str:
        """
        Preprocess HTML content for LLM analysis
        
        Args:
            html_content: Raw HTML
            max_length: Maximum length to send to LLM
            
        Returns:
            Processed HTML string
        """
        # Remove script and style tags
        html_clean = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_clean = re.sub(r'<style[^>]*>.*?</style>', '', html_clean, flags=re.DOTALL)
        
        # Remove excessive whitespace
        html_clean = re.sub(r'\s+', ' ', html_clean)
        
        # Truncate if too long
        if len(html_clean) > max_length:
            # Try to find a good truncation point
            truncated = html_clean[:max_length]
            
            # Find the last complete tag
            last_tag = truncated.rfind('>')
            if last_tag > max_length * 0.8:  # If we have a reasonable tag ending
                truncated = truncated[:last_tag + 1]
            
            html_clean = truncated + "\n<!-- ... content truncated for analysis ... -->"
        
        return html_clean
    
    def _create_analysis_prompt(self, html_content: str, target_fields: List[str]) -> str:
        """
        Create the analysis prompt for LLM
        
        Args:
            html_content: Processed HTML content
            target_fields: Fields to extract
            
        Returns:
            Formatted prompt string
        """
        fields_str = ', '.join(target_fields)
        
        prompt = f"""
Analyze this HTML page and return a BeautifulSoup-style Python extraction config to get the following fields: {fields_str}

HTML Content:
{html_content}

Please return a JSON object with the following structure:
{{
    "selectors": {{
        "title": "soup.select_one('h1.title').text.strip()",
        "summary": "soup.select_one('div.summary').text.strip()",
        "date": "soup.select_one('span.date').text.strip()"
    }},
    "confidence_scores": {{
        "title": 0.95,
        "summary": 0.88,
        "date": 0.92
    }},
    "fallback_selectors": {{
        "title": ["h1", "h2", ".page-title"],
        "summary": ["p:first-of-type", ".intro", ".description"],
        "date": [".date", ".timestamp", "time"]
    }},
    "notes": "Brief notes about the extraction strategy"
}}

Guidelines:
1. Use specific CSS selectors that are likely to be consistent across similar pages
2. Provide confidence scores (0-1) for each selector
3. Include fallback selectors for robustness
4. Focus on semantic HTML elements when possible
5. Avoid overly specific selectors that might break on similar pages

Return only the JSON object, no additional text.
"""
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response and extract JSON config
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed configuration dictionary
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                config = json.loads(json_match.group())
            else:
                # Try to parse the entire response as JSON
                config = json.loads(response)
            
            # Validate config structure
            required_keys = ['selectors', 'confidence_scores', 'fallback_selectors']
            for key in required_keys:
                if key not in config:
                    config[key] = {}
            
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response: {response}")
            
            # Return fallback config
            return {
                'selectors': {},
                'confidence_scores': {},
                'fallback_selectors': {},
                'notes': 'Failed to parse LLM response',
                'error': str(e)
            }
    
    def validate_extraction_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate extraction config structure
        
        Args:
            config: Extraction configuration
            
        Returns:
            True if valid, False otherwise
        """
        required_keys = ['selectors', 'confidence_scores', 'fallback_selectors']
        
        for key in required_keys:
            if key not in config:
                logger.error(f"Missing required key: {key}")
                return False
        
        if not isinstance(config['selectors'], dict):
            logger.error("Selectors must be a dictionary")
            return False
        
        return True
    
    def enhance_config_with_examples(self, config: Dict[str, Any], example_pages: List[str]) -> Dict[str, Any]:
        """
        Enhance extraction config with multiple example pages
        
        Args:
            config: Base extraction config
            example_pages: List of HTML content from example pages
            
        Returns:
            Enhanced configuration
        """
        if not self.client or len(example_pages) < 2:
            return config
        
        # Analyze multiple pages to improve selectors
        enhanced_selectors = {}
        
        for field in config['selectors'].keys():
            field_selectors = self._analyze_field_across_pages(field, example_pages)
            if field_selectors:
                enhanced_selectors[field] = field_selectors
        
        if enhanced_selectors:
            config['enhanced_selectors'] = enhanced_selectors
            config['multi_page_analysis'] = True
        
        return config
    
    def _analyze_field_across_pages(self, field: str, pages: List[str]) -> Dict[str, Any]:
        """
        Analyze a specific field across multiple pages
        
        Args:
            field: Field name to analyze
            pages: List of HTML content
            
        Returns:
            Analysis results for the field
        """
        if len(pages) < 2:
            return {}
        
        # Create a focused prompt for this field
        prompt = f"""
Analyze these {len(pages)} HTML pages and find the most reliable CSS selector for extracting the '{field}' field.

Pages:
"""
        
        for i, page in enumerate(pages[:3]):  # Limit to 3 pages for analysis
            processed = self._preprocess_html(page, max_length=3000)
            prompt += f"\nPage {i+1}:\n{processed}\n"
        
        prompt += f"""
Find the most consistent and reliable CSS selector for '{field}' across all pages.
Return a JSON object with:
{{
    "primary_selector": "best.css.selector",
    "confidence": 0.95,
    "alternatives": ["alt1", "alt2"],
    "reasoning": "Why this selector is most reliable"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a web scraping expert analyzing HTML structure consistency."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result = self._parse_llm_response(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze field '{field}' across pages: {e}")
            return {} 