"""
Image Crawler - Specialized crawler for images
"""

from typing import Dict, Any, List, Tuple
import logging
import requests
from bs4 import BeautifulSoup
import os
import hashlib
from urllib.parse import urljoin, urlparse
import re
import io
from PIL import Image
import time

from .base_crawler import BaseCrawler


class ImageCrawler(BaseCrawler):
    """Specialized crawler for images."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the image crawler.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        super().__init__(config)
        
        # Set image-specific user agent
        self.user_agent = self.config["specialized_crawlers"]["images"]["user_agent"]
        self.session.headers.update({"User-Agent": self.user_agent})
        
        # Get image extensions from config
        self.image_extensions = self.config["specialized_crawlers"]["images"]["image_extensions"]
        
        # Get minimum image size
        self.min_size = self.config["specialized_crawlers"]["images"]["min_size"]
        width, height = map(int, self.min_size.split("x"))
        self.min_width = width
        self.min_height = height
        
        # Whether to download images
        self.download_images = self.config["specialized_crawlers"]["images"]["download"]
        
        # Initialize a set to track visited image URLs
        self.visited_image_urls = set()
    
    def crawl(self, url: str, max_depth: int = None) -> List[Dict[str, Any]]:
        """
        Crawl a URL and extract images.
        
        Args:
            url (str): The URL to start crawling from
            max_depth (int, optional): Maximum crawl depth. If None, uses config value.
            
        Returns:
            List[Dict[str, Any]]: List of crawled images with their data
        """
        # First, get regular page data using base crawler
        page_results = super().crawl(url, max_depth)
        
        # Now extract and process images from those pages
        image_results = []
        
        for page_data in page_results:
            if page_data.get("content_type", "").startswith("text/html"):
                # Extract images from this page
                page_url = page_data["url"]
                
                try:
                    self.logger.info(f"Extracting images from {page_url}")
                    
                    # Get the actual response content from the page data
                    response = requests.get(
                        page_url,
                        headers={"User-Agent": self.user_agent},
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        images = self._extract_images(response, page_url)
                        
                        # Process each image
                        for img_url, img_data in images:
                            if img_url not in self.visited_image_urls:
                                self.visited_image_urls.add(img_url)
                                
                                try:
                                    # Fetch and analyze the image
                                    image_info = self._process_image(img_url, img_data, page_url)
                                    
                                    if image_info:
                                        image_results.append(image_info)
                                
                                except Exception as e:
                                    self.logger.error(f"Error processing image {img_url}: {str(e)}")
                
                except Exception as e:
                    self.logger.error(f"Error extracting images from {page_url}: {str(e)}")
        
        self.logger.info(f"Extracted {len(image_results)} images in total")
        return image_results
    
    def _extract_images(self, response: requests.Response, page_url: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Extract image URLs and metadata from a page.
        
        Args:
            response (requests.Response): HTTP response
            page_url (str): URL of the page
            
        Returns:
            List[Tuple[str, Dict[str, Any]]]: List of (image_url, metadata) tuples
        """
        images = []
        
        try:
            soup = BeautifulSoup(response.content, "lxml")
            
            # 1. Extract <img> tags
            for img in soup.find_all("img"):
                try:
                    # Get image URL
                    src = img.get("src")
                    if not src:
                        src = img.get("data-src")  # For lazy-loaded images
                        
                    if not src:
                        continue
                    
                    # Make absolute URL
                    img_url = urljoin(page_url, src)
                    
                    # Basic metadata
                    img_data = {
                        "page_url": page_url,
                        "alt": img.get("alt", ""),
                        "title": img.get("title", ""),
                        "width": img.get("width", ""),
                        "height": img.get("height", ""),
                        "loading": img.get("loading", ""),
                        "tag_type": "img"
                    }
                    
                    # Add to list if it's not already there
                    if img_url not in [i[0] for i in images]:
                        images.append((img_url, img_data))
                
                except Exception as e:
                    self.logger.error(f"Error extracting image data: {str(e)}")
            
            # 2. Extract <picture> and <source> tags for responsive images
            for picture in soup.find_all("picture"):
                try:
                    # Get all source tags
                    sources = picture.find_all("source")
                    img = picture.find("img")
                    
                    if img and img.get("src"):
                        # Make absolute URL for the default image
                        img_url = urljoin(page_url, img.get("src"))
                        
                        # Basic metadata
                        img_data = {
                            "page_url": page_url,
                            "alt": img.get("alt", ""),
                            "title": img.get("title", ""),
                            "width": img.get("width", ""),
                            "height": img.get("height", ""),
                            "tag_type": "picture"
                        }
                        
                        # Add source information
                        source_data = []
                        for source in sources:
                            srcset = source.get("srcset")
                            media = source.get("media")
                            type_ = source.get("type")
                            
                            if srcset:
                                source_data.append({
                                    "srcset": srcset,
                                    "media": media,
                                    "type": type_
                                })
                        
                        if source_data:
                            img_data["sources"] = source_data
                        
                        # Add to list if it's not already there
                        if img_url not in [i[0] for i in images]:
                            images.append((img_url, img_data))
                
                except Exception as e:
                    self.logger.error(f"Error extracting picture data: {str(e)}")
            
            # 3. Extract CSS background images
            try:
                for style in soup.find_all("style"):
                    css_text = style.string
                    if css_text:
                        # Extract URLs from background-image properties
                        bg_urls = re.findall(r'background-image:\s*url\([\'"]?([^\'"]+)[\'"]?\)', css_text)
                        
                        for bg_url in bg_urls:
                            # Make absolute URL
                            abs_bg_url = urljoin(page_url, bg_url)
                            
                            # Basic metadata
                            img_data = {
                                "page_url": page_url,
                                "tag_type": "css_background"
                            }
                            
                            # Add to list if it's not already there
                            if abs_bg_url not in [i[0] for i in images]:
                                images.append((abs_bg_url, img_data))
            
            except Exception as e:
                self.logger.error(f"Error extracting CSS background images: {str(e)}")
            
            # 4. Extract from Open Graph and Twitter Card meta tags
            meta_img_tags = {
                "og:image": soup.find("meta", property="og:image"),
                "twitter:image": soup.find("meta", name="twitter:image")
            }
            
            for tag_name, tag in meta_img_tags.items():
                if tag and tag.get("content"):
                    # Make absolute URL
                    img_url = urljoin(page_url, tag.get("content"))
                    
                    # Basic metadata
                    img_data = {
                        "page_url": page_url,
                        "tag_type": f"meta_{tag_name}"
                    }
                    
                    # Add to list if it's not already there
                    if img_url not in [i[0] for i in images]:
                        images.append((img_url, img_data))
            
        except Exception as e:
            self.logger.error(f"Error parsing HTML for images: {str(e)}")
        
        return images
    
    def _process_image(self, img_url: str, img_data: Dict[str, Any], page_url: str) -> Dict[str, Any]:
        """
        Fetch and analyze an image.
        
        Args:
            img_url (str): Image URL
            img_data (Dict[str, Any]): Basic metadata about the image
            page_url (str): URL of the page containing the image
            
        Returns:
            Dict[str, Any]: Complete image information
        """
        # Skip if URL doesn't have an image extension
        parsed_url = urlparse(img_url)
        path = parsed_url.path.lower()
        
        has_image_extension = any(path.endswith(ext) for ext in self.image_extensions)
        
        # If it doesn't have a known extension, check the Content-Type
        if not has_image_extension:
            try:
                # Make a HEAD request to check content type
                head_response = self.session.head(img_url, timeout=self.timeout)
                content_type = head_response.headers.get("Content-Type", "")
                
                if not content_type.startswith("image/"):
                    self.logger.info(f"Skipping {img_url}: not an image (Content-Type: {content_type})")
                    return None
            
            except Exception as e:
                self.logger.error(f"Error checking content type of {img_url}: {str(e)}")
                return None
        
        # Fetch the image
        try:
            self.logger.info(f"Fetching image: {img_url}")
            
            # Respect crawl delay
            time.sleep(self.delay)
            
            # Send request
            response = self.session.get(img_url, stream=True, timeout=self.timeout)
            
            # Check if it's a valid image
            if not response.headers.get("Content-Type", "").startswith("image/"):
                self.logger.info(f"Skipping {img_url}: not an image (Content-Type: {response.headers.get('Content-Type')})")
                return None
            
            # Get base data
            result = {
                "url": img_url,
                "page_url": page_url,
                "content_type": response.headers.get("Content-Type", ""),
                "size_bytes": int(response.headers.get("Content-Length", 0)),
                "last_modified": response.headers.get("Last-Modified", ""),
                "crawler_type": "image",
                **img_data  # Include the metadata we extracted earlier
            }
            
            # Calculate image hash for deduplication
            try:
                img_content = response.content
                result["hash"] = hashlib.md5(img_content).hexdigest()
                
                # Analyze image dimensions and other properties
                img = Image.open(io.BytesIO(img_content))
                
                # Get image dimensions and format
                result["width"] = img.width
                result["height"] = img.height
                result["format"] = img.format
                result["mode"] = img.mode
                
                # Skip if image is too small
                if result["width"] < self.min_width or result["height"] < self.min_height:
                    self.logger.info(f"Skipping {img_url}: too small ({result['width']}x{result['height']})")
                    return None
                
                # Save image if configured to do so
                if self.download_images:
                    # Create output directory
                    output_dir = os.path.join(self.config["export_settings"]["output_directory"], "images")
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Generate filename
                    filename = f"{result['hash']}.{result['format'].lower()}"
                    filepath = os.path.join(output_dir, filename)
                    
                    # Save image
                    with open(filepath, "wb") as f:
                        f.write(img_content)
                    
                    result["local_path"] = filepath
            
            except Exception as e:
                self.logger.error(f"Error analyzing image {img_url}: {str(e)}")
                
                # Still return the basic info even if analysis failed
                result["analysis_error"] = str(e)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching image {img_url}: {str(e)}")
            return None 