import requests
import time
import uuid
import datetime
from typing import List
from src.storage.db import Evidence

class RedditMiner:
    """
    Ingestion Stage 1: Mines Reddit for Evidence.
    Uses Reddit JSON endpoints with pagination.
    Returns Canonical 'Evidence' objects for the pipeline.
    """

    def __init__(self):
        # Reddit requires a unique User-Agent to avoid 429 Too Many Requests
        self.headers = {'User-Agent': 'windows:market_intelligence_pipeline:v1.0 (by /u/marketgooner)'}

    def fetch_evidence(self, subreddit: str, query: str = "", limit: int = 15) -> List[Evidence]:
        """Fetches posts and returns standardized Evidence objects using pagination."""
        clean_sub = subreddit.replace("r/", "").strip()
        print(f"[*] Ingesting Reddit r/{clean_sub} | Query: '{query}' | Target: {limit} posts")
        
        evidence_list = []
        after = None
        
        while len(evidence_list) < limit:
            # We fetch up to 100 per request (Reddit's max API limit per page)
            batch_size = min(100, limit - len(evidence_list))
            url = f"https://www.reddit.com/r/{clean_sub}/search.json?q={query}&restrict_sr=1&limit={batch_size}&sort=new"
            if after:
                url += f"&after={after}"
                
            try:
                res = requests.get(url, headers=self.headers, timeout=15)
                if res.status_code == 200:
                    json_data = res.json().get('data', {})
                    children = json_data.get('children', [])
                    after = json_data.get('after')
                    
                    if not children:
                        break # No more results
                        
                    batch_evidence = self._parse_reddit_json(children, clean_sub)
                    evidence_list.extend(batch_evidence)
                    
                    print(f"  -> Fetched batch: {len(batch_evidence)} valid items (Total: {len(evidence_list)})")
                    
                    if not after:
                        break # End of pagination
                        
                    time.sleep(2) # Respect Reddit API rate limits (1 req / sec)
                else:
                    print(f"[!] Reddit API error: {res.status_code}")
                    break
            except Exception as e:
                print(f"[!] Request failed: {e}")
                break
                
        return evidence_list[:limit]

    def _parse_reddit_json(self, children: list, subreddit: str) -> List[Evidence]:
        evidence_list = []
        for post in children:
            item = post.get('data', {})
            
            # Filter out deleted/empty posts
            if item.get('selftext', '') in ['[deleted]', '[removed]', '']:
                continue
                
            text = f"Title: {item.get('title', '')}\n\n{item.get('selftext', '')}".strip()
            if len(text) < 50:
                continue # Skip very short posts
                
            # Use timezone-aware UTC datetime (fix deprecation warning)
            dt = datetime.datetime.fromtimestamp(item.get('created_utc', time.time()), datetime.timezone.utc)
            
            evidence = Evidence(
                id=f"reddit_{item.get('id', uuid.uuid4().hex[:8])}",
                source="reddit",
                source_id=item.get('id', ''),
                url=f"https://reddit.com{item.get('permalink', '')}",
                timestamp=dt.isoformat(),
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
