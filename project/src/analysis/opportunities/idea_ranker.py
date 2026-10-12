import uuid
from typing import Optional, List
from pydantic import BaseModel, Field
from src.orchestration.router.model_router import ModelRouter
from src.storage.db import StorageManager, ProblemCluster, Opportunity

class OpportunityGate(BaseModel):
    is_valid_opportunity: bool = Field(description="Does this problem represent a commercially viable market gap?")
    commercial_relevance: int = Field(ge=1, le=10, description="Rate commercial urgency and willingness to pay from 1 to 10")

class OpportunitySynthesis(BaseModel):
    concept: str = Field(description="High-level description of the solution/startup idea")
    target_customer: str = Field(description="The primary buyer persona")
    existing_alternatives: List[str] = Field(description="What are they currently using as workarounds?")

class OpportunityEngine:
    """
    Analysis Stage 5: Evaluates ProblemClusters.
    Uses System 1 (Laya / JEV) as a high-speed mathematical gate.
    If qualified, uses Generative AI (Groq / Gemini) to synthesize the concept.
    """

    def __init__(self, router: Optional[ModelRouter] = None, storage: Optional[StorageManager] = None):
        self.router = router or ModelRouter()
        self.storage = storage or StorageManager()

    def evaluate_cluster(self, cluster: ProblemCluster) -> Optional[Opportunity]:
        """Runs decision intelligence over a cluster to determine if it is an Opportunity."""
        print(f"  [opportunity] Evaluating Cluster: {cluster.id} - '{cluster.canonical_problem}'")
        
        prompt = (
            f"Problem Theme: {cluster.canonical_problem}\n"
            f"Unique users complaining: {cluster.unique_users}\n"
            f"Market growth signal: {cluster.growth_signal}"
        )
        
        try:
            # Step 1: System 1 Decision Gate (Laya local / JEV)
            gate = self.router.make_decision(
                prompt=prompt,
                schema=OpportunityGate,
            )
            
            if not gate or not gate.is_valid_opportunity or gate.commercial_relevance < 1:
                print(f"    -> Cluster rejected by System 1 Gate (Viable: {gate.is_valid_opportunity if gate else False}, Score: {gate.commercial_relevance if gate else 0}/10).")
                return None

            print(f"    -> [System 1 Passed] Viable! Severity Score: {gate.commercial_relevance}/10. Synthesizing startup concept...")

            # Step 2: Generative Synthesis (Groq / Gemini)
            synth = self.router.generate_structured(
                prompt=f"Develop a venture startup concept to solve this market problem:\n{prompt}",
                response_model=OpportunitySynthesis,
                system_prompt="You are an elite B2B startup founder and venture capital strategist.",
                model_tier="fast"
            )

            if synth:
                opp = Opportunity(
                    id=f"opp_{uuid.uuid4().hex[:8]}",
                    cluster_id=cluster.id,
                    concept=synth.concept,
                    target_customer=synth.target_customer,
                    existing_alternatives=synth.existing_alternatives,
                    commercial_relevance=gate.commercial_relevance
                )
                
                self.storage.save_opportunity(opp)
                print(f"    -> Valid Opportunity Found: {opp.concept} (Score: {opp.commercial_relevance}/10)")
                return opp
                
        except Exception as e:
            print(f"    -> [!] Opportunity evaluation failed: {e}")
            
        return None
