import os
import re
from typing import Optional
from src.orchestration.router.model_router import ModelRouter
from src.storage.db import Opportunity

class DiffusionEngine:
    """
    Diffusion Stage 9: Generates product and marketing assets.
    Consumes a validated Opportunity and uses Deep LLM reasoning to output a markdown dossier.
    """

    def __init__(self, router: Optional[ModelRouter] = None):
        self.router = router or ModelRouter()
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "output")
        os.makedirs(self.output_dir, exist_ok=True)

    def _sanitize_filename(self, text: str) -> str:
        clean = re.sub(r'[\\/*?:"<>| ]', '_', text.strip())
        return clean[:50]

    def generate_dossier(self, opp: Opportunity) -> Optional[str]:
        """Uses Deep Reasoning to write a comprehensive startup dossier."""
        print(f"  [diffusion] Generating Dossier for Opportunity: {opp.id}")
        
        system_prompt = (
            "You are an elite product marketing manager and startup founder. "
            "Write a highly specific, professional product dossier based on the provided opportunity."
            "Include: 1) Executive Summary 2) Core Features 3) GTM Strategy 4) SEO Landing Page Copy."
        )

        prompt = (
            f"Concept: {opp.concept}\n"
            f"Target Customer: {opp.target_customer}\n"
            f"Existing Alternatives: {', '.join(opp.existing_alternatives)}\n"
            f"Commercial Relevance Score: {opp.commercial_relevance}/10\n\n"
            "Please generate the complete markdown dossier."
        )
        
        try:
            # We use the Generative Deep Tier because this requires heavy synthesis
            markdown_content = self.router.generate_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=False,
                model_tier="deep"
            )
            
            if markdown_content:
                filename = f"dossier_{self._sanitize_filename(opp.concept)}.md"
                filepath = os.path.join(self.output_dir, filename)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                    
                print(f"    -> Markdown Dossier saved to: {filepath}")

                # Automatically convert to styled Word document
                try:
                    from md_to_word import convert_md_to_docx
                    docx_filepath = os.path.splitext(filepath)[0] + ".docx"
                    convert_md_to_docx(filepath, docx_filepath)
                    print(f"    -> Word Document (.docx) saved to: {docx_filepath}")
                except Exception as docx_err:
                    print(f"    [!] Word conversion skipped: {docx_err}")

                return filepath
                
        except Exception as e:
            print(f"    -> [!] Diffusion generation failed: {e}")
            
        return None
