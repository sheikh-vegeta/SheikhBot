"""
File Storage - Simple file-based storage for crawled content
"""

import os
import json
import time
from typing import Dict, List, Any, Union
import logging

class FileStorage:
    """Storage implementation that saves crawled data to files."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the file storage.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.output_dir = config["storage"]["file"]["output_directory"]
        self.logger = logging.getLogger("sheikhbot.storage.file")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
    def store(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], data_type: str = None) -> None:
        """
        Store the crawled data to a file.
        
        Args:
            data (Union[Dict[str, Any], List[Dict[str, Any]]]): Data to store
            data_type (str, optional): Type of data (e.g., desktop, mobile)
        """
        if not data:
            return
            
        timestamp = int(time.time())
        filename = f"{data_type}_{timestamp}.json" if data_type else f"data_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Data stored to {filepath}")
        except Exception as e:
            self.logger.error(f"Error storing data to file: {str(e)}")
    
    def store_stats(self, stats: Dict[str, Any]) -> None:
        """
        Store crawl statistics to a file.
        
        Args:
            stats (Dict[str, Any]): Crawl statistics
        """
        if not stats:
            return
            
        timestamp = int(time.time())
        filename = f"stats_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            self.logger.info(f"Crawl stats stored to {filepath}")
        except Exception as e:
            self.logger.error(f"Error storing crawl stats to file: {str(e)}")
    
    def get_all_data(self, data_type: str = None) -> List[Dict[str, Any]]:
        """
        Get all stored data of a specific type.
        
        Args:
            data_type (str, optional): Type of data to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of stored data items
        """
        all_data = []
        
        try:
            for filename in os.listdir(self.output_dir):
                if not filename.endswith('.json'):
                    continue
                    
                # Skip if data_type specified and file doesn't match
                if data_type and not filename.startswith(f"{data_type}_"):
                    continue
                    
                filepath = os.path.join(self.output_dir, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if isinstance(data, list):
                    all_data.extend(data)
                else:
                    all_data.append(data)
        except Exception as e:
            self.logger.error(f"Error retrieving data: {str(e)}")
            
        return all_data 