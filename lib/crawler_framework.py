"""
Intelligent Crawler Framework
Main orchestrator for the two-phase crawling approach
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import logging

from .llm_extractor import LLMExtractor
from .rule_parser import RuleParser
from .config_manager import ConfigManager
from .utils import HTMLProcessor, TextCleaner

logger = logging.getLogger(__name__)

class IntelligentCrawler:
    """
    Main intelligent crawler framework
    Implements the two-phase approach: LLM bootstrap + scalable rule-based parsing
    """
    
    def __init__(self, api_key: Optional[str] = None, config_dir: str = "lib/configs"):
        self.llm_extractor = LLMExtractor(api_key)
        self.config_manager = ConfigManager(config_dir)
        self.rule_parser = None  # Will be initialized when config is loaded
        
        # Statistics tracking
        self.stats = {
            'phase1_calls': 0,
            'phase2_calls': 0,
            'configs_created': 0,
            'pages_crawled': 0,
            'total_extractions': 0
        }
    
    async def bootstrap_extraction_config(self, example_urls: List[str], 
                                        target_fields: List[str] = None,
                                        config_name: str = None,
                                        description: str = "",
                                        domain: str = "",
                                        tags: List[str] = None) -> str:
        """
        Phase 1: Bootstrap extraction config using LLM analysis
        
        Args:
            example_urls: List of example URLs to analyze
            target_fields: Fields to extract (e.g., ['title', 'summary', 'date'])
            config_name: Name for the configuration
            description: Configuration description
            domain: Target domain/website
            tags: List of tags for categorization
            
        Returns:
            Configuration name
        """
        if not example_urls:
            raise ValueError("At least one example URL is required")
        
        logger.info(f"Starting Phase 1: Bootstrap extraction config from {len(example_urls)} example URLs")
        
        # Initialize rule parser for fetching example pages
        temp_parser = RuleParser()
        
        # Fetch example pages
        example_pages = []
        for url in example_urls:
            try:
                result = temp_parser.crawl_page(url)
                if result.get('error'):
                    logger.warning(f"Failed to fetch {url}: {result['error']}")
                    continue
                
                # Get HTML content
                html_content = result.get('response_metadata', {}).get('raw_content', '')
                if html_content:
                    example_pages.append(html_content)
                    logger.info(f"Successfully fetched example page: {url}")
                
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
        
        if not example_pages:
            raise ValueError("No example pages could be fetched")
        
        # Use LLM to analyze page structure
        logger.info("Analyzing page structure with LLM...")
        
        # Use the first page for initial analysis
        config = self.llm_extractor.analyze_page_structure(
            example_pages[0], 
            target_fields
        )
        
        # Enhance config with multiple examples if available
        if len(example_pages) > 1:
            logger.info("Enhancing config with multiple examples...")
            config = self.llm_extractor.enhance_config_with_examples(
                config, 
                example_pages[1:]  # Use remaining pages for enhancement
            )
        
        # Generate config name if not provided
        if not config_name:
            domain_part = domain.replace('.', '_') if domain else "unknown"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            config_name = f"{domain_part}_config_{timestamp}"
        
        # Save configuration
        config_path = self.config_manager.save_config(
            config=config,
            name=config_name,
            description=description,
            domain=domain,
            tags=tags
        )
        
        # Initialize rule parser with the new config
        self.rule_parser = RuleParser(config)
        
        # Update statistics
        self.stats['phase1_calls'] += 1
        self.stats['configs_created'] += 1
        
        logger.info(f"Phase 1 completed. Configuration saved: {config_name}")
        logger.info(f"Extraction config includes {len(config.get('selectors', {}))} fields")
        
        return config_name
    
    def load_existing_config(self, config_name: str) -> bool:
        """
        Load an existing extraction configuration
        
        Args:
            config_name: Name of the configuration to load
            
        Returns:
            True if loaded successfully
        """
        try:
            config = self.config_manager.load_config(config_name)
            self.rule_parser = RuleParser(config)
            
            logger.info(f"Loaded existing configuration: {config_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration '{config_name}': {e}")
            return False
    
    def crawl_single_page(self, url: str) -> Dict[str, Any]:
        """
        Crawl a single page using the loaded configuration
        
        Args:
            url: URL to crawl
            
        Returns:
            Extracted data dictionary
        """
        if not self.rule_parser:
            raise ValueError("No extraction configuration loaded. Run bootstrap_extraction_config first or load_existing_config.")
        
        logger.info(f"Crawling single page: {url}")
        
        result = self.rule_parser.crawl_page(url)
        
        # Update statistics
        self.stats['phase2_calls'] += 1
        self.stats['pages_crawled'] += 1
        if result.get('extracted_fields'):
            self.stats['total_extractions'] += len(result['extracted_fields'])
        
        return result
    
    def crawl_multiple_pages(self, urls: List[str], max_workers: int = 5) -> List[Dict[str, Any]]:
        """
        Crawl multiple pages using the loaded configuration
        
        Args:
            urls: List of URLs to crawl
            max_workers: Maximum concurrent workers
            
        Returns:
            List of extracted data dictionaries
        """
        if not self.rule_parser:
            raise ValueError("No extraction configuration loaded. Run bootstrap_extraction_config first or load_existing_config.")
        
        logger.info(f"Starting Phase 2: Crawling {len(urls)} pages with rule-based parser")
        
        results = self.rule_parser.crawl_multiple_pages(urls, max_workers)
        
        # Update statistics
        self.stats['phase2_calls'] += 1
        self.stats['pages_crawled'] += len(urls)
        for result in results:
            if result.get('extracted_fields'):
                self.stats['total_extractions'] += len(result['extracted_fields'])
        
        logger.info(f"Phase 2 completed. Crawled {len(urls)} pages")
        
        return results
    
    async def full_crawling_workflow(self, example_urls: List[str], 
                                   target_urls: List[str],
                                   target_fields: List[str] = None,
                                   config_name: str = None,
                                   description: str = "",
                                   domain: str = "",
                                   tags: List[str] = None,
                                   max_workers: int = 5) -> Dict[str, Any]:
        """
        Complete workflow: Bootstrap config + Crawl target pages
        
        Args:
            example_urls: URLs to use for bootstrap analysis
            target_urls: URLs to crawl with generated config
            target_fields: Fields to extract
            config_name: Configuration name
            description: Configuration description
            domain: Target domain
            tags: Configuration tags
            max_workers: Maximum concurrent workers for crawling
            
        Returns:
            Complete workflow results
        """
        logger.info("Starting complete intelligent crawling workflow")
        logger.info(f"Phase 1: {len(example_urls)} example URLs")
        logger.info(f"Phase 2: {len(target_urls)} target URLs")
        
        # Phase 1: Bootstrap extraction config
        config_name = await self.bootstrap_extraction_config(
            example_urls=example_urls,
            target_fields=target_fields,
            config_name=config_name,
            description=description,
            domain=domain,
            tags=tags
        )
        
        # Phase 2: Crawl target pages
        results = self.crawl_multiple_pages(target_urls, max_workers)
        
        # Generate statistics
        stats = self.rule_parser.get_extraction_stats(results)
        
        workflow_results = {
            'config_name': config_name,
            'phase1_example_urls': example_urls,
            'phase2_target_urls': target_urls,
            'extraction_results': results,
            'statistics': stats,
            'workflow_metadata': {
                'started_at': datetime.now().isoformat(),
                'total_pages_processed': len(results),
                'successful_extractions': len([r for r in results if r.get('extracted_fields')]),
                'average_success_rate': stats.get('avg_extraction_success_rate', 0)
            }
        }
        
        logger.info("Complete workflow finished successfully")
        logger.info(f"Final statistics: {stats}")
        
        return workflow_results
    
    def save_results(self, results: List[Dict[str, Any]], 
                    output_path: Union[str, Path], 
                    format: str = 'json') -> str:
        """
        Save crawling results to file
        
        Args:
            results: List of extraction results
            output_path: Output file path
            format: Output format ('json' or 'csv')
            
        Returns:
            Output file path
        """
        if not self.rule_parser:
            raise ValueError("No rule parser initialized")
        
        return self.rule_parser.save_results(results, output_path, format)
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """
        Get overall workflow statistics
        
        Returns:
            Statistics dictionary
        """
        stats = self.stats.copy()
        
        # Add config statistics
        config_stats = self.config_manager.get_config_stats()
        stats['config_statistics'] = config_stats
        
        # Add current configuration info
        if self.rule_parser and self.rule_parser.config:
            stats['current_config'] = {
                'fields': list(self.rule_parser.config.get('selectors', {}).keys()),
                'confidence_scores': self.rule_parser.config.get('confidence_scores', {}),
                'has_fallbacks': bool(self.rule_parser.config.get('fallback_selectors'))
            }
        
        return stats
    
    def list_available_configs(self, domain: str = None, tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        List available extraction configurations
        
        Args:
            domain: Filter by domain
            tags: Filter by tags
            
        Returns:
            List of configuration information
        """
        return self.config_manager.list_configs(domain, tags)
    
    def export_configs(self, output_path: Union[str, Path], format: str = 'json'):
        """
        Export all configurations
        
        Args:
            output_path: Output file path
            format: Export format ('json' or 'zip')
        """
        self.config_manager.export_configs(output_path, format)
    
    def import_configs(self, import_path: Union[str, Path], format: str = 'json'):
        """
        Import configurations
        
        Args:
            import_path: Import file path
            format: Import format ('json' or 'zip')
        """
        self.config_manager.import_configs(import_path, format)
    
    def validate_extraction(self, extracted_data: Dict[str, Any], 
                          validation_rules: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate extracted data against rules
        
        Args:
            extracted_data: Extracted data dictionary
            validation_rules: Validation rules dictionary
            
        Returns:
            Validation results
        """
        if not self.rule_parser:
            raise ValueError("No rule parser initialized")
        
        return self.rule_parser.validate_extraction(extracted_data, validation_rules)
    
    def get_config_details(self, config_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a configuration
        
        Args:
            config_name: Configuration name
            
        Returns:
            Configuration details
        """
        try:
            config = self.config_manager.load_config(config_name)
            config_info = self.config_manager.metadata['configs'].get(config_name, {})
            
            return {
                'name': config_name,
                'config': config,
                'info': config_info,
                'field_count': len(config.get('selectors', {})),
                'has_fallbacks': bool(config.get('fallback_selectors')),
                'confidence_scores': config.get('confidence_scores', {}),
                'notes': config.get('notes', '')
            }
            
        except Exception as e:
            logger.error(f"Failed to get config details for '{config_name}': {e}")
            return {'error': str(e)}
    
    def update_config(self, config_name: str, new_config: Dict[str, Any], 
                     description: str = None) -> bool:
        """
        Update an existing configuration
        
        Args:
            config_name: Configuration name
            new_config: Updated configuration
            description: Updated description
            
        Returns:
            True if updated successfully
        """
        success = self.config_manager.update_config(config_name, new_config, description)
        
        if success and self.rule_parser:
            # Reload the updated config
            self.rule_parser.load_config(new_config)
        
        return success
    
    def delete_config(self, config_name: str) -> bool:
        """
        Delete a configuration
        
        Args:
            config_name: Configuration name
            
        Returns:
            True if deleted successfully
        """
        return self.config_manager.delete_config(config_name) 