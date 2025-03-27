"""
Robots.txt parser for respecting robots exclusion protocol.
"""

import requests
import time
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Optional, Set
import re
import logging


class RobotsTxtParser:
    """Parser for robots.txt files that handles the robots exclusion protocol."""
    
    def __init__(self):
        """Initialize the robots.txt parser."""
        self.logger = logging.getLogger("sheikhbot")
        
        # Cache for robots.txt content
        self.robots_cache = {}
        
        # Default crawl delay if not specified
        self.default_crawl_delay = 1.0
        
        # Cache expiry time in seconds (1 hour)
        self.cache_expiry = 3600
    
    def fetch(self, robots_url: str, user_agent: str) -> None:
        """
        Fetch and parse a robots.txt file.
        
        Args:
            robots_url (str): URL to the robots.txt file
            user_agent (str): User-Agent to use for the request
        """
        # Check if we have a cached version that's still valid
        now = time.time()
        if robots_url in self.robots_cache:
            cache_entry = self.robots_cache[robots_url]
            if now - cache_entry["timestamp"] < self.cache_expiry:
                self.logger.debug(f"Using cached robots.txt for {robots_url}")
                return
        
        self.logger.info(f"Fetching robots.txt from {robots_url}")
        
        try:
            response = requests.get(
                robots_url,
                headers={"User-Agent": user_agent},
                timeout=10
            )
            
            if response.status_code == 200:
                # Parse the robots.txt content
                robots_data = self._parse_robots_txt(response.text, user_agent)
                
                # Cache the parsed data
                self.robots_cache[robots_url] = {
                    "data": robots_data,
                    "timestamp": now
                }
                
                self.logger.info(f"Successfully parsed robots.txt from {robots_url}")
            
            elif response.status_code == 404:
                # No robots.txt file, allow all
                self.logger.info(f"No robots.txt found at {robots_url} (404)")
                self.robots_cache[robots_url] = {
                    "data": {
                        "disallow": set(),
                        "allow": set(),
                        "crawl_delay": None,
                        "sitemaps": []
                    },
                    "timestamp": now
                }
            
            else:
                # Other error, assume allow all
                self.logger.warning(f"Failed to fetch robots.txt from {robots_url}: HTTP {response.status_code}")
                self.robots_cache[robots_url] = {
                    "data": {
                        "disallow": set(),
                        "allow": set(),
                        "crawl_delay": None,
                        "sitemaps": []
                    },
                    "timestamp": now
                }
            
        except Exception as e:
            self.logger.error(f"Error fetching robots.txt from {robots_url}: {str(e)}")
            # In case of error, assume allow all
            self.robots_cache[robots_url] = {
                "data": {
                    "disallow": set(),
                    "allow": set(),
                    "crawl_delay": None,
                    "sitemaps": []
                },
                "timestamp": now
            }
    
    def _parse_robots_txt(self, content: str, user_agent: str) -> Dict:
        """
        Parse robots.txt content.
        
        Args:
            content (str): robots.txt content
            user_agent (str): User-Agent to find rules for
            
        Returns:
            Dict: Parsed rules
        """
        lines = content.split('\n')
        
        # Remove comments and empty lines
        lines = [line.split('#')[0].strip() for line in lines]
        lines = [line for line in lines if line]
        
        # Initialize result
        result = {
            "disallow": set(),
            "allow": set(),
            "crawl_delay": None,
            "sitemaps": []
        }
        
        # Initialize parsing state
        current_agents = []
        is_applicable = False
        
        # Extract the main part from the user agent string
        user_agent_parts = user_agent.lower().split('/')
        main_agent = user_agent_parts[0].strip() if user_agent_parts else ""
        
        # Extract specific rules from robots.txt
        for line in lines:
            # Check for sitemap directives (global)
            if line.lower().startswith("sitemap:"):
                sitemap_url = line[8:].strip()
                if sitemap_url:
                    result["sitemaps"].append(sitemap_url)
                continue
            
            # Check for user-agent directive
            if line.lower().startswith("user-agent:"):
                agent = line[11:].strip().lower()
                
                # If we were parsing for our agent and found a new agent section, stop
                if is_applicable and agent != '*' and not self._agent_matches(agent, main_agent):
                    is_applicable = False
                
                # Add to current agents
                current_agents.append(agent)
                
                # Check if this section applies to our agent
                if agent == '*' or self._agent_matches(agent, main_agent):
                    is_applicable = True
                
                continue
            
            # Skip rules if not applicable to our agent
            if not is_applicable:
                continue
            
            # Check for disallow directive
            if line.lower().startswith("disallow:"):
                path = line[9:].strip()
                if path:
                    result["disallow"].add(path)
                continue
            
            # Check for allow directive
            if line.lower().startswith("allow:"):
                path = line[6:].strip()
                if path:
                    result["allow"].add(path)
                continue
            
            # Check for crawl-delay directive
            if line.lower().startswith("crawl-delay:"):
                delay_str = line[12:].strip()
                try:
                    result["crawl_delay"] = float(delay_str)
                except ValueError:
                    self.logger.warning(f"Invalid crawl-delay value: {delay_str}")
                continue
        
        return result
    
    def _agent_matches(self, robots_agent: str, our_agent: str) -> bool:
        """
        Check if a robot agent matches our agent.
        
        Args:
            robots_agent (str): Agent from robots.txt
            our_agent (str): Our user agent
            
        Returns:
            bool: True if they match
        """
        return robots_agent.lower() in our_agent.lower()
    
    def can_fetch(self, url: str, user_agent: str) -> bool:
        """
        Check if a URL can be fetched according to robots.txt rules.
        
        Args:
            url (str): URL to check
            user_agent (str): User-Agent to check rules for
            
        Returns:
            bool: True if allowed, False if disallowed
        """
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        # Ensure we have fetched the robots.txt
        if robots_url not in self.robots_cache:
            self.fetch(robots_url, user_agent)
        
        # Extract the path from the URL
        path = parsed_url.path
        if not path:
            path = "/"
        
        # Get the stored rules
        rules = self.robots_cache[robots_url]["data"]
        
        # Check if the path matches any disallow rule
        is_disallowed = False
        most_specific_disallow = ""
        
        for disallow_path in rules["disallow"]:
            if self._path_matches(path, disallow_path) and len(disallow_path) > len(most_specific_disallow):
                most_specific_disallow = disallow_path
                is_disallowed = True
        
        # Check if the path matches any allow rule
        most_specific_allow = ""
        
        for allow_path in rules["allow"]:
            if self._path_matches(path, allow_path) and len(allow_path) > len(most_specific_allow):
                most_specific_allow = allow_path
        
        # Allow has precedence over disallow if it's more specific
        if is_disallowed and len(most_specific_allow) > len(most_specific_disallow):
            return True
        
        return not is_disallowed
    
    def _path_matches(self, url_path: str, rule_path: str) -> bool:
        """
        Check if a URL path matches a robots.txt rule path.
        
        Args:
            url_path (str): Path from the URL
            rule_path (str): Path from robots.txt rule
            
        Returns:
            bool: True if they match
        """
        # Handle wildcards in the rule path
        if '*' in rule_path:
            # Convert the rule path to a regex pattern
            pattern = rule_path.replace('.', '\\.')
            pattern = pattern.replace('*', '.*')
            pattern = '^' + pattern + '.*$'
            return bool(re.match(pattern, url_path))
        else:
            # Simple prefix matching
            return url_path.startswith(rule_path)
    
    def get_crawl_delay(self, user_agent: str) -> Optional[float]:
        """
        Get the crawl delay for a site based on robots.txt.
        
        Args:
            user_agent (str): User-Agent to check rules for
            
        Returns:
            Optional[float]: Crawl delay in seconds, or None if not specified
        """
        for robots_url, cache_entry in self.robots_cache.items():
            rules = cache_entry["data"]
            return rules["crawl_delay"]
        
        return None
    
    def get_sitemaps(self) -> List[str]:
        """
        Get sitemaps listed in robots.txt.
        
        Returns:
            List[str]: List of sitemap URLs
        """
        sitemaps = []
        
        for robots_url, cache_entry in self.robots_cache.items():
            rules = cache_entry["data"]
            sitemaps.extend(rules["sitemaps"])
        
        return sitemaps
    
    def clear_cache(self) -> None:
        """Clear the robots.txt cache."""
        self.robots_cache = {} 