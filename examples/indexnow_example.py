#!/usr/bin/env python3
"""
Example of using IndexNow API with Central Search

This script demonstrates various ways to use the IndexNow integration in Central Search,
including generating key files, submitting individual URLs, and bulk submission.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to the path to import Central Search modules
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.indexnow import IndexNowClient, generate_key_file, submit_url, submit_urls

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

# API key (replace with your own)
API_KEY = "cb7a0c39fe74468ba119283e95c08b00"

# Example website and URLs
EXAMPLE_DOMAIN = "https://example.com"  # Replace with your domain
EXAMPLE_URLS = [
    f"{EXAMPLE_DOMAIN}/",
    f"{EXAMPLE_DOMAIN}/about",
    f"{EXAMPLE_DOMAIN}/contact",
    f"{EXAMPLE_DOMAIN}/products",
    f"{EXAMPLE_DOMAIN}/blog/post1",
]


def example_1_generate_key_file():
    """Example of generating an IndexNow key file."""
    print("\n=== Example 1: Generate IndexNow Key File ===")
    
    # Create output directory
    output_dir = "indexnow_example"
    os.makedirs(output_dir, exist_ok=True)
    
    # Method 1: Using convenience function
    key_file_path = generate_key_file(API_KEY, output_dir)
    print(f"Generated key file at: {key_file_path}")
    
    # Method 2: Using the client class
    client = IndexNowClient(api_key=API_KEY)
    key_file_path = client.generate_key_file(output_dir)
    print(f"Generated key file using client at: {key_file_path}")
    
    print("\nTo use this key file:")
    print(f"1. Upload {API_KEY}.txt to your website root: https://example.com/{API_KEY}.txt")
    print(f"2. Ensure the file is accessible via HTTP/HTTPS")
    print(f"3. The file should contain only the API key: {API_KEY}")


def example_2_submit_single_url():
    """Example of submitting a single URL to IndexNow."""
    print("\n=== Example 2: Submit a Single URL ===")
    
    url = EXAMPLE_URLS[0]
    print(f"Submitting URL: {url}")
    
    # Method 1: Using convenience function
    result = submit_url(
        url=url,
        api_key=API_KEY,
        search_engine="default"  # This submits to all participating search engines
    )
    
    print(f"Submission result: {'Success' if result.get('success') else 'Failed'}")
    if not result.get('success'):
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Method 2: Using the client class
    client = IndexNowClient(api_key=API_KEY)
    
    # You can submit to a specific search engine
    bing_result = client.submit_url(url, search_engine="bing")
    print(f"Submission to Bing: {'Success' if bing_result.get('success') else 'Failed'}")
    
    # Or submit to multiple search engines at once
    client = IndexNowClient(api_key=API_KEY, search_engines=["bing", "yandex"])
    multi_result = client.submit_url(url)
    
    if "bing" in multi_result:
        print(f"Bing submission: {'Success' if multi_result['bing'].get('success') else 'Failed'}")
    if "yandex" in multi_result:
        print(f"Yandex submission: {'Success' if multi_result['yandex'].get('success') else 'Failed'}")


def example_3_submit_multiple_urls():
    """Example of submitting multiple URLs to IndexNow."""
    print("\n=== Example 3: Submit Multiple URLs ===")
    
    urls = EXAMPLE_URLS
    print(f"Submitting {len(urls)} URLs from {EXAMPLE_DOMAIN}")
    
    # Method 1: Using convenience function for bulk submission
    result = submit_urls(
        urls=urls,
        api_key=API_KEY,
        search_engine="default",
        bulk_submit=True  # Submit all URLs in a single request
    )
    
    print(f"Bulk submission result: {'Success' if result.get('success') or result.get('overall_success') else 'Failed'}")
    
    # Method 2: Using the client class for individual submissions
    client = IndexNowClient(api_key=API_KEY, bulk_submit=False)
    result = client.submit_urls(urls)
    
    if "results" in result:
        success_count = sum(1 for r in result["results"].values() if r.get("success", False))
        print(f"Individual submissions: {success_count} successful out of {len(urls)}")


def example_4_verify_key_file():
    """Example of verifying an IndexNow key file."""
    print("\n=== Example 4: Verify Key File ===")
    
    # Create a client with a key location
    key_location = f"{EXAMPLE_DOMAIN}/{API_KEY}.txt"
    client = IndexNowClient(api_key=API_KEY, key_location=key_location)
    
    # Verify the key file
    result = client.verify_key()
    
    if result.get("success"):
        print(f"Key file verification successful: {key_location}")
    else:
        print(f"Key file verification failed: {result.get('error', 'Unknown error')}")
        print("Make sure the key file is accessible at the specified URL.")


def example_5_indexnow_with_crawl_results():
    """Example of submitting URLs found during a crawl."""
    print("\n=== Example 5: Submit Crawl Results ===")
    
    # Simulate crawl results (in a real scenario, these would come from the crawler)
    crawl_results = [
        {"url": f"{EXAMPLE_DOMAIN}/", "title": "Home Page", "crawl_time": "2023-10-04T12:00:00Z"},
        {"url": f"{EXAMPLE_DOMAIN}/about", "title": "About Us", "crawl_time": "2023-10-04T12:01:00Z"},
        {"url": f"{EXAMPLE_DOMAIN}/products", "title": "Products", "crawl_time": "2023-10-04T12:02:00Z"},
    ]
    
    # Extract URLs from crawl results
    urls_to_submit = [item["url"] for item in crawl_results]
    print(f"Extracted {len(urls_to_submit)} URLs from crawl results")
    
    # Submit URLs to IndexNow
    client = IndexNowClient(api_key=API_KEY)
    result = client.submit_urls(urls_to_submit)
    
    if result.get("success") or result.get("overall_success"):
        print("Successfully submitted crawl results to IndexNow")
    else:
        print(f"Failed to submit crawl results: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    print("IndexNow API Examples for Central Search")
    print("----------------------------------------")
    print(f"Using API key: {API_KEY}")
    
    # Run examples
    example_1_generate_key_file()
    
    # Uncomment the following lines to run additional examples
    # These examples make actual API calls, so use them carefully
    # example_2_submit_single_url()
    # example_3_submit_multiple_urls()
    # example_4_verify_key_file()
    # example_5_indexnow_with_crawl_results()
    
    print("\nExamples completed. To run additional examples, uncomment the relevant lines in the script.")
    print("Note: Examples 2-5 make actual API calls to search engines, use them with caution.") 