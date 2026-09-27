import pytest
from unittest.mock import patch, MagicMock
from src.ingestion.reddit.reddit_miner import RedditMiner
from src.storage.db import Evidence
import os

@patch('src.ingestion.reddit.reddit_miner.praw.Reddit')
@patch.dict(os.environ, {"REDDIT_CLIENT_ID": "mock", "REDDIT_CLIENT_SECRET": "mock"})
def test_reddit_miner_returns_evidence(mock_reddit):
    # Mock PRAW Submission objects
    mock_sub1 = MagicMock()
    mock_sub1.id = "123"
    mock_sub1.title = "Software is broken"
    mock_sub1.selftext = "I can't stand using this inventory tool anymore. It's so slow."
    mock_sub1.author = "angry_user"
    mock_sub1.created_utc = 1690000000
    mock_sub1.permalink = "/r/smallbusiness/comments/123/"
    mock_sub1.score = 50
    mock_sub1.num_comments = 12

    mock_sub2 = MagicMock()
    mock_sub2.selftext = "[deleted]"

    # Setup mock chain
    mock_subreddit = MagicMock()
    mock_subreddit.search.return_value = [mock_sub1, mock_sub2]
    mock_reddit.return_value.subreddit.return_value = mock_subreddit

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
