"""
Desktop Crawler - Specialized crawler for desktop web pages
"""

from typing import Dict, Any, List
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
from bs4 import BeautifulSoup

from .base_crawler import BaseCrawler


class DesktopCrawler(BaseCrawler):
    """Specialized crawler for desktop web pages."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the desktop crawler.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        super().__init__(config)
        
        # Set desktop-specific user agent
        self.user_agent = self.config["specialized_crawlers"]["desktop"]["user_agent"]
        self.session.headers.update({"User-Agent": self.user_agent})
        
        # Set viewport size
        self.viewport = self.config["specialized_crawlers"]["desktop"]["viewport"]
        
        # Initialize Selenium if needed for JavaScript rendering
        self.selenium_enabled = False
        self.driver = None
    
    def _initialize_selenium(self):
        """Initialize Selenium WebDriver for JavaScript rendering."""
        if self.selenium_enabled and self.driver is None:
            try:
                self.logger.info("Initializing Selenium for desktop rendering")
                
                chrome_options = Options()
                chrome_options.add_argument(f"--user-agent={self.user_agent}")
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument(f"--window-size={self.viewport}")
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
                self.logger.info("Selenium initialized successfully")
                
            except Exception as e:
                self.logger.error(f"Error initializing Selenium: {str(e)}")
                self.selenium_enabled = False
    
    def _fetch_with_selenium(self, url: str) -> BeautifulSoup:
        """
        Fetch a URL using Selenium for JavaScript rendering.
        
        Args:
            url (str): URL to fetch
            
        Returns:
            BeautifulSoup: Parsed HTML
        """
        self._initialize_selenium()
        
        if not self.selenium_enabled or self.driver is None:
            raise RuntimeError("Selenium is not enabled or failed to initialize")
        
        try:
            self.logger.info(f"Fetching {url} with Selenium")
            
            self.driver.get(url)
            
            # Wait for dynamic content to load
            time.sleep(5)
            
            # Get the page source after JavaScript execution
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup
            return BeautifulSoup(page_source, "lxml")
            
        except Exception as e:
            self.logger.error(f"Error fetching {url} with Selenium: {str(e)}")
            raise
    
    def _process_page(self, response: requests.Response, url: str, depth: int) -> Dict[str, Any]:
        """
        Process a page with desktop-specific enhancements.
        
        Args:
            response (requests.Response): HTTP response
            url (str): URL of the page
            depth (int): Current crawl depth
            
        Returns:
            Dict[str, Any]: Extracted page data
        """
        # First get the base page data
        page_data = super()._process_page(response, url, depth)
        
        # Add desktop-specific data
        page_data["crawler_type"] = "desktop"
        page_data["viewport"] = self.viewport
        
        try:
            # If it's HTML content, extract additional desktop-specific content
            if "text/html" in page_data["content_type"]:
                soup = BeautifulSoup(response.content, "lxml")
                
                # Check if page might require JavaScript
                scripts = soup.find_all("script")
                javascript_heavy = len(scripts) > 10 or any("react" in str(s).lower() or "vue" in str(s).lower() or "angular" in str(s).lower() for s in scripts)
                
                # If the page is JavaScript-heavy and Selenium is not yet enabled, try with Selenium
                if javascript_heavy and not self.selenium_enabled:
                    self.logger.info(f"Page {url} appears to be JavaScript-heavy, trying with Selenium")
                    self.selenium_enabled = True
                    try:
                        # Fetch with Selenium
                        selenium_soup = self._fetch_with_selenium(url)
                        
                        # Compare text content length to see if Selenium got more content
                        original_text = soup.get_text()
                        selenium_text = selenium_soup.get_text()
                        
                        if len(selenium_text) > len(original_text) * 1.1:  # At least 10% more content
                            self.logger.info(f"Selenium fetched more content for {url}, using Selenium parsed content")
                            
                            # Extract content from the Selenium-rendered page
                            # Re-extract content using our selectors
                            content_selectors = self.config["content_extraction"]["content_selectors"]
                            content = []
                            
                            for selector in content_selectors:
                                elements = selenium_soup.select(selector)
                                if elements:
                                    content.extend([elem.get_text(strip=True) for elem in elements])
                            
                            page_data["content"] = "\n".join(content) if content else page_data["content"]
                            page_data["used_selenium"] = True
                        
                    except Exception as e:
                        self.logger.error(f"Error using Selenium for {url}: {str(e)}")
                
                # Extract structured data (JSON-LD, etc.)
                structured_data = []
                for script in soup.find_all("script", {"type": "application/ld+json"}):
                    try:
                        structured_data.append(script.string)
                    except Exception as e:
                        self.logger.error(f"Error extracting JSON-LD from {url}: {str(e)}")
                
                if structured_data:
                    page_data["structured_data"] = structured_data
        
        except Exception as e:
            self.logger.error(f"Error in desktop-specific processing for {url}: {str(e)}")
        
        return page_data
    
    def close(self):
        """Clean up resources when done."""
        if self.selenium_enabled and self.driver is not None:
            try:
                self.driver.quit()
                self.logger.info("Selenium WebDriver closed")
            except Exception as e:
                self.logger.error(f"Error closing Selenium WebDriver: {str(e)}")
            finally:
                self.driver = None 