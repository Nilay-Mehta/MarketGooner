import os
import uuid
import datetime
import praw
from typing import List
from src.storage.db import Evidence

class RedditMiner:
    """
    Ingestion Stage 1: Mines Reddit for Evidence.
    Uses the official, free Reddit API via PRAW.
    Extremely stable and immune to public proxy 429 blocks.
    Requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env.
    """

    def __init__(self):
        client_id = os.getenv("REDDIT_CLIENT_ID", "")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        user_agent = os.getenv("REDDIT_USER_AGENT", "windows:market_intelligence_pipeline:v1.0 (by /u/marketgooner)")
        
        self.is_configured = bool(client_id and client_secret)
        
        if self.is_configured:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )

    def fetch_evidence(self, subreddit: str, query: str = "", limit: int = 50) -> List[Evidence]:
        """Fetches posts using PRAW and returns standardized Evidence objects."""
        if not self.is_configured:
            print("[!] Reddit API keys missing. Please add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to .env")
            return []
            
        clean_sub = subreddit.replace("r/", "").strip()
        print(f"[*] Ingesting via PRAW r/{clean_sub} | Query: '{query}' | Target: {limit} posts")
        
        evidence_list = []
        
        try:
            sub = self.reddit.subreddit(clean_sub)
            search_results = sub.search(query, sort="new", limit=limit)
            
            for submission in search_results:
                # Filter out empty/deleted posts
                if submission.selftext in ['[deleted]', '[removed]', '']:
                    continue
                    
                text = f"Title: {submission.title}\n\n{submission.selftext}".strip()
                if len(text) < 50:
                    continue
                    
                dt = datetime.datetime.fromtimestamp(submission.created_utc, datetime.timezone.utc)
                
                evidence = Evidence(
                    id=f"reddit_{submission.id}",
                    source="reddit",
                    source_id=submission.id,
                    url=f"https://reddit.com{submission.permalink}",
                    timestamp=dt.isoformat(),
                    author=str(submission.author) if submission.author else "unknown",
                    text=text,
                    metadata={
                        "subreddit": clean_sub,
                        "upvotes": submission.score,
                        "comments": submission.num_comments
                    }
                )
                evidence_list.append(evidence)
                
            print(f"  -> Fetched {len(evidence_list)} valid items.")
            
        except Exception as e:
            print(f"[!] PRAW Request failed: {e}")
            
        return evidence_list
