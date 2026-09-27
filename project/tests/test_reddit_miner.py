import pytest
from unittest.mock import patch, MagicMock
from src.ingestion.reddit.reddit_miner import RedditMiner
from src.storage.db import Evidence

@patch('src.ingestion.reddit.reddit_miner.requests.get')
def test_reddit_miner_returns_evidence(mock_get):
    # Mock Reddit RSS XML response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>t3_123</id>
        <title>Software is broken</title>
        <author><name>/u/angry_user</name></author>
        <updated>2026-09-01T00:00:00+00:00</updated>
        <link href="https://reddit.com/r/smallbusiness/comments/123/software_is_broken" />
        <content type="html">&lt;!-- SC_OFF --&gt;&lt;div class="md"&gt;&lt;p&gt;I can't stand using this inventory tool anymore. It's so slow.&lt;/p&gt;&lt;/div&gt;&lt;!-- SC_ON --&gt;</content>
      </entry>
      <entry>
        <id>t3_456</id>
        <title>Deleted post</title>
        <content type="html">[deleted]</content>
      </entry>
    </feed>
    """
    mock_get.return_value = mock_response

    miner = RedditMiner()
    evidence_list = miner.fetch_evidence(subreddit="smallbusiness", query="software", limit=1)
    
    # Should skip the deleted post (too short) and keep the valid one
    assert len(evidence_list) == 1
    ev = evidence_list[0]
    
    assert isinstance(ev, Evidence)
    assert ev.source == "reddit"
    assert ev.source_id == "123"
    assert "inventory tool" in ev.text
