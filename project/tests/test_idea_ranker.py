import pytest
from unittest.mock import MagicMock
from src.extractors.idea_ranker import IdeaRanker, IdeaProposal, ScoreAxis

@pytest.fixture
def mock_km():
    km = MagicMock()
    
    # Create a valid mock proposal
    mock_proposal = IdeaProposal(
        name="TestIdea",
        wedge="TestWedge length fix > 10 chars",
        icp="TestICP length fix > 5 chars",
        frequency=ScoreAxis(score=8, justification="This is a valid frequency justification.", cited_pain_ids=[1]),
        wtp=ScoreAxis(score=5, justification="This is a valid wtp justification.", cited_pain_ids=[1]),
        incumbent_weakness=ScoreAxis(score=7, justification="This is a valid incumbent justification.", cited_pain_ids=[1]),
        feasibility=ScoreAxis(score=9, justification="This is a valid feasibility justification.", cited_pain_ids=[1]),
        distribution=ScoreAxis(score=6, justification="This is a valid distribution justification.", cited_pain_ids=[1]),
        representative_quote="Test Quote"
    )
    
    km.generate_structured.return_value = mock_proposal
    return km

@pytest.mark.asyncio
async def test_synthesize_idea_uses_deep_tier(mock_km):
    ranker = IdeaRanker(key_manager=mock_km, db_path=":memory:")
    
    test_cluster = {
        "id": 100,
        "label": "Test Cluster",
        "size": 5,
        "first_seen": "2026-01-01",
        "last_seen": "2026-01-02",
        "source_diversity": 1,
        "avg_severity_score": 5.0,
        "wtp_evidence_count": 5
    }
    
    test_pains = [
        {
            "id": 1,
            "summary": "Test summary",
            "quote": "Test quote",
            "severity": 5.0,
            "willingness_to_pay": 5.0,
            "incumbent": "TestIncumbent"
        }
    ]
    
    # Call the synthesis method
    result = await ranker._synthesize_idea_for_cluster_with_validation(test_cluster, test_pains)
    
    assert result is not None
    assert result["name"] == "TestIdea"
    
    # Verify generate_structured was called with model_tier="deep"
    assert mock_km.generate_structured.called, "generate_structured was not called"
    
    # Get the keyword arguments of the last call
    _, kwargs = mock_km.generate_structured.call_args
    assert kwargs.get("model_tier") == "deep", f"Expected model_tier='deep', got {kwargs.get('model_tier')}"
