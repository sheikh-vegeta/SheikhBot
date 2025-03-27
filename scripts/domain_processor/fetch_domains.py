import os
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DomainFetcher:
    def __init__(self):
        self.base_dirs = {
            "whoisds": "data/whoisds",
            "dnpedia": "data/dnpedia",
            "phishing": "data/phishing"
        }
        self.create_directories()
    
    def create_directories(self):
        """Create necessary directories"""
        for directory in self.base_dirs.values():
            os.makedirs(directory, exist_ok=True)
    
    def fetch_whoisds_domains(self, days_back=7):
        """Fetch domains from whoisds repository"""
        base_url = "https://raw.githubusercontent.com/steffensbola/new-domains-daily/main/data/whoisds"
        
        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            url = f"{base_url}/{date}/domain-names.txt"
            
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    output_file = f"{self.base_dirs['whoisds']}/{date}.txt"
                    with open(output_file, 'w') as f:
                        f.write(response.text)
                    logger.info(f"Downloaded domains for {date}")
            except Exception as e:
                logger.error(f"Error fetching whoisds domains for {date}: {str(e)}")
    
    def fetch_phishing_domains(self):
        """Fetch phishing domains list"""
        url = "https://github.com/cuongdt1994/Block-Phising-Crypto-Domains/raw/main/lists/daily"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                output_file = f"{self.base_dirs['phishing']}/daily.txt"
                with open(output_file, 'w') as f:
                    f.write(response.text)
                logger.info("Downloaded phishing domains")
        except Exception as e:
            logger.error(f"Error fetching phishing domains: {str(e)}")

def main():
    fetcher = DomainFetcher()
    fetcher.fetch_whoisds_domains()
    fetcher.fetch_phishing_domains()

if __name__ == "__main__":
    main()
