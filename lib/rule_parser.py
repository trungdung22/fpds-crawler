"""
Rule Parser Module
Phase 2: Scalable crawling with rule-based parsing using generated configs
"""

import re
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging

try:
    from bs4 import BeautifulSoup
    import requests
except ImportError:
    logger.error("BeautifulSoup and requests required for rule parsing")
    BeautifulSoup = None
    requests = None

logger = logging.getLogger(__name__)

class RuleParser:
    """
    Rule-based parser for scalable web crawling
    Uses generated extraction configs to parse pages efficiently
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.session = None
        self._setup_session()
    
    def _setup_session(self):
        """Setup requests session with proper headers"""
        if requests:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
    
    def load_config(self, config: Dict[str, Any]):
        """Load extraction configuration"""
        self.config = config
        logger.info(f"Loaded extraction config with {len(config.get('selectors', {}))} fields")
    
    def load_config_from_file(self, config_path: Union[str, Path]):
        """Load extraction configuration from JSON file"""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.load_config(config)
    
    def extract_from_html(self, html_content: str, url: str = None) -> Dict[str, Any]:
        """
        Extract data from HTML content using loaded config
        
        Args:
            html_content: Raw HTML content
            url: Source URL (for metadata)
            
        Returns:
            Extracted data dictionary
        """
        if not BeautifulSoup:
            raise ImportError("BeautifulSoup is required for HTML parsing")
        
        if not self.config.get('selectors'):
            raise ValueError("No extraction config loaded")
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract data
        extracted_data = {
            'url': url,
            'extracted_fields': {},
            'extraction_metadata': {
                'config_used': list(self.config.get('selectors', {}).keys()),
                'success_rate': 0,
                'errors': []
            }
        }
        
        selectors = self.config.get('selectors', {})
        fallback_selectors = self.config.get('fallback_selectors', {})
        confidence_scores = self.config.get('confidence_scores', {})
        
        successful_extractions = 0
        total_fields = len(selectors)
        
        for field, selector_code in selectors.items():
            try:
                # Extract using primary selector
                value = self._execute_selector(soup, selector_code, field)
                
                # If primary selector fails, try fallback selectors
                if not value and field in fallback_selectors:
                    value = self._try_fallback_selectors(soup, fallback_selectors[field], field)
                
                extracted_data['extracted_fields'][field] = {
                    'value': value,
                    'confidence': confidence_scores.get(field, 0.5),
                    'extraction_method': 'primary' if value else 'fallback'
                }
                
                if value:
                    successful_extractions += 1
                
            except Exception as e:
                error_msg = f"Failed to extract {field}: {str(e)}"
                logger.warning(error_msg)
                extracted_data['extraction_metadata']['errors'].append(error_msg)
                
                extracted_data['extracted_fields'][field] = {
                    'value': None,
                    'confidence': 0.0,
                    'extraction_method': 'failed',
                    'error': str(e)
                }
        
        # Calculate success rate
        if total_fields > 0:
            extracted_data['extraction_metadata']['success_rate'] = successful_extractions / total_fields
        
        return extracted_data
    
    def _execute_selector(self, soup: BeautifulSoup, selector_code: str, field: str) -> Optional[str]:
        """
        Execute a selector code string on BeautifulSoup object
        
        Args:
            soup: BeautifulSoup object
            selector_code: Selector code string (e.g., "soup.select_one('h1.title').text.strip()")
            field: Field name for error reporting
            
        Returns:
            Extracted value or None
        """
        try:
            # Create a safe execution environment
            safe_dict = {
                'soup': soup,
                're': re,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict
            }
            
            # Execute the selector code
            result = eval(selector_code, {"__builtins__": {}}, safe_dict)
            
            # Clean and validate result
            if result is not None:
                if isinstance(result, str):
                    result = result.strip()
                    return result if result else None
                else:
                    return str(result).strip()
            
            return None
            
        except Exception as e:
            logger.debug(f"Selector execution failed for {field}: {e}")
            return None
    
    def _try_fallback_selectors(self, soup: BeautifulSoup, fallback_selectors: List[str], field: str) -> Optional[str]:
        """
        Try fallback selectors if primary selector fails
        
        Args:
            soup: BeautifulSoup object
            fallback_selectors: List of fallback CSS selectors
            field: Field name for error reporting
            
        Returns:
            Extracted value or None
        """
        for selector in fallback_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    value = element.get_text(strip=True)
                    if value:
                        logger.debug(f"Fallback selector '{selector}' succeeded for {field}")
                        return value
            except Exception as e:
                logger.debug(f"Fallback selector '{selector}' failed for {field}: {e}")
                continue
        
        return None
    
    def crawl_page(self, url: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Crawl a single page and extract data
        
        Args:
            url: URL to crawl
            timeout: Request timeout in seconds
            
        Returns:
            Extracted data dictionary
        """
        if not requests or not self.session:
            raise ImportError("Requests is required for web crawling")
        
        try:
            logger.info(f"Crawling page: {url}")
            
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            # Extract data
            extracted_data = self.extract_from_html(response.text, url)
            
            # Add response metadata
            extracted_data['response_metadata'] = {
                'status_code': response.status_code,
                'content_length': len(response.text),
                'content_type': response.headers.get('content-type', ''),
                'encoding': response.encoding
            }
            
            return extracted_data
            
        except requests.RequestException as e:
            logger.error(f"Failed to crawl {url}: {e}")
            return {
                'url': url,
                'error': str(e),
                'extracted_fields': {},
                'extraction_metadata': {
                    'success_rate': 0,
                    'errors': [f"Request failed: {e}"]
                }
            }
    
    def crawl_multiple_pages(self, urls: List[str], max_workers: int = 5, timeout: int = 30) -> List[Dict[str, Any]]:
        """
        Crawl multiple pages concurrently
        
        Args:
            urls: List of URLs to crawl
            max_workers: Maximum concurrent workers
            timeout: Request timeout in seconds
            
        Returns:
            List of extracted data dictionaries
        """
        import concurrent.futures
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all crawl tasks
            future_to_url = {
                executor.submit(self.crawl_page, url, timeout): url 
                for url in urls
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Completed crawling {url}")
                except Exception as e:
                    logger.error(f"Exception occurred while crawling {url}: {e}")
                    results.append({
                        'url': url,
                        'error': str(e),
                        'extracted_fields': {},
                        'extraction_metadata': {
                            'success_rate': 0,
                            'errors': [f"Exception: {e}"]
                        }
                    })
        
        return results
    
    def validate_extraction(self, extracted_data: Dict[str, Any], validation_rules: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate extracted data against rules
        
        Args:
            extracted_data: Extracted data dictionary
            validation_rules: Validation rules dictionary
            
        Returns:
            Validation results
        """
        if not validation_rules:
            return {'valid': True, 'errors': []}
        
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        fields = extracted_data.get('extracted_fields', {})
        
        for field, rules in validation_rules.items():
            if field not in fields:
                validation_results['errors'].append(f"Required field '{field}' not found")
                validation_results['valid'] = False
                continue
            
            field_data = fields[field]
            value = field_data.get('value')
            
            # Check required fields
            if rules.get('required', False) and not value:
                validation_results['errors'].append(f"Required field '{field}' is empty")
                validation_results['valid'] = False
            
            # Check minimum length
            if 'min_length' in rules and value and len(value) < rules['min_length']:
                validation_results['warnings'].append(f"Field '{field}' is shorter than minimum length")
            
            # Check maximum length
            if 'max_length' in rules and value and len(value) > rules['max_length']:
                validation_results['warnings'].append(f"Field '{field}' is longer than maximum length")
            
            # Check pattern matching
            if 'pattern' in rules and value:
                if not re.search(rules['pattern'], value):
                    validation_results['errors'].append(f"Field '{field}' doesn't match required pattern")
                    validation_results['valid'] = False
        
        return validation_results
    
    def save_results(self, results: List[Dict[str, Any]], output_path: Union[str, Path], format: str = 'json'):
        """
        Save extraction results to file
        
        Args:
            results: List of extraction results
            output_path: Output file path
            format: Output format ('json' or 'csv')
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        
        elif format.lower() == 'csv':
            import csv
            
            # Flatten results for CSV
            flattened_results = []
            for result in results:
                flat_row = {
                    'url': result.get('url', ''),
                    'success_rate': result.get('extraction_metadata', {}).get('success_rate', 0)
                }
                
                # Add extracted fields
                for field, field_data in result.get('extracted_fields', {}).items():
                    flat_row[field] = field_data.get('value', '')
                    flat_row[f'{field}_confidence'] = field_data.get('confidence', 0)
                
                flattened_results.append(flat_row)
            
            if flattened_results:
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=flattened_results[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened_results)
        
        logger.info(f"Results saved to: {output_path}")
    
    def get_extraction_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate statistics from extraction results
        
        Args:
            results: List of extraction results
            
        Returns:
            Statistics dictionary
        """
        if not results:
            return {}
        
        total_pages = len(results)
        successful_pages = sum(1 for r in results if r.get('extraction_metadata', {}).get('success_rate', 0) > 0)
        
        # Calculate average success rate
        success_rates = [r.get('extraction_metadata', {}).get('success_rate', 0) for r in results]
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        
        # Count errors
        total_errors = sum(len(r.get('extraction_metadata', {}).get('errors', [])) for r in results)
        
        # Field extraction statistics
        field_stats = {}
        all_fields = set()
        
        for result in results:
            fields = result.get('extracted_fields', {})
            all_fields.update(fields.keys())
            
            for field, field_data in fields.items():
                if field not in field_stats:
                    field_stats[field] = {'successful': 0, 'total': 0}
                
                field_stats[field]['total'] += 1
                if field_data.get('value'):
                    field_stats[field]['successful'] += 1
        
        # Calculate field success rates
        for field in field_stats:
            stats = field_stats[field]
            stats['success_rate'] = stats['successful'] / stats['total'] if stats['total'] > 0 else 0
        
        return {
            'total_pages': total_pages,
            'successful_pages': successful_pages,
            'page_success_rate': successful_pages / total_pages if total_pages > 0 else 0,
            'avg_extraction_success_rate': avg_success_rate,
            'total_errors': total_errors,
            'field_statistics': field_stats,
            'fields_extracted': list(all_fields)
        } 