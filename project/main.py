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
    for ev in evidence_list: db.save_evidence(ev)
    print(f"✅ Ingestion Complete: Saved {len(evidence_list)} posts to DB.")

def extract_pains():
    print("=== EXTRACTING PAIN POINTS ===")
    router = ModelRouter()
    db = StorageManager()
    evidence_list = db.get_unprocessed_evidence(limit=50)
    if not evidence_list:
        print("No unprocessed evidence found.")
        return
    extractor = PainExtractor(router=router, storage=db)
    pain_points = extractor.process_evidence(evidence_list)
    print(f"✅ Extraction Complete: Generated {len(pain_points)} pain points.")

def cluster_pains():
    print("=== CLUSTERING PAIN POINTS ===")
    router = ModelRouter()
    db = StorageManager()
    pain_points = db.get_unclustered_pain_points()
    if not pain_points:
        print("No unclustered pain points found.")
        return
    engine = ClusteringEngine(router=router, storage=db)
    clusters = engine.build_clusters(pain_points)
    print(f"✅ Clustering Complete: Built {len(clusters)} clusters.")

def evaluate_opportunities():
    print("=== EVALUATING OPPORTUNITIES ===")
    router = ModelRouter()
    db = StorageManager()
    clusters = db.get_unevaluated_clusters()
    if not clusters:
        print("No unevaluated clusters found.")
        return
    engine = OpportunityEngine(router=router, storage=db)
    opportunities = []
    for cluster in clusters:
        opp = engine.evaluate_cluster(cluster)
        if opp: opportunities.append(opp)
    print(f"✅ Evaluation Complete: Found {len(opportunities)} viable opportunities.")

def diffuse_dossiers():
    print("=== GENERATING DOSSIERS ===")
    router = ModelRouter()
    db = StorageManager()
    opportunities = db.get_opportunities()
    if not opportunities:
        print("No opportunities found.")
        return
    diffusion = DiffusionEngine(router=router)
    for opp in opportunities:
        diffusion.generate_dossier(opp)
    print("✅ Diffusion Complete.")

def main():
    parser = argparse.ArgumentParser(description="Market Intelligence Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    ingest_parser = subparsers.add_parser("mine", help="Mine data from a source")
    ingest_parser.add_argument("source", choices=["reddit"], help="Source to mine")
    ingest_parser.add_argument("--subreddit", required=True, help="Target subreddit")
    ingest_parser.add_argument("--query", default="", help="Search query")
    ingest_parser.add_argument("--limit", type=int, default=50, help="Number of posts")

    subparsers.add_parser("extract", help="Extract pain points from unprocessed evidence")
    subparsers.add_parser("cluster", help="Cluster unclustered pain points")
    subparsers.add_parser("evaluate", help="Evaluate clusters into opportunities")
    subparsers.add_parser("diffuse", help="Generate dossiers for opportunities")

    args = parser.parse_args()

    if args.command == "mine" and args.source == "reddit":
        ingest_reddit(args.subreddit, args.query, args.limit)
    elif args.command == "extract":
        extract_pains()
    elif args.command == "cluster":
        cluster_pains()
    elif args.command == "evaluate":
        evaluate_opportunities()
    elif args.command == "diffuse":
        diffuse_dossiers()

if __name__ == "__main__":
    main()
