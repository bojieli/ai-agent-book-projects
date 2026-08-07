from semantic_router import StructuredRequestParser


def test_parse_request_preceding_closing_tag_mention():
    text = (
        "Note: Do not format as </tool_request> without an opening tag.\n\n"
        "<tool_request>\n"
        "server: GitHub for repository operations\n"
        "tool: search repositories by keywords\n"
        "</tool_request>\n"
    )
    parsed = StructuredRequestParser.parse_request(text)
    assert parsed is not None, "Failed to parse tool request when </tool_request> is mentioned in preceding text"
    assert parsed["server"] == "GitHub for repository operations"
    assert parsed["tool"] == "search repositories by keywords"


if __name__ == "__main__":
    test_parse_request_preceding_closing_tag_mention()
