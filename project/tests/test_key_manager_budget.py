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
    with patch('src.key_manager.requests.post') as mock_post:
        with pytest.raises(RateLimitExceededError) as excinfo:
            km.generate_completion(prompt="Hello", model_tier="fast", task_type="extract")
        
        assert "Rate limit exceeded for provider: groq" in str(excinfo.value)
        mock_post.assert_not_called()

def test_keymanager_consumes_budget_on_success():
    km = KeyManager()
    km.groq_key = "test_groq"
    km.budget = BudgetManager(limits={"groq": {"rpm": 10, "tpm": 1000}})
    
    with patch('src.key_manager.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "success"}}]}
        mock_post.return_value = mock_response
        
        assert km.budget.usage["groq"]["requests"] == 0
        
        km.generate_completion(prompt="Hello", model_tier="fast", task_type="extract")
        
        assert km.budget.usage["groq"]["requests"] == 1
        assert km.budget.usage["groq"]["tokens"] > 0
