import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from mkdocs_pandoc_strip import on_page_markdown


def test_mkdocs_pandoc_strip_none_input():
    """Prove that on_page_markdown handles None input without raising TypeError."""
    result = on_page_markdown(None)
    assert result == ""


def test_mkdocs_pandoc_strip_empty_input():
    """Prove that on_page_markdown handles empty input returning empty string."""
    result = on_page_markdown("")
    assert result == ""
