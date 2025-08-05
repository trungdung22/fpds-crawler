#!/usr/bin/env python3
"""
Example usage of the Intelligent Web Crawling Framework
Demonstrates the two-phase approach with a real-world scenario
"""

import asyncio
import json
import os
from pathlib import Path
from lib import IntelligentCrawler

async def example_news_crawling():
    """
    Example: Crawling news articles from a hypothetical news site
    """
    print("🌐 Intelligent Web Crawling Framework Example")
    print("=" * 60)
    
    # Initialize the crawler
    crawler = IntelligentCrawler()
    
    # Example URLs (replace with real URLs for testing)
    example_urls = [
        "https://example-news.com/article1",
        "https://example-news.com/article2"
    ]
    
    target_urls = [
        "https://example-news.com/article3",
        "https://example-news.com/article4",
        "https://example-news.com/article5",
        # Add more URLs as needed
    ]
    
    try:
        print("\n📋 Phase 1: Bootstrap Extraction Config")
        print("-" * 40)
        
        # Bootstrap extraction configuration
        config_name = await crawler.bootstrap_extraction_config(
            example_urls=example_urls,
            target_fields=['title', 'summary', 'date', 'author', 'content', 'category'],
            config_name="example_news_articles",
            description="News article extraction configuration for example-news.com",
            domain="example-news.com",
            tags=['news', 'articles', 'content']
        )
        
        print(f"✅ Configuration created: {config_name}")
        
        print("\n🚀 Phase 2: Scalable Crawling")
        print("-" * 40)
        
        # Crawl target pages using the generated config
        results = crawler.crawl_multiple_pages(target_urls, max_workers=3)
        
        print(f"✅ Crawled {len(results)} pages")
        
        # Save results
        output_file = "example_news_results.json"
        crawler.save_results(results, output_file)
        print(f"✅ Results saved to: {output_file}")
        
        # Print statistics
        stats = crawler.get_workflow_statistics()
        print(f"\n📊 Statistics:")
        print(f"   Pages crawled: {stats['pages_crawled']}")
        print(f"   Total extractions: {stats['total_extractions']}")
        print(f"   Configs created: {stats['configs_created']}")
        
        # Show sample results
        if results:
            print(f"\n📄 Sample Results:")
            for i, result in enumerate(results[:2]):  # Show first 2 results
                print(f"\n   Result {i+1}:")
                print(f"   URL: {result.get('url', 'N/A')}")
                print(f"   Success rate: {result.get('extraction_metadata', {}).get('success_rate', 0):.2%}")
                
                fields = result.get('extracted_fields', {})
                for field, data in fields.items():
                    value = data.get('value', 'N/A')
                    if value and len(str(value)) > 50:
                        value = str(value)[:50] + "..."
                    print(f"   {field}: {value}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

async def example_complete_workflow():
    """
    Example: Complete workflow with both phases
    """
    print("\n🔄 Complete Workflow Example")
    print("=" * 60)
    
    crawler = IntelligentCrawler()
    
    # Example URLs
    example_urls = [
        "https://example-blog.com/post1",
        "https://example-blog.com/post2"
    ]
    
    target_urls = [
        "https://example-blog.com/post3",
        "https://example-blog.com/post4",
        "https://example-blog.com/post5",
        "https://example-blog.com/post6"
    ]
    
    try:
        # Run complete workflow
        workflow_results = await crawler.full_crawling_workflow(
            example_urls=example_urls,
            target_urls=target_urls,
            target_fields=['title', 'content', 'author', 'date', 'tags'],
            config_name="example_blog_posts",
            description="Blog post extraction for example-blog.com",
            domain="example-blog.com",
            tags=['blog', 'posts'],
            max_workers=3
        )
        
        print(f"✅ Workflow completed successfully!")
        print(f"📊 Final Statistics:")
        stats = workflow_results['statistics']
        print(f"   Total pages: {stats.get('total_pages', 0)}")
        print(f"   Successful pages: {stats.get('successful_pages', 0)}")
        print(f"   Success rate: {stats.get('page_success_rate', 0):.2%}")
        print(f"   Average extraction rate: {stats.get('avg_extraction_success_rate', 0):.2%}")
        
        # Save workflow results
        workflow_file = "workflow_results.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow_results, f, indent=2)
        print(f"✅ Workflow results saved to: {workflow_file}")
        
        return workflow_results
        
    except Exception as e:
        print(f"❌ Workflow error: {e}")
        return None

def example_config_management():
    """
    Example: Configuration management features
    """
    print("\n⚙️  Configuration Management Example")
    print("=" * 60)
    
    crawler = IntelligentCrawler()
    
    try:
        # List available configurations
        configs = crawler.list_available_configs()
        print(f"📋 Available configurations: {len(configs)}")
        
        for config in configs:
            print(f"   - {config['name']}: {config.get('description', 'No description')}")
            print(f"     Domain: {config.get('domain', 'N/A')}")
            print(f"     Fields: {len(config.get('fields', []))}")
            print(f"     Tags: {', '.join(config.get('tags', []))}")
        
        # Get config statistics
        stats = crawler.get_workflow_statistics()
        config_stats = stats.get('config_statistics', {})
        
        print(f"\n📊 Configuration Statistics:")
        print(f"   Total configs: {config_stats.get('total_configs', 0)}")
        print(f"   Domains: {', '.join(config_stats.get('domains', []))}")
        print(f"   Tags: {', '.join(config_stats.get('tags', []))}")
        
        # Export configurations
        export_file = "configs_export.json"
        crawler.export_configs(export_file)
        print(f"✅ Configurations exported to: {export_file}")
        
    except Exception as e:
        print(f"❌ Configuration management error: {e}")

def example_validation():
    """
    Example: Data validation features
    """
    print("\n✅ Data Validation Example")
    print("=" * 60)
    
    crawler = IntelligentCrawler()
    
    # Example validation rules
    validation_rules = {
        'title': {
            'required': True,
            'min_length': 10,
            'max_length': 200
        },
        'content': {
            'required': True,
            'min_length': 100
        },
        'date': {
            'required': True,
            'pattern': r'\d{4}-\d{2}-\d{2}'  # YYYY-MM-DD format
        },
        'email': {
            'pattern': r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
        }
    }
    
    # Example extracted data
    sample_data = {
        'url': 'https://example.com/article1',
        'extracted_fields': {
            'title': {
                'value': 'This is a sample article title',
                'confidence': 0.95
            },
            'content': {
                'value': 'This is the article content with more than 100 characters to meet the minimum length requirement.',
                'confidence': 0.88
            },
            'date': {
                'value': '2024-01-15',
                'confidence': 0.92
            },
            'email': {
                'value': 'author@example.com',
                'confidence': 0.85
            }
        }
    }
    
    try:
        # Validate the data
        validation_result = crawler.validate_extraction(sample_data, validation_rules)
        
        print(f"📋 Validation Results:")
        print(f"   Valid: {validation_result['valid']}")
        
        if validation_result['errors']:
            print(f"   Errors: {validation_result['errors']}")
        
        if validation_result['warnings']:
            print(f"   Warnings: {validation_result['warnings']}")
        
        if validation_result['valid']:
            print("   ✅ All validation rules passed!")
        
    except Exception as e:
        print(f"❌ Validation error: {e}")

async def main():
    """
    Main function to run all examples
    """
    print("🚀 Intelligent Web Crawling Framework Examples")
    print("=" * 60)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set")
        print("   Set your API key to run the LLM bootstrap examples:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        print()
        print("   For now, running configuration management examples only...")
        
        # Run examples that don't require LLM
        example_config_management()
        example_validation()
        return
    
    # Run all examples
    try:
        # Example 1: Basic news crawling
        await example_news_crawling()
        
        # Example 2: Complete workflow
        await example_complete_workflow()
        
        # Example 3: Configuration management
        example_config_management()
        
        # Example 4: Data validation
        example_validation()
        
        print("\n🎉 All examples completed successfully!")
        print("\n📁 Generated files:")
        print("   - example_news_results.json")
        print("   - workflow_results.json")
        print("   - configs_export.json")
        
    except Exception as e:
        print(f"❌ Example execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 