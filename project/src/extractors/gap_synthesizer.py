# TODO: replaced in Phase 2 (Two-stage extraction + clustering + ranking)
from typing import List, Dict, Any
from src.key_manager import KeyManager

class GapSynthesizer:
    """Uses LLMs (Groq Llama 3.3 70B, Google Gemini Flash, or Hugging Face) to extract market gaps."""

    def __init__(self, key_manager: KeyManager):
        self.km = key_manager

    def synthesize_market_report(self, topic: str, raw_items: List[Dict[str, Any]]) -> str:
        """Synthesizes raw scraped discussions into an actionable Markdown Opportunity Dossier."""
        
        # Build prompt payload
        items_text = ""
        for i, item in enumerate(raw_items[:30]):
            items_text += f"\n--- Item {i+1} [{item.get('source')}] ---\n"
            items_text += f"Title: {item.get('title')}\n"
            items_text += f"Score: {item.get('score')} | Comments: {item.get('comments_count')}\n"
            items_text += f"URL: {item.get('url')}\n"
            if item.get("content"):
                items_text += f"Body: {item.get('content')}\n"

        system_prompt = (
            "You are an elite Principal Startup Architect and Market Intelligence Analyst. "
            "Your job is to analyze real customer discussions, complaints, and requests to identify "
            "high-value, underserved B2B / Prosumer SaaS and AI infrastructure gaps that can be built in 2-3 weeks."
        )

        user_prompt = f"""
# MARKET RESEARCH DOSSIER GENERATION

**Target Domain / Topic:** {topic}
**Collected Discussions:** {len(raw_items)} items

Analyze the following raw discussions collected from Reddit, Hacker News, and community boards.
Extract the real-world friction and format the response as a comprehensive Markdown report matching this exact structure:

---

# Market Intelligence Dossier: {topic}

## 1. Executive Summary & Opportunity Score
- **Market Signal Strength:** (Low / Medium / High / Extreme)
- **Top 1-Line Gap Identified:** (Concise summary of the unmet need)
- **Target Buyer Persona (ICP):** (e.g., DevOps Engineers at Series A AI Startups)
- **Estimated Build Feasibility:** (e.g., 2-3 Weeks using Next.js + Supabase)

## 2. Core Friction Points & Verifiable Pain Quotes
List the top 3-5 distinct pain points with direct user sentiment:
- **Pain Point #1:** [Description]
  - *User Sentiment / Direct Quote:* "[Quote from data]"
  - *Source:* [Link to source item]
  - *Severity:* (Annoyance / Workflow Blocker / Financial Bleed)

## 3. Existing Incumbents & Why Customers Are Frustrated
- What existing tools do users mention? (e.g. Datadog, Kubeflow, Stripe Billing)
- What are the common complaints about them? (Too bloated, too expensive, slow, complex setup)

## 4. Current Workarounds (Proof of Demand)
- What messy DIY scripts, spreadsheets, or manual hacks are teams currently using to solve this?

## 5. Synthesized Startup Opportunities (2-3 Week MVP Scope)
- **Product Concept Name:** 
- **Core Value Proposition:**
- **Essential V1 Features (Kill the bloat):**
  1. [Feature 1]
  2. [Feature 2]
  3. [Feature 3]
- **Recommended Monetization:** (e.g., $49/mo flat or $199/mo team tier)

## 6. Fake Door Validation Plan
- **High-Converting Landing Page Headline:** 
- **Sub-headline:**
- **3-Question Demand Quiz:**
  1. [Question 1]
  2. [Question 2]
  3. [Question 3]

---

### RAW SOURCE DATA TO ANALYZE:
{items_text}
"""
        return self.km.generate_completion(prompt=user_prompt, system_prompt=system_prompt)
