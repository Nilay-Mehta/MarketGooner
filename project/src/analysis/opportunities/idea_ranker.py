import uuid
from typing import Optional, List
from pydantic import BaseModel, Field
from src.orchestration.router.model_router import ModelRouter
from src.storage.db import StorageManager, ProblemCluster, Opportunity

class OpportunityEval(BaseModel):
    is_valid_opportunity: bool = Field(description="Does this problem represent a commercially viable market gap?")
    concept: str = Field(description="High-level description of the solution/startup idea (if valid)")
    target_customer: str = Field(description="The primary buyer persona (if valid)")
    existing_alternatives: List[str] = Field(description="What are they currently using?")
    commercial_relevance: int = Field(description="Score 1-10 on willingness to pay for a solution")

class OpportunityEngine:
    """
    Analysis Stage 5: Evaluates ProblemClusters.
    Uses JEV/Decision models to filter out weak signals.
    Generates Opportunity candidates for Deep Reasoning.
    """

    def __init__(self, router: Optional[ModelRouter] = None, storage: Optional[StorageManager] = None):
        self.router = router or ModelRouter()
        self.storage = storage or StorageManager()

    def evaluate_cluster(self, cluster: ProblemCluster) -> Optional[Opportunity]:
        """Runs decision intelligence over a cluster to determine if it is an Opportunity."""
        print(f"  [opportunity] Evaluating Cluster: {cluster.id} - '{cluster.canonical_problem}'")
        
        system_prompt = (
            "You are a rigorous Venture Capital analyst and product strategist. "
            "Evaluate this recurring market problem. Determine if it represents a commercially viable startup opportunity. "
            "If it is a weak complaint or has no commercial value, set 'is_valid_opportunity' to false."
        )

        prompt = f"Cluster Theme: {cluster.canonical_problem}\nUsers complaining: {cluster.unique_users}\nGrowth Signal: {cluster.growth_signal}"
        
        try:
            # We use the Decision capability (JEV integration point)
            # Fallback will use standard fast extraction if JEV isn't plugged in yet
            result = self.router.make_decision(
                prompt=prompt,
                schema=OpportunityEval,
            )
            
            if result and result.is_valid_opportunity and result.commercial_relevance >= 1:
                opp = Opportunity(
                    id=f"opp_{uuid.uuid4().hex[:8]}",
                    cluster_id=cluster.id,
                    concept=result.concept,
                    target_customer=result.target_customer,
                    existing_alternatives=result.existing_alternatives,
                    commercial_relevance=result.commercial_relevance
                )
                
                self.storage.save_opportunity(opp)
                print(f"    -> Valid Opportunity Found: {opp.concept} (Score: {opp.commercial_relevance}/10)")
                return opp
            else:
                print(f"    -> Cluster rejected (Not commercially viable or score too low).")
                
        except Exception as e:
            print(f"    -> [!] Opportunity evaluation failed: {e}")
            
        return None
