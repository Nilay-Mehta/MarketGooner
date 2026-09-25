import time
from typing import Dict, Any

class BudgetManager:
    """
    Tracks and enforces rate limits (Requests Per Minute and Tokens Per Minute)
    across different LLM providers to prevent 429 errors and enforce graceful degradation.
    """
    
    def __init__(self, limits: Dict[str, Dict[str, int]]):
        """
        limits format:
        {
            "groq": {"rpm": 30, "tpm": 6000},
            "gemini": {"rpm": 15, "tpm": 1000000}
        }
        """
        self.limits = limits
        self.usage: Dict[str, Dict[str, Any]] = {}
        
        # Initialize usage tracking for each provider
        for provider in limits.keys():
            self.usage[provider] = {
                "requests": 0,
                "tokens": 0,
                "window_start": time.time()
            }

    def _reset_if_needed(self, provider: str) -> None:
        """Resets the rolling minute window if 60 seconds have passed."""
        if provider not in self.usage:
            return
            
        current_time = time.time()
        elapsed = current_time - self.usage[provider]["window_start"]
        
        if elapsed >= 60.0:
            self.usage[provider]["requests"] = 0
            self.usage[provider]["tokens"] = 0
            self.usage[provider]["window_start"] = current_time

    def can_proceed(self, provider: str, estimated_tokens: int = 0) -> bool:
        """
        Checks if the requested tokens and 1 request can fit into the current budget.
        """
        if provider not in self.limits:
            return True  # No limits defined for this provider
            
        self._reset_if_needed(provider)
        
        provider_limits = self.limits[provider]
        current_usage = self.usage[provider]
        
        # Check RPM
        if current_usage["requests"] + 1 > provider_limits.get("rpm", float('inf')):
            return False
            
        # Check TPM
        if current_usage["tokens"] + estimated_tokens > provider_limits.get("tpm", float('inf')):
            return False
            
        return True

    def consume(self, provider: str, tokens_used: int) -> None:
        """
        Records the usage of a request and its associated tokens.
        """
        if provider not in self.limits:
            return
            
        self._reset_if_needed(provider)
        
        self.usage[provider]["requests"] += 1
        self.usage[provider]["tokens"] += tokens_used
