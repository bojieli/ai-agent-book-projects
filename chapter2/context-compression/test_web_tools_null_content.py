"""
Test suite locking out TypeError in WebTools.search_web
when fetch_webpage returns a dictionary containing 'content': None.
"""

import os
import sys
from unittest.mock import MagicMock

sys.modules['html2text'] = MagicMock()

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from web_tools import WebTools


def test_search_web_handles_null_page_content():
    """
    Ensure search_web calculates content_length correctly when page_content['content'] is None.
    """
    tool = WebTools.__new__(WebTools)
    tool.serper_api_key = "dummy"
    tool.fetch_webpage = MagicMock(return_value={'content': None, 'success': True})

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        'organic': [
            {'title': 'Example', 'link': 'http://example.com', 'snippet': 'Test snippet'}
        ]
    }
    
    import requests
    requests.post = MagicMock(return_value=mock_resp)

    res = tool.search_web("test query", num_results=1)
    assert res['num_results'] == 1
    assert res['results'][0]['content_length'] == 0
