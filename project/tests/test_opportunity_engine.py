import pytest
from unittest.mock import MagicMock
from src.analysis.opportunities.idea_ranker import OpportunityEngine, OpportunityGate, OpportunitySynthesis
from src.storage.db import ProblemCluster

def test_opportunity_engine_evaluates_cluster():
    mock_router = MagicMock()
    mock_storage = MagicMock()
    
    # Mock System 1 Gate (Laya) approving the cluster
    mock_router.make_decision.return_value = OpportunityGate(
        is_valid_opportunity=True,
        commercial_relevance=9
    )
    # Mock Generative synthesis
    mock_router.generate_structured.return_value = OpportunitySynthesis(
        concept="Automated Restaurant Inventory Sync",
        target_customer="Multi-location restaurant owners",
        existing_alternatives=["Excel", "Toast"]
    )
    
    engine = OpportunityEngine(router=mock_router, storage=mock_storage)
    
    cluster = ProblemCluster(
        id="clus_123",
        canonical_problem="Manual inventory synchronization is slow",
        pain_point_ids=["pp_1", "pp_2"],
        unique_users=10,
        source_diversity=2,
        growth_signal=5.0
    )
    
    opp = engine.evaluate_cluster(cluster)
    
    assert opp is not None
    assert opp.concept == "Automated Restaurant Inventory Sync"
    assert opp.commercial_relevance == 9
    assert opp.cluster_id == "clus_123"
    
    mock_storage.save_opportunity.assert_called_once()
