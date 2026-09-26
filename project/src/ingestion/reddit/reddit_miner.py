import requests
import time
import uuid
import re
from typing import List
from datetime import datetime
from src.storage.db import Evidence

class RedditMiner:
    """
    Ingestion Stage 1: Mines Reddit for Evidence.
    Uses free public endpoints (Arctic Shift / Pullpush) or standard Reddit JSON.
    Returns Canonical 'Evidence' objects for the pipeline.
    """

    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 MarketIntelligence/1.0'}

    def fetch_evidence(self, subreddit: str, query: str = "", limit: int = 15) -> List[Evidence]:
        """Fetches posts and returns standardized Evidence objects."""
        clean_sub = subreddit.replace("r/", "").strip()
        print(f"[*] Ingesting Reddit r/{clean_sub} | Query: '{query}'")
        
        # Try native Reddit JSON endpoint for simplicity (can add fallbacks later)
        url = f"https://www.reddit.com/r/{clean_sub}/search.json?q={query}&restrict_sr=1&limit={limit}&sort=new"
        
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            if res.status_code == 200:
                data = res.json().get('data', {}).get('children', [])
                return self._parse_reddit_json(data, clean_sub)
            else:
                print(f"[!] Reddit API error: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"[!] Request failed: {e}")
            
        return []

    def _parse_reddit_json(self, children: list, subreddit: str) -> List[Evidence]:
        evidence_list = []
        for post in children:
            item = post.get('data', {})
            
            # Filter out deleted/empty posts
            if item.get('selftext', '') in ['[deleted]', '[removed]']:
                continue
                
            text = f"Title: {item.get('title', '')}\n\n{item.get('selftext', '')}".strip()
            if len(text) < 50:
                continue # Skip very short posts
                
            evidence = Evidence(
                id=f"reddit_{item.get('id', uuid.uuid4().hex[:8])}",
                source="reddit",
                source_id=item.get('id', ''),
                url=f"https://reddit.com{item.get('permalink', '')}",
                timestamp=datetime.utcfromtimestamp(item.get('created_utc', time.time())).isoformat(),
                author=item.get('author', 'unknown'),
                text=text,
                metadata={
                    "subreddit": subreddit,
                    "upvotes": item.get('score', 0),
                    "comments": item.get('num_comments', 0)
                }
            )
            evidence_list.append(evidence)
            
        return evidence_list
