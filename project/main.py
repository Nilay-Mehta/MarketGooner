import argparse
from src.orchestration.router.model_router import ModelRouter
from src.storage.db import StorageManager
from src.ingestion.reddit.reddit_miner import RedditMiner
from src.intelligence.extraction.pain_extractor import PainExtractor

def run_pipeline():
    """
    The main execution pipeline for the Market Intelligence system.
    Following the vertical slice architecture:
    Reddit -> Normalization -> Extraction -> JEV -> Clustering -> Opportunity -> Deep Reasoning
    """
    print("Initializing Model Router & Storage...")
    router = ModelRouter()
    db = StorageManager()
    
    print("\n--- PHASE 3: INGESTION ---")
    miner = RedditMiner()
    # Fetch a small test batch of evidence
    evidence_list = miner.fetch_evidence(subreddit="smallbusiness", query="software sucks", limit=3)
    
    for ev in evidence_list:
        db.save_evidence(ev)
        print(f"Saved Evidence: {ev.id} - {ev.url}")
        
    print("\n--- PHASE 3.5: EXTRACTION ---")
    extractor = PainExtractor(router=router, storage=db)
    pain_points = extractor.process_evidence(evidence_list)
    
    print("\n[PIPELINE READY]")
    print(f"Successfully processed {len(pain_points)} pain points from Reddit to DB.")
    print("Next step: Build the Analysis/Clustering Engine (Phase 4).")

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
