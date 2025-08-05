# Intelligent Web Crawling Framework

A powerful, intelligent web crawling framework that implements a **two-phase approach**: LLM bootstrap extraction followed by scalable rule-based parsing. This framework enables efficient crawling of thousands of pages by learning the structure once and applying it repeatedly.

## 🌟 Key Features

### Phase 1: LLM Bootstrap Extraction
- **Intelligent Analysis**: Uses LLM to understand page structure
- **Automatic Config Generation**: Creates reusable extraction configurations
- **Multi-Page Learning**: Enhances configs with multiple example pages
- **Smart Selectors**: Generates robust CSS selectors with fallbacks

### Phase 2: Scalable Rule-Based Parsing
- **High Performance**: Crawls 1000+ pages efficiently using generated configs
- **Concurrent Processing**: Multi-threaded crawling with configurable workers
- **Robust Extraction**: Primary selectors with automatic fallback handling
- **Data Validation**: Built-in validation and error handling

### Framework Features
- **Configuration Management**: Save, load, and version extraction configs
- **Statistics & Analytics**: Comprehensive extraction statistics
- **Export/Import**: Share and backup configurations
- **Validation**: Data quality validation and error reporting

## 🚀 Quick Start

### Installation

```bash
# Install required dependencies
pip install openai beautifulsoup4 requests

# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

### Basic Usage

```python
from lib import IntelligentCrawler
import asyncio

async def main():
    # Initialize the crawler
    crawler = IntelligentCrawler()
    
    # Phase 1: Bootstrap extraction config from example pages
    config_name = await crawler.bootstrap_extraction_config(
        example_urls=[
            "https://example.com/article1",
            "https://example.com/article2"
        ],
        target_fields=['title', 'summary', 'date', 'author', 'content'],
        config_name="example_articles",
        description="Extraction config for example.com articles",
        domain="example.com",
        tags=['articles', 'news']
    )
    
    # Phase 2: Crawl target pages using the generated config
    target_urls = [
        "https://example.com/article3",
        "https://example.com/article4",
        # ... 1000+ more URLs
    ]
    
    results = crawler.crawl_multiple_pages(target_urls, max_workers=5)
    
    # Save results
    crawler.save_results(results, "extracted_data.json")
    
    # Print statistics
    stats = crawler.get_workflow_statistics()
    print(f"Crawled {stats['pages_crawled']} pages")
    print(f"Success rate: {stats.get('current_config', {}).get('avg_success_rate', 0):.2%}")

# Run the crawler
asyncio.run(main())
```

## 📚 Detailed Usage

### Phase 1: Bootstrap Extraction

The bootstrap phase uses LLM to analyze example pages and generate extraction configurations:

```python
# Bootstrap with multiple example pages for better accuracy
config_name = await crawler.bootstrap_extraction_config(
    example_urls=[
        "https://news-site.com/article1",
        "https://news-site.com/article2", 
        "https://news-site.com/article3"
    ],
    target_fields=['title', 'summary', 'date', 'author', 'content', 'tags'],
    config_name="news_articles",
    description="News article extraction configuration",
    domain="news-site.com",
    tags=['news', 'articles', 'content']
)
```

**Generated Config Example:**
```json
{
  "selectors": {
    "title": "soup.select_one('h1.article-title').text.strip()",
    "summary": "soup.select_one('div.article-summary').text.strip()",
    "date": "soup.select_one('span.publish-date').text.strip()",
    "author": "soup.select_one('span.author-name').text.strip()",
    "content": "soup.select_one('div.article-content').text.strip()"
  },
  "confidence_scores": {
    "title": 0.95,
    "summary": 0.88,
    "date": 0.92,
    "author": 0.85,
    "content": 0.90
  },
  "fallback_selectors": {
    "title": ["h1", "h2", ".title"],
    "summary": ["p:first-of-type", ".intro"],
    "date": [".date", ".timestamp", "time"],
    "author": [".author", ".byline"],
    "content": [".content", ".body", "article"]
  }
}
```

### Phase 2: Scalable Crawling

Once the config is generated, crawl thousands of pages efficiently:

```python
# Load existing config
crawler.load_existing_config("news_articles")

# Crawl single page
result = crawler.crawl_single_page("https://news-site.com/article100")

# Crawl multiple pages concurrently
urls = [f"https://news-site.com/article{i}" for i in range(1, 1001)]
results = crawler.crawl_multiple_pages(urls, max_workers=10)

# Save results
crawler.save_results(results, "news_data.json", format='json')
crawler.save_results(results, "news_data.csv", format='csv')
```

### Complete Workflow

Run both phases in a single workflow:

```python
# Complete workflow: Bootstrap + Crawl
workflow_results = await crawler.full_crawling_workflow(
    example_urls=["https://site.com/page1", "https://site.com/page2"],
    target_urls=["https://site.com/page3", "https://site.com/page4", ...],
    target_fields=['title', 'content', 'date'],
    config_name="site_pages",
    description="Complete site crawling",
    domain="site.com",
    max_workers=5
)

print(f"Workflow completed: {workflow_results['statistics']}")
```

## 🔧 Configuration Management

### List Available Configs

```python
# List all configurations
configs = crawler.list_available_configs()

# Filter by domain
news_configs = crawler.list_available_configs(domain="news-site.com")

# Filter by tags
article_configs = crawler.list_available_configs(tags=['articles'])
```

### Export/Import Configurations

```python
# Export all configurations
crawler.export_configs("configs_backup.json", format='json')
crawler.export_configs("configs_backup.zip", format='zip')

# Import configurations
crawler.import_configs("configs_backup.json", format='json')
```

### Update Configurations

```python
# Get config details
config_details = crawler.get_config_details("news_articles")

# Update configuration
new_config = {
    "selectors": {
        "title": "soup.select_one('h1.new-title').text.strip()",
        # ... other selectors
    },
    "confidence_scores": {...},
    "fallback_selectors": {...}
}

crawler.update_config("news_articles", new_config, "Updated news config")
```

## 📊 Statistics and Analytics

### Extraction Statistics

```python
# Get workflow statistics
stats = crawler.get_workflow_statistics()

print(f"Phase 1 calls: {stats['phase1_calls']}")
print(f"Phase 2 calls: {stats['phase2_calls']}")
print(f"Pages crawled: {stats['pages_crawled']}")
print(f"Total extractions: {stats['total_extractions']}")

# Config statistics
config_stats = stats['config_statistics']
print(f"Total configs: {config_stats['total_configs']}")
print(f"Domains: {config_stats['domains']}")
print(f"Fields: {config_stats['fields']}")
```

### Validation

```python
# Define validation rules
validation_rules = {
    'title': {'required': True, 'min_length': 10, 'max_length': 200},
    'content': {'required': True, 'min_length': 100},
    'date': {'required': True, 'pattern': r'\d{4}-\d{2}-\d{2}'}
}

# Validate extracted data
for result in results:
    validation = crawler.validate_extraction(result, validation_rules)
    if not validation['valid']:
        print(f"Validation failed: {validation['errors']}")
```

## 🎯 Use Cases

### News Article Crawling

```python
# Bootstrap news extraction
config_name = await crawler.bootstrap_extraction_config(
    example_urls=[
        "https://news-site.com/article1",
        "https://news-site.com/article2"
    ],
    target_fields=['title', 'summary', 'date', 'author', 'content', 'category'],
    domain="news-site.com",
    tags=['news', 'articles']
)

# Crawl thousands of articles
article_urls = get_article_urls_from_sitemap()  # Your URL collection logic
results = crawler.crawl_multiple_pages(article_urls, max_workers=10)
```

### E-commerce Product Crawling

```python
# Bootstrap product extraction
config_name = await crawler.bootstrap_extraction_config(
    example_urls=[
        "https://shop.com/product1",
        "https://shop.com/product2"
    ],
    target_fields=['title', 'price', 'description', 'rating', 'reviews', 'images'],
    domain="shop.com",
    tags=['ecommerce', 'products']
)

# Crawl product pages
product_urls = get_product_urls()  # Your URL collection logic
results = crawler.crawl_multiple_pages(product_urls, max_workers=5)
```

### Blog Post Crawling

```python
# Bootstrap blog extraction
config_name = await crawler.bootstrap_extraction_config(
    example_urls=[
        "https://blog.com/post1",
        "https://blog.com/post2"
    ],
    target_fields=['title', 'content', 'author', 'date', 'tags', 'comments'],
    domain="blog.com",
    tags=['blog', 'posts']
)

# Crawl blog posts
post_urls = get_blog_post_urls()  # Your URL collection logic
results = crawler.crawl_multiple_pages(post_urls, max_workers=8)
```

## 🔍 Advanced Features

### Custom Validation Rules

```python
# Define custom validation patterns
validation_rules = {
    'price': {
        'required': True,
        'pattern': r'\$\d+(?:\.\d{2})?',
        'min_length': 1
    },
    'email': {
        'pattern': r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
    },
    'phone': {
        'pattern': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    }
}
```

### Error Handling

```python
try:
    results = crawler.crawl_multiple_pages(urls, max_workers=5)
except Exception as e:
    print(f"Crawling failed: {e}")
    
    # Check individual results for errors
    for result in results:
        if result.get('error'):
            print(f"Error on {result['url']}: {result['error']}")
```

### Performance Optimization

```python
# Adjust workers based on target site
if domain == "fast-site.com":
    max_workers = 20
elif domain == "slow-site.com":
    max_workers = 3
else:
    max_workers = 10

results = crawler.crawl_multiple_pages(urls, max_workers=max_workers)
```

## 📁 File Structure

```
lib/
├── __init__.py              # Main package exports
├── crawler_framework.py     # Main orchestrator
├── llm_extractor.py         # Phase 1: LLM bootstrap
├── rule_parser.py           # Phase 2: Rule-based parsing
├── config_manager.py        # Configuration management
├── utils.py                 # HTML processing utilities
├── README.md               # This file
└── configs/                # Stored configurations
    ├── config_metadata.json
    └── *.json              # Individual config files
```

## 🔗 Dependencies

- **openai**: LLM integration for bootstrap extraction
- **beautifulsoup4**: HTML parsing for rule-based extraction
- **requests**: HTTP requests for web crawling
- **asyncio**: Asynchronous operations
- **pathlib**: File path handling
- **json**: Configuration serialization

## 📈 Performance

### Typical Performance Metrics

- **Phase 1 (Bootstrap)**: 30-60 seconds for 2-3 example pages
- **Phase 2 (Crawling)**: 100-1000 pages per minute (depending on site speed)
- **Memory Usage**: ~50-100MB for 1000 pages
- **Success Rate**: 85-95% with proper fallback selectors

### Optimization Tips

1. **Use multiple example pages** for better config generation
2. **Adjust max_workers** based on target site performance
3. **Implement rate limiting** for sensitive sites
4. **Use fallback selectors** for robust extraction
5. **Validate extracted data** to ensure quality

## 🤝 Contributing

This framework is designed to be extensible. Key areas for contribution:

- **Additional LLM providers** (Claude, Gemini, etc.)
- **Enhanced validation rules**
- **More export formats** (XML, YAML, etc.)
- **Advanced error handling**
- **Performance optimizations**

## 📄 License

This framework is part of the FPDS Crawler project and follows the same licensing terms. 