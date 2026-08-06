import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.miners.reddit_miner import RedditMiner
from src.miners.hn_miner import HackerNewsMiner
from src.miners.github_miner import GitHubMiner
from src.miners.g2_miner import G2Miner
from src.miners.producthunt_miner import ProductHuntMiner
from src.miners.stackoverflow_miner import StackOverflowMiner
from src.miners.github_issues_miner import GitHubIssuesMiner

class TestMiners(unittest.TestCase):
    def test_reddit_miner_real_api(self):
        miner = RedditMiner(request_delay=0.5)
        results = miner.search_subreddit("devops", "monitoring", limit=3)
        self.assertGreater(len(results), 0, "Should fetch at least 1 real Reddit post")
        first = results[0]
        self.assertIn("score", first)
        self.assertIn("num_comments", first)
        self.assertIn("created_utc", first)
        self.assertIn("top_comments", first)
        self.assertTrue(first["url"].startswith("http"))
        print(f"\n[PASS] Reddit Miner: Fetched {len(results)} items. Sample: {first['title'][:50]} (score={first['score']}, comments={first['num_comments']})")

    def test_hn_miner(self):
        miner = HackerNewsMiner()
        results = miner.search_discussions("database", limit=3)
        self.assertGreater(len(results), 0, "Should fetch at least 1 HN post")
        print(f"\n[PASS] HN Miner: Fetched {len(results)} items. Sample: {results[0]['title'][:50]}")

    def test_github_miner(self):
        miner = GitHubMiner()
        results = miner.search_repositories("observability", limit=3)
        self.assertGreater(len(results), 0, "Should fetch at least 1 GitHub repo")
        print(f"\n[PASS] GitHub Miner: Fetched {len(results)} items. Sample: {results[0]['name']}")

    def test_stackoverflow_miner(self):
        miner = StackOverflowMiner()
        results = miner.search_questions("kubernetes egress cost", limit=3)
        self.assertGreater(len(results), 0, "Should fetch at least 1 SO question")
        print(f"\n[PASS] StackOverflow Miner: Fetched {len(results)} items. Sample: {results[0]['title'][:50]}")

    def test_github_issues_miner(self):
        miner = GitHubIssuesMiner()
        results = miner.search_issues("prometheus/prometheus", limit=3)
        self.assertGreater(len(results), 0, "Should fetch at least 1 GitHub issue")
        print(f"\n[PASS] GitHub Issues Miner: Fetched {len(results)} items. Sample: {results[0]['title'][:50]}")

if __name__ == "__main__":
    unittest.main()
