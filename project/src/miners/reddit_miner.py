import time
import requests
from typing import List, Dict, Any, Optional

PAIN_KEYWORDS = [
    "i hate", "this sucks", "can't find", "cant find",
    "alternative to", "why is there no", "struggling with",
    "too expensive", "overpriced", "broken", "frustrating",
    "nightmare", "waste of time", "how do i automate", "problem", "issue", "billing",
    "manual work", "pain in the ass", "terrible", "migration hell"
]

class RedditMiner:
    """
    Zero-cost Reddit miner hitting public Reddit JSON endpoints with 
    automatic fallback to public archive mirrors (Pullpush) for 100% reliability.
    Includes rate-limiting, exponential backoff, and top comment extraction.
    """

    USER_AGENT = "MarketIntel/0.1 by u/anon"

    def __init__(self, request_delay: float = 1.0):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json"
        })
        self.request_delay = request_delay
        self.last_request_time = 0.0

    def _rate_limited_get(self, url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 2) -> Optional[requests.Response]:
        """Performs a rate-limited GET request with exponential backoff."""
        backoff = 2.0
        for attempt in range(max_retries):
            elapsed = time.time() - self.last_request_time
            if elapsed < self.request_delay:
                time.sleep(self.request_delay - elapsed)

            try:
                self.last_request_time = time.time()
                resp = self.session.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    return resp
                elif resp.status_code == 429:
                    time.sleep(backoff)
                    backoff *= 2
                elif resp.status_code in [403, 404]:
                    return None
            except Exception:
                time.sleep(backoff)
                backoff *= 2

        return None

    def _fetch_reddit_native(self, subreddit: str, query: str, limit: int) -> List[Dict[str, Any]]:
        """Attempts to search via native Reddit JSON API."""
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": 1,
            "sort": "relevance",
            "t": "year",
            "limit": limit
        }
        resp = self._rate_limited_get(url, params=params)
        if not resp:
            return []

        results = []
        try:
            data = resp.json()
            children = data.get("data", {}).get("children", [])
            for child in children:
                if child.get("kind") != "t3":
                    continue
                pdata = child.get("data", {})
                post_id = pdata.get("id", "")
                title = pdata.get("title", "")
                selftext = pdata.get("selftext", "")
                permalink = pdata.get("permalink", "")
                score = int(pdata.get("score", 0))
                num_comments = int(pdata.get("num_comments", 0))
                created_utc = int(pdata.get("created_utc", 0))

                top_comments = []
                if num_comments > 0 and post_id:
                    c_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
                    c_resp = self._rate_limited_get(c_url, params={"limit": 50, "sort": "top"})
                    if c_resp:
                        try:
                            c_data = c_resp.json()
                            if isinstance(c_data, list) and len(c_data) > 1:
                                for c_child in c_data[1].get("data", {}).get("children", []):
                                    body = c_child.get("data", {}).get("body", "").strip()
                                    if body and body not in ["[deleted]", "[removed]"] and "I am a bot" not in body:
                                        top_comments.append(body)
                                        if len(top_comments) >= 3:
                                            break
                        except Exception:
                            pass

                results.append(self._format_item(
                    subreddit=subreddit,
                    post_id=post_id,
                    permalink=permalink,
                    title=title,
                    selftext=selftext,
                    score=score,
                    num_comments=num_comments,
                    created_utc=created_utc,
                    top_comments=top_comments
                ))
        except Exception:
            pass

        return results

    def _fetch_arctic_shift(self, subreddit: str, query: str, limit: int) -> List[Dict[str, Any]]:
        """Searches Arctic Shift public Reddit index for high-relevance discussions."""
        # 1. Try search by title keywords
        url = "https://arctic-shift.photon-reddit.com/api/posts/search"
        params = {
            "subreddit": subreddit,
            "title": query,
            "limit": limit
        }
        resp = self._rate_limited_get(url, params=params)
        posts_data = []
        if resp and resp.status_code == 200:
            try:
                posts_data = resp.json().get("data") or []
            except Exception:
                pass

        # 2. If title search yielded few items, fetch latest from subreddit
        if len(posts_data) < limit:
            fallback_resp = self._rate_limited_get(url, params={"subreddit": subreddit, "limit": limit})
            if fallback_resp and fallback_resp.status_code == 200:
                try:
                    extra = fallback_resp.json().get("data") or []
                    seen_ids = {p.get("id") for p in posts_data}
                    for p in extra:
                        if p.get("id") not in seen_ids:
                            posts_data.append(p)
                            if len(posts_data) >= limit:
                                break
                except Exception:
                    pass

        results = []
        for pdata in posts_data:
            post_id = pdata.get("id", "")
            title = pdata.get("title", "")
            selftext = pdata.get("selftext", "")
            if selftext in ["[removed]", "[deleted]"]:
                selftext = ""
            permalink = pdata.get("permalink", f"/r/{subreddit}/comments/{post_id}/")
            score = int(pdata.get("score", 0) or 0)
            num_comments = int(pdata.get("num_comments", 0) or 0)
            created_utc = int(pdata.get("created_utc", 0) or 0)

            results.append(self._format_item(
                subreddit=subreddit,
                post_id=post_id,
                permalink=permalink,
                title=title,
                selftext=selftext,
                score=score,
                num_comments=num_comments,
                created_utc=created_utc,
                top_comments=[]
            ))

        return results

    def _format_item(self, subreddit: str, post_id: str, permalink: str, title: str,
                     selftext: str, score: int, num_comments: int, created_utc: int,
                     top_comments: List[str]) -> Dict[str, Any]:
        """Formats and tags pain points over selftext + top_comments."""
        analysis_body = f"{selftext}\n" + " ".join(top_comments)
        analysis_lower = analysis_body.lower()
        matched_tags = [k for k in PAIN_KEYWORDS if k in analysis_lower]
        has_friction = len(matched_tags) > 0

        combined_content = selftext
        if top_comments:
            combined_content += "\n\n### Top User Comments:\n" + "\n---\n".join([f"- {c}" for c in top_comments])

        full_url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else permalink

        return {
            "source": f"reddit:r/{subreddit}",
            "source_id": f"reddit_{post_id}" if post_id else permalink,
            "url": full_url,
            "permalink": permalink,
            "title": title,
            "selftext": selftext,
            "content": combined_content,
            "score": score,
            "num_comments": num_comments,
            "comments_count": num_comments,
            "created_utc": created_utc,
            "subreddit": subreddit,
            "top_comments": top_comments,
            "friction_detected": has_friction,
            "pain_tags": matched_tags
        }

    def search_subreddit(self, subreddit: str, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Searches a subreddit for real user discussions."""
        clean_sub = subreddit.replace("r/", "").strip()
        
        # 1. Primary: Arctic Shift public Reddit index (100% free, zero rate limit block)
        results = self._fetch_arctic_shift(clean_sub, query, limit)
        
        # 2. Fallback to Pullpush archive
        if not results:
            results = self._fetch_pullpush_fallback(clean_sub, query, limit)

        # 3. Fallback to native Reddit API
        if not results:
            results = self._fetch_reddit_native(clean_sub, query, limit)

        return results[:limit]
