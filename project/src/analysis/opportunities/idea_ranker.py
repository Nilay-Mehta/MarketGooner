import json
import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from pydantic import BaseModel, Field
from src.orchestration.router.model_router import ModelRouter
from src.storage import db
from src.config import RANK_SEMAPHORE_LIMIT

class ScoreAxis(BaseModel):
    score: int = Field(..., ge=0, le=10, description="Score between 0 and 10")
    justification: str = Field(..., min_length=20, max_length=300, description="Concrete rationale for the score")
    cited_pain_ids: List[int] = Field(..., min_length=1, description="List of valid pain_point.id values from this cluster supporting the score")

class IdeaProposal(BaseModel):
    name: str = Field(..., min_length=2, max_length=60, description="Concise product name")
    wedge: str = Field(..., min_length=10, max_length=250, description="Laser-focused value proposition")
    icp: str = Field(..., min_length=5, max_length=250, description="Ideal customer persona")
    frequency: ScoreAxis
    wtp: ScoreAxis
    incumbent_weakness: ScoreAxis
    feasibility: ScoreAxis
    distribution: ScoreAxis
    representative_quote: str = Field(..., min_length=5, max_length=250, description="Verbatim customer quote snippet")

class IdeaRanker:
    """
    Stage 3 Extractor & Ranker: Generates citation-grounded unbundled SaaS wedges
    and scores opportunities based strictly on verified pain points using instructor.
    """

    def __init__(self, key_manager: Optional[ModelRouter] = None, db_path: str = db.DEFAULT_DB_PATH):
        self.km = key_manager or ModelRouter()
        self.db_path = db_path
        self.semaphore = asyncio.Semaphore(RANK_SEMAPHORE_LIMIT)


    def rank_clusters(self, min_cluster_size: int = 5, min_source_diversity: int = 2) -> List[Dict[str, Any]]:
        with db.get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ideas WHERE status = 'candidate'")
            cursor.execute("""
            SELECT * FROM clusters 
            WHERE size >= ? AND source_diversity >= ? AND (status IS NULL OR status = 'active')
            ORDER BY size DESC
            """, (min_cluster_size, min_source_diversity))
            clusters = [dict(r) for r in cursor.fetchall()]
            conn.commit()

        if not clusters:
            print("\\n[!] No qualifying clusters.")
            return []

        async def _process_all():
            tasks = []
            valid_tasks = []
            for cluster in clusters:
                cluster_id = cluster["id"]
                c_size = cluster.get("size", 0)
                c_div = cluster.get("source_diversity", 0)
                if c_size < min_cluster_size or c_div < min_source_diversity:
                    continue
                pains = db.get_pains_by_cluster(cluster_id, db_path=self.db_path)
                if not pains or len(pains) < min_cluster_size:
                    continue
                tasks.append(self._synthesize_idea_for_cluster_with_validation(cluster, pains))
                valid_tasks.append((cluster, pains))
            
            if not tasks: return []
            
            results = await asyncio.gather(*tasks)
            return list(zip(valid_tasks, results))

        outcomes = asyncio.run(_process_all())

        ranked_ideas = []
        for (cluster, pains), idea_data in outcomes:
            if not idea_data:
                continue

            trend_verdict, trend_slope = self._check_trend(idea_data["wedge"])
            dist_score = idea_data["score_distribution"]
            if trend_verdict == "declining":
                dist_score = min(3, dist_score)
            elif trend_verdict == "insufficient_data":
                dist_score = min(6, dist_score)
            
            idea_data["score_distribution"] = dist_score
            idea_data["score_total"] = (
                idea_data["score_frequency"] +
                idea_data["score_wtp"] +
                idea_data["score_incumbent_weakness"] +
                idea_data["score_feasibility"] +
                idea_data["score_distribution"]
            )

            idea_id = db.insert_idea(
                cluster_id=cluster["id"],
                name=idea_data["name"],
                wedge=idea_data["wedge"],
                icp=idea_data["icp"],
                score_frequency=idea_data["score_frequency"],
                score_wtp=idea_data["score_wtp"],
                score_incumbent_weakness=idea_data["score_incumbent_weakness"],
                score_feasibility=idea_data["score_feasibility"],
                score_distribution=idea_data["score_distribution"],
                representative_quote=idea_data.get("representative_quote"),
                status="candidate",
                trend_verdict=trend_verdict,
                trend_slope=trend_slope,
                db_path=self.db_path
            )

            idea_data["id"] = idea_id
            idea_data["cluster_id"] = cluster["id"]
            idea_data["trend_verdict"] = trend_verdict
            ranked_ideas.append(idea_data)

        return ranked_ideas


    def _check_trend(self, wedge: str) -> tuple[str, float]:
        """Runs pytrends validation on wedge keywords."""
        try:
            from src.validators.trend_validator import TrendValidator
            validator = TrendValidator()
            report = validator.validate_wedge([wedge])
            return report.trend_verdict, report.slope_last_24mo
        except Exception:
            return "insufficient_data", 0.0


    async def _synthesize_idea_for_cluster_with_validation(
        self, cluster: Dict[str, Any], pains: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Synthesizes an idea proposal using instructor and strictly validates citations.
        Retries once on invalid citations; if retry fails, marks cluster status='unscoreable'.
        """
        valid_pain_ids = {p["id"] for p in pains}
        pains_payload = [
            {
                "id": p["id"],
                "summary": p["summary"],
                "quote": p["quote"][:150],  # trim quote to prevent huge tokens
                "severity": p["severity"],
                "willingness_to_pay": p["willingness_to_pay"],
                "incumbent": p.get("incumbent")
            }
            for p in pains[:30]  # Limit to 30 pains max to avoid 413 token limits on Groq
        ]

        prompt = self._build_prompt(cluster, pains_payload, valid_pain_ids)
        system_prompt = (
            "You are a strict B2B SaaS Venture Architect. "
            "You MUST score opportunities based strictly on the provided pain points. "
            "Every score axis MUST cite one or more exact pain_id integers from the provided list. "
            "Never fabricate or guess pain IDs."
        )

        # Attempt 1
        print(f"  [rank] Scoring cluster {cluster['id']} ('{cluster['label']}' - {len(pains_payload)} pains)...", flush=True)
        async with self.semaphore:
            proposal: Optional[IdeaProposal] = await asyncio.to_thread(
                self.km.generate_structured,
                prompt,
                IdeaProposal,
                system_prompt,
                task_type="rank",
                model_tier="deep"
            )

        is_valid, invalid_ids = self._validate_citations(proposal, valid_pain_ids)
        if not is_valid and proposal is not None:
            # Attempt 2 (Retry with error feedback)
            retry_prompt = (
                f"{prompt}\n\n"
                f"ERROR IN PREVIOUS ATTEMPT: You cited invalid pain IDs: {invalid_ids}.\n"
                f"The ONLY valid pain_id integers in this cluster are: {sorted(list(valid_pain_ids))}.\n"
                f"Please regenerate the proposal citing ONLY valid pain IDs from this list."
            )
            async with self.semaphore:
                proposal = await asyncio.to_thread(
                    self.km.generate_structured,
                    retry_prompt,
                    IdeaProposal,
                    system_prompt,
                    task_type="rank",
                    model_tier="deep"
                )
            is_valid, invalid_ids = self._validate_citations(proposal, valid_pain_ids)

        if not is_valid and proposal is not None:
            # Attempt 2 (Retry with error feedback)
            retry_prompt = (
                f"{prompt}\n\n"
                f"ERROR IN PREVIOUS ATTEMPT: You cited invalid pain IDs: {invalid_ids}.\n"
                f"The ONLY valid pain_id integers in this cluster are: {sorted(list(valid_pain_ids))}.\n"
                f"Please regenerate the proposal citing ONLY valid pain IDs from this list."
            )
            proposal = self.km.generate_structured(
                prompt=retry_prompt,
                response_model=IdeaProposal,
                system_prompt=system_prompt,
                task_type="rank",
                model_tier="deep"
            )
            is_valid, invalid_ids = self._validate_citations(proposal, valid_pain_ids)

        if not is_valid or proposal is None:
            # Mark cluster unscoreable in DB
            db.upsert_cluster(
                label=cluster["label"],
                size=cluster["size"],
                first_seen=cluster.get("first_seen"),
                last_seen=cluster.get("last_seen"),
                source_diversity=cluster.get("source_diversity", 1),
                avg_severity_score=cluster.get("avg_severity_score", 0.0),
                wtp_evidence_count=cluster.get("wtp_evidence_count", 0),
                status="unscoreable",
                cluster_id=cluster["id"],
                db_path=self.db_path
            )
            print(f"  [!] Cluster {cluster['id']} ('{cluster['label']}') rejected: invalid citations {invalid_ids}. Marked unscoreable.")
            return None

        # Clean sanitized data
        name = re.sub(r'[>#*\[\]`"\']', '', proposal.name).strip()
        wedge = re.sub(r'[>#*\[\]`"\']', '', proposal.wedge).strip()
        icp = re.sub(r'[>#*\[\]`"\']', '', proposal.icp).strip()
        quote = proposal.representative_quote[:200]

        # Bug #3 fix: Cap score_wtp by actual WTP evidence rows in cluster.
        # LLM cannot score WTP > 0 without evidence — non-negotiable.
        wtp_ev = cluster.get("wtp_evidence_count", 0)
        raw_wtp_score = proposal.wtp.score
        if wtp_ev == 0:
            proposal.wtp.score = 0
            proposal.wtp.justification = f"Capped: 0 WTP evidence rows in cluster (LLM returned {raw_wtp_score})"
            print(f"  [wtp-cap] Cluster {cluster['id']}: wtp_ev=0 → score forced to 0 (LLM had {raw_wtp_score})")
        elif wtp_ev < 5:
            capped = min(proposal.wtp.score, 3)
            if capped < proposal.wtp.score:
                print(f"  [wtp-cap] Cluster {cluster['id']}: wtp_ev={wtp_ev} → score capped at 3 (LLM had {proposal.wtp.score})")
            proposal.wtp.score = capped
            proposal.wtp.justification = f"{proposal.wtp.justification} [Capped at 3: only {wtp_ev} WTP evidence rows]"
        # else: wtp_ev >= 5 — allow LLM score as-is

        scores = [
            proposal.frequency.score,
            proposal.wtp.score,
            proposal.incumbent_weakness.score,
            proposal.feasibility.score,
            proposal.distribution.score
        ]

        return {
            "name": name,
            "wedge": wedge,
            "icp": icp,
            "score_frequency": scores[0],
            "score_wtp": scores[1],
            "score_incumbent_weakness": scores[2],
            "score_feasibility": scores[3],
            "score_distribution": scores[4],
            "score_total": sum(scores),
            "representative_quote": quote
        }

    def _validate_citations(self, proposal: Optional[IdeaProposal], valid_ids: set[int]) -> tuple[bool, set[int]]:
        if not proposal:
            return False, set()
        
        cited = set(
            proposal.frequency.cited_pain_ids +
            proposal.wtp.cited_pain_ids +
            proposal.incumbent_weakness.cited_pain_ids +
            proposal.feasibility.cited_pain_ids +
            proposal.distribution.cited_pain_ids
        )
        invalid = cited - valid_ids
        return (len(invalid) == 0 and len(cited) > 0), invalid

    def _build_prompt(self, cluster: Dict[str, Any], pains: List[Dict[str, Any]], valid_ids: set[int]) -> str:
        return f"""
Analyze this problem cluster and propose an unbundled B2B SaaS wedge:

PROBLEM DOMAIN: {cluster.get('label')}
CLUSTER SIZE: {cluster.get('size')} complaints across {cluster.get('source_diversity')} distinct sources.
VALID PAIN IDs IN THIS CLUSTER: {sorted(list(valid_ids))}

VERIFIED PAIN POINTS:
{json.dumps(pains, indent=2)}

Scoring Guidelines:
- score_frequency (0-10): Problem prevalence in market.
- score_wtp (0-10): Customer willingness to pay (evidence of financial loss, high software spend).
- score_incumbent_weakness (0-10): Incumbent bloat, high churn, or severe limitations.
- score_feasibility (0-10): Speed to build an MVP (<2-4 weeks = 8-10).
- score_distribution (0-10): Organic acquisition velocity in target communities.

CRITICAL: Every ScoreAxis MUST include 'cited_pain_ids' containing at least one integer from the valid pain IDs list above.
"""
