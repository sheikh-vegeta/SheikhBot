#!/usr/bin/env python3
"""
Modify the Central Search configuration based on command line arguments.
Used by GitHub Actions workflow.
"""
import yaml
import sys

def main():
    """Main function to modify the configuration."""
    if len(sys.argv) < 3:
        print("Usage: modify_config.py <crawler_types> <depth>")
        sys.exit(1)

    # Parse arguments
    crawler_types = sys.argv[1].split(',')
    depth = int(sys.argv[2])

    print(f"Modifying config with crawlers: {crawler_types} and depth: {depth}")

    # Load the config
    try:
        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        sys.exit(1)

    # Set crawler enabled flags based on input
    for crawler_type in config['specialized_crawlers']:
        config['specialized_crawlers'][crawler_type]['enabled'] = crawler_type in crawler_types

    # Set crawl depth
    config['crawl_settings']['max_depth'] = depth

    # Save the modified config
    try:
        with open('config_modified.yml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        print("Created modified configuration successfully")
    except Exception as e:
        print(f"Error saving modified configuration: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 