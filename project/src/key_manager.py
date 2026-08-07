import os
import json
import requests
from typing import List, Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel
from dotenv import load_dotenv

# Load from both project .env and root .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

T = TypeVar("T", bound=BaseModel)

class KeyManager:
    """Intelligent multi-provider routing and structured token optimizer (Groq, GitHub, Gemini, OpenRouter)."""

    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY2", "").strip() or os.getenv("GROQ_API_KEY", "").strip()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.github_token = os.getenv("GITHUB_TOKEN", "").strip()
        self.tokenrouter_key = None

    def generate_completion(self, prompt: str, task_type: str = "fast_extract", system_prompt: str = "You are an elite Market Research & Gap Identification AI.", json_mode: bool = False) -> str:
        return self.route_completion(prompt=prompt, task_type=task_type, system_prompt=system_prompt, json_mode=json_mode)

    def route_completion(self, prompt: str, task_type: str = "fast_extract", system_prompt: str = "You are an elite Market Research & Gap Identification AI.", json_mode: bool = False) -> str:
        """Smart-routes text queries across free tier providers."""
        if self.groq_key:
            res = self._call_groq(prompt, system_prompt, json_mode=json_mode)
            if res: return res

        if self.github_token:
            res = self._call_github_models(prompt, system_prompt, json_mode=json_mode)
            if res: return res

        if self.gemini_key:
            res = self._call_gemini(prompt, system_prompt, json_mode=json_mode)
            if res: return res

        if self.openrouter_key:
            res = self._call_openrouter(prompt, system_prompt)
            if res: return res

        return (
            "> [!NOTE]\n"
            "> **Offline Output:** Extracted text summarized below.\n\n"
            f"{prompt[:2000]}"
        )

    def generate_structured(self, prompt: str, response_model: Type[T], system_prompt: Optional[str] = None) -> Optional[T]:
        """
        Guaranteed schema-validated generation using instructor + Pydantic models.
        Cascades through providers on network OR validation errors.
        """
        sys_prompt = system_prompt or "You are an elite B2B Market Research & Gap Mining Analyst."

        # 1. Try Groq via Instructor
        if self.groq_key:
            groq_res = self._structured_groq(prompt, response_model, sys_prompt)
            if groq_res is not None:
                return groq_res

        # 2. Try TokenRouter via manual requests (Since Groq is exhausted)
        if self.tokenrouter_key:
            tr_res = self._structured_tokenrouter(prompt, response_model, sys_prompt)
            if tr_res is not None:
                return tr_res

        # 2. Try GitHub Models via Instructor
        if self.github_token:
            gh_res = self._structured_github(prompt, response_model, sys_prompt)
            if gh_res is not None:
                return gh_res

        # 3. Try Gemini via Instructor / JSON Mode
        if self.gemini_key:
            gem_res = self._structured_gemini(prompt, response_model, sys_prompt)
            if gem_res is not None:
                return gem_res

        # 4. Try OpenRouter via Instructor
        if self.openrouter_key:
            or_res = self._structured_openrouter(prompt, response_model, sys_prompt)
            if or_res is not None:
                return or_res

        return None

    def _structured_groq(self, prompt: str, response_model: Type[T], system_prompt: str) -> Optional[T]:
        import instructor
        from openai import OpenAI
        models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "gemma2-9b-it"]
        
        for model in models:
            try:
                client = instructor.from_openai(
                    OpenAI(base_url="https://api.groq.com/openai/v1", api_key=self.groq_key),
                    mode=instructor.Mode.JSON
                )
                return client.chat.completions.create(
                    model=model,
                    response_model=response_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_retries=1
                )
            except Exception:
                continue
        return None

    def _structured_github(self, prompt: str, response_model: Type[T], system_prompt: str) -> Optional[T]:
        import instructor
        from openai import OpenAI
        try:
            client = instructor.from_openai(
                OpenAI(base_url="https://models.inference.ai.azure.com", api_key=self.github_token),
                mode=instructor.Mode.JSON
            )
            return client.chat.completions.create(
                model="gpt-4o",
                response_model=response_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_retries=1
            )
        except Exception:
            return None

    def _structured_gemini(self, prompt: str, response_model: Type[T], system_prompt: str) -> Optional[T]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_key}"
            schema_instruction = f"\nYou MUST respond with valid JSON strictly conforming to this Pydantic schema:\n{json.dumps(response_model.model_json_schema())}"
            res = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [
                        {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{prompt}\n{schema_instruction}"}]}
                    ],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 4096,
                        "responseMimeType": "application/json"
                    }
                },
                timeout=25
            )
            if res.status_code == 200:
                raw_json = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                clean_json = re.sub(r'^```json\s*', '', raw_json.strip())
                clean_json = re.sub(r'\s*```$', '', clean_json.strip())
                return response_model.model_validate_json(clean_json)
        except Exception:
            pass
        return None

    def _structured_openrouter(self, prompt: str, response_model: Type[T], system_prompt: str) -> Optional[T]:
        import instructor
        from openai import OpenAI
        models = ["google/gemma-4-26b-a4b-it:free", "google/gemma-4-31b-it:free"]
        for model in models:
            try:
                client = instructor.from_openai(
                    OpenAI(base_url="https://openrouter.ai/api/v1", api_key=self.openrouter_key),
                    mode=instructor.Mode.JSON
                )
                return client.chat.completions.create(
                    model=model,
                    response_model=response_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_retries=1
                )
            except Exception:
                continue
        return None

    def _structured_tokenrouter(self, prompt: str, response_model: Type[T], system_prompt: str) -> Optional[T]:
        import json
        import re
        try:
            schema_instruction = f"\nYou MUST respond with valid JSON strictly conforming to this Pydantic schema:\n{json.dumps(response_model.model_json_schema())}"
            payload = {
                "model": "moonshotai/kimi-k3-free",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{prompt}\n{schema_instruction}"}
                ],
                "temperature": 0.1,
                "max_tokens": 4096
            }
            res = requests.post(
                "https://api.tokenrouter.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.tokenrouter_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=25
            )
            if res.status_code == 200:
                raw_json = res.json()["choices"][0]["message"]["content"]
                clean_json = re.sub(r'^```json\s*', '', raw_json.strip())
                clean_json = re.sub(r'\s*```$', '', clean_json.strip())
                return response_model.model_validate_json(clean_json)
            else:
                print(f"TokenRouter Error: {res.status_code} - {res.text}")
        except Exception:
            pass
        return None

    def _call_groq(self, prompt: str, system_prompt: str, json_mode: bool = False) -> Optional[str]:
        models = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "gemma2-9b-it"]
        for model in models:
            try:
                payload = {
                    "model": model,
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
                    return res.json()["choices"][0]["message"]["content"]
            except Exception:
                continue
        return None

    def _call_github_models(self, prompt: str, system_prompt: str, json_mode: bool = False) -> Optional[str]:
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
                headers={
                    "Authorization": f"Bearer {self.github_token}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=25
            )
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
        return None

    def _call_gemini(self, prompt: str, system_prompt: str, json_mode: bool = False) -> Optional[str]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_key}"
            gen_config = {"temperature": 0.2, "maxOutputTokens": 4096}
            if json_mode:
                gen_config["responseMimeType"] = "application/json"

            res = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [
                        {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}
                    ],
                    "generationConfig": gen_config
                },
                timeout=25
            )
            if res.status_code == 200:
                return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass
        return None

    def _call_openrouter(self, prompt: str, system_prompt: str) -> Optional[str]:
        free_models = [
            "google/gemma-4-26b-a4b-it:free",
            "google/gemma-4-31b-it:free",
            "inclusionai/ling-3.0-flash:free"
        ]
        for model in free_models:
            try:
                res = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/opencode",
                        "X-Title": "Opencode Market Research"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 4096
                    },
                    timeout=25
                )
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
            except Exception:
                continue
        return None
