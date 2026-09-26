import hashlib
import re
import time
import requests
from typing import List, Dict, Any, Optional
from src.storage import db

class AlternativeToMiner:
    """
    Mines user dissatisfaction, switch reasons, and competitor gaps from AlternativeTo
    via Jina Reader to identify specific weaknesses in incumbent enterprise & SMB software.
    """

    JINA_PREFIX = "https://r.jina.ai/"
    BASE_URL = "https://alternativeto.net/software"
    RATE_LIMIT_DELAY = 2.0  # Strict 1 req per 2.0 seconds

    def __init__(self, db_path: str = db.DEFAULT_DB_PATH):
        self.db_path = db_path
        self._last_request_time = 0.0

    def _rate_limited_get(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Performs a GET request respecting the 2.0s rate limit with exponential backoff on 429."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MarketIntelligence/2.0",
            "X-Return-Format": "markdown"
        }

        for attempt in range(max_retries):
            try:
                self._last_request_time = time.time()
                resp = requests.get(url, headers=headers, timeout=25)
                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code == 429:
                    sleep_time = (attempt + 1) * 3.0
                    print(f"  [!] Jina 429 rate limit hit. Backing off {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    return None
            except Exception:
                time.sleep(2.0)
        return None

    def fetch_alternatives(self, incumbent_name: str, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Fetches AlternativeTo page for an incumbent software, extracting why users look for alternatives.
        Target: https://alternativeto.net/software/{slug}/
        """
        clean_slug = incumbent_name.strip().lower().replace(" ", "-")
        target_url = f"{self.BASE_URL}/{clean_slug}/"
        jina_url = f"{self.JINA_PREFIX}{target_url}"

        print(f"[>] Mining AlternativeTo weaknesses for '{clean_slug}' via Jina...")
        raw_markdown = self._rate_limited_get(jina_url)
        if not raw_markdown:
            print(f"  [-] Could not retrieve AlternativeTo page for '{clean_slug}'.")
            return []

        items = self._parse_alternativeto_markdown(raw_markdown, clean_slug, target_url, limit)
        saved_count = 0
        for item in items:
            inserted_id = db.insert_raw_item(
                source=item["source"],
                source_id=item["source_id"],
                url=item["url"],
                title=item["title"],
                content=item["content"],
                score=item["score"],
                comments_count=0,
                created_utc=item["created_utc"],
                topic_query=f"alternativeto:{clean_slug}",
                mentioned_incumbent=clean_slug,
                db_path=self.db_path
            )
            if inserted_id:
                saved_count += 1

        print(f"  [+] Parsed {len(items)} discussion points for '{clean_slug}' ({saved_count} new saved to DB).")
        return items

    def _parse_alternativeto_markdown(self, markdown: str, incumbent_slug: str, target_url: str, limit: int) -> List[Dict[str, Any]]:
        """Parses reviews, alternative descriptions, and complaints from markdown text."""
        items = []
        
        # Split by markdown headers or reviews
        sections = re.split(r"(?:###\s+|##\s+)", markdown)
        for section in sections:
            if len(items) >= limit:
                break

            clean_sec = section.strip()
            if len(clean_sec) < 50:
                continue

            # Check if section discusses why someone left or dislikes the tool
            pain_keywords = ["dislike", "expensive", "problem", "missing", "lack", "complex", "slow", "bug", "switched", "pricing", "alternative", "support", "bloated"]
            contains_pain = any(kw in clean_sec.lower() for kw in pain_keywords)
            if not contains_pain:
                continue

            lines = [l.strip() for l in clean_sec.split("\n") if l.strip()]
            title = lines[0][:100] if lines else f"AlternativeTo feedback for {incumbent_slug}"
            content = clean_sec[:2000]

            body_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:12]
            source_id = f"alt_{incumbent_slug}_{body_hash}"

            items.append({
                "source": f"alternativeto:{incumbent_slug}",
                "source_id": source_id,
                "url": target_url,
                "title": title,
                "content": content,
                "score": 5,
                "created_utc": int(time.time()),
                "mentioned_incumbent": incumbent_slug
            })

        return items
