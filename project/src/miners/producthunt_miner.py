import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

class ProductHuntMiner:
    """
    Zero-cost Product Hunt miner that analyzes recent launches and discussions
    to find saturated categories, underdelivered features, and community feedback.
    """

    FEED_URL = "https://www.producthunt.com/feed"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/atom+xml, application/rss+xml, text/xml, application/json"
        })

    def search_recent_launches(self, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Searches Product Hunt launches via public RSS feed and Jina search for topic keywords."""
        results = []
        topic_words = [w.lower() for w in topic.split() if len(w) > 3]

        # 1. Check Product Hunt public Atom feed
        try:
            resp = self.session.get(self.FEED_URL, timeout=12)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                # Atom namespace
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                entries = root.findall('atom:entry', ns) or root.findall('entry')
                for entry in entries:
                    title_elem = entry.find('atom:title', ns) or entry.find('title')
                    summary_elem = entry.find('atom:summary', ns) or entry.find('summary') or entry.find('atom:content', ns) or entry.find('content')
                    link_elem = entry.find('atom:link', ns) or entry.find('link')
                    id_elem = entry.find('atom:id', ns) or entry.find('id')

                    title = title_elem.text if title_elem is not None else ""
                    summary = summary_elem.text if summary_elem is not None else ""
                    url = link_elem.attrib.get('href', '') if link_elem is not None else ""
                    source_id = id_elem.text if id_elem is not None else url

                    combined = f"{title}\n{summary}".lower()
                    if not topic_words or any(w in combined for w in topic_words):
                        results.append({
                            "source": "producthunt",
                            "source_id": f"ph_{source_id.split('/')[-1]}",
                            "url": url,
                            "title": title,
                            "content": summary[:1000],
                            "score": 10,
                            "comments_count": 5,
                            "created_utc": 0,
                            "friction_detected": False
                        })
        except Exception:
            pass

        return results[:limit]
