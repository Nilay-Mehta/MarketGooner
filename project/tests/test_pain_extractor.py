import pytest
from unittest.mock import MagicMock
from src.intelligence.extraction.pain_extractor import PainExtractor, ExtractedPain
from src.storage.db import Evidence

def test_pain_extractor_process_evidence():
    # Mock the router and storage
    mock_router = MagicMock()
    mock_storage = MagicMock()
    
    # Mock LLM returning a valid pain point
    mock_router.generate_structured.return_value = ExtractedPain(
        has_pain=True,
        problem="Inventory sync fails constantly",
        affected_user="Restaurant Owner",
        category="Inventory",
        severity=8,
        workaround="Manual excel"
    )
    
    extractor = PainExtractor(router=mock_router, storage=mock_storage)
    
    ev = Evidence(
        id="ev_123", source="reddit", source_id="abc", url="test", 
        timestamp="test", author="user", text="Fake complaint text here which is long enough",
        metadata={}
    )
    
    pain_points = extractor.process_evidence([ev])
    
    # Check that it extracted successfully
    assert len(pain_points) == 1
    pp = pain_points[0]
    assert pp.problem == "Inventory sync fails constantly"
    assert pp.severity == 8
    
    # Ensure it tried to save to DB
    mock_storage.save_pain_point.assert_called_once()
    saved_pp = mock_storage.save_pain_point.call_args[0][0]
    assert saved_pp.id == pp.id
