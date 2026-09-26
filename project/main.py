import sys
import argparse
from dotenv import load_dotenv
from src.orchestration.router.model_router import ModelRouter
from src.storage.db import StorageManager
from src.ingestion.reddit.reddit_miner import RedditMiner
from src.intelligence.extraction.pain_extractor import PainExtractor
from src.analysis.clustering.cluster import ClusteringEngine
from src.analysis.opportunities.idea_ranker import OpportunityEngine
from src.diffusion.dossier.vault_exporter import DiffusionEngine

# Force UTF-8 to prevent Windows terminal crash on emojis
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

def ingest_reddit(subreddit: str, query: str, limit: int):
    print(f"=== INGESTING REDDIT: r/{subreddit} ===")
    db = StorageManager()
    miner = RedditMiner()
    
    evidence_list = miner.fetch_evidence(subreddit=subreddit, query=query, limit=limit)
    for ev in evidence_list:
        db.save_evidence(ev)
        
    print(f"\n✅ Ingestion Complete: Saved {len(evidence_list)} posts to DB.")

def extract_pains():
    print("=== EXTRACTING PAIN POINTS ===")
    router = ModelRouter()
    db = StorageManager()
    
    # We should grab un-processed evidence from DB, but for now we'll mock pulling all
    # TODO: Add `get_unprocessed_evidence()` to db.py
    print("Warning: Fetching unprocessed evidence is pending DB method update.")
    print("Run `eval_ground_truth.py` for extraction testing.")

def run_pipeline():
    """Run the entire end-to-end mock flow for testing."""
    print("=== RUNNING FULL VERTICAL SLICE ===")
    router = ModelRouter()
    db = StorageManager()
    
    miner = RedditMiner()
    evidence_list = miner.fetch_evidence(subreddit="smallbusiness", query="software", limit=3)
    for ev in evidence_list: db.save_evidence(ev)
        
    extractor = PainExtractor(router=router, storage=db)
    pain_points = extractor.process_evidence(evidence_list)
    
    cluster_engine = ClusteringEngine(router=router, storage=db)
    clusters = cluster_engine.build_clusters(pain_points)
    
    opp_engine = OpportunityEngine(router=router, storage=db)
    opportunities = []
    for cluster in clusters:
        opp = opp_engine.evaluate_cluster(cluster)
        if opp: opportunities.append(opp)

    diffusion = DiffusionEngine(router=router)
    for opp in opportunities:
        diffusion.generate_dossier(opp)
    
    print("\n✅ PIPELINE FINISHED")

def main():
    parser = argparse.ArgumentParser(description="Market Intelligence Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Run full test
    subparsers.add_parser("test-pipeline", help="Runs the full vertical slice test")
    
    # Ingestion
    ingest_parser = subparsers.add_parser("mine", help="Mine data from a source")
    ingest_parser.add_argument("source", choices=["reddit"], help="Source to mine")
    ingest_parser.add_argument("--subreddit", required=True, help="Target subreddit (e.g., smallbusiness)")
    ingest_parser.add_argument("--query", default="", help="Search query (e.g., software sucks)")
    ingest_parser.add_argument("--limit", type=int, default=50, help="Number of posts to fetch")

    args = parser.parse_args()

    if args.command == "test-pipeline":
        run_pipeline()
    elif args.command == "mine":
        if args.source == "reddit":
            ingest_reddit(args.subreddit, args.query, args.limit)

if __name__ == "__main__":
    main()
