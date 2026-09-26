import requests
from typing import Optional

class JinaFetcher:
    """Fetches any webpage, blog, or competitor URL as clean, LLM-ready markdown for free."""

    BASE_URL = "https://r.jina.ai/"

    @classmethod
    def fetch_markdown(cls, target_url: str) -> Optional[str]:
        """Prepends r.jina.ai/ to the URL to extract clean text without HTML noise."""
        try:
            endpoint = f"{cls.BASE_URL}{target_url}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MarketResearchReader/1.0",
                "X-Return-Format": "markdown"
            }
            resp = requests.get(endpoint, headers=headers, timeout=20)
            if resp.status_code == 200:
                return resp.text
        except Exception as e:
            pass
        return None
