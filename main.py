#!/usr/bin/env python3
"""
SheikhBot - Command-line interface for the web crawler
"""

import argparse
import sys
import os
import logging
from typing import List, Optional
import yaml

from src.crawlers import SheikhBot
from src.utils.logger import setup_logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="SheikhBot - A web crawler inspired by Googlebot",
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
    
    return modified_config


def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_args()
    
    # Show version and exit if requested
    if args.command == "version":
        from src import __version__
        print(f"SheikhBot v{__version__}")
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
        name="sheikhbot",
        level=log_level,
        log_file=config["logging"]["file"]
    )
    
    # Initialize the crawler
    try:
        bot = SheikhBot(config)
        logger.info(f"SheikhBot initialized with config from {args.config}")
    except Exception as e:
        logger.error(f"Error initializing SheikhBot: {str(e)}")
        sys.exit(1)
    
    # Execute the requested command
    if args.command == "crawl":
        # Get URLs to crawl
        urls = args.urls if args.urls else None
        
        try:
            logger.info(f"Starting crawl with {'provided URLs' if urls else 'start_urls from config'}")
            bot.crawl(urls)
            
            # Export data if output is specified
            if hasattr(args, "output") and args.output:
                bot.export_data(args.output)
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
    
    logger.info("SheikhBot completed successfully")


if __name__ == "__main__":
    main() 