import pytest
from unittest.mock import patch, MagicMock
from src.orchestration.router.model_router import ModelRouter

@pytest.fixture
def km():
    km = ModelRouter()
    km.groq_key = "test_groq"
    km.gemini_key = "test_gemini"
    km.github_token = "test_github"
    km.openrouter_key = "test_openrouter"
    km.tokenrouter_key = "test_tokenrouter"
    return km

def test_route_completion_fast_tier(km, capsys):
    # Mock all providers
    with patch.object(km, '_call_groq', return_value="groq_fast_response") as mock_groq, \
         patch.object(km, '_call_gemini') as mock_gemini, \
         patch.object(km, '_call_github_models') as mock_github:
         
        # Fast tier should hit Groq first and return
        res = km.generate_completion(prompt="hello", model_tier="fast")
        
        assert res == "groq_fast_response"
        mock_groq.assert_called_once()
        mock_gemini.assert_not_called()
        mock_github.assert_not_called()
        
        captured = capsys.readouterr()
        assert "[route_completion] tier: fast, provider: groq" in captured.out

def test_route_completion_deep_tier(km, capsys):
    # Mock all providers
    with patch.object(km, '_call_groq') as mock_groq, \
         patch.object(km, '_call_gemini', return_value="gemini_deep_response") as mock_gemini, \
         patch.object(km, '_call_github_models') as mock_github:
         
        # Deep tier should hit Gemini first
        res = km.generate_completion(prompt="hello", model_tier="deep")
        
        assert res == "gemini_deep_response"
        mock_gemini.assert_called_once()
        mock_groq.assert_not_called()
        
        captured = capsys.readouterr()
        assert "[route_completion] tier: deep, provider: gemini" in captured.out

def test_route_completion_deep_fallback(km, capsys):
    # Deep fails, falls back to fast
    with patch.object(km, '_call_gemini', return_value=None) as mock_gemini, \
         patch.object(km, '_call_github_models', return_value=None) as mock_github, \
         patch.object(km, '_call_openrouter', return_value=None) as mock_openrouter, \
         patch.object(km, '_call_groq', return_value="groq_fallback_response") as mock_groq:
         
        res = km.generate_completion(prompt="hello", model_tier="deep")
        
        assert res == "groq_fallback_response"
        mock_gemini.assert_called_once()
        mock_github.assert_called_once()
        mock_openrouter.assert_called_once()
        mock_groq.assert_called_once()
        
        captured = capsys.readouterr()
        assert "[route_completion] tier: deep, all deep providers failed. Falling back to fast tier." in captured.out
        assert "[route_completion] tier: fast, provider: groq" in captured.out
