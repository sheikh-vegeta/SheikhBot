#!/usr/bin/env python3
"""
Central Search CLI - Command-line interface for the web crawler and SEO analysis tool

This is the main entry point for running Central Search from the command line.
It provides a clean interface to all the functionality of the Central Search tool.
"""

import os
import sys
import logging
from pathlib import Path

# Add the current directory to the path to ensure modules can be found
sys.path.insert(0, str(Path(__file__).parent))

# Import CLI functionality
from src.cli.commands import create_parser, execute_command
from src.utils.logger import setup_logger


def main():
    """
    Main entry point for the Central Search CLI.
    
    Handles command line parsing, executes the appropriate command,
    and manages overall program flow and error handling.
    """
    # Parse command line arguments
    parser = create_parser()
    args = parser.parse_args()
    
    # Show help if no command is specified
    if not hasattr(args, 'command') or not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Show version and exit if requested
    if args.command == "version":
        from src import __version__, __title__, __author__
        print(f"{__title__} v{__version__} by {__author__}")
        sys.exit(0)
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else (
        logging.INFO if args.verbose else logging.WARNING
    )
    
    logger = setup_logger(
        name="central",
        level=log_level,
        log_file=os.path.join("logs", "central.log")
    )
    
    logger.debug(f"Starting Central Search with command: {args.command}")
    
    try:
        # Execute the command
        exit_code = execute_command(args)
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\nProcess interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        print("See logs for detailed error information.")
        sys.exit(1)


if __name__ == "__main__":
    main() 