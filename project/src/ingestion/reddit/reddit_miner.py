import requests
import time
import uuid
import datetime
import random
import re
import xml.etree.ElementTree as ET
from typing import List
from src.storage.db import Evidence

class RedditMiner:
    """
    Ingestion Stage 1: Mines Reddit for Evidence.
    Ultimate Stealth Scraper: Uses Reddit's public RSS feeds.
    Reddit's WAF (Cloudflare) blocks .json requests from bots, but strictly allows .rss 
    so it doesn't break Feedly/Slack. This bypasses the need for API keys completely.
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.ns = {'atom': 'http://www.w3.org/2005/Atom'}

    def fetch_evidence(self, subreddit: str, query: str = "", limit: int = 50) -> List[Evidence]:
        clean_sub = subreddit.replace("r/", "").strip()
        print(f"[*] RSS Ingesting r/{clean_sub} | Query: '{query}' | Target: {limit} posts")
        
        evidence_list = []
        after = None
        
        while len(evidence_list) < limit:
            # The public RSS endpoint
            url = f"https://www.reddit.com/r/{clean_sub}/search.rss?q={query}&restrict_sr=1&sort=new"
            if after:
                url += f"&after={after}"
                
            try:
                time.sleep(random.uniform(2.0, 4.0)) # Polite scraping
                res = requests.get(url, headers=self.headers, timeout=15)
                
                if res.status_code == 200:
                    root = ET.fromstring(res.text)
                    entries = root.findall('atom:entry', self.ns)
                    
                    if not entries:
                        print("  -> End of available RSS search results.")
                        break
                        
                    batch_evidence = self._parse_rss(entries, clean_sub)
                    
                    # Deduplicate in case pagination acts weird
                    new_evs = [e for e in batch_evidence if e.id not in [x.id for x in evidence_list]]
                    if not new_evs:
                        break # Stuck in a loop
                        
                    evidence_list.extend(new_evs)
                    print(f"  -> Fetched batch: {len(new_evs)} valid items (Total: {len(evidence_list)})")
                    
                    # RSS pagination: get the ID of the last item
                    # Reddit RSS IDs look like: t3_12345
                    last_id = entries[-1].find('atom:id', self.ns).text
                    after = last_id.split('/')[-1] if '/' in last_id else last_id
                    
                    if len(evidence_list) >= limit:
                        break
                        
                elif res.status_code == 429:
                    print("[!] Hit Reddit rate limit. Pausing for 10 seconds...")
                    time.sleep(10)
                else:
                    print(f"[!] Reddit returned HTTP {res.status_code}. Stopping.")
                    break
                    
            except Exception as e:
                print(f"[!] RSS Request failed: {e}")
                break
                
        return evidence_list[:limit]

    def _strip_html(self, html_content: str) -> str:
        """Removes HTML tags from the RSS content payload."""
        if not html_content:
            return ""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html_content)
        # Unescape basic HTML entities
        text = text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        # Remove extra whitespace
        return re.sub(r'\s+', ' ', text).strip()

    def _parse_rss(self, entries: list, subreddit: str) -> List[Evidence]:
        evidence_list = []
        for entry in entries:
            title_node = entry.find('atom:title', self.ns)
            content_node = entry.find('atom:content', self.ns)
            link_node = entry.find('atom:link', self.ns)
            author_node = entry.find('atom:author/atom:name', self.ns)
            updated_node = entry.find('atom:updated', self.ns)
            id_node = entry.find('atom:id', self.ns)
            
            title = title_node.text if title_node is not None else ''
            raw_content = content_node.text if content_node is not None else ''
            url = link_node.attrib.get('href', '') if link_node is not None else ''
            author = author_node.text if author_node is not None else 'unknown'
            updated_str = updated_node.text if updated_node is not None else datetime.datetime.utcnow().isoformat()
            
            clean_text = self._strip_html(raw_content)
            
            full_text = f"Title: {title}\n\n{clean_text}".strip()
            
            if len(full_text) < 50:
                continue
                
            # Extract post ID from URL or Atom ID
            post_id = url.split('/comments/')[1].split('/')[0] if '/comments/' in url else uuid.uuid4().hex[:8]
            
            evidence = Evidence(
                id=f"reddit_{post_id}",
                source="reddit",
                source_id=post_id,
                url=url,
                timestamp=updated_str,
                author=author.replace('/u/', ''),
                text=full_text,
                metadata={"subreddit": subreddit}
            )
            evidence_list.append(evidence)
            
        return evidence_list
