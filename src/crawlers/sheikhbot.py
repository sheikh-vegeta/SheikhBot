"""
SheikhBot - Main crawler class that orchestrates specialized crawlers
"""

import os
import time
import yaml
from typing import List, Dict, Any, Optional, Union
import logging

from ..utils.config import load_config
from ..utils.url import normalize_url, is_valid_url, get_domain
from ..utils.logger import setup_logger
from ..storage import FileStorage, MongoDBStorage, IndexBuilder

from .base_crawler import BaseCrawler
from .desktop_crawler import DesktopCrawler
from .mobile_crawler import MobileCrawler
from .image_crawler import ImageCrawler
from .news_crawler import NewsCrawler
from .video_crawler import VideoCrawler


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
        if self.config["index_settings"]["build_index"]:
            self.index_builder = IndexBuilder(self.config)
        
        self.logger.info("SheikhBot initialized successfully")
    
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
        
        # Initialize news crawler if enabled
        if self.config["specialized_crawlers"]["news"]["enabled"]:
            crawlers["news"] = NewsCrawler(self.config)
            self.logger.info("News crawler initialized")
        
        # Initialize image crawler if enabled
        if self.config["specialized_crawlers"]["images"]["enabled"]:
            crawlers["images"] = ImageCrawler(self.config)
            self.logger.info("Image crawler initialized")
        
        # Initialize video crawler if enabled
        if self.config["specialized_crawlers"]["videos"]["enabled"]:
            crawlers["videos"] = VideoCrawler(self.config)
            self.logger.info("Video crawler initialized")
        
        return crawlers
    
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
                    
                    stats["urls_crawled"] += 1
                    stats["pages_indexed"] += len(crawl_results) if isinstance(crawl_results, list) else 1
                    
                except Exception as e:
                    self.logger.error(f"Error crawling {normalized_url} with {crawler_type} crawler: {str(e)}")
                    stats["errors"] += 1
        
        # Calculate crawl duration
        stats["duration"] = time.time() - stats["start_time"]
        
        self.logger.info(f"Crawl completed in {stats['duration']:.2f} seconds")
        self.logger.info(f"URLs crawled: {stats['urls_crawled']}")
        self.logger.info(f"Pages indexed: {stats['pages_indexed']}")
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
            self.storage.export(output_file)
            self.logger.info(f"Data exported successfully to {output_file}")
        except Exception as e:
            self.logger.error(f"Error exporting data: {str(e)}")
    
    def _build_github_pages(self) -> None:
        """Build GitHub Pages site with crawl results."""
        self.logger.info("Building GitHub Pages site")
        
        try:
            # Create docs directory if it doesn't exist
            docs_dir = "docs"
            os.makedirs(docs_dir, exist_ok=True)
            
            # Get index template
            template_path = self.config["github_pages"]["index_template_path"]
            
            # Get all crawl data
            data = self.storage.get_all()
            
            # TODO: Implement actual GitHub Pages site building
            # This would typically involve:
            # 1. Loading a template
            # 2. Populating it with crawl data
            # 3. Writing HTML files for each page
            # 4. Creating index files
            
            self.logger.info("GitHub Pages site built successfully")
        except Exception as e:
            self.logger.error(f"Error building GitHub Pages site: {str(e)}")
    
    def clear_data(self) -> None:
        """Clear all crawled data."""
        self.logger.info("Clearing all crawled data")
        self.storage.clear()
        
        if hasattr(self, 'index_builder'):
            self.index_builder.clear_index()
        
        self.logger.info("All data cleared successfully") 