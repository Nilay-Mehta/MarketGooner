import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage import db
from src.extractors.pain_extractor import PainExtractor
from src.extractors.cluster import ProblemClusterer
from src.extractors.idea_ranker import IdeaRanker

class TestExtractionPipeline(unittest.TestCase):
    def setUp(self):
        self.test_db_path = os.path.join(os.path.dirname(__file__), "test_pipeline.db")
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except Exception:
                pass
        db.init_db(self.test_db_path)

    def test_full_pipeline_flow(self):
        # 1. Insert simulated raw items
        item_id1 = db.insert_raw_item(
            source="reddit:r/devops",
            source_id="post_1",
            url="https://reddit.com/r/devops/1",
            title="Why does Datadog APM cost so much?",
            content="Our Datadog bill exploded to $15k/month because of custom metrics. We need an open source alternative.",
            score=50,
            comments_count=20,
            db_path=self.test_db_path
        )
        item_id2 = db.insert_raw_item(
            source="hn",
            source_id="hn_2",
            url="https://news.ycombinator.com/item?id=2",
            title="Ask HN: Datadog pricing is out of control",
            content="Anyone else struggling with Datadog pricing? We are moving to Prometheus/Grafana but dashboard migration is painful.",
            score=120,
            comments_count=45,
            db_path=self.test_db_path
        )

        unextracted = db.get_unextracted_raw_items(db_path=self.test_db_path)
        self.assertEqual(len(unextracted), 2)

        # 2. Extract Pains
        extractor = PainExtractor(db_path=self.test_db_path)
        extracted = extractor.extract_pains_from_items(unextracted)
        print(f"\n[PASS] Pain Extractor: Extracted {len(extracted)} pain records.")
        self.assertGreater(len(extracted), 0)

        # 3. Cluster Pains
        clusterer = ProblemClusterer(db_path=self.test_db_path)
        clusters = clusterer.cluster_pain_points()
        print(f"[PASS] Clusterer: Generated {len(clusters)} clusters.")
        self.assertGreater(len(clusters), 0)

        # 4. Rank Ideas
        ranker = IdeaRanker(db_path=self.test_db_path)
        ideas = ranker.rank_clusters(min_cluster_size=1)
        print(f"[PASS] Ranker: Generated {len(ideas)} scored ideas.")
        self.assertGreater(len(ideas), 0)
        top = ideas[0]
        print(f"       Top Idea: {top.get('name')} | Wedge: {top.get('wedge')} | Score: {top.get('score_total')}/50")
        self.assertGreater(top.get('score_total', 0), 0)

if __name__ == "__main__":
    unittest.main()
