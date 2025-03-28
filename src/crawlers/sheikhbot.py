"""
SheikhBot - Main crawler class that orchestrates specialized crawlers
"""

import os
import time
import yaml
import json
from typing import List, Dict, Any, Optional, Union
import logging

from ..utils.config import load_config
from ..utils.url import normalize_url, is_valid_url, get_domain
from ..utils.logger import setup_logger
from ..utils.indexnow import IndexNowClient
from ..utils.sitemap import SitemapGenerator
from ..storage import FileStorage, MongoDBStorage, IndexBuilder

from .base_crawler import BaseCrawler
from .desktop_crawler import DesktopCrawler
from .mobile_crawler import MobileCrawler
from .image_crawler import ImageCrawler


class SheikhBot:
    """Main SheikhBot class that orchestrates the crawling process."""

    def __init__(self, config_file: str = "config.yml"):
        """
        Initialize the SheikhBot crawler.
        
        Args:
            config_file (str): Path to the configuration file
        """
        self.config = load_config(config_file)
        self.logger = setup_logger(
            name="sheikhbot",
            level=getattr(logging, self.config["logging"]["level"]),
            log_file=self.config["logging"]["file"]
        )
        
        self.logger.info(f"Initializing SheikhBot v{self.config['general']['version']}")
        
        # Initialize storage
        self._init_storage()
        
        # Initialize specialized crawlers
        self.crawlers = self._init_crawlers()
        
        # Initialize index builder if enabled
        if self.config.get("index_settings", {}).get("build_index", False):
            self.index_builder = IndexBuilder(self.config)
        
        # Initialize IndexNow client if enabled
        self.indexnow_client = None
        if "indexnow" in self.config and self.config["indexnow"]["enabled"]:
            self._init_indexnow()
        
        self.sitemap_generator = SitemapGenerator(self.config)
        
        self.logger.info("SheikhBot initialized successfully")
    
    def _init_indexnow(self):
        """Initialize the IndexNow client for instant search engine notification."""
        try:
            indexnow_config = self.config["indexnow"]
            
            if not indexnow_config["api_key"]:
                self.logger.warning("IndexNow enabled but no API key provided")
                return
                
            self.logger.info(f"Initializing IndexNow client with API key: {indexnow_config['api_key'][:8]}...")
            
            self.indexnow_client = IndexNowClient(
                api_key=indexnow_config["api_key"],
                key_location=indexnow_config["key_location"] if indexnow_config["key_location"] else None
            )
            
            # Generate key file if enabled
            if indexnow_config["generate_key_file"]:
                output_dir = self.config["export_settings"]["output_directory"]
                if self.indexnow_client.generate_key_file(output_dir):
                    self.logger.info(f"IndexNow key file generated in {output_dir}")
            
            self.logger.info("IndexNow client initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing IndexNow client: {str(e)}")
            self.indexnow_client = None

    def _init_storage(self) -> None:
        """Initialize the appropriate storage backend based on configuration."""
        storage_type = self.config["storage"]["type"]
        self.logger.info(f"Initializing {storage_type} storage")
        
        if storage_type == "file":
            self.storage = FileStorage(self.config)
        elif storage_type == "mongodb":
            self.storage = MongoDBStorage(self.config)
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
    
    def _init_crawlers(self) -> Dict[str, BaseCrawler]:
        """Initialize all the specialized crawlers based on configuration."""
        crawlers = {}
        
        # Initialize desktop crawler if enabled
        if self.config["specialized_crawlers"]["desktop"]["enabled"]:
            crawlers["desktop"] = DesktopCrawler(self.config)
            self.logger.info("Desktop crawler initialized")
        
        # Initialize mobile crawler if enabled
        if self.config["specialized_crawlers"]["mobile"]["enabled"]:
            crawlers["mobile"] = MobileCrawler(self.config)
            self.logger.info("Mobile crawler initialized")
        
        # Initialize image crawler if enabled
        if self.config["specialized_crawlers"].get("images", {}).get("enabled", False):
            crawlers["images"] = ImageCrawler(self.config)
            self.logger.info("Image crawler initialized")
        
        return crawlers
    
    def submit_urls_to_indexnow(self, urls):
        """
        Submit URLs to search engines using IndexNow protocol.
        
        Args:
            urls (List[str]): URLs to submit to search engines
        """
        if not self.indexnow_client or not urls:
            return
            
        try:
            indexnow_config = self.config["indexnow"]
            search_engines = indexnow_config["search_engines"]
            
            # Group URLs by domain
            urls_by_domain = {}
            for url in urls:
                domain = get_domain(url)
                if domain not in urls_by_domain:
                    urls_by_domain[domain] = []
                urls_by_domain[domain].append(url)
            
            submitted_count = 0
            
            # Submit URLs for each domain
            for domain, domain_urls in urls_by_domain.items():
                self.logger.info(f"Submitting {len(domain_urls)} URLs for domain {domain} to IndexNow")
                
                for search_engine in search_engines:
                    if indexnow_config["bulk_submit"] and len(domain_urls) > 1:
                        # Submit URLs in bulk
                        success, message = self.indexnow_client.submit_urls_bulk(
                            domain_urls, 
                            search_engine=search_engine
                        )
                        
                        if success:
                            submitted_count += len(domain_urls)
                            self.logger.info(f"Successfully submitted {len(domain_urls)} URLs to {search_engine}")
                        else:
                            self.logger.error(f"Failed to submit URLs to {search_engine}: {message}")
                    else:
                        # Submit URLs individually
                        for url in domain_urls:
                            success, message = self.indexnow_client.submit_url(
                                url, 
                                search_engine=search_engine
                            )
                            
                            if success:
                                submitted_count += 1
                                self.logger.info(f"Successfully submitted {url} to {search_engine}")
                            else:
                                self.logger.error(f"Failed to submit {url} to {search_engine}: {message}")
            
            return submitted_count
        except Exception as e:
            self.logger.error(f"Error submitting URLs to IndexNow: {str(e)}")
            return 0
    
    def crawl(self, urls: Union[str, List[str]] = None) -> None:
        """
        Start the crawling process.
        
        Args:
            urls (Union[str, List[str]], optional): URL or list of URLs to crawl.
                If None, uses the start_urls from config.
        """
        if urls is None:
            urls = self.config["start_urls"]
        elif isinstance(urls, str):
            urls = [urls]
        
        self.logger.info(f"Starting crawl with {len(urls)} seed URLs")
        
        # Track crawl statistics
        stats = {
            "start_time": time.time(),
            "urls_crawled": 0,
            "pages_indexed": 0,
            "errors": 0
        }
        
        # For collecting URLs to submit to IndexNow
        indexnow_urls = []
        
        # Crawl each URL with each enabled crawler
        for url in urls:
            if not is_valid_url(url):
                self.logger.warning(f"Invalid URL: {url}, skipping")
                continue
                
            normalized_url = normalize_url(url)
            domain = get_domain(normalized_url)
            
            self.logger.info(f"Crawling {normalized_url} ({domain})")
            
            # Check if domain is allowed if allowed_domains is not empty
            if self.config["allowed_domains"] and domain not in self.config["allowed_domains"]:
                self.logger.warning(f"Domain {domain} not in allowed domains, skipping")
                continue
            
            # Use each enabled crawler for this URL
            for crawler_type, crawler in self.crawlers.items():
                try:
                    self.logger.info(f"Using {crawler_type} crawler for {normalized_url}")
                    crawl_results = crawler.crawl(normalized_url)
                    
                    # Store the results
                    self.storage.store(crawl_results, crawler_type)
                    
                    # Build index if enabled
                    if self.config["index_settings"]["build_index"]:
                        self.index_builder.add_to_index(crawl_results)
                    
                    # Collect URLs for IndexNow submission if enabled
                    if "indexnow" in self.config and self.config["indexnow"]["enabled"] and self.config["indexnow"]["auto_submit"]:
                        if self.indexnow_client:
                            if isinstance(crawl_results, list):
                                for result in crawl_results:
                                    if "url" in result and result["url"]:
                                        indexnow_urls.append(result["url"])
                            elif isinstance(crawl_results, dict) and "url" in crawl_results and crawl_results["url"]:
                                indexnow_urls.append(crawl_results["url"])
                    
                    stats["urls_crawled"] += 1
                    stats["pages_indexed"] += len(crawl_results) if isinstance(crawl_results, list) else 1
                    
                except Exception as e:
                    self.logger.error(f"Error crawling {normalized_url} with {crawler_type} crawler: {str(e)}")
                    stats["errors"] += 1
        
        # Submit collected URLs to IndexNow if enabled
        if indexnow_urls and "indexnow" in self.config and self.config["indexnow"]["enabled"] and self.config["indexnow"]["auto_submit"]:
            submitted_count = self.submit_urls_to_indexnow(indexnow_urls)
            stats["urls_submitted_to_indexnow"] = submitted_count
        
        # Generate sitemaps for crawled domains
        if self.config["sitemap_settings"]["enabled"]:
            try:
                domain_urls = {}
                for result in crawl_results:
                    domain = get_domain(result["url"])
                    if domain not in domain_urls:
                        domain_urls[domain] = []
                    domain_urls[domain].append(result)
                
                sitemaps = []
                for domain, urls in domain_urls.items():
                    sitemap_path = self.sitemap_generator.generate_sitemap(urls, domain)
                    sitemaps.append(sitemap_path)
                
                # Create sitemap index if multiple sitemaps
                if len(sitemaps) > 1:
                    index_path = self.sitemap_generator.create_sitemap_index(sitemaps)
                    self.logger.info(f"Created sitemap index at {index_path}")
                
                # Optionally ping search engines
                if self.config["sitemap_settings"]["ping_search_engines"]:
                    self._ping_search_engines(sitemaps)
            
            except Exception as e:
                self.logger.error(f"Error generating sitemaps: {str(e)}")
        
        # Calculate crawl duration
        stats["duration"] = time.time() - stats["start_time"]
        
        self.logger.info(f"Crawl completed in {stats['duration']:.2f} seconds")
        self.logger.info(f"URLs crawled: {stats['urls_crawled']}")
        self.logger.info(f"Pages indexed: {stats['pages_indexed']}")
        if "urls_submitted_to_indexnow" in stats:
            self.logger.info(f"URLs submitted to IndexNow: {stats['urls_submitted_to_indexnow']}")
        self.logger.info(f"Errors: {stats['errors']}")
        
        # Save crawl stats
        self.storage.store_stats(stats)
        
        # Build GitHub Pages if enabled
        if self.config["github_pages"]["enabled"]:
            self._build_github_pages()
    
    def export_data(self, output_file: str = None) -> None:
        """
        Export the crawled data to a file.
        
        Args:
            output_file (str, optional): Path to output file.
                If None, uses the output_directory and filename_template from config.
        """
        if output_file is None:
            timestamp = int(time.time())
            output_file = os.path.join(
                self.config["export_settings"]["output_directory"],
                f"export_{timestamp}.{self.config['export_settings']['format']}"
            )
        
        self.logger.info(f"Exporting data to {output_file}")
        
        try:
            # Get all data from storage
            all_data = {}
            for crawler_type in self.crawlers.keys():
                crawler_data = self.storage.get_all_data(crawler_type)
                if crawler_data:
                    all_data[crawler_type] = crawler_data
            
            # Create export directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Write data to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Data exported to {output_file}")
        except Exception as e:
            self.logger.error(f"Error exporting data: {str(e)}")
    
    def _build_github_pages(self) -> None:
        """Build GitHub Pages site with crawl results."""
        self.logger.info("Building GitHub Pages site")
        
        try:
            # Get GitHub Pages config
            gh_pages_config = self.config["github_pages"]
            output_dir = gh_pages_config["output_directory"]
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Get template directory
            template_dir = gh_pages_config.get("template_directory", "templates")
            default_template = gh_pages_config.get("default_template", "index.html")
            template_path = os.path.join(template_dir, default_template)
            
            # Check if template exists
            if not os.path.exists(template_path):
                self.logger.warning(f"Template {template_path} not found, using default HTML")
                html_template = """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>{{site_title}}</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                        .container { max-width: 1200px; margin: 0 auto; }
                        .result { border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 5px; }
                        .title { font-size: 1.2em; font-weight: bold; margin-bottom: 5px; }
                        .url { color: green; margin-bottom: 10px; }
                        .snippet { color: #333; }
                        .meta { color: #666; font-size: 0.8em; margin-top: 10px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>{{site_title}}</h1>
                        <p>{{site_description}}</p>
                        <div id="results">
                            <!-- Results will be inserted here -->
                        </div>
                    </div>
                    <script>
                    // JavaScript to load and display results
                    document.addEventListener('DOMContentLoaded', function() {
                        fetch('search_index.json')
                            .then(response => response.json())
                            .then(data => {
                                const resultsContainer = document.getElementById('results');
                                
                                if (data.documents && data.documents.length > 0) {
                                    data.documents.forEach(doc => {
                                        const resultDiv = document.createElement('div');
                                        resultDiv.className = 'result';
                                        
                                        resultDiv.innerHTML = `
                                            <div class="title">${doc.title}</div>
                                            <div class="url">${doc.url}</div>
                                            <div class="snippet">${doc.snippet || ''}</div>
                                            <div class="meta">Type: ${doc.type} | Date: ${doc.date || 'Unknown'}</div>
                                        `;
                                        
                                        resultsContainer.appendChild(resultDiv);
                                    });
                                } else {
                                    resultsContainer.innerHTML = '<p>No results found.</p>';
                                }
                            })
                            .catch(error => {
                                console.error('Error loading results:', error);
                                document.getElementById('results').innerHTML = '<p>Error loading results.</p>';
                            });
                    });
                    </script>
                </body>
                </html>
                """
            else:
                # Read template file
                with open(template_path, 'r', encoding='utf-8') as f:
                    html_template = f.read()
            
            # Replace template variables
            html_content = html_template.replace("{{site_title}}", gh_pages_config["site_title"])
            html_content = html_content.replace("{{site_description}}", gh_pages_config["site_description"])
            
            # Write index.html
            index_path = os.path.join(output_dir, "index.html")
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Create search index file for GitHub Pages
            if self.config["index_settings"]["build_index"]:
                # Get the path to the index file
                src_index_file = os.path.join(
                    self.config["index_settings"]["index_directory"],
                    self.config["index_settings"]["index_file"]
                )
                
                if os.path.exists(src_index_file):
                    # Copy index file to GitHub Pages directory
                    dst_index_file = os.path.join(output_dir, "search_index.json")
                    
                    # Read and write instead of shutil.copy to handle different encodings
                    with open(src_index_file, 'r', encoding='utf-8') as src:
                        with open(dst_index_file, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
                    
                    self.logger.info(f"Copied search index to {dst_index_file}")
                else:
                    self.logger.warning(f"Search index file {src_index_file} not found")
            
            self.logger.info(f"GitHub Pages site built successfully in {output_dir}")
            
        except KeyError as e:
            self.logger.error(f"Error building GitHub Pages site: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error building GitHub Pages site: {str(e)}")
    
    def clear_data(self) -> None:
        """Clear all crawled data."""
        self.logger.info("Clearing all crawled data")
        self.storage.clear()
        
        if hasattr(self, 'index_builder'):
            self.index_builder.clear_index()
        
        self.logger.info("All data cleared successfully")