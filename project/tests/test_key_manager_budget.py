import pytest
from unittest.mock import patch, MagicMock
from src.orchestration.router.model_router import ModelRouter
from src.orchestration.budget.budget_manager import BudgetManager, RateLimitExceededError

@pytest.fixture
def km():
    km = ModelRouter()
    km.groq_key = "test_groq"
    # Set up a budget manager that explicitly blocks 'groq'
    km.budget = BudgetManager(limits={"groq": {"rpm": 0, "tpm": 0}})
    return km

@patch('src.key_manager.time.sleep')
def test_keymanager_raises_error_when_budget_exceeded(mock_sleep, km):
    with patch('src.key_manager.requests.post') as mock_post:
        with pytest.raises(RateLimitExceededError) as excinfo:
            km.generate_completion(prompt="Hello", model_tier="fast", task_type="extract")
        
        assert "Max retries exceeded due to rate limits" in str(excinfo.value)
        mock_post.assert_not_called()
        assert mock_sleep.call_count == 3

def test_keymanager_consumes_budget_on_success():
    km = ModelRouter()
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

@patch('src.key_manager.time.sleep')
def test_keymanager_retries_on_rate_limit(mock_sleep):
    km = ModelRouter()
    km.groq_key = "test_groq"
    km.budget = BudgetManager(limits={"groq": {"rpm": 10, "tpm": 1000}})
    
    # We will simulate the budget rejecting the first attempt, but allowing the second
    call_count = {"count": 0}
    
    def fake_can_proceed(provider, estimated_tokens=0):
        if call_count["count"] == 0:
            call_count["count"] += 1
            return False  # Force RateLimitExceededError
        return True
        
    km.budget.can_proceed = fake_can_proceed
    
    with patch('src.key_manager.requests.post') as mock_post:
        # The API call itself succeeds when it is finally allowed
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "success_after_wait"}}]}
        mock_post.return_value = mock_response
        
        # generate_completion should catch the error, sleep, and try again, finally succeeding
        res = km.generate_completion(prompt="Hello", model_tier="fast", task_type="extract")
        
        assert res == "success_after_wait"
        mock_sleep.assert_called_once_with(60)
