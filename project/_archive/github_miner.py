import os
import requests
from typing import List, Dict, Any, Optional

class GitHubMiner:
    """Mines GitHub for market saturation and unresolved customer feature requests using GitHub PAT."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "").strip()
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "MarketIntelligenceMiner/1.0"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def search_repositories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Searches GitHub repos to evaluate open-source market saturation and star velocity."""
        url = f"https://api.github.com/search/repositories?q={requests.utils.quote(query)}&sort=stars&order=desc&per_page={limit}"
        results = []
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                for item in items:
                    results.append({
                        "name": item.get("full_name"),
                        "description": item.get("description"),
                        "stars": item.get("stargazers_count"),
                        "forks": item.get("forks_count"),
                        "open_issues": item.get("open_issues_count"),
                        "url": item.get("html_url"),
                        "topics": item.get("topics", []),
                        "updated_at": item.get("updated_at")
                    })
        except Exception:
            pass
        return results

    def search_unresolved_issues(self, repo: str, query: str = "feature request", limit: int = 10) -> List[Dict[str, Any]]:
        """Scans a competitor's repository for top upvoted feature requests and unresolved user complaints."""
        search_query = f"repo:{repo} is:issue is:open {query}"
        url = f"https://api.github.com/search/issues?q={requests.utils.quote(search_query)}&sort=reactions-+1-desc&per_page={limit}"
        results = []
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                for item in items:
                    results.append({
                        "title": item.get("title"),
                        "body": (item.get("body") or "")[:800],
                        "comments_count": item.get("comments", 0),
                        "reactions_plus1": item.get("reactions", {}).get("+1", 0),
                        "url": item.get("html_url"),
                        "created_at": item.get("created_at")
                    })
        except Exception:
            pass
        return results
