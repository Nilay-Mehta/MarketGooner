import requests
from typing import List, Dict, Any

class HackerNewsMiner:
    """Zero-cost Hacker News miner using the free Algolia HN API."""

    BASE_URL = "https://hn.algolia.com/api/v1/search"

    def search_discussions(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Searches HN submissions and 'Ask HN' threads for topic friction."""
        results = []
        try:
            params = {
                "query": query,
                "tags": "(story,ask_hn,show_hn)",
                "hitsPerPage": limit
            }
            resp = requests.get(self.BASE_URL, params=params, timeout=15)
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                for h in hits:
                    title = h.get("title") or ""
                    story_text = h.get("story_text") or ""
                    url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
                    points = h.get("points") or 0
                    comments_count = h.get("num_comments") or 0

                    results.append({
                        "source": "hackernews",
                        "title": title,
                        "content": story_text[:1500],
                        "url": url,
                        "score": points,
                        "comments_count": comments_count,
                        "friction_detected": any(w in title.lower() for w in ["ask hn", "alternative", "replace", "pain", "problem", "broken"])
                    })
        except Exception as e:
            pass
        return results
