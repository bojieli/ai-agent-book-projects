import sys
from pathlib import Path

# Ensure coding-agent modules can be resolved regardless of working directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from system_state import SystemState
from tools.grep_tool import GrepTool


def test_grep_tool_supports_multiline_content_matching(tmp_path):
    """Verify GrepTool content mode supports multiline regex matching.

    Contract: When multiline=True is provided, GrepTool output_mode="content" must
    match patterns that span multiple lines and return the matching lines with context,
    rather than iterating line-by-line and returning "No matches found."
    """
    file_path = tmp_path / "sample.py"
    file_path.write_text("def foo():\n    return 42\n", encoding="utf-8")

    state = SystemState()
    tool = GrepTool(state)

    result = tool.execute({
        "pattern": r"def foo\(\):\n\s+return",
        "path": str(file_path),
        "multiline": True,
        "output_mode": "content",
    })

    assert result.success
    assert result.data["matches"] > 0
    assert result.data["output"] != "No matches found."
    assert "def foo():" in result.data["output"]
    assert "return 42" in result.data["output"]
