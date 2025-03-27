"""
Base Crawler - Foundation class for all specialized crawlers
"""

import time
import random
import requests
from typing import Dict, Any, List, Optional, Union, Set
from urllib.parse import urlparse, urljoin
import logging
from bs4 import BeautifulSoup
import re
from datetime import datetime

from ..utils.url import normalize_url, is_valid_url, get_domain
from ..utils.robots import RobotsTxtParser


class BaseCrawler:
    """Base crawler class with common functionality for all specialized crawlers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the base crawler.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger("sheikhbot")
        
        # Set user agent
        self.user_agent = self.config["crawl_settings"]["user_agent"]
        
        # Initialize crawl stats
        self.stats = {
            "pages_crawled": 0,
            "urls_discovered": 0,
            "bytes_downloaded": 0,
            "crawl_time": 0,
            "errors": 0
        }
        
        # Initialize robots.txt parser
        self.robots_parser = RobotsTxtParser()
        
        # Keep track of visited URLs to avoid duplicates
        self.visited_urls = set()
        
        # Keep a cache of ETag and Last-Modified values for URLs
        self.etag_cache = {}
        self.last_modified_cache = {}
        
        # Initialize session with proper headers and settings
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        })
        
        # Set timeout from config
        self.timeout = self.config["crawl_settings"]["timeout"]
        
        # Set delay from config with small random variation for politeness
        self.delay = self.config["crawl_settings"]["delay"]
        
    def crawl(self, url: str, max_depth: int = None) -> List[Dict[str, Any]]:
        """
        Crawl a URL and its linked pages up to max_depth.
        
        Args:
            url (str): The URL to start crawling from
            max_depth (int, optional): Maximum crawl depth. If None, uses config value.
            
        Returns:
            List[Dict[str, Any]]: List of crawled pages with their data
        """
        if max_depth is None:
            max_depth = self.config["crawl_settings"]["max_depth"]
        
        start_time = time.time()
        
        self.logger.info(f"Starting crawl of {url} with max depth {max_depth}")
        
        # Reset stats for this crawl
        self.stats = {
            "pages_crawled": 0,
            "urls_discovered": 0,
            "bytes_downloaded": 0,
            "crawl_time": 0,
            "errors": 0
        }
        
        # Reset visited URLs
        self.visited_urls = set()
        
        # Results will contain all the crawled pages data
        results = []
        
        # Queue of URLs to crawl with their depth
        queue = [(normalize_url(url), 0)]
        
        # Check robots.txt first if enabled
        if self.config["crawl_settings"]["respect_robots_txt"]:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            try:
                self.robots_parser.fetch(robots_url, self.user_agent)
                
                if not self.robots_parser.can_fetch(url, self.user_agent):
                    self.logger.warning(f"URL {url} is disallowed by robots.txt")
                    return results
                
                crawl_delay = self.robots_parser.get_crawl_delay(self.user_agent)
                if crawl_delay is not None:
                    # Use robots.txt crawl delay if it's specified and higher than our configured delay
                    self.delay = max(self.delay, crawl_delay)
                    self.logger.info(f"Using crawl delay from robots.txt: {self.delay} seconds")
            except Exception as e:
                self.logger.warning(f"Error fetching robots.txt: {str(e)}")
        
        # Process URLs in the queue
        while queue:
            current_url, current_depth = queue.pop(0)
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
            
            # Skip if exceeds max depth
            if current_depth > max_depth:
                continue
            
            # Add to visited set
            self.visited_urls.add(current_url)
            
            # Check if URL matches any excluded pattern
            if any(re.match(pattern, current_url) for pattern in self.config["excluded_urls"]):
                self.logger.info(f"Skipping URL {current_url} - matches excluded pattern")
                continue
            
            # Respect crawl delay - add small random variation for politeness
            time.sleep(self.delay + random.uniform(0, 0.5))
            
            try:
                # Fetch the page with HTTP caching support
                response, from_cache = self._fetch_with_cache(current_url)
                
                if response.status_code == 200:
                    # Process the page
                    page_data = self._process_page(response, current_url, current_depth)
                    results.append(page_data)
                    
                    # Extract links if not at max depth
                    if current_depth < max_depth:
                        next_urls = self._extract_links(response, current_url)
                        
                        # Add new URLs to the queue
                        for next_url in next_urls:
                            if next_url not in self.visited_urls:
                                queue.append((next_url, current_depth + 1))
                                self.stats["urls_discovered"] += 1
                    
                    self.stats["pages_crawled"] += 1
                    self.stats["bytes_downloaded"] += len(response.content)
                    
                elif response.status_code == 304:  # Not Modified
                    self.logger.info(f"Page not modified: {current_url}")
                    
                    # Look up previously cached content
                    # In a real implementation, this would retrieve the content from storage
                    
                else:
                    self.logger.warning(f"Failed to fetch {current_url}: HTTP {response.status_code}")
                    self.stats["errors"] += 1
                    
            except Exception as e:
                self.logger.error(f"Error crawling {current_url}: {str(e)}")
                self.stats["errors"] += 1
        
        # Calculate total crawl time
        self.stats["crawl_time"] = time.time() - start_time
        
        self.logger.info(f"Crawl completed: {self.stats['pages_crawled']} pages crawled, "
                         f"{self.stats['urls_discovered']} URLs discovered, "
                         f"{self.stats['errors']} errors, "
                         f"{self.stats['crawl_time']:.2f} seconds")
        
        return results
    
    def _fetch_with_cache(self, url: str) -> tuple:
        """
        Fetch a URL with support for HTTP caching headers.
        
        Args:
            url (str): URL to fetch
            
        Returns:
            tuple: (response, from_cache) where from_cache is a boolean
        """
        headers = {}
        
        # Add If-None-Match header if we have a cached ETag
        if url in self.etag_cache:
            headers["If-None-Match"] = self.etag_cache[url]
        
        # Add If-Modified-Since header if we have a cached Last-Modified
        if url in self.last_modified_cache:
            headers["If-Modified-Since"] = self.last_modified_cache[url]
        
        # Make the request with the conditional headers
        try:
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=self.config["crawl_settings"]["follow_redirects"],
                verify=self.config["crawl_settings"]["verify_ssl"]
            )
            
            # Save ETag if present in response
            if "ETag" in response.headers:
                self.etag_cache[url] = response.headers["ETag"]
            
            # Save Last-Modified if present in response
            if "Last-Modified" in response.headers:
                self.last_modified_cache[url] = response.headers["Last-Modified"]
            
            # Check if we got a 304 Not Modified
            from_cache = response.status_code == 304
            
            return response, from_cache
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error for {url}: {str(e)}")
            raise
    
    def _process_page(self, response: requests.Response, url: str, depth: int) -> Dict[str, Any]:
        """
        Process a page and extract its content.
        
        Args:
            response (requests.Response): HTTP response
            url (str): URL of the page
            depth (int): Current crawl depth
            
        Returns:
            Dict[str, Any]: Extracted page data
        """
        # Base page data
        page_data = {
            "url": url,
            "depth": depth,
            "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type", ""),
            "crawl_time": datetime.now().isoformat(),
            "size": len(response.content),
            "headers": dict(response.headers)
        }
        
        try:
            # Parse HTML with BeautifulSoup if it's HTML content
            if "text/html" in page_data["content_type"]:
                soup = BeautifulSoup(response.content, "lxml")
                
                # Extract title
                page_data["title"] = soup.title.string.strip() if soup.title else ""
                
                # Extract content based on selectors from config
                content_selectors = self.config["content_extraction"]["content_selectors"]
                content = []
                
                for selector in content_selectors:
                    elements = soup.select(selector)
                    if elements:
                        content.extend([elem.get_text(strip=True) for elem in elements])
                
                page_data["content"] = "\n".join(content) if content else ""
                
                # Extract metadata
                metadata = {}
                for meta_type, selectors in self.config["content_extraction"]["metadata_selectors"].items():
                    for selector in selectors:
                        if selector.startswith("meta"):
                            # Handle meta tags
                            meta_elements = soup.select(selector)
                            if meta_elements:
                                metadata[meta_type] = meta_elements[0].get("content", "")
                                break
                        else:
                            # Handle regular elements
                            elements = soup.select(selector)
                            if elements:
                                metadata[meta_type] = elements[0].get_text(strip=True)
                                break
                
                page_data["metadata"] = metadata
            
            # Handle other content types as needed - to be implemented in specialized crawlers
            
        except Exception as e:
            self.logger.error(f"Error processing page {url}: {str(e)}")
            page_data["error"] = str(e)
        
        return page_data
    
    def _extract_links(self, response: requests.Response, base_url: str) -> List[str]:
        """
        Extract links from a page.
        
        Args:
            response (requests.Response): HTTP response
            base_url (str): Base URL for resolving relative URLs
            
        Returns:
            List[str]: List of normalized URLs
        """
        links = []
        
        try:
            # Only extract links from HTML content
            if "text/html" not in response.headers.get("Content-Type", ""):
                return links
            
            soup = BeautifulSoup(response.content, "lxml")
            
            # Extract all <a> tags with href attribute
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                
                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)
                
                # Normalize and validate URL
                if is_valid_url(absolute_url):
                    normalized_url = normalize_url(absolute_url)
                    
                    # Check if the domain is allowed (if allowed_domains is specified)
                    domain = get_domain(normalized_url)
                    if (not self.config["allowed_domains"] or 
                            domain in self.config["allowed_domains"]):
                        links.append(normalized_url)
        
        except Exception as e:
            self.logger.error(f"Error extracting links from {base_url}: {str(e)}")
        
        return links
    
    def verify_crawler(self) -> Dict[str, Any]:
        """
        Return verification information for this crawler
        
        Returns:
            Dict[str, Any]: Crawler verification information
        """
        return {
            "user_agent": self.user_agent,
            "name": self.config["general"]["name"],
            "version": self.config["general"]["version"],
            "verification_string": f"{self.config['general']['name']}/{self.config['general']['version']}",
        } 