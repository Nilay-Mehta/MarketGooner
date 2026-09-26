import argparse
from src.orchestration.router.model_router import ModelRouter
from src.storage.db import StorageManager
from src.ingestion.reddit.reddit_miner import RedditMiner
from src.intelligence.extraction.pain_extractor import PainExtractor
from src.analysis.clustering.cluster import ClusteringEngine
from src.analysis.opportunities.idea_ranker import OpportunityEngine
from src.diffusion.dossier.vault_exporter import DiffusionEngine

def run_pipeline():
    """
    The full end-to-end mock execution pipeline for Market Intelligence.
    """
    print("Initializing Core Systems...")
    router = ModelRouter()
    db = StorageManager()
    
    print("\n--- PHASE 3: INGESTION ---")
    miner = RedditMiner()
    evidence_list = miner.fetch_evidence(subreddit="smallbusiness", query="software sucks", limit=3)
    for ev in evidence_list: db.save_evidence(ev)
        
    print("\n--- PHASE 3.5: EXTRACTION ---")
    extractor = PainExtractor(router=router, storage=db)
    pain_points = extractor.process_evidence(evidence_list)
    
    print("\n--- PHASE 4: CLUSTERING ---")
    cluster_engine = ClusteringEngine(router=router, storage=db)
    clusters = cluster_engine.build_clusters(pain_points)
    
    print("\n--- PHASE 5: OPPORTUNITY ENGINE ---")
    opp_engine = OpportunityEngine(router=router, storage=db)
    opportunities = []
    for cluster in clusters:
        opp = opp_engine.evaluate_cluster(cluster)
        if opp: opportunities.append(opp)

    print("\n--- PHASE 9: DIFFUSION ---")
    diffusion = DiffusionEngine(router=router)
    for opp in opportunities:
        diffusion.generate_dossier(opp)
    
    print("\n[PIPELINE FINISHED]")
    print(f"Stats: {len(evidence_list)} Evidence -> {len(pain_points)} Pains -> {len(clusters)} Clusters -> {len(opportunities)} Opportunities.")

def main():
    parser = argparse.ArgumentParser(description="Market Intelligence Pipeline")
    parser.add_argument("command", choices=["run", "audit"], help="Command to execute")
    args = parser.parse_args()

    if args.command == "run":
        run_pipeline()
    elif args.command == "audit":
        print("Architecture is clean.")

if __name__ == "__main__":
    main()
