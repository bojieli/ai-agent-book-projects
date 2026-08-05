from pathlib import Path
import shutil
import subprocess
import tempfile


import pytest

HAS_LUA = shutil.which("texlua") is not None or shutil.which("lua") is not None
pytestmark = pytest.mark.skipif(not HAS_LUA, reason="texlua or lua executable not found in PATH")
ROOT = Path(__file__).parents[1]


def run_lua_link(target: str) -> str:
    lua_script_path = (ROOT / "epub_external_links.lua").as_posix()
    lua_code = f"""
dofile("{lua_script_path}")
local link = {{ target = "{target}" }}
Link(link)
print(link.target)
"""
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
        f.write(lua_code)
        f_path = f.name
    try:
        lua_bin = shutil.which("texlua") or shutil.which("lua") or "texlua"
        res = subprocess.run(
            [lua_bin, f_path], capture_output=True, text=True, check=True
        )
        return res.stdout.strip()
    finally:
        Path(f_path).unlink(missing_ok=True)


def test_epub_external_links_transforms_chapter_dirs_without_trailing_slash():
    """Contract: Lua Link filter must match chapter targets without a trailing slash (e.g. '../chapter8')
    and convert them to tree URLs on GitHub main branch.
    """
    url = run_lua_link("../chapter8")
    assert url == "https://github.com/bojieli/ai-agent-book/tree/main/chapter8"


def test_epub_external_links_uses_blob_for_file_links():
    """Contract: Lua Link filter must detect file targets with file extensions and use GitHub 'blob' path
    instead of 'tree' path.
    """
    url = run_lua_link("../chapter7/AdaptThink/TRAINING_REPORT.md")
    assert url == "https://github.com/bojieli/ai-agent-book/blob/main/chapter7/AdaptThink/TRAINING_REPORT.md"


def test_epub_external_links_markdown_and_subdir_targets():
    """Contract: Lua Link filter handles markdown file targets, chapter dirs with trailing slash, and non-chapter targets correctly."""
    # Markdown file target uses /blob/
    url_md = run_lua_link("../chapter7/README.md")
    assert url_md == "https://github.com/bojieli/ai-agent-book/blob/main/chapter7/README.md"

    # Directory target with trailing slash uses /tree/ and strips trailing slash
    url_dir_slash = run_lua_link("../chapter8/")
    assert url_dir_slash == "https://github.com/bojieli/ai-agent-book/tree/main/chapter8"

    # Chapter sub-directory target uses /tree/
    url_subdir = run_lua_link("../chapter7/speech-sft-experiment")
    assert url_subdir == "https://github.com/bojieli/ai-agent-book/tree/main/chapter7/speech-sft-experiment"

    # Non-matching link target remains unchanged
    url_external = run_lua_link("https://example.com")
    assert url_external == "https://example.com"


def test_epub_external_links_preserves_fragments_and_requires_chapter_boundary():
    url = run_lua_link("../chapter7/AdaptThink/TRAINING_REPORT.md#results")
    assert url == (
        "https://github.com/bojieli/ai-agent-book/blob/main/"
        "chapter7/AdaptThink/TRAINING_REPORT.md#results"
    )

    invalid = run_lua_link("../chapter7-not-a-directory")
    assert invalid == "../chapter7-not-a-directory"
