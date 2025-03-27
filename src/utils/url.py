"""
URL utilities for handling and normalizing URLs.
"""

import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from typing import List, Dict, Any, Optional


def normalize_url(url: str) -> str:
    """
    Normalize a URL to a canonical form.
    
    Args:
        url (str): URL to normalize
        
    Returns:
        str: Normalized URL
    """
    if not url:
        return ""
    
    # Parse the URL
    parsed = urlparse(url)
    
    # Convert scheme and netloc to lowercase
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # Strip 'www.' prefix if present
    if netloc.startswith("www."):
        netloc = netloc[4:]
    
    # Remove default port if present
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]
    
    # Parse query parameters
    query_params = parse_qs(parsed.query)
    
    # Sort query parameters and remove duplicates
    sorted_query = urlencode(
        {k: v[0] if len(v) == 1 else v for k, v in sorted(query_params.items())},
        doseq=True
    )
    
    # Remove trailing slash from path if present
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    
    # Rebuild the URL
    normalized_url = urlunparse((
        scheme,
        netloc,
        path,
        parsed.params,
        sorted_query,
        ""  # Remove fragment
    ))
    
    return normalized_url


def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid.
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if URL is valid
    """
    if not url:
        return False
    
    # Check URL format
    try:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc]) and parsed.scheme in ["http", "https"]
    except Exception:
        return False


def get_domain(url: str) -> str:
    """
    Extract domain from a URL.
    
    Args:
        url (str): URL to extract domain from
        
    Returns:
        str: Domain name
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove port if present
        if ":" in domain:
            domain = domain.split(":")[0]
        
        # Remove 'www.' prefix if present
        if domain.startswith("www."):
            domain = domain[4:]
        
        return domain
    except Exception:
        return ""


def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs belong to the same domain.
    
    Args:
        url1 (str): First URL
        url2 (str): Second URL
        
    Returns:
        bool: True if both URLs have the same domain
    """
    return get_domain(url1) == get_domain(url2)


def extract_urls_from_text(text: str) -> List[str]:
    """
    Extract URLs from text content.
    
    Args:
        text (str): Text to extract URLs from
        
    Returns:
        List[str]: List of extracted URLs
    """
    # URL pattern matching most common URL formats
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    
    # Find all matches
    urls = re.findall(url_pattern, text)
    
    return urls


def url_to_filepath(url: str) -> str:
    """
    Convert a URL to a valid filepath.
    
    Args:
        url (str): URL to convert
        
    Returns:
        str: Valid filepath
    """
    # Parse the URL
    parsed = urlparse(url)
    
    # Get domain and path
    domain = parsed.netloc
    path = parsed.path
    
    # Remove invalid characters
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        domain = domain.replace(char, '_')
        path = path.replace(char, '_')
    
    # Build filepath
    if path and path != "/":
        filepath = f"{domain}{path}"
    else:
        filepath = domain
    
    # Add query parameters if present
    if parsed.query:
        # Hash the query string to keep the filename length reasonable
        import hashlib
        query_hash = hashlib.md5(parsed.query.encode()).hexdigest()[:8]
        filepath = f"{filepath}_q{query_hash}"
    
    return filepath 