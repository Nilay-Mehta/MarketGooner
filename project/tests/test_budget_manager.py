import pytest
import time
from unittest.mock import patch

# We are importing the BudgetManager which we haven't built yet
from src.orchestration.budget.budget_manager import BudgetManager

def test_budget_manager_initialization():
    limits = {"groq": {"rpm": 30, "tpm": 6000}}
    bm = BudgetManager(limits=limits)
    
    # Verify limits are stored and usage starts at 0
    assert bm.limits == limits
    assert bm.usage["groq"]["requests"] == 0
    assert bm.usage["groq"]["tokens"] == 0

def test_consume_and_can_proceed():
    # Set very tight limits: 2 requests per minute, or 100 tokens per minute
    bm = BudgetManager(limits={"groq": {"rpm": 2, "tpm": 100}})
    
    # Request 1: 50 tokens (Allowed)
    assert bm.can_proceed("groq", estimated_tokens=50) is True
    bm.consume("groq", tokens_used=50)
    
    # Request 2: 40 tokens (Allowed)
    assert bm.can_proceed("groq", estimated_tokens=40) is True
    bm.consume("groq", tokens_used=40)
    
    # Request 3: 5 tokens (Denied - Hit RPM limit of 2)
    assert bm.can_proceed("groq", estimated_tokens=5) is False
    
    # Reset RPM to test TPM
    bm.usage["groq"]["requests"] = 1 
    
    # Request 4: 20 tokens (Denied - 90 + 20 = 110 > 100 TPM limit)
    assert bm.can_proceed("groq", estimated_tokens=20) is False

@patch("time.time")
def test_budget_reset_after_window(mock_time):
    # Start time at 100.0
    mock_time.return_value = 100.0
    bm = BudgetManager(limits={"groq": {"rpm": 1, "tpm": 100}})
    
    # Consume the only allowed request
    bm.consume("groq", tokens_used=50)
    assert bm.can_proceed("groq", estimated_tokens=10) is False
    
    # Move time forward by 61 seconds (past the 1-minute window)
    mock_time.return_value = 161.0
    
    # The manager should automatically reset the window and allow the request
    assert bm.can_proceed("groq", estimated_tokens=10) is True
