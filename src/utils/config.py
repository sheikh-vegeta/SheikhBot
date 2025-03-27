"""
Config utilities for loading and saving configuration.
"""

import os
import yaml
from typing import Dict, Any


def load_config(config_file: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_file (str): Path to configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    
    return config


def save_config(config: Dict[str, Any], config_file: str) -> None:
    """
    Save configuration to a YAML file.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        config_file (str): Path where to save the configuration
    """
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration structure and values.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        bool: True if configuration is valid
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Check required top-level sections
    required_sections = [
        "general", "crawl_settings", "specialized_crawlers",
        "export_settings", "storage", "content_extraction"
    ]
    
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")
    
    # Validate crawl_settings
    required_crawl_settings = [
        "user_agent", "max_depth", "delay", "timeout", "respect_robots_txt"
    ]
    
    for setting in required_crawl_settings:
        if setting not in config["crawl_settings"]:
            raise ValueError(f"Missing required crawl setting: {setting}")
    
    # Validate specialized crawlers
    required_crawlers = ["desktop", "mobile", "images"]
    
    for crawler in required_crawlers:
        if crawler not in config["specialized_crawlers"]:
            raise ValueError(f"Missing required specialized crawler configuration: {crawler}")
    
    # Check that at least one crawler is enabled
    if not any(config["specialized_crawlers"][crawler].get("enabled", False) 
               for crawler in config["specialized_crawlers"]):
        raise ValueError("At least one specialized crawler must be enabled")
    
    return True


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries, with override_config taking precedence.
    
    Args:
        base_config (Dict[str, Any]): Base configuration
        override_config (Dict[str, Any]): Override configuration
        
    Returns:
        Dict[str, Any]: Merged configuration
    """
    result = base_config.copy()
    
    for key, value in override_config.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            # Recursively merge nested dictionaries
            result[key] = merge_configs(result[key], value)
        else:
            # Override the value
            result[key] = value
    
    return result 