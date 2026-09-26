import uuid
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from src.orchestration.router.model_router import ModelRouter
from src.storage.db import StorageManager, Evidence, PainPoint

# Intermediate LLM Schema (Optimized for AI to output)
class ExtractedPain(BaseModel):
    has_pain: bool = Field(description="Is there a legitimate complaint, problem, or pain point in this text?")
    problem: str = Field(default="", description="The core problem described (if has_pain is true)")
    affected_user: str = Field(default="", description="The specific user persona experiencing the pain")
    category: str = Field(default="", description="High-level category (e.g., 'Inventory Management', 'DevOps')")
    severity: int = Field(default=1, description="1-10 severity score based on the frustration level")
    workaround: Optional[str] = Field(None, description="What the user is doing to manually solve it right now")

class PainExtractor:
    """
    Intelligence Stage 2: Analyzes canonical Evidence objects using the ModelRouter.
    Extracts structured PainPoints and saves them to the StorageManager.
    """

    def __init__(self, router: Optional[ModelRouter] = None, storage: Optional[StorageManager] = None):
        self.router = router or ModelRouter()
        self.storage = storage or StorageManager()

    def process_evidence(self, evidence_list: List[Evidence]) -> List[PainPoint]:
        """
        Processes a list of Evidence objects one by one (or in batches eventually).
        Saves successfully extracted PainPoints to the database.
        """
        extracted_pains = []
        
        system_prompt = (
            "You are an expert B2B Market Research AI. "
            "Your task is to analyze user discussions and extract strictly verified customer friction, complaints, or problems. "
            "If the user is not complaining or describing a problem, set 'has_pain' to false."
        )

        for ev in evidence_list:
            print(f"  [extract] Analyzing Evidence: {ev.id}")
            
            prompt = f"Analyze the following user post from {ev.source}:\n\n{ev.text[:2500]}"
            
            try:
                # Use the Extraction Model capability of the Router
                result = self.router.generate_structured(
                    prompt=prompt,
                    response_model=ExtractedPain,
                    system_prompt=system_prompt,
                    task_type="fast_extract",
                    model_tier="fast"
                )
                
                if result and result.has_pain and len(result.problem) > 10:
                    # Map the LLM output to our Canonical PainPoint Schema
                    pain_point = PainPoint(
                        id=f"pp_{uuid.uuid4().hex[:8]}",
                        problem=result.problem,
                        affected_user=result.affected_user,
                        category=result.category,
                        severity=result.severity,
                        workaround=result.workaround,
                        evidence_ids=[ev.id]
                    )
                    
                    # Save to DB
                    self.storage.save_pain_point(pain_point)
                    extracted_pains.append(pain_point)
                    print(f"    -> Extracted Pain: {pain_point.problem[:50]}...")
                else:
                    print("    -> No actionable pain detected.")
                    
            except Exception as e:
                print(f"    -> [!] Extraction failed for {ev.id}: {e}")

        print(f"\n[PainExtractor] Finished processing {len(evidence_list)} evidence items. Generated {len(extracted_pains)} PainPoints.")
        return extracted_pains
