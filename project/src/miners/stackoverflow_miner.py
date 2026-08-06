import html
import requests
from typing import List, Dict, Any, Optional

class StackOverflowMiner:
    """
    Zero-cost Stack Overflow miner using the public StackExchange 2.3 API.
    Identifies high-friction developer workflow questions, missing tooling, and workarounds.
    """

    BASE_URL = "https://api.stackexchange.com/2.3/search/advanced"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MarketIntelligenceMiner/1.0",
            "Accept-Encoding": "gzip"
        })

    def search_questions(self, query: str, tagged: Optional[str] = None, limit: int = 15) -> List[Dict[str, Any]]:
        """Searches Stack Overflow for high-friction developer problem discussions."""
        clean_q = query.strip()
        params = {
            "order": "desc",
            "sort": "relevance",
            "q": clean_q,
            "site": "stackoverflow",
            "filter": "withbody",
            "pagesize": limit
        }
        if tagged:
            params["tagged"] = tagged

        results = self._execute_search(params)
        
        # If strict query returned no results, try top 2 keywords
        if not results and " " in clean_q:
            terms = " ".join(clean_q.split()[:2])
            params["q"] = terms
            results = self._execute_search(params)

        return results[:limit]

    def _execute_search(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        try:
            resp = self.session.get(self.BASE_URL, params=params, timeout=10)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                for item in items:
                    qid = str(item.get("question_id", ""))
                    title = html.unescape(item.get("title", ""))
                    link = item.get("link", "")
                    score = int(item.get("score", 0))
                    answers = int(item.get("answer_count", 0))
                    tags = item.get("tags", [])
                    body = html.unescape(item.get("body", "")) if "body" in item else ""

                    results.append({
                        "source": "stackoverflow",
                        "source_id": f"so_{qid}",
                        "url": link,
                        "title": title,
                        "content": body[:1200] if body else title,
                        "score": score,
                        "comments_count": answers,
                        "created_utc": int(item.get("creation_date", 0)),
                        "tags": tags,
                        "friction_detected": True
                    })
        except Exception:
            pass
        return results
