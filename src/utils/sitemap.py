from typing import List, Dict, Any
from datetime import datetime
import os
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import logging

class SitemapGenerator:
    """Generate and manage XML sitemaps for crawled pages."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("sheikhbot")
        self.output_dir = self.config.get("sitemap_settings", {}).get("output_directory", "sitemaps")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_sitemap(self, urls: List[Dict[str, Any]], domain: str) -> str:
        """
        Generate a sitemap for the given URLs.

        Args:
            urls: List of URL data dictionaries
            domain: Domain name for the sitemap

        Returns:
            str: Path to the generated sitemap file
        """
        urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

        # Group URLs by last modified date to only include latest version
        url_map = {}
        for url_data in urls:
            url = url_data["url"]
            modified = url_data.get("crawl_time", datetime.now().isoformat())
            
            # Keep newest version of each URL
            if url not in url_map or modified > url_map[url]["modified"]:
                url_map[url] = {
                    "modified": modified,
                    "priority": self._calculate_priority(url_data),
                    "changefreq": self._determine_change_freq(url_data)
                }

        # Add URLs to sitemap
        for url, data in url_map.items():
            url_elem = ET.SubElement(urlset, "url")
            ET.SubElement(url_elem, "loc").text = url
            ET.SubElement(url_elem, "lastmod").text = data["modified"]
            ET.SubElement(url_elem, "changefreq").text = data["changefreq"]
            ET.SubElement(url_elem, "priority").text = str(data["priority"])

        # Create sitemap filename
        filename = f"sitemap_{urlparse(domain).netloc}.xml"
        filepath = os.path.join(self.output_dir, filename)

        # Write sitemap file
        tree = ET.ElementTree(urlset)
        tree.write(filepath, encoding="utf-8", xml_declaration=True)
        
        self.logger.info(f"Generated sitemap at {filepath}")
        return filepath

    def create_sitemap_index(self, sitemaps: List[str]) -> str:
        """Create a sitemap index file for multiple sitemaps."""
        sitemapindex = ET.Element("sitemapindex", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

        for sitemap_path in sitemaps:
            sitemap = ET.SubElement(sitemapindex, "sitemap")
            # Convert local path to URL
            url = self.config["sitemap_settings"]["base_url"].rstrip("/") + "/" + os.path.basename(sitemap_path)
            ET.SubElement(sitemap, "loc").text = url
            ET.SubElement(sitemap, "lastmod").text = datetime.now().isoformat()

        # Write sitemap index
        index_path = os.path.join(self.output_dir, "sitemap_index.xml")
        tree = ET.ElementTree(sitemapindex)
        tree.write(index_path, encoding="utf-8", xml_declaration=True)
        
        return index_path

    def _calculate_priority(self, url_data: Dict[str, Any]) -> float:
        """Calculate priority based on page importance factors."""
        priority = 0.5  # Default priority
        
        # Increase priority for pages with high SEO score
        if "seo_score" in url_data:
            seo_score = float(url_data["seo_score"])
            if seo_score >= 90:
                priority = 1.0
            elif seo_score >= 80:
                priority = 0.8
            elif seo_score >= 70:
                priority = 0.6

        # Adjust for depth
        if "depth" in url_data:
            priority = max(0.1, priority - (float(url_data["depth"]) * 0.1))

        return round(priority, 1)

    def _determine_change_freq(self, url_data: Dict[str, Any]) -> str:
        """Determine change frequency based on content type and updates."""
        if "content_type" in url_data:
            content_type = url_data["content_type"].lower()
            if "news" in content_type or "blog" in content_type:
                return "daily"
            elif "product" in content_type:
                return "weekly"
        return "monthly"  # Default frequency
