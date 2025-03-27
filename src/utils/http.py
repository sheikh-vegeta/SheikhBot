"""
HTTP utilities for making requests and downloading files.
"""

import os
import requests
import time
import random
from typing import Dict, Any, Optional, Tuple, Union
import logging
from urllib.parse import urlparse
import hashlib


def make_request(
    url: str, 
    method: str = "GET", 
    headers: Optional[Dict[str, str]] = None, 
    params: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    retries: int = 3,
    retry_delay: float = 1.0,
    verify_ssl: bool = True,
    allow_redirects: bool = True,
    stream: bool = False
) -> requests.Response:
    """
    Make an HTTP request with retries and error handling.
    
    Args:
        url (str): URL to request
        method (str): HTTP method (GET, POST, etc.)
        headers (Dict[str, str], optional): HTTP headers
        params (Dict[str, str], optional): URL parameters
        data (Dict[str, Any], optional): Form data
        json (Dict[str, Any], optional): JSON data
        timeout (int): Request timeout in seconds
        retries (int): Number of retries on failure
        retry_delay (float): Delay between retries in seconds
        verify_ssl (bool): Whether to verify SSL certificates
        allow_redirects (bool): Whether to follow redirects
        stream (bool): Whether to stream the response
        
    Returns:
        requests.Response: HTTP response
        
    Raises:
        requests.exceptions.RequestException: If the request fails after all retries
    """
    logger = logging.getLogger("sheikhbot")
    
    # Set default headers if not provided
    if headers is None:
        headers = {
            "User-Agent": "SheikhBot/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br"
        }
    
    # Keep track of attempts
    attempt = 0
    last_error = None
    
    while attempt < retries:
        try:
            logger.debug(f"Making {method} request to {url} (attempt {attempt + 1}/{retries})")
            
            # Make the request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                timeout=timeout,
                verify=verify_ssl,
                allow_redirects=allow_redirects,
                stream=stream
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            logger.debug(f"Request to {url} succeeded with status code {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            attempt += 1
            last_error = e
            
            logger.warning(f"Request to {url} failed: {str(e)}")
            
            # If status code indicates we should not retry (e.g., 404, 403), break
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                if status_code in (400, 401, 403, 404, 422):
                    logger.warning(f"Request to {url} failed with status code {status_code}, not retrying")
                    break
            
            if attempt < retries:
                # Add jitter to retry delay to prevent thundering herd
                jitter = random.uniform(0, 0.5)
                delay = retry_delay * (2 ** (attempt - 1)) + jitter  # Exponential backoff
                
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
    
    # If we've exhausted all retries, raise the last error
    if last_error:
        logger.error(f"Request to {url} failed after {retries} attempts")
        raise last_error
    
    # This should never happen, but just in case
    raise requests.exceptions.RequestException(f"Request to {url} failed for unknown reason")


def download_file(
    url: str,
    output_path: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 60,
    retries: int = 3,
    chunk_size: int = 8192,
    verify_ssl: bool = True
) -> Tuple[bool, str]:
    """
    Download a file from a URL.
    
    Args:
        url (str): URL to download
        output_path (str): Path where to save the downloaded file
        headers (Dict[str, str], optional): HTTP headers
        timeout (int): Request timeout in seconds
        retries (int): Number of retries on failure
        chunk_size (int): Size of chunks to read/write
        verify_ssl (bool): Whether to verify SSL certificates
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    logger = logging.getLogger("sheikhbot")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        logger.info(f"Downloading file from {url} to {output_path}")
        
        # Make the request with streaming enabled
        response = make_request(
            url=url,
            method="GET",
            headers=headers,
            timeout=timeout,
            retries=retries,
            verify_ssl=verify_ssl,
            stream=True
        )
        
        # Get file size if available
        file_size = int(response.headers.get("Content-Length", 0))
        
        # Log download details
        if file_size > 0:
            logger.info(f"File size: {file_size / 1024 / 1024:.2f} MB")
        
        # Download the file in chunks
        with open(output_path, "wb") as f:
            bytes_downloaded = 0
            start_time = time.time()
            
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
            
            download_time = time.time() - start_time
            
            # Calculate download speed
            if download_time > 0:
                speed = bytes_downloaded / download_time / 1024 / 1024  # MB/s
                logger.info(f"Download completed in {download_time:.2f} seconds ({speed:.2f} MB/s)")
        
        return True, "Download successful"
        
    except Exception as e:
        logger.error(f"Error downloading file from {url}: {str(e)}")
        
        # Clean up partial downloads
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                logger.info(f"Removed partial download: {output_path}")
            except Exception as e:
                logger.warning(f"Failed to remove partial download: {str(e)}")
        
        return False, str(e)


def generate_cache_key(url: str, params: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a cache key for a URL and parameters.
    
    Args:
        url (str): URL
        params (Dict[str, Any], optional): URL parameters
        
    Returns:
        str: Cache key
    """
    key = url
    
    if params:
        # Sort params to ensure consistent keys
        sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        key = f"{url}?{sorted_params}"
    
    # Create a hash of the key to avoid issues with file naming
    return hashlib.md5(key.encode()).hexdigest()


def get_content_type(response: requests.Response) -> str:
    """
    Get the content type from a response.
    
    Args:
        response (requests.Response): HTTP response
        
    Returns:
        str: Content type
    """
    content_type = response.headers.get("Content-Type", "")
    
    # Remove charset and parameters
    if ";" in content_type:
        content_type = content_type.split(";")[0]
    
    return content_type.strip().lower() 