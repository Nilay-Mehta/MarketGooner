import json
import time
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from src.orchestration.router.model_router import ModelRouter
from src.storage import db

class PainPoint(BaseModel):
    summary: str = Field(..., max_length=500, description="Clear summary of user complaint")
    incumbent: Optional[str] = Field(None, description="Incumbent product mentioned or None")
    severity: Literal["annoyance", "blocker", "financial_bleed"] = Field("annoyance", description="Severity level")
    willingness_to_pay: str = Field("unknown", description="'$X/mo mentioned', 'would switch from Y', or 'unknown'")
    wtp_type: Literal["explicit_dollar", "switching", "time_cost", "incumbent_pricing", "unknown"] = Field("unknown", description="Categorize the WTP evidence type")
    persona: str = Field("unknown", description="User persona or role")
    quote: str = Field(..., max_length=2000, description="Verbatim snippet from the content")

class ItemExtraction(BaseModel):
    item_id: int
    has_pain: bool
    pains: List[PainPoint] = []

class BatchExtractionResponse(BaseModel):
    items: List[ItemExtraction] = []

class PainExtractor:
    """
    Stage 1 Extractor: Analyzes raw scraped discussions in batches to extract
    concrete, verifiable B2B friction, incumbent complaints, and willingness to pay using instructor.
    """

    def __init__(self, key_manager: Optional[ModelRouter] = None, db_path: str = db.DEFAULT_DB_PATH):
        self.km = key_manager or ModelRouter()
        self.db_path = db_path

    def extract_pains_from_items(self, raw_items: List[Dict[str, Any]], batch_size: int = 5) -> List[Dict[str, Any]]:
        """
        Processes a list of raw_items in batches of 5.
        Extracts pains, saves them into the SQLite pain_points table, and returns extracted records.
        """
        from collections import defaultdict
        all_extracted_pains = []
        batch_map = {item.get("id"): item for item in raw_items if item.get("id")}
        
        items_processed = 0
        total_items = len(raw_items)
        failed_items = 0
        failure_reasons = defaultdict(int)

        for batch_idx, i in enumerate(range(0, len(raw_items), batch_size)):
            batch = raw_items[i:i + batch_size]
            
            if items_processed > 0 and items_processed % 15 == 0:
                print(f"  [extract] {items_processed}/{total_items} done, {len(all_extracted_pains)} pains extracted, {failed_items} failures skipped", flush=True)
                
            items_processed += len(batch)
            batch_prompt = self._build_batch_prompt(batch)
            
            system_prompt = (
                "You are an expert customer feedback and market research analyst. "
                "Your task is to analyze user discussions from Reddit, Hacker News, G2, GitHub, Shopify Reviews, and YouTube. "
                "Extract specific, verifiable customer pain points, incumbent complaints, and willingness to pay (WTP). "
                "Look for implicit WTP signals and categorize them into wtp_type:\n"
                "- explicit_dollar: '$15k/month bill', 'paying too much'\n"
                "- switching: 'switched away because pricing', 'looking for alternative'\n"
                "- time_cost: 'wasting 10 hours a week on this', 'ROI doesn\\'t justify the time'\n"
                "- incumbent_pricing: 'Datadog is too expensive', 'pricing model is predatory'\n"
                "- unknown: no WTP signals detected.\n"
                "CRITICAL: The quote MUST be an exact verbatim substring (<= 200 chars) from the content of that specific item_id. "
                "Never hallucinate complaints that are not in the provided text."
            )

            try:
                structured_res = self.km.generate_structured(
                    prompt=batch_prompt,
                    response_model=BatchExtractionResponse,
                    system_prompt=system_prompt
                )
                
                if not structured_res or not structured_res.items:
                    failed_items += len(batch)
                    failure_reasons["empty_or_null_response"] += len(batch)
                    time.sleep(2)
                    continue

                for item_result in structured_res.items:
                    item_id = item_result.item_id
                    raw_item = batch_map.get(item_id)
                    if not raw_item or not item_result.has_pain:
                        continue

                    for p in item_result.pains:
                        summary = p.summary.strip()
                        quote = p.quote.strip()[:200]
                        
                        if not summary or not quote or len(quote) < 6:
                            continue

                        incumbent = p.incumbent
                        if incumbent in ["null", "None", "none", "", "null (or name)"]:
                            incumbent = None

                        pain_id = db.insert_pain_point(
                            raw_item_id=item_id,
                            summary=summary,
                            incumbent=incumbent,
                            severity=p.severity,
                            willingness_to_pay=p.willingness_to_pay,
                            wtp_type=p.wtp_type,
                            persona=p.persona,
                            quote=quote,
                            db_path=self.db_path
                        )

                        all_extracted_pains.append({
                            "id": pain_id,
                            "raw_item_id": item_id,
                            "summary": summary,
                            "incumbent": incumbent,
                            "severity": p.severity,
                            "willingness_to_pay": p.willingness_to_pay,
                            "wtp_type": p.wtp_type,
                            "persona": p.persona,
                            "quote": quote
                        })
            except Exception as e:
                failed_items += len(batch)
                failure_reasons[str(e)[:50]] += len(batch)

            time.sleep(2)

        print(f"  [extract] Final summary: total={total_items} succeeded={total_items - failed_items} failed={failed_items} — new pains created={len(all_extracted_pains)}")
        if failed_items > 0:
            print("  [extract] Failure reasons:")
            for reason, count in failure_reasons.items():
                print(f"    - {count} items failed due to: {reason}")
                
        return all_extracted_pains

    def _build_batch_prompt(self, batch: List[Dict[str, Any]]) -> str:
        """Constructs a strict JSON extraction prompt for a batch of raw items."""
        items_payload = []
        for item in batch:
            items_payload.append({
                "item_id": item.get("id"),
                "title": item.get("title", ""),
                "source": item.get("source", ""),
                "content": (item.get("content") or item.get("selftext") or "")[:1500]
            })

        return f"""
Analyze the following user discussions and extract real customer friction, complaints, or problems.

DISCUSSIONS TO ANALYZE:
{json.dumps(items_payload, indent=2)}
"""
