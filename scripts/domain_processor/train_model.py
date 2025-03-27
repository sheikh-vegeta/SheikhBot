from transformers import AutoModelForSequenceClassification, AutoTokenizer, TrainingArguments, Trainer
from datasets import load_dataset
import os
import logging

logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self):
        self.hf_token = os.environ["HF_TOKEN"]
        self.dataset_repo = os.environ["DATASET_REPO"]
        self.model_repo = os.environ["MODEL_REPO"]
        
    def prepare_dataset(self):
        """Load and prepare dataset for training"""
        dataset = load_dataset(self.dataset_repo)
        return dataset
        
    def train_model(self):
        """Train and push model to HuggingFace"""
        try:
            # Load base model and tokenizer
            model = AutoModelForSequenceClassification.from_pretrained(
                "distilbert-base-uncased", 
                num_labels=2
            )
            tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir="./results",
                num_train_epochs=3,
                per_device_train_batch_size=16,
                per_device_eval_batch_size=64,
                warmup_steps=500,
                weight_decay=0.01,
                logging_dir='./logs'
            )
            
            # Initialize trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=self.prepare_dataset()["train"]
            )
            
            # Train model
            trainer.train()
            
            # Push to HuggingFace
            model.push_to_hub(
                self.model_repo,
                token=self.hf_token,
                private=False
            )
            tokenizer.push_to_hub(
                self.model_repo,
                token=self.hf_token,
                private=False
            )
            
            logger.info(f"Successfully trained and pushed model to {self.model_repo}")
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")

def main():
    trainer = ModelTrainer()
    trainer.train_model()

if __name__ == "__main__":
    main()
