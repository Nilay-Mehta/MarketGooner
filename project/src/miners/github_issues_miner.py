import os
import requests
from typing import List, Dict, Any, Optional

class GitHubIssuesMiner:
    """
    Mines unresolved issues, top-voted feature requests, and complaints on open-source
    and incumbent GitHub repositories.
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "").strip()
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "MarketIntelligenceMiner/1.0"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def search_issues(self, repo: str, query: str = "bug OR feature OR slow OR problem", limit: int = 15) -> List[Dict[str, Any]]:
        """Scans a repository for issues indicating user bottlenecks and unmet needs."""
        clean_repo = repo.replace("https://github.com/", "").strip().strip("/")
        search_query = f"repo:{clean_repo} is:issue is:open {query}"
        url = f"https://api.github.com/search/issues?q={requests.utils.quote(search_query)}&sort=comments&order=desc&per_page={limit}"
        
        results = []
        try:
            resp = requests.get(url, headers=self.headers, timeout=12)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                for item in items:
                    issue_id = str(item.get("id", ""))
                    title = item.get("title", "")
                    body = item.get("body") or ""
                    html_url = item.get("html_url", "")
                    comments = item.get("comments", 0)
                    reactions = item.get("reactions", {}).get("total_count", 0)
                    created_at = item.get("created_at", "")

                    results.append({
                        "source": f"github:{clean_repo}",
                        "source_id": f"gh_issue_{issue_id}",
                        "url": html_url,
                        "title": f"[{clean_repo}] {title}",
                        "content": body[:1200],
                        "score": reactions + comments,
                        "comments_count": comments,
                        "created_utc": 0,
                        "incumbent": clean_repo,
                        "friction_detected": True
                    })
        except Exception:
            pass

        return results
