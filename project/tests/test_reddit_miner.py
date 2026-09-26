import pytest
from unittest.mock import patch, MagicMock
from src.ingestion.reddit.reddit_miner import RedditMiner
from src.storage.db import Evidence

@patch('src.ingestion.reddit.reddit_miner.requests.get')
def test_reddit_miner_returns_evidence(mock_get):
    # Mock Reddit JSON response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "children": [
                {
                    "data": {
                        "id": "123",
                        "title": "Software is broken",
                        "selftext": "I can't stand using this inventory tool anymore. It's so slow.",
                        "author": "angry_user",
                        "created_utc": 1690000000,
                        "permalink": "/r/smallbusiness/comments/123/software_is_broken",
                        "score": 50,
                        "num_comments": 12
                    }
                },
                {
                    "data": {
                        "id": "456",
                        "title": "Deleted post",
                        "selftext": "[deleted]",
                        "author": "deleted",
                        "created_utc": 1690000001
                    }
                }
            ]
        }
    }
    mock_get.return_value = mock_response

    miner = RedditMiner()
    evidence_list = miner.fetch_evidence(subreddit="smallbusiness", query="software", limit=5)
    
    # Should skip the deleted post and keep the valid one
    assert len(evidence_list) == 1
    ev = evidence_list[0]
    
    assert isinstance(ev, Evidence)
    assert ev.source == "reddit"
    assert ev.source_id == "123"
    assert "inventory tool" in ev.text
    assert ev.metadata["upvotes"] == 50
