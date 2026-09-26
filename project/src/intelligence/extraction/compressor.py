import re
from typing import Optional
from .key_manager import ModelRouter

EXTRACTION_PROMPT = """You are a high-speed token compression engine for market intelligence.
Extract ONLY:
1. Exact user quotes showing pain, anger, frustration, or confusion.
2. Specific product flaws, pricing objections, or missing features.
3. DIY workarounds (e.g., custom scripts, manual spreadsheets).

Rules:
- Strip out ALL marketing fluff, navigation links, cookie banners, and generic descriptions.
- Format as compact bullet points with exact quotes in quotation marks.
- Keep the entire summary under 250 words to conserve tokens.
"""

class TokenCompressor:
    """Compresses massive raw web/forum data off-context to save 95%+ of LLM tokens."""

    def __init__(self):
        self.km = ModelRouter()

    def compress(self, raw_text: str, topic: str = "") -> str:
        """Compresses raw text using fast Groq/Gemini background extraction or local heuristic."""
        if not raw_text or len(raw_text.strip()) < 100:
            return raw_text

        # 1. Try fast off-context extraction using Groq (Llama 3.3 @ 500 t/s) or Gemini
        if self.km.groq_key or self.km.gemini_key or self.km.github_token:
            prompt = f"Target Topic: {topic}\n\nRaw Text to distill:\n{raw_text[:12000]}"
            summary = self.km.route_completion(prompt=prompt, task_type="fast_extract", system_prompt=EXTRACTION_PROMPT)
            if summary and not summary.startswith("> [!NOTE]"):
                return summary.strip()

        # 2. Fallback: Local Regex Heuristic (Zero API calls, extracts only pain sentences)
        return self._heuristic_extract(raw_text)

    def _heuristic_extract(self, text: str) -> str:
        """Extracts only sentences containing friction/pain keywords."""
        keywords = [
            "suck", "hate", "pain", "broken", "fail", "slow", "bug", "issue",
            "expensive", "cost", "pricing", "alternative", "waste", "struggle",
            "nightmare", "crash", "missing", "confusing", "hard to"
        ]
        pattern = re.compile(r'([^.?!]*\b(?:' + '|'.join(keywords) + r')\b[^.?!]*[.?!])', re.IGNORECASE)
        matches = pattern.findall(text)
        
        if not matches:
            # Fallback to first 800 characters
            return text[:800] + "..."

        unique_sentences = list(dict.fromkeys([s.strip().replace('\n', ' ') for s in matches]))[:8]
        return "### Key User Signals (Extracted):\n- " + "\n- ".join(unique_sentences)
