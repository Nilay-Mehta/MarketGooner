import argparse
from src.orchestration.router.model_router import ModelRouter
from src.storage.db import StorageManager

def run_pipeline():
    """
    The main execution pipeline for the Market Intelligence system.
    Following the vertical slice architecture:
    Reddit -> Normalization -> Extraction -> JEV -> Clustering -> Opportunity -> Deep Reasoning
    """
    print("Initializing Model Router...")
    router = ModelRouter()
    
    print("Initializing Storage Manager...")
    db = StorageManager()
    
    print("\n[PIPELINE READY]")
    print("Next step: Build the Ingestion layer (Reddit) to feed data into the storage manager.")
    print("Then we will build the Extraction layer to process it.")

def main():
    parser = argparse.ArgumentParser(description="Market Intelligence Pipeline")
    parser.add_argument("command", choices=["run", "audit"], help="Command to execute")
    args = parser.parse_args()

    if args.command == "run":
        run_pipeline()
    elif args.command == "audit":
        print("Run `python -c \"import os...\"` or look at phase_0_audit.md for the architecture state.")

if __name__ == "__main__":
    main()
