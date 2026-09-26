import pytest
from unittest.mock import patch, MagicMock
from src.key_manager import KeyManager
from src.orchestration.budget_manager import BudgetManager, RateLimitExceededError

@pytest.fixture
def km():
    km = KeyManager()
    km.groq_key = "test_groq"
    # Set up a budget manager that explicitly blocks 'groq'
    km.budget = BudgetManager(limits={"groq": {"rpm": 0, "tpm": 0}})
    return km

def test_keymanager_raises_error_when_budget_exceeded(km):
    # Mock the actual call so it doesn't try to make a network request if it bypasses the budget
    with patch.object(km, '_call_groq') as mock_groq:
        # Expect the RateLimitExceededError to be raised
        with pytest.raises(RateLimitExceededError) as excinfo:
            km.generate_completion(prompt="Hello", model_tier="fast", task_type="extract")
        
        # Verify the exception message mentions the rate limit
        assert "Rate limit exceeded for provider: groq" in str(excinfo.value)
        # Ensure the API call was never actually made
        mock_groq.assert_not_called()

def test_keymanager_consumes_budget_on_success():
    km = KeyManager()
    km.groq_key = "test_groq"
    # Budget that allows requests
    km.budget = BudgetManager(limits={"groq": {"rpm": 10, "tpm": 1000}})
    
    with patch.object(km, '_call_groq', return_value="success response"):
        # Initial budget check
        assert km.budget.usage["groq"]["requests"] == 0
        
        # Make a successful call
        km.generate_completion(prompt="Hello", model_tier="fast", task_type="extract")
        
        # Verify budget was consumed
        assert km.budget.usage["groq"]["requests"] == 1
        assert km.budget.usage["groq"]["tokens"] > 0  # Assuming it estimates or counts tokens
