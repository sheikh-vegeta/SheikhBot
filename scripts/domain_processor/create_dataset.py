import os
from datasets import Dataset
from huggingface_hub import HfApi
import json
import logging

logger = logging.getLogger(__name__)

class DatasetBuilder:
    def __init__(self):
        self.hf_token = os.environ["HF_TOKEN"]
        self.dataset_repo = os.environ["DATASET_REPO"]
        self.api = HfApi()
    
    def load_domain_data(self):
        """Load and combine all domain data"""
        domains = []
        
        # Load WhoisDS data
        whoisds_dir = "data/whoisds"
        for file in os.listdir(whoisds_dir):
            if file.endswith(".txt"):
                date = file.replace(".txt", "")
                with open(os.path.join(whoisds_dir, file)) as f:
                    for line in f:
                        domains.append({
                            "domain": line.strip(),
                            "source": "whoisds",
                            "date": date,
                            "type": "new_registration"
                        })
        
        # Load phishing data
        phishing_file = "data/phishing/daily.txt"
        if os.path.exists(phishing_file):
            with open(phishing_file) as f:
                for line in f:
                    domains.append({
                        "domain": line.strip(),
                        "source": "phishing_list",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "type": "phishing"
                    })
        
        return domains
    
    def create_and_push_dataset(self):
        """Create and push dataset to HuggingFace"""
        try:
            domains = self.load_domain_data()
            dataset = Dataset.from_dict({
                "domain": [d["domain"] for d in domains],
                "source": [d["source"] for d in domains],
                "date": [d["date"] for d in domains],
                "type": [d["type"] for d in domains]
            })
            
            # Push to HuggingFace
            dataset.push_to_hub(
                self.dataset_repo,
                token=self.hf_token,
                private=False
            )
            logger.info(f"Successfully pushed dataset to {self.dataset_repo}")
            
        except Exception as e:
            logger.error(f"Error creating/pushing dataset: {str(e)}")

def main():
    builder = DatasetBuilder()
    builder.create_and_push_dataset()

if __name__ == "__main__":
    main()
