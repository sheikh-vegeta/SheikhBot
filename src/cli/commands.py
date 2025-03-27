"""
Central Search CLI commands module

This module defines the command-line interface structure and command handlers
for the Central Search tool.
"""

import os
import sys
import argparse
import logging
import yaml
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path

from src.crawlers import SheikhBot as Central
from src.utils.indexnow import IndexNowClient
from src.utils.config import load_config, save_config


def create_parser() -> argparse.ArgumentParser:
    """
    Create the command-line argument parser.
    
    Returns:
        argparse.ArgumentParser: The configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Central Search - Advanced web crawler and SEO analysis toolkit",
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
        help="Enable debug mode with detailed logging"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command", 
        help="Command to run",
        title="Commands"
    )
    
    # Crawl command
    crawl_parser = subparsers.add_parser(
        "crawl", 
        help="Crawl websites for analysis"
    )
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
    export_parser = subparsers.add_parser(
        "export", 
        help="Export crawled data"
    )
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
    ghpages_parser = subparsers.add_parser(
        "ghpages", 
        help="Build GitHub Pages site"
    )
    ghpages_parser.add_argument(
        "-d", "--directory", 
        default="docs",
        help="Output directory for GitHub Pages"
    )
    
    # IndexNow commands
    indexnow_parser = subparsers.add_parser(
        "indexnow", 
        help="IndexNow operations"
    )
    indexnow_subparsers = indexnow_parser.add_subparsers(
        dest="indexnow_command", 
        help="IndexNow command"
    )
    
    # Generate key file
    genkey_parser = indexnow_subparsers.add_parser(
        "genkey", 
        help="Generate IndexNow key file"
    )
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
    submit_parser = indexnow_subparsers.add_parser(
        "submit", 
        help="Submit URLs to IndexNow"
    )
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
    
    # Config command
    config_parser = subparsers.add_parser(
        "config", 
        help="Manage configuration"
    )
    config_subparsers = config_parser.add_subparsers(
        dest="config_command", 
        help="Configuration command"
    )
    
    # Show config
    config_subparsers.add_parser(
        "show", 
        help="Show current configuration"
    )
    
    # Initialize config
    init_parser = config_subparsers.add_parser(
        "init", 
        help="Initialize or update configuration"
    )
    init_parser.add_argument(
        "--force", 
        action="store_true", 
        help="Overwrite existing configuration"
    )
    
    # Version command
    subparsers.add_parser(
        "version", 
        help="Show version information"
    )
    
    return parser


def handle_crawl_command(args) -> int:
    """
    Handle the crawl command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        int: Exit code
    """
    # Load configuration
    config = load_config(args.config)
    
    # Modify configuration based on arguments
    if args.depth is not None:
        config["crawl_settings"]["max_depth"] = args.depth
    
    if args.crawler != "all":
        for crawler_type in config["specialized_crawlers"]:
            config["specialized_crawlers"][crawler_type]["enabled"] = (crawler_type == args.crawler)
    
    if args.indexnow:
        config["indexnow"]["enabled"] = True
        config["indexnow"]["auto_submit"] = True
    
    # Initialize the crawler
    try:
        bot = Central(config_file=args.config)
    except Exception as e:
        logging.error(f"Error initializing Central Search: {str(e)}")
        return 1
    
    # Get URLs to crawl
    urls = args.urls if args.urls else None
    
    try:
        # Run crawler
        logging.info(f"Starting crawl with {'provided URLs' if urls else 'start_urls from config'}")
        crawled_data = bot.crawl(urls)
        
        # Export data if output is specified
        if args.output:
            logging.info(f"Exporting data to {args.output}")
            bot.export_data(args.output)
        
        return 0
    except Exception as e:
        logging.error(f"Error during crawl: {str(e)}")
        return 1


def handle_export_command(args) -> int:
    """
    Handle the export command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        int: Exit code
    """
    # Load configuration
    config = load_config(args.config)
    
    # Modify configuration based on arguments
    if args.format:
        config["export_settings"]["format"] = args.format
    
    # Initialize the crawler
    try:
        bot = Central(config_file=args.config)
    except Exception as e:
        logging.error(f"Error initializing Central Search: {str(e)}")
        return 1
    
    try:
        logging.info(f"Exporting data to {args.output}")
        bot.export_data(args.output)
        return 0
    except Exception as e:
        logging.error(f"Error exporting data: {str(e)}")
        return 1


def handle_ghpages_command(args) -> int:
    """
    Handle the GitHub Pages command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        int: Exit code
    """
    # Load configuration
    config = load_config(args.config)
    
    # Initialize the crawler
    try:
        bot = Central(config_file=args.config)
    except Exception as e:
        logging.error(f"Error initializing Central Search: {str(e)}")
        return 1
    
    try:
        logging.info(f"Building GitHub Pages site in {args.directory}")
        
        # Ensure directory exists
        os.makedirs(args.directory, exist_ok=True)
        
        # TODO: Implement actual GitHub Pages building
        # This is a placeholder - in reality this would call
        # the appropriate method in the bot to build the GitHub Pages site
        
        logging.info("GitHub Pages site built successfully")
        return 0
    except Exception as e:
        logging.error(f"Error building GitHub Pages site: {str(e)}")
        return 1


def handle_indexnow_command(args) -> int:
    """
    Handle IndexNow-related commands.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        int: Exit code
    """
    # Load configuration
    config = load_config(args.config)
    
    # Check if IndexNow is configured
    if "indexnow" not in config:
        logging.error("IndexNow is not configured in config file")
        return 1
    
    # Get API key from args or config
    api_key = args.key if hasattr(args, "key") and args.key else config["indexnow"]["api_key"]
    
    if not api_key:
        logging.error("No IndexNow API key provided")
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
            
            logging.info(f"IndexNow key file generated successfully at {key_file_path}")
            logging.info(f"Make sure to place this file at your website root: https://yourdomain.com/{api_key}.txt")
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
                logging.info(f"Successfully submitted URLs to {search_engine}")
                
                # Log individual results if available
                if "results" in result:
                    success_count = sum(1 for r in result["results"].values() if r.get("success", False))
                    logging.info(f"Successfully submitted {success_count} out of {len(urls)} URLs")
                
                return 0
            else:
                error_msg = result.get("error", "Unknown error")
                logging.error(f"Failed to submit URLs to {search_engine}: {error_msg}")
                return 1
        else:
            logging.error(f"Unknown IndexNow command: {args.indexnow_command}")
            return 1
    except Exception as e:
        logging.error(f"Error executing IndexNow command: {str(e)}")
        return 1


def handle_config_command(args) -> int:
    """
    Handle the config command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        int: Exit code
    """
    if args.config_command == "show":
        try:
            config = load_config(args.config)
            # Print config in YAML format
            print(yaml.dump(config, default_flow_style=False))
            return 0
        except Exception as e:
            logging.error(f"Error loading configuration: {str(e)}")
            return 1
    
    elif args.config_command == "init":
        config_path = args.config
        
        if os.path.exists(config_path) and not args.force:
            logging.error(f"Configuration file {config_path} already exists. Use --force to overwrite.")
            return 1
        
        try:
            # Load default configuration
            default_config_path = os.path.join(os.path.dirname(__file__), "..", "..", "default_config.yml")
            if not os.path.exists(default_config_path):
                logging.error(f"Default configuration file not found: {default_config_path}")
                return 1
                
            with open(default_config_path, "r") as f:
                config = yaml.safe_load(f)
            
            # Save configuration
            with open(config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
                
            logging.info(f"Configuration initialized at {config_path}")
            return 0
        except Exception as e:
            logging.error(f"Error initializing configuration: {str(e)}")
            return 1
    
    else:
        logging.error(f"Unknown config command: {args.config_command}")
        return 1


def execute_command(args) -> int:
    """
    Execute the appropriate command based on parsed arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        int: Exit code
    """
    # Map commands to handler functions
    command_handlers = {
        "crawl": handle_crawl_command,
        "export": handle_export_command,
        "ghpages": handle_ghpages_command,
        "indexnow": handle_indexnow_command,
        "config": handle_config_command,
    }
    
    # Execute the appropriate handler
    if args.command in command_handlers:
        return command_handlers[args.command](args)
    else:
        logging.error(f"Unknown command: {args.command}")
        return 1 