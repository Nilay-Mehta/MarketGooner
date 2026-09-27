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
    Fetches the Search feed, then drills down into the Comment Threads for context.
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.ns = {'atom': 'http://www.w3.org/2005/Atom'}

    def fetch_evidence(self, subreddit: str, query: str = "", limit: int = 5) -> List[Evidence]:
        clean_sub = subreddit.replace("r/", "").strip()
        print(f"[*] RSS Ingesting r/{clean_sub} | Query: '{query}' | Target: {limit} full threads")
        
        evidence_list = []
        after = None
        
        while len(evidence_list) < limit:
            url = f"https://www.reddit.com/r/{clean_sub}/search.rss?q={query}&restrict_sr=1&sort=new"
            if after:
                url += f"&after={after}"
                
            try:
                time.sleep(random.uniform(2.0, 3.0))
                res = requests.get(url, headers=self.headers, timeout=15)
                
                if res.status_code == 200:
                    root = ET.fromstring(res.text)
                    entries = root.findall('atom:entry', self.ns)
                    
                    if not entries:
                        print("  -> End of available RSS search results.")
                        break
                        
                    for entry in entries:
                        if len(evidence_list) >= limit:
                            break
                            
                        # Extract post ID
                        link_node = entry.find('atom:link', self.ns)
                        url_val = link_node.attrib.get('href', '') if link_node is not None else ''
                        if '/comments/' not in url_val:
                            continue
                            
                        post_id = url_val.split('/comments/')[1].split('/')[0]
                        
                        # Now fetch the FULL THREAD
                        print(f"  -> Downloading full thread for post: {post_id}...")
                        thread_evidence = self._fetch_full_thread(post_id, clean_sub, url_val)
                        if thread_evidence:
                            evidence_list.append(thread_evidence)
                            
                    # Pagination logic
                    last_id = entries[-1].find('atom:id', self.ns).text
                    after = last_id.split('/')[-1] if '/' in last_id else last_id
                        
                elif res.status_code == 429:
                    print("[!] Hit Reddit rate limit. Pausing for 10 seconds...")
                    time.sleep(10)
                else:
                    print(f"[!] Reddit returned HTTP {res.status_code}. Stopping.")
                    break
                    
            except Exception as e:
                print(f"[!] RSS Request failed: {e}")
                break
                
        return evidence_list

    def _fetch_full_thread(self, post_id: str, subreddit: str, original_url: str) -> Evidence:
        """Fetches the OP and all top comments into a single Evidence payload."""
        url = f"https://www.reddit.com/comments/{post_id}.rss"
        try:
            time.sleep(random.uniform(1.5, 3.0)) # Be polite to Reddit servers
            res = requests.get(url, headers=self.headers, timeout=15)
            if res.status_code != 200:
                return None
                
            root = ET.fromstring(res.text)
            entries = root.findall('atom:entry', self.ns)
            if not entries:
                return None
                
            # First entry is the OP
            op_entry = entries[0]
            title = op_entry.find('atom:title', self.ns).text or ''
            author_node = op_entry.find('atom:author/atom:name', self.ns)
            author = author_node.text.replace('/u/', '') if author_node is not None else 'unknown'
            updated = op_entry.find('atom:updated', self.ns).text or datetime.datetime.utcnow().isoformat()
            op_content = self._strip_html(op_entry.find('atom:content', self.ns).text)
            
            # Combine OP and Comments
            full_text = f"Title: {title}\nAuthor: {author}\n\nPOST:\n{op_content}\n\n--- COMMENTS ---\n"
            
            # The rest are comments
            comment_count = 0
            for comment_entry in entries[1:20]: # Grab up to 20 top comments
                c_author_node = comment_entry.find('atom:author/atom:name', self.ns)
                c_author = c_author_node.text.replace('/u/', '') if c_author_node is not None else 'unknown'
                
                # Skip automod
                if c_author.lower() == "automoderator":
                    continue
                    
                c_content = self._strip_html(comment_entry.find('atom:content', self.ns).text)
                if c_content:
                    full_text += f"\n[User: {c_author}]: {c_content}\n"
                    comment_count += 1
            
            if len(full_text) < 50:
                return None
                
            return Evidence(
                id=f"reddit_{post_id}",
                source="reddit",
                source_id=post_id,
                url=original_url,
                timestamp=updated,
                author=author,
                text=full_text,
                metadata={"subreddit": subreddit, "comments_scraped": comment_count}
            )
            
        except Exception as e:
            print(f"    [!] Failed to parse thread {post_id}: {e}")
            return None

    def _strip_html(self, html_content: str) -> str:
        """Removes HTML tags from the RSS content payload."""
        if not html_content: return ""
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return re.sub(r'\s+', ' ', text).strip()
