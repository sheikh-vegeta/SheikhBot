#!/usr/bin/env python3
"""
IndexNow API client for instant URL submission to search engines.

This module provides functionality to generate IndexNow key files and
submit URLs to search engines that support the IndexNow protocol.
https://www.indexnow.org/
"""

import os
import json
import random
import string
import logging
import urllib.parse
from typing import List, Dict, Any, Union, Optional
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# IndexNow API endpoints for different search engines
INDEXNOW_ENDPOINTS = {
    "default": "https://api.indexnow.org/indexnow",
    "bing": "https://www.bing.com/indexnow",
    "yandex": "https://yandex.com/indexnow",
    "seznam": "https://search.seznam.cz/indexnow",
    "naver": "https://searchadvisor.naver.com/indexnow",
    "yep": "https://yep.com/indexnow"
}

class IndexNowClient:
    """Client for interacting with the IndexNow API."""
    
    def __init__(self, 
                 api_key: str = None, 
                 key_location: str = None,
                 search_engines: List[str] = None,
                 bulk_submit: bool = True):
        """
        Initialize the IndexNow client.
        
        Args:
            api_key: The IndexNow API key. If None, a random key will be generated.
            key_location: URL where the key file is accessible. If not provided,
                          it will be assumed that the key file is at the root of the website.
            search_engines: List of search engines to submit URLs to. Use "default" for
                           the unified API endpoint.
            bulk_submit: Whether to submit URLs in bulk where possible.
        """
        self.api_key = api_key or self._generate_api_key()
        self.key_location = key_location
        self.search_engines = search_engines or ["default"]
        self.bulk_submit = bulk_submit
        
    def _generate_api_key(self, length: int = 32) -> str:
        """
        Generate a random API key for IndexNow.
        
        Args:
            length: Length of the API key to generate.
            
        Returns:
            A random string of hexadecimal characters.
        """
        return ''.join(random.choice(string.hexdigits.lower()) for _ in range(length))
    
    def generate_key_file(self, output_dir: str = ".") -> str:
        """
        Generate the key file for verification.
        
        Args:
            output_dir: Directory where the key file will be saved.
            
        Returns:
            Path to the generated key file.
        """
        os.makedirs(output_dir, exist_ok=True)
        key_file_path = os.path.join(output_dir, f"{self.api_key}.txt")
        
        with open(key_file_path, "w") as f:
            f.write(self.api_key)
        
        logger.info(f"Generated IndexNow key file at {key_file_path}")
        logger.info(f"You need to make this file accessible at: https://yourdomain.com/{self.api_key}.txt")
        
        return key_file_path
    
    def _get_key_location(self, url: str) -> str:
        """
        Get the key location for a given URL.
        
        If key_location is provided during initialization, it will be used.
        Otherwise, the key location is assumed to be at the root of the URL's domain.
        
        Args:
            url: The URL being submitted.
            
        Returns:
            The URL where the key file is expected to be found.
        """
        if self.key_location:
            return self.key_location
        
        parsed_url = urllib.parse.urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return f"{domain}/{self.api_key}.txt"
    
    def _get_domain(self, url: str) -> str:
        """
        Extract the domain from a URL.
        
        Args:
            url: The URL to extract the domain from.
            
        Returns:
            The domain part of the URL.
        """
        parsed_url = urllib.parse.urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    def submit_url(self, url: str, search_engine: str = None) -> Dict[str, Any]:
        """
        Submit a single URL to a search engine.
        
        Args:
            url: The URL to submit.
            search_engine: The search engine to submit to. If None, the default
                          search engines configured will be used.
                          
        Returns:
            A dictionary with the submission results.
        """
        if not search_engine:
            results = {}
            for engine in self.search_engines:
                result = self.submit_url(url, engine)
                results[engine] = result
            return results
        
        # Ensure the search engine is valid
        if search_engine not in INDEXNOW_ENDPOINTS:
            logger.error(f"Unknown search engine: {search_engine}")
            return {"success": False, "error": f"Unknown search engine: {search_engine}"}
            
        endpoint = INDEXNOW_ENDPOINTS[search_engine]
        key_location = self._get_key_location(url)
        
        payload = {
            "host": self._get_domain(url).replace("http://", "").replace("https://", ""),
            "key": self.api_key,
            "keyLocation": key_location,
            "urlList": [url]
        }
        
        logger.debug(f"Submitting URL to {search_engine}: {url}")
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=30
            )
            
            status_code = response.status_code
            logger.debug(f"Response from {search_engine}: {status_code}")
            
            if status_code == 200:
                logger.info(f"Successfully submitted URL to {search_engine}: {url}")
                return {"success": True, "response": response.text}
            else:
                logger.warning(f"Failed to submit URL to {search_engine}: {url}, status: {status_code}")
                return {
                    "success": False, 
                    "status_code": status_code,
                    "response": response.text
                }
                
        except Exception as e:
            logger.error(f"Error submitting URL to {search_engine}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def submit_urls(self, urls: List[str], search_engine: str = None) -> Dict[str, Any]:
        """
        Submit multiple URLs to search engines.
        
        If bulk_submit is True and all URLs are from the same domain, they will be
        submitted in a single request. Otherwise, they will be submitted individually.
        
        Args:
            urls: List of URLs to submit.
            search_engine: The search engine to submit to. If None, the default
                          search engines configured will be used.
                          
        Returns:
            A dictionary with the submission results.
        """
        if not urls:
            logger.warning("No URLs provided for submission")
            return {"success": False, "error": "No URLs provided"}
        
        # If only one URL, use the single URL submission method
        if len(urls) == 1:
            return self.submit_url(urls[0], search_engine)
        
        # Check if all URLs are from the same domain for bulk submission
        domains = {self._get_domain(url) for url in urls}
        
        if len(domains) == 1 and self.bulk_submit:
            return self._bulk_submit_urls(urls, search_engine)
        else:
            # If multiple domains or bulk submission is disabled, submit individually
            results = {"overall_success": True, "results": {}}
            
            for url in urls:
                result = self.submit_url(url, search_engine)
                results["results"][url] = result
                
                if not result.get("success", False):
                    results["overall_success"] = False
                    
            return results
    
    def _bulk_submit_urls(self, urls: List[str], search_engine: str = None) -> Dict[str, Any]:
        """
        Submit multiple URLs from the same domain in a single request.
        
        Args:
            urls: List of URLs to submit.
            search_engine: The search engine to submit to.
            
        Returns:
            A dictionary with the submission results.
        """
        if not search_engine:
            results = {}
            for engine in self.search_engines:
                result = self._bulk_submit_urls(urls, engine)
                results[engine] = result
            return results
        
        # Ensure the search engine is valid
        if search_engine not in INDEXNOW_ENDPOINTS:
            logger.error(f"Unknown search engine: {search_engine}")
            return {"success": False, "error": f"Unknown search engine: {search_engine}"}
            
        endpoint = INDEXNOW_ENDPOINTS[search_engine]
        
        # All URLs should be from the same domain, so we can use the first URL
        # to determine the host and key location
        sample_url = urls[0]
        host = self._get_domain(sample_url).replace("http://", "").replace("https://", "")
        key_location = self._get_key_location(sample_url)
        
        payload = {
            "host": host,
            "key": self.api_key,
            "keyLocation": key_location,
            "urlList": urls
        }
        
        logger.debug(f"Bulk submitting {len(urls)} URLs to {search_engine}")
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=30
            )
            
            status_code = response.status_code
            logger.debug(f"Bulk submission response from {search_engine}: {status_code}")
            
            if status_code == 200:
                logger.info(f"Successfully submitted {len(urls)} URLs to {search_engine}")
                return {"success": True, "response": response.text, "urls": urls}
            else:
                logger.warning(f"Failed to submit URLs to {search_engine}, status: {status_code}")
                return {
                    "success": False, 
                    "status_code": status_code,
                    "response": response.text,
                    "urls": urls
                }
                
        except Exception as e:
            logger.error(f"Error bulk submitting URLs to {search_engine}: {str(e)}")
            return {"success": False, "error": str(e), "urls": urls}

    def verify_key(self, url: str = None) -> Dict[str, Any]:
        """
        Verify that the key file is accessible.
        
        Args:
            url: The URL of a page on the domain to verify.
                If None, key_location must be set.
                
        Returns:
            A dictionary with the verification results.
        """
        if not url and not self.key_location:
            return {"success": False, "error": "Either URL or key_location must be provided"}
        
        key_location = self.key_location
        if url and not key_location:
            key_location = self._get_key_location(url)
        
        try:
            response = requests.get(key_location, timeout=30)
            status_code = response.status_code
            
            if status_code == 200:
                # Check if the content matches the API key
                if response.text.strip() == self.api_key:
                    logger.info(f"Successfully verified key file at {key_location}")
                    return {"success": True, "message": "Key file verified successfully"}
                else:
                    logger.warning(f"Key file content doesn't match the API key at {key_location}")
                    return {
                        "success": False, 
                        "error": "Key file content doesn't match the API key",
                        "expected": self.api_key,
                        "actual": response.text.strip()
                    }
            else:
                logger.warning(f"Failed to access key file at {key_location}, status: {status_code}")
                return {
                    "success": False, 
                    "error": f"Failed to access key file, status: {status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error verifying key file at {key_location}: {str(e)}")
            return {"success": False, "error": str(e)}


def generate_key_file(api_key: str, output_dir: str = ".") -> str:
    """
    Convenience function to generate an IndexNow key file.
    
    Args:
        api_key: The IndexNow API key.
        output_dir: Directory where the key file will be saved.
        
    Returns:
        Path to the generated key file.
    """
    client = IndexNowClient(api_key=api_key)
    return client.generate_key_file(output_dir)


def submit_url(url: str, api_key: str, key_location: str = None, 
              search_engine: str = "default") -> Dict[str, Any]:
    """
    Convenience function to submit a single URL to IndexNow.
    
    Args:
        url: The URL to submit.
        api_key: The IndexNow API key.
        key_location: URL where the key file is accessible.
        search_engine: The search engine to submit to.
        
    Returns:
        A dictionary with the submission results.
    """
    client = IndexNowClient(api_key=api_key, key_location=key_location, 
                           search_engines=[search_engine])
    return client.submit_url(url, search_engine)


def submit_urls(urls: List[str], api_key: str, key_location: str = None,
               search_engine: str = "default", bulk_submit: bool = True) -> Dict[str, Any]:
    """
    Convenience function to submit multiple URLs to IndexNow.
    
    Args:
        urls: List of URLs to submit.
        api_key: The IndexNow API key.
        key_location: URL where the key file is accessible.
        search_engine: The search engine to submit to.
        bulk_submit: Whether to submit URLs in bulk where possible.
        
    Returns:
        A dictionary with the submission results.
    """
    client = IndexNowClient(api_key=api_key, key_location=key_location,
                           search_engines=[search_engine], bulk_submit=bulk_submit)
    return client.submit_urls(urls, search_engine) 