import pytest
import os
import sqlite3
import json
from src.storage.db import StorageManager, Evidence, PainPoint, ProblemCluster, Opportunity

@pytest.fixture
def storage():
    sm = StorageManager(db_path="file::memory:?cache=shared")
    yield sm

def test_save_evidence(storage):
    ev = Evidence(
        id="ev_123", source="reddit", source_id="abc",
        url="http://test", timestamp="2026-09-01T00:00:00",
        author="test_user", text="test text", metadata={"ups": 10}
    )
    storage.save_evidence(ev)
    
    with sqlite3.connect(storage.db_path, uri=True) as conn:
        cursor = conn.execute("SELECT id, text, metadata FROM evidence WHERE id='ev_123'")
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == "test text"
        assert json.loads(row[2])["ups"] == 10

def test_save_opportunity(storage):
    opp = Opportunity(
        id="opp_1", cluster_id="clus_1", concept="Test Startup",
        target_customer="Devs", existing_alternatives=["Excel"], commercial_relevance=8
    )
    storage.save_opportunity(opp)
    
    with sqlite3.connect(storage.db_path, uri=True) as conn:
        cursor = conn.execute("SELECT id, concept, commercial_relevance FROM opportunities WHERE id='opp_1'")
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == "Test Startup"
        assert row[2] == 8
