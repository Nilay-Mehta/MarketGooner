import hashlib
import json
import os
import re
import time
from typing import List, Dict, Any, Optional
from src.storage import db

class YouTubeMiner:
    """
    Mines real customer and operator complaints from YouTube podcast / founder interviews
    using yt-dlp metadata extraction and youtube-transcript-api.
    """

    PAIN_PHRASES = [
        "switched from", "cancelled", "nightmare", "too expensive", "bill exploded",
        "frustrating", "broken", "pricing increase", "support was awful", "churn",
        "lost money", "lost $", "migration headache", "couldn't scale", "hated using"
    ]

    def __init__(self, db_path: str = db.DEFAULT_DB_PATH):
        self.db_path = db_path
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "youtube_sources.json")
        self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.channels = data.get("channels", [])
                    self.pain_phrases = data.get("pain_keywords", self.PAIN_PHRASES)
            except Exception:
                self.channels = []
                self.pain_phrases = self.PAIN_PHRASES
        else:
            self.channels = []
            self.pain_phrases = self.PAIN_PHRASES

    def search_pain_transcripts(self, query: str, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Searches YouTube for query discussions, fetches transcripts, and extracts pain moments.
        """
        import yt_dlp
        from youtube_transcript_api import YouTubeTranscriptApi

        print(f"[>] Mining YouTube founder/operator transcripts for '{query}'...")
        ydl_opts = {
            "extract_flat": True,
            "quiet": True,
            "skip_download": True,
            "no_warnings": True
        }

        videos = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_query = f"ytsearch{limit}:{query} podcast interview"
                result = ydl.extract_info(search_query, download=False)
                if result and "entries" in result:
                    videos = result["entries"][:limit]
        except Exception as e:
            print(f"  [!] YouTube search error: {e}")
            return []

        yta = YouTubeTranscriptApi()
        extracted_items = []

        for v in videos:
            if not v:
                continue
            video_id = v.get("id")
            title = v.get("title", f"YouTube discussion on {query}")
            if not video_id:
                continue

            try:
                # Fetch transcript segments
                transcript = yta.fetch(video_id)
            except Exception:
                # Captions not available for this video
                continue

            # Scan transcript for high-friction moments
            pain_moments = self._extract_pain_snippets(transcript, video_id, title, query)
            for item in pain_moments:
                inserted_id = db.insert_raw_item(
                    source=item["source"],
                    source_id=item["source_id"],
                    url=item["url"],
                    title=item["title"],
                    content=item["content"],
                    score=10,
                    comments_count=0,
                    created_utc=int(time.time()),
                    topic_query=f"youtube:{query}",
                    mentioned_incumbent=item.get("mentioned_incumbent"),
                    db_path=self.db_path
                )
                if inserted_id:
                    extracted_items.append(item)

        print(f"  [+] Extracted {len(extracted_items)} high-signal pain moments from YouTube transcripts.")
        return extracted_items

    def _extract_pain_snippets(
        self, transcript: Any, video_id: str, video_title: str, query: str
    ) -> List[Dict[str, Any]]:
        """Finds windows containing pain keywords in transcript snippets."""
        items = []
        snippets = list(transcript)
        
        # Look for matching segments
        for i, seg in enumerate(snippets):
            # seg is either dict-like or object with .text
            text = seg.get("text", "") if isinstance(seg, dict) else getattr(seg, "text", str(seg))
            start = seg.get("start", 0) if isinstance(seg, dict) else getattr(seg, "start", 0)
            
            clean_text = text.lower()
            matched_phrase = next((kw for kw in self.pain_phrases if kw in clean_text), None)

            if matched_phrase:
                # Build a contiguous 6-segment context window around the mention (~30 seconds)
                win_start = max(0, i - 2)
                win_end = min(len(snippets), i + 4)
                window_texts = [
                    (s.get("text", "") if isinstance(s, dict) else getattr(s, "text", str(s)))
                    for s in snippets[win_start:win_end]
                ]
                content = " ".join(window_texts).strip()

                start_secs = int(start)
                timestamp_url = f"https://www.youtube.com/watch?v={video_id}&t={start_secs}s"
                body_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:10]
                source_id = f"yt_{video_id}_{start_secs}_{body_hash}"

                items.append({
                    "source": "youtube:transcript",
                    "source_id": source_id,
                    "url": timestamp_url,
                    "title": f"{video_title} (at {start_secs // 60}:{start_secs % 60:02d})",
                    "content": content,
                    "score": 10,
                    "mentioned_incumbent": None
                })

                # Limit to 2 pain moments per video to prevent spamming
                if len(items) >= 2:
                    break

        return items
