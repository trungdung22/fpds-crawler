"""
Utilities Module
Helper functions for HTML processing and text cleaning
"""

import re
import html
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

class HTMLProcessor:
    """
    HTML processing utilities for web crawling
    """
    
    @staticmethod
    def clean_html(html_content: str, remove_scripts: bool = True, remove_styles: bool = True) -> str:
        """
        Clean HTML content by removing unnecessary elements
        
        Args:
            html_content: Raw HTML content
            remove_scripts: Whether to remove script tags
            remove_styles: Whether to remove style tags
            
        Returns:
            Cleaned HTML content
        """
        if remove_scripts:
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        if remove_styles:
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove comments
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        
        # Remove excessive whitespace
        html_content = re.sub(r'\s+', ' ', html_content)
        
        return html_content.strip()
    
    @staticmethod
    def extract_text_from_html(html_content: str, preserve_structure: bool = False) -> str:
        """
        Extract clean text from HTML content
        
        Args:
            html_content: HTML content
            preserve_structure: Whether to preserve some structure (line breaks, etc.)
            
        Returns:
            Clean text content
        """
        # Clean HTML first
        clean_html = HTMLProcessor.clean_html(html_content)
        
        if preserve_structure:
            # Replace some tags with line breaks
            clean_html = re.sub(r'</(p|div|br|h[1-6])>', '\n', clean_html, flags=re.IGNORECASE)
            clean_html = re.sub(r'<(p|div|br|h[1-6])[^>]*>', '\n', clean_html, flags=re.IGNORECASE)
        
        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', '', clean_html)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple line breaks to double line breaks
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n +', '\n', text)  # Remove leading spaces after line breaks
        
        return text.strip()
    
    @staticmethod
    def extract_links(html_content: str, base_url: str = None) -> List[Dict[str, str]]:
        """
        Extract links from HTML content
        
        Args:
            html_content: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of link dictionaries with 'url' and 'text' keys
        """
        links = []
        
        # Find all anchor tags
        link_pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>'
        matches = re.findall(link_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for href, text in matches:
            # Clean the text
            text = HTMLProcessor.extract_text_from_html(text)
            
            # Resolve relative URLs
            if base_url and href:
                url = urljoin(base_url, href)
            else:
                url = href
            
            if url and text.strip():
                links.append({
                    'url': url,
                    'text': text.strip()
                })
        
        return links
    
    @staticmethod
    def extract_images(html_content: str, base_url: str = None) -> List[Dict[str, str]]:
        """
        Extract image information from HTML content
        
        Args:
            html_content: HTML content
            base_url: Base URL for resolving relative image URLs
            
        Returns:
            List of image dictionaries with 'src', 'alt', and 'title' keys
        """
        images = []
        
        # Find all img tags with their attributes
        img_pattern = r'<img([^>]*)>'
        matches = re.findall(img_pattern, html_content, re.IGNORECASE)
        
        for img_attrs in matches:
            # Extract src attribute
            src_match = re.search(r'src=["\']([^"\']*)["\']', img_attrs, re.IGNORECASE)
            if not src_match:
                continue
            
            src = src_match.group(1)
            
            # Extract alt and title attributes
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', img_attrs, re.IGNORECASE)
            title_match = re.search(r'title=["\']([^"\']*)["\']', img_attrs, re.IGNORECASE)
            
            alt = alt_match.group(1) if alt_match else ""
            title = title_match.group(1) if title_match else ""
            
            # Resolve relative URLs
            if base_url:
                url = urljoin(base_url, src)
            else:
                url = src
            
            images.append({
                'src': url,
                'alt': alt,
                'title': title
            })
        
        return images
    
    @staticmethod
    def extract_meta_tags(html_content: str) -> Dict[str, str]:
        """
        Extract meta tags from HTML content
        
        Args:
            html_content: HTML content
            
        Returns:
            Dictionary of meta tag name-value pairs
        """
        meta_tags = {}
        
        # Find all meta tags
        meta_pattern = r'<meta[^>]*name=["\']([^"\']*)["\'][^>]*content=["\']([^"\']*)["\'][^>]*>'
        matches = re.findall(meta_pattern, html_content, re.IGNORECASE)
        
        for name, content in matches:
            meta_tags[name.lower()] = content
        
        # Also extract property meta tags (Open Graph, etc.)
        property_pattern = r'<meta[^>]*property=["\']([^"\']*)["\'][^>]*content=["\']([^"\']*)["\'][^>]*>'
        property_matches = re.findall(property_pattern, html_content, re.IGNORECASE)
        
        for prop, content in property_matches:
            meta_tags[prop.lower()] = content
        
        return meta_tags
    
    @staticmethod
    def extract_title(html_content: str) -> Optional[str]:
        """
        Extract page title from HTML content
        
        Args:
            html_content: HTML content
            
        Returns:
            Page title or None
        """
        title_pattern = r'<title[^>]*>(.*?)</title>'
        match = re.search(title_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        if match:
            title = HTMLProcessor.extract_text_from_html(match.group(1))
            return title.strip() if title else None
        
        return None
    
    @staticmethod
    def extract_headings(html_content: str) -> List[Dict[str, str]]:
        """
        Extract headings from HTML content
        
        Args:
            html_content: HTML content
            
        Returns:
            List of heading dictionaries with 'level', 'text', and 'id' keys
        """
        headings = []
        
        # Find all heading tags (h1-h6)
        heading_pattern = r'<(h[1-6])[^>]*id=["\']([^"\']*)["\'][^>]*>(.*?)</\1>'
        matches = re.findall(heading_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for tag, heading_id, text in matches:
            level = int(tag[1])  # Extract number from h1, h2, etc.
            clean_text = HTMLProcessor.extract_text_from_html(text)
            
            if clean_text.strip():
                headings.append({
                    'level': level,
                    'text': clean_text.strip(),
                    'id': heading_id
                })
        
        return headings

class TextCleaner:
    """
    Text cleaning utilities for extracted content
    """
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalize whitespace in text
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        if not text:
            return ""
        
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def remove_special_characters(text: str, keep_newlines: bool = True) -> str:
        """
        Remove special characters from text
        
        Args:
            text: Input text
            keep_newlines: Whether to preserve newlines
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        if keep_newlines:
            # Keep alphanumeric, spaces, newlines, and common punctuation
            text = re.sub(r'[^\w\s\n.,!?;:()[\]{}"\'-]', '', text)
        else:
            # Keep alphanumeric, spaces, and common punctuation
            text = re.sub(r'[^\w\s.,!?;:()[\]{}"\'-]', '', text)
        
        return text
    
    @staticmethod
    def extract_dates(text: str) -> List[str]:
        """
        Extract date patterns from text
        
        Args:
            text: Input text
            
        Returns:
            List of found date strings
        """
        dates = []
        
        # Common date patterns
        patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY or M/D/YY
            r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',    # YYYY-MM-DD
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}',  # DD Month YYYY
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}'  # Month DD, YYYY
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))  # Remove duplicates
    
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """
        Extract email addresses from text
        
        Args:
            text: Input text
            
        Returns:
            List of email addresses
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return list(set(emails))  # Remove duplicates
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """
        Extract phone numbers from text
        
        Args:
            text: Input text
            
        Returns:
            List of phone numbers
        """
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890 or 123.456.7890
            r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',  # (123) 456-7890
            r'\b\d{3}\s\d{3}\s\d{4}\b',  # 123 456 7890
            r'\+\d{1,3}\s\d{3}\s\d{3}\s\d{4}\b'  # +1 123 456 7890
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)
        
        return list(set(phones))  # Remove duplicates
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """
        Extract URLs from text
        
        Args:
            text: Input text
            
        Returns:
            List of URLs
        """
        url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
        urls = re.findall(url_pattern, text)
        return list(set(urls))  # Remove duplicates
    
    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        """
        Extract numbers from text
        
        Args:
            text: Input text
            
        Returns:
            List of number strings
        """
        # Find integers and decimals
        number_pattern = r'\b\d+(?:\.\d+)?\b'
        numbers = re.findall(number_pattern, text)
        return numbers
    
    @staticmethod
    def extract_currency_amounts(text: str) -> List[str]:
        """
        Extract currency amounts from text
        
        Args:
            text: Input text
            
        Returns:
            List of currency amount strings
        """
        currency_patterns = [
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?',  # $1,234.56
            r'\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|dollars?)',  # 1,234.56 USD
            r'(?:USD|dollars?)\s*\d+(?:,\d{3})*(?:\.\d{2})?'  # USD 1,234.56
        ]
        
        amounts = []
        for pattern in currency_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
        
        return list(set(amounts))  # Remove duplicates
    
    @staticmethod
    def clean_text_for_analysis(text: str) -> str:
        """
        Clean text for analysis (remove noise, normalize)
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text suitable for analysis
        """
        if not text:
            return ""
        
        # Normalize whitespace
        text = TextCleaner.normalize_whitespace(text)
        
        # Remove excessive punctuation
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[.]{2,}', '.', text)
        
        # Remove common noise patterns
        text = re.sub(r'\[.*?\]', '', text)  # Remove bracketed content
        text = re.sub(r'\([^)]*\)', '', text)  # Remove parenthetical content
        
        # Normalize quotes
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r'[''']', "'", text)
        
        return text.strip()
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 1000, add_ellipsis: bool = True) -> str:
        """
        Truncate text to specified length
        
        Args:
            text: Input text
            max_length: Maximum length
            add_ellipsis: Whether to add "..." at the end
            
        Returns:
            Truncated text
        """
        if not text or len(text) <= max_length:
            return text
        
        truncated = text[:max_length]
        
        # Try to break at word boundary
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # If we have a reasonable word break
            truncated = truncated[:last_space]
        
        if add_ellipsis:
            truncated += "..."
        
        return truncated 