import hashlib
import re
import time
import requests
from typing import List, Dict, Any, Optional
from src.storage import db

class ShopifyReviewsMiner:
    """
    Mines 1, 2, and 3-star merchant complaints and negative reviews from the Shopify App Store
    via Jina Reader to discover non-developer B2B e-commerce pain points.
    """

    JINA_PREFIX = "https://r.jina.ai/"
    BASE_URL = "https://apps.shopify.com"
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

    def fetch_app_reviews(self, app_slug: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetches 1, 2, and 3-star reviews for a Shopify app.
        Target URL: https://apps.shopify.com/{app_slug}/reviews?sort_by=newest&filter=1,2,3
        """
        clean_slug = app_slug.strip("/ ").split("/")[-1]
        target_url = f"{self.BASE_URL}/{clean_slug}/reviews?sort_by=newest&filter=1,2,3"
        jina_url = f"{self.JINA_PREFIX}{target_url}"

        print(f"[>] Mining Shopify reviews for '{clean_slug}' via Jina...")
        raw_markdown = self._rate_limited_get(jina_url)
        if not raw_markdown:
            print(f"  [-] Could not retrieve reviews for Shopify app '{clean_slug}'.")
            return []

        reviews = self._parse_reviews_markdown(raw_markdown, clean_slug, target_url, limit)
        saved_count = 0
        for r in reviews:
            inserted_id = db.insert_raw_item(
                source=r["source"],
                source_id=r["source_id"],
                url=r["url"],
                title=r["title"],
                content=r["content"],
                score=r["score"],
                comments_count=0,
                created_utc=r["created_utc"],
                topic_query=f"shopify:{clean_slug}",
                mentioned_incumbent=None,
                db_path=self.db_path
            )
            if inserted_id:
                saved_count += 1

        print(f"  [+] Parsed {len(reviews)} reviews for '{clean_slug}' ({saved_count} new saved to DB).")
        return reviews

    def _parse_reviews_markdown(self, markdown: str, app_slug: str, target_url: str, limit: int) -> List[Dict[str, Any]]:
        """Parses review entries from Jina markdown text."""
        items = []
        
        # Split by review blocks or headers
        blocks = re.split(r"(?:###\s+|(?:\*{1,2}\s*(?:1|2|3|4|5)\s*(?:out of 5|\/5|stars?)\*{0,2}))", markdown, flags=re.IGNORECASE)
        if len(blocks) <= 1:
            blocks = markdown.split("\n\n---\n\n")

        for block in blocks:
            if len(items) >= limit:
                break
            
            clean_block = block.strip()
            if len(clean_block) < 30 or "Terms of Service" in clean_block or "Cookie Policy" in clean_block:
                continue

            # Extract rating if present
            rating_match = re.search(r"([1-5])\s*(?:out of 5|\/5|stars?)", clean_block, re.IGNORECASE)
            rating = int(rating_match.group(1)) if rating_match else 2

            # Extract title / first line
            lines = [line.strip() for line in clean_block.split("\n") if line.strip()]
            title = lines[0][:100] if lines else f"Shopify review for {app_slug}"
            content = clean_block[:2000]

            # Generate stable hash for deduplication
            body_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:12]
            source_id = f"shopify_{app_slug}_{body_hash}"

            items.append({
                "source": f"shopify:{app_slug}",
                "source_id": source_id,
                "url": target_url,
                "title": title,
                "content": content,
                "score": rating,
                "created_utc": int(time.time()),
                "mentioned_incumbent": None
            })

        return items

    def search_shopify_category(self, category: str, limit: int = 10) -> List[str]:
        """
        Discovers popular app slugs in a Shopify category (e.g. 'marketing', 'orders-and-shipping').
        """
        clean_cat = category.strip("/ ").replace(" ", "-").lower()
        target_url = f"{self.BASE_URL}/categories/{clean_cat}"
        jina_url = f"{self.JINA_PREFIX}{target_url}"

        print(f"[>] Discovering Shopify apps in category '{clean_cat}'...")
        raw_markdown = self._rate_limited_get(jina_url)
        if not raw_markdown:
            return []

        # Find app links: /apps/slug
        slugs = re.findall(r"apps\.shopify\.com\/([a-z0-9\-]+)", raw_markdown)
        unique_slugs = []
        for s in slugs:
            if s not in unique_slugs and s not in ["categories", "stories", "pricing", "login"]:
                unique_slugs.append(s)
            if len(unique_slugs) >= limit:
                break

        return unique_slugs
