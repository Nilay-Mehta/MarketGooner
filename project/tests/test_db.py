import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage import db

class TestStorageDB(unittest.TestCase):
    def setUp(self):
        self.test_db_path = os.path.join(os.path.dirname(__file__), "test_intel.db")
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        db.init_db(self.test_db_path)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_insert_and_dedupe_raw_items(self):
        item_id1 = db.insert_raw_item(
            source="reddit:r/devops",
            source_id="reddit_123",
            url="https://reddit.com/r/devops/123",
            title="Kubernetes cost monitoring pain",
            content="Datadog is too expensive, bill was $12,000",
            score=45,
            comments_count=18,
            topic_query="devops monitoring",
            db_path=self.test_db_path
        )
        self.assertIsNotNone(item_id1)

        # Duplicate insert should return None
        item_id2 = db.insert_raw_item(
            source="reddit:r/devops",
            source_id="reddit_123",
            url="https://reddit.com/r/devops/123",
            title="Kubernetes cost monitoring pain",
            db_path=self.test_db_path
        )
        self.assertIsNone(item_id2)

    def test_pain_point_and_idea_lifecycle(self):
        raw_id = db.insert_raw_item(
            source="hn",
            source_id="hn_999",
            url="https://news.ycombinator.com/item?id=999",
            title="Ask HN: Why is cloud egress so expensive?",
            score=100,
            db_path=self.test_db_path
        )

        pain_id = db.insert_pain_point(
            raw_item_id=raw_id,
            summary="S3 egress fees are eating 40% of AI startup margin",
            incumbent="AWS S3",
            severity="financial_bleed",
            willingness_to_pay="$500/mo",
            persona="MLOps Lead",
            quote="We spent $4k on egress last month alone.",
            db_path=self.test_db_path
        )
        self.assertIsNotNone(pain_id)

        cluster_id = db.upsert_cluster(
            label="Cloud Egress & GPU Model Caching",
            size=5,
            source_diversity=2,
            avg_severity_score=8.5,
            wtp_evidence_count=3,
            db_path=self.test_db_path
        )
        self.assertIsNotNone(cluster_id)

        db.update_pain_cluster(pain_id, cluster_id, db_path=self.test_db_path)

        idea_id = db.insert_idea(
            cluster_id=cluster_id,
            name="EgressShield",
            wedge="Transparent P2P Edge Cache for AI Model Weights",
            icp="AI & Video Inference Startups",
            score_frequency=8,
            score_wtp=9,
            score_incumbent_weakness=8,
            score_feasibility=7,
            score_distribution=8,
            representative_quote="We spent $4k on egress last month alone.",
            db_path=self.test_db_path
        )
        self.assertIsNotNone(idea_id)

        ideas = db.list_ideas(db_path=self.test_db_path)
        self.assertEqual(len(ideas), 1)
        self.assertEqual(ideas[0]["score_total"], 40)
        self.assertEqual(ideas[0]["cluster_label"], "Cloud Egress & GPU Model Caching")
        print("\n[PASS] SQLite Database Lifecycle & Relationships verified!")

if __name__ == "__main__":
    unittest.main()
