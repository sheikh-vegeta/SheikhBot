#!/usr/bin/env python3
"""
Run the Central Search crawler with specified parameters.
Used by GitHub Actions workflow.
"""
import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.crawlers import SheikhBot as Central

def main():
    """Main function to run the crawler."""
    # Parse command line arguments
    url = sys.argv[1] if len(sys.argv) > 1 else None
    config_file = sys.argv[2] if len(sys.argv) > 2 else 'config.yml'

    print(f"Initializing Central Search with config: {config_file}")
    
    try:
        # Initialize the crawler
        bot = Central(config_file=config_file)
        
        # Run the crawler
        if url:
            print(f"Crawling URL: {url}")
            bot.crawl(url)
        else:
            print("Crawling default URLs from config")
            bot.crawl()
        
        # Export the data
        print("Exporting data...")
        bot.export_data()
        
        print("Crawling and export completed successfully")
    except Exception as e:
        print(f"Error during crawling: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 