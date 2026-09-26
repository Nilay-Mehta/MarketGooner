import os
import time
import requests
import re
from typing import Optional, Type, TypeVar, Literal, Dict, Any
from pydantic import BaseModel

from src.orchestration.budget.budget_manager import BudgetManager, RateLimitExceededError

T = TypeVar('T', bound=BaseModel)

class ModelRouter:
    """
    Intelligent Model Router (Phase 2).
    Separates Intelligence into:
    1. Decision Models (JEV, local classifiers) - For narrow, structured outputs.
    2. Extraction Models (Groq, Gemini Flash) - For fast text extraction.
    3. Generative/Reasoning Models (GitHub/GPT-4o, Gemini Pro) - For deep synthesis.
    """

    def __init__(self):
        # API Keys
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
        self.github_token = os.getenv("GITHUB_TOKEN", "").strip()
        self.jev_key = os.getenv("JEV_API_KEY", "").strip()  # Placeholder for TypeSafe AI JEV
        
        # Budget Manager (Protects against rate limits and enforces zero-cost where possible)
        self.budget = BudgetManager(limits={
            "groq": {"rpm": 30, "tpm": 6000},
            "gemini": {"rpm": 15, "tpm": 1000000},
            "github": {"rpm": 15, "tpm": 40000},
            "jev": {"rpm": 60, "tpm": 100000}  # Expected fast limits for System 1
        })

    # =====================================================================
    # DECISION INTELLIGENCE (System 1 / Narrow Decisions)
    # =====================================================================
    
    def make_decision(self, prompt: str, schema: Type[T]) -> Optional[T]:
        """
        Uses a highly optimized model (like JEV) for narrow structured decisions
        (e.g., 'Is this a complaint?' -> YES/NO).
        """
        # If JEV is enabled, route there. Otherwise fallback to Groq/Gemini as polyfill.
        if self.jev_key:
            return self._call_jev(prompt, schema)
            
        # Fallback to extraction models for decisions
        return self.generate_structured(prompt, schema, task_type="decision", model_tier="fast")

    def _call_jev(self, prompt: str, schema: Type[T]) -> Optional[T]:
        """Future integration point for TypeSafe AI's Jev model."""
        # TODO: Implement Jev Langchain harness / API integration here
        pass

    # =====================================================================
    # GENERATIVE / EXTRACTION INTELLIGENCE
    # =====================================================================

    def generate_completion(self, prompt: str, task_type: str = "fast_extract", system_prompt: str = "You are an elite AI.", json_mode: bool = False, model_tier: Literal['fast','deep'] = 'fast') -> str:
        """Text generation with automatic retry loop for Rate Limits."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self._route_completion_internal(prompt, system_prompt, json_mode, model_tier)
            except RateLimitExceededError as e:
                print(f"\\n[budget_manager] {e}. Pausing for 60 seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(60)
        raise RateLimitExceededError("Max retries exceeded due to rate limits.")

    def generate_structured(self, prompt: str, response_model: Type[T], system_prompt: Optional[str] = None, task_type: str = "fast_extract", model_tier: Literal['fast','deep'] = 'fast') -> Optional[T]:
        """Structured JSON generation with automatic retry loop."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self._route_structured_internal(prompt, response_model, system_prompt, model_tier)
            except RateLimitExceededError as e:
                print(f"\\n[budget_manager] {e}. Pausing for 60 seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(60)
        raise RateLimitExceededError("Max retries exceeded due to rate limits.")

    # =====================================================================
    # INTERNAL ROUTING LOGIC
    # =====================================================================

    def _route_completion_internal(self, prompt: str, system_prompt: str, json_mode: bool, model_tier: str) -> str:
        if model_tier == "deep":
            if self.gemini_key:
                res = self._call_gemini(prompt, system_prompt, json_mode=json_mode)
                if res: return res
            if self.github_token:
                res = self._call_github_models(prompt, system_prompt, json_mode=json_mode)
                if res: return res
                
        if self.groq_key:
            res = self._call_groq(prompt, system_prompt, json_mode=json_mode)
            if res: return res
        if self.gemini_key:
            res = self._call_gemini(prompt, system_prompt, json_mode=json_mode)
            if res: return res
            
        return "ERROR: All providers failed."

    def _route_structured_internal(self, prompt: str, response_model: Type[T], system_prompt: Optional[str], model_tier: str) -> Optional[T]:
        sys_prompt = system_prompt or "You are an elite B2B Market Research AI."
        
        if model_tier == "deep":
            if self.gemini_key:
                res = self._structured_gemini(prompt, response_model, sys_prompt)
                if res: return res
                
        if self.groq_key:
            # We use Groq's fast inference for structured extraction usually
            pass # TODO implement fast structured groq extraction
            
        if self.gemini_key:
            res = self._structured_gemini(prompt, response_model, sys_prompt)
            if res: return res

        return None

    # =====================================================================
    # PROVIDER IMPLEMENTATIONS
    # =====================================================================

    def _call_groq(self, prompt: str, system_prompt: str, json_mode: bool = False) -> Optional[str]:
        if not self.budget.can_proceed("groq"):
            raise RateLimitExceededError("Rate limit exceeded for provider: groq")
        try:
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 4096
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=20
            )
            if res.status_code == 200:
                self.budget.consume("groq", tokens_used=1000)
                return res.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
        return None

    def _structured_gemini(self, prompt: str, response_model: Type[T], system_prompt: str) -> Optional[T]:
        if not self.budget.can_proceed("gemini"):
            raise RateLimitExceededError("Rate limit exceeded for provider: gemini")
        import json
        try:
            schema_instruction = f"\\nYou MUST respond with valid JSON strictly conforming to this Pydantic schema:\\n{json.dumps(response_model.model_json_schema())}"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={self.gemini_key}"
            res = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"role": "user", "parts": [{"text": f"{system_prompt}\\n\\n{prompt}\\n{schema_instruction}"}]}],
                    "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
                },
                timeout=25
            )
            if res.status_code == 200:
                self.budget.consume("gemini", tokens_used=1000)
                raw_json = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                clean_json = re.sub(r'^```json\\s*', '', raw_json.strip())
                clean_json = re.sub(r'\\s*```$', '', clean_json.strip())
                return response_model.model_validate_json(clean_json)
        except Exception as e:
            print(f"Gemini Error: {e}")
        return None

    def _call_gemini(self, prompt: str, system_prompt: str, json_mode: bool = False) -> Optional[str]:
        if not self.budget.can_proceed("gemini"):
            raise RateLimitExceededError("Rate limit exceeded for provider: gemini")
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={self.gemini_key}"
            gen_config = {"temperature": 0.2, "maxOutputTokens": 4096}
            if json_mode:
                gen_config["responseMimeType"] = "application/json"

            res = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"role": "user", "parts": [{"text": f"{system_prompt}\\n\\n{prompt}"}]}],
                    "generationConfig": gen_config
                },
                timeout=25
            )
            if res.status_code == 200:
                self.budget.consume("gemini", tokens_used=1000)
                return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass
        return None

    def _call_github_models(self, prompt: str, system_prompt: str, json_mode: bool = False) -> Optional[str]:
        if not self.budget.can_proceed("github"):
            raise RateLimitExceededError("Rate limit exceeded for provider: github")
        try:
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 4096
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            res = requests.post(
                "https://models.inference.ai.azure.com/chat/completions",
                headers={"Authorization": f"Bearer {self.github_token}", "Content-Type": "application/json"},
                json=payload,
                timeout=25
            )
            if res.status_code == 200:
                self.budget.consume("github", tokens_used=1000)
                return res.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
        return None
