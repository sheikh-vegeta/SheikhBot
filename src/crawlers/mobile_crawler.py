"""
Mobile Crawler - Specialized crawler for mobile web pages
"""

from typing import Dict, Any, List
import logging
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .base_crawler import BaseCrawler


class MobileCrawler(BaseCrawler):
    """Specialized crawler for mobile web pages."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the mobile crawler.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        super().__init__(config)
        
        # Set mobile-specific user agent
        self.user_agent = self.config["specialized_crawlers"]["mobile"]["user_agent"]
        self.session.headers.update({"User-Agent": self.user_agent})
        
        # Set viewport size for mobile
        self.viewport = self.config["specialized_crawlers"]["mobile"]["viewport"]
        
        # Initialize Selenium if needed for JavaScript rendering
        self.selenium_enabled = False
        self.driver = None
    
    def _initialize_selenium(self):
        """Initialize Selenium WebDriver for JavaScript rendering with mobile emulation."""
        if self.selenium_enabled and self.driver is None:
            try:
                self.logger.info("Initializing Selenium with mobile emulation")
                
                # Parse viewport dimensions
                width, height = map(int, self.viewport.split("x"))
                
                # Define mobile emulation parameters
                mobile_emulation = {
                    "deviceMetrics": {
                        "width": width,
                        "height": height,
                        "pixelRatio": 3.0
                    },
                    "userAgent": self.user_agent
                }
                
                chrome_options = Options()
                chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--enable-features=NetworkService")
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
                self.logger.info("Selenium with mobile emulation initialized successfully")
                
            except Exception as e:
                self.logger.error(f"Error initializing Selenium for mobile: {str(e)}")
                self.selenium_enabled = False
    
    def _fetch_with_selenium(self, url: str) -> BeautifulSoup:
        """
        Fetch a URL using Selenium with mobile emulation.
        
        Args:
            url (str): URL to fetch
            
        Returns:
            BeautifulSoup: Parsed HTML
        """
        self._initialize_selenium()
        
        if not self.selenium_enabled or self.driver is None:
            raise RuntimeError("Selenium is not enabled or failed to initialize")
        
        try:
            self.logger.info(f"Fetching {url} with Selenium mobile emulation")
            
            self.driver.get(url)
            
            # Wait for dynamic content to load
            time.sleep(5)
            
            # Get the page source after JavaScript execution
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup
            return BeautifulSoup(page_source, "lxml")
            
        except Exception as e:
            self.logger.error(f"Error fetching {url} with Selenium mobile: {str(e)}")
            raise
    
    def _modify_request_headers(self, url: str) -> Dict[str, str]:
        """
        Add additional mobile-specific headers to the request.
        
        Args:
            url (str): URL to fetch
            
        Returns:
            Dict[str, str]: Headers dictionary
        """
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            # Mobile-specific headers
            "X-Requested-With": "XMLHttpRequest",
            "Sec-CH-UA-Mobile": "?1",  # Indicate this is a mobile browser
            "Sec-CH-UA-Platform": "Android",
            "Sec-CH-UA": '"Android WebView";v="115"',
        }
        
        return headers
    
    def _fetch_with_cache(self, url: str) -> tuple:
        """
        Override to add mobile-specific headers.
        
        Args:
            url (str): URL to fetch
            
        Returns:
            tuple: (response, from_cache) where from_cache is a boolean
        """
        headers = self._modify_request_headers(url)
        
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
    
    def _check_for_mobile_redirect(self, response: requests.Response, url: str) -> bool:
        """
        Check if the page is redirecting to a mobile version.
        
        Args:
            response (requests.Response): HTTP response
            url (str): Original URL
            
        Returns:
            bool: True if a mobile redirect was detected
        """
        # Check location header for redirects
        if 300 <= response.status_code < 400 and "Location" in response.headers:
            location = response.headers["Location"]
            if "mobile" in location or "m." in location:
                self.logger.info(f"Detected mobile redirect from {url} to {location}")
                return True
        
        # Check meta refresh redirects
        try:
            soup = BeautifulSoup(response.content, "lxml")
            meta_refresh = soup.find("meta", attrs={"http-equiv": "refresh"})
            
            if meta_refresh and "content" in meta_refresh.attrs:
                content = meta_refresh["content"].lower()
                if "url=" in content:
                    redirect_url = content.split("url=")[1].strip()
                    if "mobile" in redirect_url or "m." in redirect_url:
                        self.logger.info(f"Detected meta refresh mobile redirect from {url} to {redirect_url}")
                        return True
        except Exception:
            pass
        
        return False
    
    def _process_page(self, response: requests.Response, url: str, depth: int) -> Dict[str, Any]:
        """
        Process a page with mobile-specific enhancements.
        
        Args:
            response (requests.Response): HTTP response
            url (str): URL of the page
            depth (int): Current crawl depth
            
        Returns:
            Dict[str, Any]: Extracted page data
        """
        # First get the base page data
        page_data = super()._process_page(response, url, depth)
        
        # Add mobile-specific data
        page_data["crawler_type"] = "mobile"
        page_data["viewport"] = self.viewport
        
        try:
            # Check for mobile redirects
            has_mobile_redirect = self._check_for_mobile_redirect(response, url)
            page_data["has_mobile_redirect"] = has_mobile_redirect
            
            # If it's HTML content, check for mobile-specific elements
            if "text/html" in page_data["content_type"]:
                soup = BeautifulSoup(response.content, "lxml")
                
                # Check for mobile viewport meta tag
                viewport_meta = soup.find("meta", attrs={"name": "viewport"})
                if viewport_meta and "content" in viewport_meta.attrs:
                    page_data["viewport_meta"] = viewport_meta["content"]
                
                # Check for AMP version
                amp_link = soup.find("link", attrs={"rel": "amphtml"})
                if amp_link and "href" in amp_link.attrs:
                    page_data["amp_url"] = amp_link["href"]
                
                # Check for mobile-specific structured data
                mobile_app_elements = {
                    "apple_app": soup.find("meta", attrs={"name": "apple-itunes-app"}),
                    "google_app": soup.find("meta", attrs={"name": "google-play-app"}),
                    "app_links": soup.find_all("meta", attrs={"property": lambda x: x and x.startswith("al:")})
                }
                
                mobile_app_data = {}
                for key, elem in mobile_app_elements.items():
                    if elem and hasattr(elem, "attrs") and "content" in elem.attrs:
                        mobile_app_data[key] = elem["content"]
                    elif isinstance(elem, list) and elem:
                        mobile_app_data[key] = {e.attrs.get("property"): e.attrs.get("content") for e in elem if hasattr(e, "attrs")}
                
                if mobile_app_data:
                    page_data["mobile_app_data"] = mobile_app_data
                
                # Check if page might require JavaScript
                scripts = soup.find_all("script")
                javascript_heavy = len(scripts) > 10 or any("react" in str(s).lower() or "vue" in str(s).lower() or "angular" in str(s).lower() for s in scripts)
                
                # If the page is JavaScript-heavy, try with Selenium
                if javascript_heavy and not self.selenium_enabled:
                    self.logger.info(f"Page {url} appears to be JavaScript-heavy, trying with Selenium mobile")
                    self.selenium_enabled = True
                    try:
                        # Fetch with Selenium mobile emulation
                        selenium_soup = self._fetch_with_selenium(url)
                        
                        # Compare text content length to see if Selenium got more content
                        original_text = soup.get_text()
                        selenium_text = selenium_soup.get_text()
                        
                        if len(selenium_text) > len(original_text) * 1.1:  # At least 10% more content
                            self.logger.info(f"Selenium mobile fetched more content for {url}, using Selenium parsed content")
                            
                            # Extract content from the Selenium-rendered page
                            content_selectors = self.config["content_extraction"]["content_selectors"]
                            content = []
                            
                            for selector in content_selectors:
                                elements = selenium_soup.select(selector)
                                if elements:
                                    content.extend([elem.get_text(strip=True) for elem in elements])
                            
                            page_data["content"] = "\n".join(content) if content else page_data["content"]
                            page_data["used_selenium"] = True
                            
                    except Exception as e:
                        self.logger.error(f"Error using Selenium mobile for {url}: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Error in mobile-specific processing for {url}: {str(e)}")
        
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