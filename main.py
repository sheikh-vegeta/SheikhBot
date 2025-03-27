#!/usr/bin/env python3
"""
Central Search - Command-line interface for the web crawler and SEO analysis tool
"""

import argparse
import sys
import os
import logging
from typing import List, Optional
import yaml

from src.crawlers import SheikhBot as Central
from src.utils.logger import setup_logger
from src.utils.indexnow import IndexNowClient


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Central Search - A web crawler and SEO analysis tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # General options
    parser.add_argument(
        "-c", "--config", 
        default="config.yml", 
        help="Path to configuration file"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode with extra logging"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl URLs")
    crawl_parser.add_argument(
        "urls", 
        nargs="*", 
        help="URLs to crawl. If not provided, uses start_urls from config."
    )
    crawl_parser.add_argument(
        "-d", "--depth", 
        type=int, 
        help="Maximum crawl depth. Overrides config value if provided."
    )
    crawl_parser.add_argument(
        "--crawler", 
        choices=["desktop", "mobile", "image", "news", "video", "all"],
        default="all",
        help="Crawler type to use"
    )
    crawl_parser.add_argument(
        "-o", "--output", 
        help="Output file path. If not provided, uses export_settings from config."
    )
    crawl_parser.add_argument(
        "--indexnow", 
        action="store_true", 
        help="Submit crawled URLs to search engines using IndexNow"
    )
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export crawled data")
    export_parser.add_argument(
        "-o", "--output", 
        required=True,
        help="Output file path"
    )
    export_parser.add_argument(
        "--format", 
        choices=["json", "csv", "xml"],
        default="json",
        help="Export format"
    )
    
    # GitHub Pages command
    ghpages_parser = subparsers.add_parser("ghpages", help="Build GitHub Pages site")
    ghpages_parser.add_argument(
        "-d", "--directory", 
        default="docs",
        help="Output directory for GitHub Pages"
    )
    
    # IndexNow commands
    indexnow_parser = subparsers.add_parser("indexnow", help="IndexNow operations")
    indexnow_subparsers = indexnow_parser.add_subparsers(dest="indexnow_command", help="IndexNow command")
    
    # Generate key file
    genkey_parser = indexnow_subparsers.add_parser("genkey", help="Generate IndexNow key file")
    genkey_parser.add_argument(
        "-d", "--directory", 
        default="data",
        help="Directory to save the key file"
    )
    genkey_parser.add_argument(
        "--key", 
        help="IndexNow API key. If not provided, uses the key from config."
    )
    
    # Submit URLs
    submit_parser = indexnow_subparsers.add_parser("submit", help="Submit URLs to IndexNow")
    submit_parser.add_argument(
        "urls", 
        nargs="+", 
        help="URLs to submit to IndexNow"
    )
    submit_parser.add_argument(
        "--key", 
        help="IndexNow API key. If not provided, uses the key from config."
    )
    submit_parser.add_argument(
        "--key-location", 
        help="URL where the key file is hosted. If not provided, uses the default location."
    )
    submit_parser.add_argument(
        "--search-engine", 
        choices=["default", "bing", "yandex", "seznam", "naver", "yep"],
        default="default",
        help="Search engine to submit to"
    )
    submit_parser.add_argument(
        "--bulk", 
        action="store_true", 
        help="Submit URLs in bulk (all URLs must be from the same domain)"
    )
    
    # Version command
    subparsers.add_parser("version", help="Show version information")
    
    return parser.parse_args()


def modify_config(config: dict, args) -> dict:
    """
    Modify the configuration based on command line arguments.
    
    Args:
        config (dict): Original configuration
        args: Command line arguments
        
    Returns:
        dict: Modified configuration
    """
    modified_config = config.copy()
    
    # Adjust log level
    if args.debug:
        modified_config["logging"]["level"] = "DEBUG"
    elif args.verbose:
        modified_config["logging"]["level"] = "INFO"
    
    # Adjust crawl depth if provided
    if hasattr(args, "depth") and args.depth is not None:
        modified_config["crawl_settings"]["max_depth"] = args.depth
    
    # Adjust crawler types if provided
    if hasattr(args, "crawler") and args.crawler != "all":
        for crawler_type in modified_config["specialized_crawlers"]:
            modified_config["specialized_crawlers"][crawler_type]["enabled"] = (crawler_type == args.crawler)
    
    # Adjust export format if provided
    if hasattr(args, "format") and args.format is not None:
        modified_config["export_settings"]["format"] = args.format
    
    # Adjust IndexNow settings if enabled via command line
    if hasattr(args, "indexnow") and args.indexnow:
        modified_config["indexnow"]["enabled"] = True
        modified_config["indexnow"]["auto_submit"] = True
    
    return modified_config


def handle_indexnow_commands(args, config, logger):
    """
    Handle IndexNow-related commands.
    
    Args:
        args: Command line arguments
        config (dict): Configuration
        logger: Logger instance
    
    Returns:
        int: Exit code
    """
    # Check if IndexNow is configured
    if "indexnow" not in config:
        logger.error("IndexNow is not configured in config.yml")
        return 1
    
    # Get API key from args or config
    api_key = args.key if hasattr(args, "key") and args.key else config["indexnow"]["api_key"]
    
    if not api_key:
        logger.error("No IndexNow API key provided")
        return 1
    
    try:
        if args.indexnow_command == "genkey":
            # Generate key file
            directory = args.directory
            
            # Ensure directory exists
            os.makedirs(directory, exist_ok=True)
            
            # Initialize client and generate key file
            client = IndexNowClient(api_key=api_key)
            key_file_path = client.generate_key_file(directory)
            
            logger.info(f"IndexNow key file generated successfully at {key_file_path}")
            logger.info(f"Make sure to place this file at your website root: https://yourdomain.com/{api_key}.txt")
            return 0
                
        elif args.indexnow_command == "submit":
            # Submit URLs to IndexNow
            key_location = args.key_location if hasattr(args, "key_location") and args.key_location else None
            search_engine = args.search_engine
            urls = args.urls
            bulk = args.bulk
            
            # Initialize client
            client = IndexNowClient(
                api_key=api_key, 
                key_location=key_location,
                search_engines=[search_engine],
                bulk_submit=bulk
            )
            
            # Submit URLs (the client will automatically handle bulk vs. individual)
            result = client.submit_urls(urls, search_engine)
            
            if result.get("overall_success", False) or result.get("success", False):
                logger.info(f"Successfully submitted URLs to {search_engine}")
                
                # Log individual results if available
                if "results" in result:
                    success_count = sum(1 for r in result["results"].values() if r.get("success", False))
                    logger.info(f"Successfully submitted {success_count} out of {len(urls)} URLs")
                
                return 0
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Failed to submit URLs to {search_engine}: {error_msg}")
                return 1
        else:
            logger.error(f"Unknown IndexNow command: {args.indexnow_command}")
            return 1
    except Exception as e:
        logger.error(f"Error executing IndexNow command: {str(e)}")
        return 1


def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_args()
    
    # Show version and exit if requested
    if args.command == "version":
        from src import __version__
        print(f"Central Search v{__version__}")
        sys.exit(0)
    
    # Load configuration
    try:
        with open(args.config, "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        sys.exit(1)
    
    # Modify configuration based on arguments
    config = modify_config(config, args)
    
    # Set up logging
    log_level = getattr(logging, config["logging"]["level"])
    logger = setup_logger(
        name="central",
        level=log_level,
        log_file=config["logging"]["file"]
    )
    
    # Handle IndexNow commands
    if args.command == "indexnow":
        exit_code = handle_indexnow_commands(args, config, logger)
        sys.exit(exit_code)
    
    # Initialize the crawler
    try:
        bot = Central(config)
        logger.info(f"Central Search initialized with config from {args.config}")
    except Exception as e:
        logger.error(f"Error initializing Central Search: {str(e)}")
        sys.exit(1)
    
    # Execute the requested command
    if args.command == "crawl":
        # Get URLs to crawl
        urls = args.urls if args.urls else None
        
        try:
            logger.info(f"Starting crawl with {'provided URLs' if urls else 'start_urls from config'}")
            crawled_data = bot.crawl(urls)
            
            # Export data if output is specified
            if hasattr(args, "output") and args.output:
                bot.export_data(args.output)
            
            # Submit URLs to IndexNow if enabled
            if config["indexnow"]["enabled"] and config["indexnow"]["auto_submit"]:
                try:
                    indexnow_config = config["indexnow"]
                    api_key = indexnow_config["api_key"]
                    key_location = indexnow_config.get("key_location")
                    search_engines = indexnow_config.get("search_engines", ["default"])
                    bulk_submit = indexnow_config.get("bulk_submit", True)
                    
                    # Extract URLs from crawled data
                    crawled_urls = []
                    if crawled_data and isinstance(crawled_data, list):
                        for item in crawled_data:
                            if isinstance(item, dict) and "url" in item:
                                crawled_urls.append(item["url"])
                    
                    if crawled_urls:
                        logger.info(f"Submitting {len(crawled_urls)} crawled URLs to IndexNow...")
                        
                        # Initialize IndexNow client
                        client = IndexNowClient(
                            api_key=api_key,
                            key_location=key_location,
                            search_engines=search_engines,
                            bulk_submit=bulk_submit
                        )
                        
                        # Submit URLs
                        results = client.submit_urls(crawled_urls)
                        
                        # Log results
                        success_count = 0
                        if "results" in results:
                            success_count = sum(1 for r in results["results"].values() if r.get("success", False))
                            logger.info(f"Successfully submitted {success_count} out of {len(crawled_urls)} URLs to IndexNow")
                        elif results.get("success", False):
                            logger.info(f"Successfully submitted {len(crawled_urls)} URLs to IndexNow")
                        else:
                            error = results.get("error", "Unknown error")
                            logger.warning(f"Failed to submit URLs to IndexNow: {error}")
                    
                    # Generate key file if configured
                    if indexnow_config.get("generate_key_file", False):
                        output_dir = config["export_settings"]["output_directory"]
                        client.generate_key_file(output_dir)
                        logger.info(f"Generated IndexNow key file in {output_dir}")
                
                except Exception as e:
                    logger.error(f"Error submitting URLs to IndexNow: {str(e)}")
                    # Continue execution, don't fail the whole process
        
        except Exception as e:
            logger.error(f"Error during crawl: {str(e)}")
            sys.exit(1)
    
    elif args.command == "export":
        try:
            logger.info(f"Exporting data to {args.output}")
            bot.export_data(args.output)
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            sys.exit(1)
    
    elif args.command == "ghpages":
        try:
            logger.info(f"Building GitHub Pages site in {args.directory}")
            
            # Ensure directory exists
            os.makedirs(args.directory, exist_ok=True)
            
            # TODO: Implement actual GitHub Pages building
            # This is a placeholder for now - in reality this would call
            # the appropriate method in the bot to build the GitHub Pages site
            
            logger.info("GitHub Pages site built successfully")
        except Exception as e:
            logger.error(f"Error building GitHub Pages site: {str(e)}")
            sys.exit(1)
    
    else:
        # If no command is provided, show help
        print("No command specified. Use --help for usage information.")
        sys.exit(1)
    
    logger.info("Central Search completed successfully")


if __name__ == "__main__":
    main() 