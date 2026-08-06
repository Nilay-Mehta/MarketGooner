import re
import requests
from typing import List, Dict, Any, Optional

class G2Miner:
    """
    Zero-cost G2 / TrustRadius reviewer miner using Jina Reader (https://r.jina.ai/)
    to fetch 1, 2, and 3-star negative reviews and complaints on incumbent software.
    """

    JINA_PREFIX = "https://r.jina.ai/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/plain"
        })

    def fetch_incumbent_complaints(self, product_slug: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetches negative reviews for a product on G2 or Capterra via Jina Reader.
        Example product_slug: 'datadog', 'stripe-billing', 'sentry'
        """
        clean_slug = product_slug.lower().strip().replace(" ", "-")
        target_url = f"https://www.g2.com/products/{clean_slug}/reviews"
        jina_url = f"{self.JINA_PREFIX}{target_url}"

        results = []
        try:
            resp = self.session.get(jina_url, timeout=18)
            if resp.status_code == 200:
                markdown_text = resp.text
                reviews = self._extract_reviews_from_markdown(markdown_text, product_name=clean_slug)
                results.extend(reviews[:limit])
        except Exception:
            pass

        return results

    def _extract_reviews_from_markdown(self, text: str, product_name: str) -> List[Dict[str, Any]]:
        """Parses markdown text from Jina reader to isolate 'What do you dislike' sections."""
        results = []
        # Look for "What do you dislike" or negative review sections
        dislike_blocks = re.findall(
            r"(?:What do you dislike\??|What do you dislike about [^\n\?]+\??|Cons:?)\s*([\s\S]*?)(?=(?:What problems is the product solving|What do you like|Recommendations to others|Review collected by|---\n|\Z))",
            text,
            re.IGNORECASE
        )

        for idx, block in enumerate(dislike_blocks):
            clean_block = block.strip()
            # Filter out tiny or junk snippets
            if len(clean_block) > 40:
                # Take first sentence as summary
                first_line = clean_block.split("\n")[0][:120]
                results.append({
                    "source": f"g2:{product_name}",
                    "source_id": f"g2_{product_name}_{idx+1}",
                    "url": f"https://www.g2.com/products/{product_name}/reviews",
                    "title": f"G2 Review Dissatisfaction: {product_name} - {first_line}",
                    "content": clean_block[:1200],
                    "score": 3,  # Negative review proxy score
                    "comments_count": 0,
                    "created_utc": 0,
                    "incumbent": product_name,
                    "friction_detected": True
                })

        return results
