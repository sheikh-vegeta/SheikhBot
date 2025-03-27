import os
import logging
from datetime import datetime
import re
import json
from urllib.parse import urlparse
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import whois
import dns.resolver
from collections import Counter

logger = logging.getLogger(__name__)

class DomainAnalyzer:
    def __init__(self):
        """Initialize the domain analyzer."""
        self.base_dirs = {
            "whoisds": "data/whoisds",
            "phishing": "data/phishing",
            "analysis": "data/analysis"
        }
        self.create_directories()
        
        # Common TLD categories
        self.tld_categories = {
            "generic": {"com", "net", "org", "info", "biz"},
            "country": {"uk", "us", "eu", "cn", "ru", "in"},
            "new": {"app", "dev", "web", "cloud", "ai", "io"}
        }
        
        # Known malicious patterns
        self.suspicious_patterns = [
            r"login.*\d+",
            r"secure.*\d+",
            r"account.*verify",
            r"wallet.*verify",
            r"crypto.*invest",
            r"\d+.*login",
            r"verify.*\d+"
        ]
    
    def create_directories(self):
        """Create necessary directories."""
        for directory in self.base_dirs.values():
            os.makedirs(directory, exist_ok=True)
    
    def load_domain_data(self) -> List[str]:
        """Load domains from all sources."""
        domains = set()
        
        # Load WhoisDS data
        whoisds_dir = self.base_dirs["whoisds"]
        for file in os.listdir(whoisds_dir):
            if file.endswith(".txt"):
                with open(os.path.join(whoisds_dir, file)) as f:
                    domains.update(line.strip() for line in f)
        
        # Load phishing data
        phishing_file = os.path.join(self.base_dirs["phishing"], "daily.txt")
        if os.path.exists(phishing_file):
            with open(phishing_file) as f:
                domains.update(line.strip() for line in f)
        
        return list(domains)
    
    def analyze_domain(self, domain: str) -> Dict[str, Any]:
        """Analyze a single domain."""
        result = {
            "domain": domain,
            "analysis_time": datetime.now().isoformat(),
            "features": {}
        }
        
        # Basic domain features
        parsed = urlparse("http://" + domain)
        parts = parsed.netloc.split(".")
        
        result["features"].update({
            "length": len(domain),
            "num_parts": len(parts),
            "num_digits": sum(c.isdigit() for c in domain),
            "num_hyphens": domain.count("-"),
            "tld": parts[-1] if len(parts) > 1 else "",
        })
        
        # TLD categorization
        tld = result["features"]["tld"]
        for category, tlds in self.tld_categories.items():
            if tld in tlds:
                result["features"]["tld_category"] = category
                break
        else:
            result["features"]["tld_category"] = "other"
        
        # Check suspicious patterns
        result["features"]["suspicious_patterns"] = []
        for pattern in self.suspicious_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                result["features"]["suspicious_patterns"].append(pattern)
        
        # Try to get WHOIS data
        try:
            w = whois.whois(domain)
            result["whois"] = {
                "creation_date": str(w.creation_date) if w.creation_date else None,
                "registrar": w.registrar,
                "country": w.country
            }
        except:
            result["whois"] = None
        
        # Try to get DNS records
        result["dns"] = {}
        for record_type in ["A", "MX", "NS", "TXT"]:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                result["dns"][record_type] = [str(rdata) for rdata in answers]
            except:
                result["dns"][record_type] = None
        
        return result
    
    def analyze_domains(self):
        """Analyze all loaded domains."""
        domains = self.load_domain_data()
        results = []
        
        logger.info(f"Starting analysis of {len(domains)} domains")
        
        for domain in domains:
            try:
                result = self.analyze_domain(domain)
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing domain {domain}: {str(e)}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.base_dirs["analysis"], f"analysis_{timestamp}.json")
        
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Analysis completed. Results saved to {output_file}")
        
        # Generate summary statistics
        self.generate_summary(results, timestamp)
    
    def generate_summary(self, results: List[Dict[str, Any]], timestamp: str):
        """Generate summary statistics from analysis results."""
        summary = {
            "total_domains": len(results),
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "tld_distribution": Counter(r["features"]["tld"] for r in results),
                "tld_category_distribution": Counter(r["features"]["tld_category"] for r in results),
                "suspicious_patterns": Counter(
                    pattern 
                    for r in results 
                    for pattern in r["features"]["suspicious_patterns"]
                ),
                "avg_domain_length": np.mean([r["features"]["length"] for r in results]),
                "avg_num_parts": np.mean([r["features"]["num_parts"] for r in results]),
                "avg_num_digits": np.mean([r["features"]["num_digits"] for r in results])
            }
        }
        
        # Save summary
        summary_file = os.path.join(self.base_dirs["analysis"], f"summary_{timestamp}.json")
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Summary statistics saved to {summary_file}")

def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    analyzer = DomainAnalyzer()
    analyzer.analyze_domains()

if __name__ == "__main__":
    main()
