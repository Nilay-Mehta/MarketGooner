import pytest
from unittest.mock import patch, MagicMock
from src.ingestion.reddit.reddit_miner import RedditMiner
from src.storage.db import Evidence

@patch('src.ingestion.reddit.reddit_miner.requests.get')
def test_reddit_miner_returns_evidence(mock_get):
    # Mock First Call (Search RSS)
    search_response = MagicMock()
    search_response.status_code = 200
    search_response.text = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>t3_123</id>
        <title>Software is broken</title>
        <link href="https://reddit.com/r/smallbusiness/comments/123/software_is_broken" />
      </entry>
    </feed>
    """

    # Mock Second Call (Thread RSS)
    thread_response = MagicMock()
    thread_response.status_code = 200
    thread_response.text = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <!-- OP -->
      <entry>
        <title>Software is broken</title>
        <author><name>/u/angry_user</name></author>
        <updated>2026-09-01T00:00:00+00:00</updated>
        <content type="html">I can't stand using this inventory tool anymore. It's so slow.</content>
      </entry>
      <!-- Comment 1 -->
      <entry>
        <title>Comment</title>
        <author><name>/u/helpful_user</name></author>
        <content type="html">Yeah, I agree! I use Excel instead because it is faster.</content>
      </entry>
    </feed>
    """

    mock_get.side_effect = [search_response, thread_response]

    miner = RedditMiner()
    evidence_list = miner.fetch_evidence(subreddit="smallbusiness", query="software", limit=1)
    
    assert len(evidence_list) == 1
    ev = evidence_list[0]
    
    assert isinstance(ev, Evidence)
    assert ev.source == "reddit"
    assert ev.source_id == "123"
    assert "inventory tool" in ev.text
    assert "[User: helpful_user]" in ev.text
    assert "Excel instead" in ev.text
