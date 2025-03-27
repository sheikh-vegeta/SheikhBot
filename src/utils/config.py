"""
Configuration utilities for Central Search.

This module provides functions to load, save, and validate configuration files.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        dict: Loaded configuration
        
    Raises:
        FileNotFoundError: If the configuration file does not exist
        yaml.YAMLError: If the configuration file is invalid YAML
    """
    logger.debug(f"Loading configuration from {config_path}")
    
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        if not isinstance(config, dict):
            logger.error(f"Invalid configuration format: not a dictionary")
            raise ValueError("Invalid configuration format: not a dictionary")
            
        logger.debug(f"Configuration loaded successfully from {config_path}")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {str(e)}")
        raise


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Save configuration to a YAML file.
    
    Args:
        config: Configuration to save
        config_path: Path to save the configuration to
        
    Raises:
        ValueError: If the configuration is invalid
        IOError: If the configuration cannot be saved
    """
    logger.debug(f"Saving configuration to {config_path}")
    
    if not isinstance(config, dict):
        logger.error(f"Invalid configuration format: not a dictionary")
        raise ValueError("Invalid configuration format: not a dictionary")
    
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
        logger.debug(f"Configuration saved successfully to {config_path}")
    except IOError as e:
        logger.error(f"Error saving configuration file: {str(e)}")
        raise


def create_default_config() -> Dict[str, Any]:
    """
    Create a default configuration.
    
    Returns:
        dict: Default configuration
    """
    # Try to load from default_config.yml in the package
    package_dir = Path(__file__).parent.parent.parent
    default_config_path = package_dir / "default_config.yml"
    
    if default_config_path.exists():
        return load_config(str(default_config_path))
    
    # Fall back to hardcoded defaults
    return {
        "general": {
            "name": "Central Search",
            "version": "1.0.0",
            "description": "Advanced web crawler with SEO analysis and search discoverability tools",
            "author": "Central Team"
        },
        "logging": {
            "level": "INFO",
            "file": "logs/central.log",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "backup_count": 5,
            "max_size_mb": 10
        },
        "crawl_settings": {
            "start_urls": ["https://example.com"],
            "max_depth": 3,
            "delay": 1.0,
            "timeout": 30,
            "max_pages": 1000,
            "respect_robots_txt": True,
            "follow_redirects": True,
            "verify_ssl": True,
            "user_agent": "Central/1.0 (+https://github.com/yourusername/central)"
        },
        "export_settings": {
            "format": "json",
            "output_directory": "data",
            "create_timestamp_subdir": True,
            "pretty_print": True
        },
        "specialized_crawlers": {
            "desktop": {"enabled": True},
            "mobile": {"enabled": True},
            "image": {"enabled": True}
        },
        "indexnow": {
            "enabled": False,
            "api_key": "",
            "key_location": "",
            "search_engines": ["default"],
            "auto_submit": True,
            "bulk_submit": True,
            "generate_key_file": True
        }
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate the configuration.
    
    Args:
        config: Configuration to validate
        
    Returns:
        bool: True if the configuration is valid, False otherwise
    """
    # Basic validation - check required sections
    required_sections = ["general", "logging", "crawl_settings", "export_settings"]
    
    for section in required_sections:
        if section not in config:
            logger.error(f"Required configuration section missing: {section}")
            return False
    
    # Check required crawl settings
    if "crawl_settings" in config:
        required_crawl_settings = ["max_depth", "timeout", "max_pages"]
        
        for setting in required_crawl_settings:
            if setting not in config["crawl_settings"]:
                logger.error(f"Required crawl setting missing: {setting}")
                return False
    
    # Check indexnow settings if enabled
    if "indexnow" in config and config["indexnow"].get("enabled", False):
        if not config["indexnow"].get("api_key"):
            logger.warning("IndexNow is enabled but no API key is provided")
    
    return True


def get_config_value(config: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Get a value from the configuration using a dot-separated path.
    
    Args:
        config: Configuration dictionary
        path: Dot-separated path to the value (e.g., "crawl_settings.max_depth")
        default: Default value to return if the path does not exist
        
    Returns:
        The value at the specified path, or the default value if it does not exist
    """
    keys = path.split('.')
    
    current = config
    try:
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key)
            if current is None:
                return default
        return current
    except Exception:
        return default 