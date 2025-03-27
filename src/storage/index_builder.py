"""
Index Builder - Creates a simple search index for crawled content
"""

import os
import json
import re
from typing import Dict, List, Any, Union
import logging

class IndexBuilder:
    """Builds a simple search index for crawled content."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the index builder.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger("sheikhbot.storage.indexbuilder")
        
        index_config = config["index_settings"]
        self.index_directory = index_config.get("index_directory", "data/index")
        self.index_file = os.path.join(self.index_directory, "search_index.json")
        
        # Create index directory if it doesn't exist
        os.makedirs(self.index_directory, exist_ok=True)
        
        # Initialize empty index
        self.index = self._load_existing_index() or {"documents": [], "terms": {}}
    
    def _load_existing_index(self) -> Dict[str, Any]:
        """
        Load existing index from file if it exists.
        
        Returns:
            Dict[str, Any]: The loaded index or None if it doesn't exist
        """
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                self.logger.info(f"Loaded existing index with {len(index['documents'])} documents")
                return index
        except Exception as e:
            self.logger.error(f"Error loading existing index: {str(e)}")
        
        return None
    
    def _save_index(self) -> None:
        """Save the current index to disk."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2)
            self.logger.info(f"Index saved with {len(self.index['documents'])} documents")
        except Exception as e:
            self.logger.error(f"Error saving index: {str(e)}")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into searchable terms.
        
        Args:
            text (str): Text to tokenize
            
        Returns:
            List[str]: List of tokens
        """
        if not text:
            return []
            
        # Convert to lowercase and split on non-alphanumeric chars
        text = text.lower()
        tokens = re.findall(r'\w+', text)
        
        # Remove short tokens and common stopwords
        stopwords = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 
            'to', 'for', 'with', 'by', 'about', 'from', 'of'
        }
        tokens = [t for t in tokens if len(t) > 2 and t not in stopwords]
        
        return tokens
    
    def add_to_index(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """
        Add data to the search index.
        
        Args:
            data (Union[Dict[str, Any], List[Dict[str, Any]]]): Data to add to the index
        """
        if not data:
            return
            
        if not isinstance(data, list):
            data = [data]
            
        for item in data:
            try:
                # Only index items with at least url and title
                if "url" not in item or "title" not in item:
                    continue
                    
                # Check if URL already exists in index
                doc_id = None
                for i, doc in enumerate(self.index["documents"]):
                    if doc["url"] == item["url"]:
                        doc_id = i
                        break
                
                # If doc doesn't exist, add it
                if doc_id is None:
                    doc_id = len(self.index["documents"])
                    document = {
                        "url": item["url"],
                        "title": item["title"],
                        "snippet": item.get("snippet", ""),
                        "type": item.get("type", "unknown"),
                        "date": item.get("date", "")
                    }
                    
                    # Add SEO data if available
                    if "seo_score" in item:
                        document["seo_score"] = item["seo_score"]
                    if "seo_issues" in item:
                        document["seo_issues"] = item["seo_issues"]
                    
                    self.index["documents"].append(document)
                else:
                    # Update existing document
                    self.index["documents"][doc_id].update({
                        "title": item["title"],
                        "snippet": item.get("snippet", ""),
                        "type": item.get("type", "unknown"),
                        "date": item.get("date", "")
                    })
                    
                    # Update SEO data if available
                    if "seo_score" in item:
                        self.index["documents"][doc_id]["seo_score"] = item["seo_score"]
                    if "seo_issues" in item:
                        self.index["documents"][doc_id]["seo_issues"] = item["seo_issues"]
                
                # Collect indexable text
                indexable_text = f"{item['title']} {item.get('snippet', '')}"
                if "content" in item:
                    indexable_text += f" {item['content']}"
                
                # Tokenize and add to index
                tokens = self._tokenize(indexable_text)
                
                for token in tokens:
                    if token not in self.index["terms"]:
                        self.index["terms"][token] = []
                    
                    if doc_id not in self.index["terms"][token]:
                        self.index["terms"][token].append(doc_id)
            
            except Exception as e:
                self.logger.error(f"Error indexing item: {str(e)}")
        
        # Save the updated index
        self._save_index()
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search the index for documents matching a query.
        
        Args:
            query (str): Search query
            limit (int, optional): Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: Matching documents
        """
        if not query or not self.index["documents"]:
            return []
            
        try:
            # Tokenize the query
            query_tokens = self._tokenize(query)
            
            if not query_tokens:
                return []
                
            # Find document IDs that match any query token
            matching_doc_ids = set()
            token_doc_map = {}
            
            for token in query_tokens:
                # Look for partial token matches
                for indexed_token, doc_ids in self.index["terms"].items():
                    if token in indexed_token:
                        for doc_id in doc_ids:
                            if doc_id not in token_doc_map:
                                token_doc_map[doc_id] = 0
                            token_doc_map[doc_id] += 1
                            matching_doc_ids.add(doc_id)
            
            # Sort by number of matching tokens (descending)
            sorted_doc_ids = sorted(
                matching_doc_ids, 
                key=lambda doc_id: token_doc_map.get(doc_id, 0),
                reverse=True
            )
            
            # Get the actual documents
            results = []
            for doc_id in sorted_doc_ids[:limit]:
                results.append(self.index["documents"][doc_id])
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching index: {str(e)}")
            return [] 