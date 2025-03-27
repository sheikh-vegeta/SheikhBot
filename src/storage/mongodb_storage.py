"""
MongoDB Storage - MongoDB-based storage for crawled content
"""

import time
from typing import Dict, List, Any, Union
import logging

class MongoDBStorage:
    """Storage implementation that saves crawled data to MongoDB."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the MongoDB storage.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger("sheikhbot.storage.mongodb")
        
        # MongoDB connection is initialized only if actually used
        self.client = None
        self.db = None
    
    def _ensure_connection(self) -> None:
        """Ensure MongoDB connection is established."""
        if self.client is not None:
            return
            
        try:
            # Import pymongo here to make it an optional dependency
            import pymongo
            
            mongodb_config = self.config["storage"]["mongodb"]
            connection_string = mongodb_config["connection_string"]
            
            self.client = pymongo.MongoClient(connection_string)
            self.db = self.client[mongodb_config["database"]]
            
            self.logger.info("Connected to MongoDB")
        except ImportError:
            self.logger.error("pymongo is not installed. Please install it to use MongoDB storage.")
            raise
        except Exception as e:
            self.logger.error(f"Error connecting to MongoDB: {str(e)}")
            raise
    
    def store(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], data_type: str = None) -> None:
        """
        Store the crawled data to MongoDB.
        
        Args:
            data (Union[Dict[str, Any], List[Dict[str, Any]]]): Data to store
            data_type (str, optional): Type of data (e.g., desktop, mobile)
        """
        if not data:
            return
            
        try:
            self._ensure_connection()
            
            # Use data_type as collection name, or fallback to 'data'
            collection_name = data_type if data_type else "data"
            collection = self.db[collection_name]
            
            # Add timestamp to the data
            timestamp = int(time.time())
            
            if isinstance(data, list):
                for item in data:
                    item["timestamp"] = timestamp
                
                collection.insert_many(data)
                self.logger.info(f"Stored {len(data)} items in '{collection_name}' collection")
            else:
                data["timestamp"] = timestamp
                collection.insert_one(data)
                self.logger.info(f"Stored 1 item in '{collection_name}' collection")
                
        except Exception as e:
            self.logger.error(f"Error storing data to MongoDB: {str(e)}")
    
    def store_stats(self, stats: Dict[str, Any]) -> None:
        """
        Store crawl statistics to MongoDB.
        
        Args:
            stats (Dict[str, Any]): Crawl statistics
        """
        if not stats:
            return
            
        try:
            self._ensure_connection()
            
            collection = self.db["stats"]
            collection.insert_one(stats)
            
            self.logger.info("Crawl stats stored to MongoDB")
        except Exception as e:
            self.logger.error(f"Error storing crawl stats to MongoDB: {str(e)}")
    
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
            self._ensure_connection()
            
            # If data_type is specified, query that collection, otherwise query all collections
            if data_type:
                collection = self.db[data_type]
                all_data = list(collection.find({}, {"_id": 0}))
            else:
                # Query all collections except stats and system collections
                for collection_name in self.db.list_collection_names():
                    if collection_name != "stats" and not collection_name.startswith("system."):
                        collection = self.db[collection_name]
                        all_data.extend(list(collection.find({}, {"_id": 0})))
        
        except Exception as e:
            self.logger.error(f"Error retrieving data from MongoDB: {str(e)}")
            
        return all_data 