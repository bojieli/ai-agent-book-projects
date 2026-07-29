"""
Test suite locking out TypeError in ContextCompressor._no_compression
when a search result dictionary contains 'content': None.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from compression_strategies import ContextCompressor


def test_no_compression_handles_null_content():
    """
    Ensure _no_compression does not raise TypeError when result['content'] is None.
    """
    compressor = ContextCompressor.__new__(ContextCompressor)
    search_results = {
        'results': [
            {'title': 'Test', 'url': 'http://example.com', 'snippet': 'snippet', 'content': None}
        ]
    }
    compressed = compressor._no_compression(search_results)
    assert compressed.original_length == 0
    assert "Full Content:" in compressed.content
