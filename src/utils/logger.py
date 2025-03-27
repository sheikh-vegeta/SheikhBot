"""
Logging utilities for consistent logging throughout the application.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(name: str = "sheikhbot", 
                level: int = logging.INFO, 
                log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up and configure a logger.
    
    Args:
        name (str): Logger name
        level (int): Logging level
        log_file (Optional[str]): Path to log file
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log file is specified
    if log_file:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Create rotating file handler (10 MB max size, 5 backups)
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "sheikhbot") -> logging.Logger:
    """
    Get the logger with the specified name.
    
    Args:
        name (str): Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter for adding context to log messages.
    
    Example:
        logger = get_logger("sheikhbot")
        crawler_logger = LoggerAdapter(logger, {"crawler": "desktop"})
        crawler_logger.info("Crawling page")  # Logs: "Crawling page [crawler=desktop]"
    """
    
    def process(self, msg, kwargs):
        """
        Process the logging message and add context.
        
        Args:
            msg: The message to log
            kwargs: Additional keyword arguments
            
        Returns:
            tuple: (modified_message, kwargs)
        """
        context_str = " ".join(f"[{k}={v}]" for k, v in self.extra.items())
        return f"{msg} {context_str}", kwargs 