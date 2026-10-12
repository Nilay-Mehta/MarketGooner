import uuid
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from src.orchestration.router.model_router import ModelRouter
from src.storage.db import StorageManager, PainPoint, ProblemCluster

# LLM Clustering Output Schema
class GroupedCluster(BaseModel):
    canonical_problem: str = Field(description="The overarching theme or core problem combining these pain points")
    pain_point_ids: List[str] = Field(description="The IDs of the specific PainPoints that belong in this cluster")

class ClusteringResponse(BaseModel):
    clusters: List[GroupedCluster] = Field(description="List of identified problem clusters")

class ClusteringEngine:
    """
    Analysis Stage 4: Deduplicates and semantically groups PainPoints.
    Produces mathematical ProblemClusters.
    """

    def __init__(self, router: Optional[ModelRouter] = None, storage: Optional[StorageManager] = None):
        self.router = router or ModelRouter()
        self.storage = storage or StorageManager()

    def build_clusters(self, pain_points: List[PainPoint]) -> List[ProblemCluster]:
        """Groups PainPoints into ProblemClusters using the Fast/Extraction model tier."""
        if not pain_points:
            return []
            
        print(f"  [clustering] Grouping {len(pain_points)} pain points...")
        
        # Prepare payload for LLM
        payload = []
        for pp in pain_points:
            payload.append({
                "id": pp.id,
                "problem": pp.problem,
                "category": pp.category,
                "severity": pp.severity
            })

        system_prompt = (
            "You are an elite B2B Product Strategist and Market Clustering Engine. "
            "Your job is to read user pain points and group them into TIGHT, HIGHLY SPECIFIC problem clusters. "
            "\nCRITICAL RULES:"
            "\n1. DO NOT create broad catch-all buckets like 'Manual processes burden businesses' or 'General inefficiencies'."
            "\n2. Group by SPECIFIC operational workflow or buying trigger (e.g., 'Shopfloor Inventory Reconciliation vs Excel', 'Per-Seat Software Feature Gating', 'Client Conversation Context & Follow-up', 'Shared Inbox Ownership Friction')."
            "\n3. Each cluster MUST represent a distinct, focused software product or wedge, not an entire business suite."
            "\n4. If a pain point represents a unique, distinct workflow, give it its own focused cluster."
            "\nReturn a strictly formatted JSON object with 'clusters', each having a concise, punchy 'canonical_problem' and 'pain_point_ids'."
        )

        prompt = (
            f"Group these {len(payload)} pain points into focused, domain-specific problem themes. "
            f"Keep clusters tight and actionable (2-4 pain points per cluster maximum unless they are identical workflows):\n"
            f"{json.dumps(payload, indent=2)}"
        )
        
        generated_clusters = []
        try:
            # We use the Extraction tier because this is structured data processing
            result = self.router.generate_structured(
                prompt=prompt,
                response_model=ClusteringResponse,
                system_prompt=system_prompt,
                task_type="fast_extract",
                model_tier="fast"
            )

            if result and result.clusters:
                for grp in result.clusters:
                    # Basic calculation for signals based on the clustered pain points
                    valid_ids = [pid for pid in grp.pain_point_ids if any(p.id == pid for p in pain_points)]
                    if not valid_ids:
                        continue
                        
                    cluster_obj = ProblemCluster(
                        id=f"clus_{uuid.uuid4().hex[:8]}",
                        canonical_problem=grp.canonical_problem,
                        pain_point_ids=valid_ids,
                        unique_users=len(valid_ids),  # Approximated
                        source_diversity=1,           # Approximated
                        growth_signal=len(valid_ids) * 1.5 # Placeholder math
                    )
                    
                    self.storage.save_cluster(cluster_obj)
                    generated_clusters.append(cluster_obj)
                    print(f"    -> Built Cluster: '{cluster_obj.canonical_problem[:40]}...' (Size: {len(valid_ids)})")
                    
        except Exception as e:
            print(f"    -> [!] Clustering failed: {e}")
            import traceback
            traceback.print_exc()

        if not generated_clusters:
            print(f"    -> [DEBUG] Result from LLM: {result if 'result' in locals() else 'None'}")

        print(f"\n[ClusteringEngine] Finished. Built {len(generated_clusters)} ProblemClusters.")
        return generated_clusters
