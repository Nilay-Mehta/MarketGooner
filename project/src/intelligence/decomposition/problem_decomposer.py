import json
import re
from typing import List, Optional
from pydantic import BaseModel, Field

class ProblemDecomposition(BaseModel):
    summary: str = Field(description="One-sentence distilled summary of the core problem or demand thesis")
    target_icp: str = Field(description="Target Customer / Ideal Customer Profile")
    core_friction: str = Field(description="Root operational friction, bottleneck, or unmet need")
    displaced_incumbents: List[str] = Field(description="Existing tools or workarounds currently used (e.g. Excel, QuickBooks, manual emails)")
    subreddits: List[str] = Field(description="Target subreddits without r/ prefix for discussion mining (e.g. smallbusiness, Contractor)")
    search_queries: List[str] = Field(description="2 to 3 targeted keyword queries to uncover customer complaints")
    agent_tasks: List[str] = Field(description="3 to 4 sequential actionable steps for downstream miner/extractor/decision agents")

class ProblemDecomposer:
    """
    Main LLM Strategic Orchestrator.
    Takes a raw user problem statement (single line or full paragraph)
    and autonomously breaks it down into ICP, friction hypotheses, target subreddits,
    search keywords, and multi-agent execution steps.
    """

    def __init__(self, router=None):
        self.router = router

    def decompose(self, problem_statement: str) -> ProblemDecomposition:
        cleaned_text = (problem_statement or "").strip()
        if not cleaned_text:
            cleaned_text = "Small business contractors and solo operators struggle with job costing, invoice reminders, and chasing overdue payments."

        # Attempt LLM decomposition if router is available
        if self.router:
            prompt = f"""You are the Lead Market Intelligence Architect and Multi-Agent Orchestrator.
Analyze the following user problem statement or market demand thesis:
"{cleaned_text}"

Deconstruct this into a concrete research and discovery strategy:
1. One-sentence summary
2. Target Customer / ICP (be specific, e.g. "Trade contractors with 1-10 staff", "B2B boutique marketing agencies")
3. Core operational friction or pain point
4. Displaced incumbent tools (e.g. ["QuickBooks Online", "Manual spreadsheets", "Email threads"])
5. Target subreddits for discovery (2 to 3 subreddits without 'r/' prefix, e.g. ["smallbusiness", "Contractor"])
6. Search queries / keyword phrases to discover raw customer complaints (2 to 3 queries, e.g. ["invoice chasing", "unpaid clients", "change orders"])
7. 4 sequential tasks for the downstream multi-agent pipeline (Miner, Extractor, Decision Gate, Synthesis)

Return pure JSON matching this schema:
{{
  "summary": "...",
  "target_icp": "...",
  "core_friction": "...",
  "displaced_incumbents": ["...", "..."],
  "subreddits": ["smallbusiness", "..."],
  "search_queries": ["...", "..."],
  "agent_tasks": [
    "Agent 1 (Miner): Scan target subreddits using derived keywords",
    "Agent 2 (Extractor): Parse verbatim customer friction and emotional intensity",
    "Agent 3 (Gate): Screen conviction density via local System 1 decision model",
    "Agent 4 (Diffusion): Synthesize commercial B2B micro-SaaS dossiers"
  ]
}}
"""
            try:
                raw_json = self.router.generate_completion(
                    prompt=prompt,
                    task_type="fast_extract",
                    system_prompt="You are an autonomous AI research orchestrator. Respond only with valid JSON.",
                    json_mode=True,
                    model_tier="fast"
                )
                if raw_json:
                    # Clean markdown code blocks if any
                    raw_json = re.sub(r"^```json\s*", "", raw_json, flags=re.MULTILINE)
                    raw_json = re.sub(r"^```\s*$", "", raw_json, flags=re.MULTILINE).strip()
                    data = json.loads(raw_json)
                    return ProblemDecomposition(**data)
            except Exception as e:
                print(f"  [decomposer] LLM decomposition notice ({e}). Using deterministic heuristics.")

        # Deterministic / Offline Heuristic Fallback
        return self._heuristic_decomposition(cleaned_text)

    def _heuristic_decomposition(self, text: str) -> ProblemDecomposition:
        lower = text.lower()

        # 1. Target ICP
        if any(w in lower for w in ["contractor", "trade", "plumb", "hvac", "electric", "construct"]):
            icp = "Small business trade contractors (1-10 staff) & field operators"
            subs = ["smallbusiness", "Contractor"]
            alts = ["QuickBooks Online", "Excel spreadsheets", "Paper job logs"]
            default_queries = ["contractor invoice", "job costing", "unpaid client"]
        elif any(w in lower for w in ["agency", "client", "outreach", "lead", "marketing"]):
            icp = "B2B marketing agencies & service consultancies (5-50 staff)"
            subs = ["smallbusiness", "marketing"]
            alts = ["HubSpot CRM", "Manual LinkedIn outreach", "Google Sheets"]
            default_queries = ["lead generation", "cold outreach", "client onboarding"]
        elif any(w in lower for w in ["contract", "legal", "clm", "renewal", "deadline"]):
            icp = "Operations Managers & SMB Founders managing vendor agreements"
            subs = ["smallbusiness", "entrepreneur"]
            alts = ["Manual calendar alerts", "Email chains", "DocuSign"]
            default_queries = ["contract renewal", "missed deadline", "vendor agreement"]
        elif any(w in lower for w in ["ecommerce", "e-commerce", "inventory", "shopify", "stock"]):
            icp = "Mid-market B2B e-commerce operators & inventory managers"
            subs = ["smallbusiness", "ecommerce"]
            alts = ["Manual inventory sync", "Basic ERP", "Spreadsheets"]
            default_queries = ["inventory sync", "stock reconciliation", "order delay"]
        elif any(w in lower for w in ["freelance", "solo", "billing", "invoice"]):
            icp = "Freelancers, solo creators & independent professional practices"
            subs = ["smallbusiness", "freelance"]
            alts = ["Manual invoices", "FreshBooks", "Excel"]
            default_queries = ["unpaid invoice", "chasing payments", "invoice reminder"]
        else:
            icp = "Cost-conscious SMB founders & operational team leads"
            subs = ["smallbusiness", "entrepreneur"]
            alts = ["Spreadsheets & manual tracking", "Enterprise legacy tools"]
            default_queries = ["software friction", "manual workarounds", "tool gating"]

        # 2. Extract keywords from text
        stopwords = {
            "this", "that", "with", "have", "from", "they", "will", "would", "about", 
            "there", "their", "what", "when", "where", "which", "tool", "need", "want", 
            "like", "some", "more", "small", "huge", "because", "means", "gets", "done", 
            "without", "getting", "very", "much", "many", "also", "into", "over", "such",
            "been", "were", "other", "than", "then", "them", "these", "those", "both",
            "keep", "lose", "losing", "make", "take", "help", "good", "well", "time"
        }
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        keywords = [w for w in words if w not in stopwords][:3]
        if keywords:
            derived_queries = [f"{k} pain" for k in keywords[:2]] + default_queries[:1]
        else:
            derived_queries = default_queries

        summary = text if len(text) <= 120 else text[:117] + "..."

        return ProblemDecomposition(
            summary=summary,
            target_icp=icp,
            core_friction=f"Manual workflow friction & operational bottlenecks highlighted in user demand: {summary}",
            displaced_incumbents=alts,
            subreddits=subs,
            search_queries=derived_queries,
            agent_tasks=[
                f"Agent 1 (Miner): Syndicate real Reddit discussions across r/{'/r/'.join(subs)} matching queries: {', '.join(derived_queries)}",
                "Agent 2 (Extractor): Mine verbatim user complaints, root causes, and willingness-to-pay indicators",
                "Agent 3 (Gate): Screen operational pain density via ConvAI Laya System 1 decision model (ModernBERT-421M)",
                "Agent 4 (Diffusion): Synthesize commercial B2B micro-SaaS dossiers and compile Master Word Intelligence Report"
            ]
        )
