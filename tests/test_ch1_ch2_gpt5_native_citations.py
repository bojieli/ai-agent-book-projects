"""
Test suite verifying RED on pristine code and GREEN on choke-point fix for
GPT5NativeAgent._citations and _output_text handling None/non-dict items.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "chapter1" / "search-codegen"))
from agent import GPT5NativeAgent


def test_citations_and_output_text_handles_none_and_non_dict_items():
    agent = GPT5NativeAgent.__new__(GPT5NativeAgent)
    
    # Malformed response where output list contains None, non-dict, or item content is None/string
    malformed_response = {
        "output": [
            None,
            "not_a_dict",
            {
                "type": "message",
                "content": [
                    None,
                    "string_content",
                    {"type": "output_text", "text": "hello"},
                    {"type": "url_citation", "annotations": None}
                ]
            },
            {
                "type": "web_search_call",
                "action": None
            }
        ]
    }

    # Should not raise AttributeError when parsing citations or output text
    citations = agent._citations(malformed_response)
    assert isinstance(citations, list)
    
    text = agent._output_text(malformed_response)
    assert text == "hello"
