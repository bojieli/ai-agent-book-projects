import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from mkdocs_pandoc_strip import on_page_markdown


def test_pandoc_strip_preserves_code_blocks_and_inline_code():
    """Prove that code blocks and inline code containing Pandoc-like attribute patterns

    (e.g., {.unnumbered}, {.highlight}, `const sel = "{.my-class}"`) are left completely untouched,
    locking out code corruption bugs where attributes inside code snippets are stripped.
    """
    content = """# Title {.unnumbered}

```markdown
## Example Title {.unnumbered}
This uses the class {.highlight}.
```

Inline code: `const sel = "{.my-class}";`
"""

    result = on_page_markdown(content)

    assert "## Example Title {.unnumbered}" in result
    assert "This uses the class {.highlight}." in result
    assert '`const sel = "{.my-class}";`' in result
    assert result.startswith("# Title\n")


def test_pandoc_strip_handles_combined_attributes():
    """Prove that combined Pandoc attribute blocks (e.g. {#sec:ch1 .unnumbered},

    {#fig:arch .responsive width=80%}) and link attributes ({#link1 .unnumbered}) outside
    code blocks are stripped correctly, locking out unhandled attribute rendering bugs.
    """
    content = """## Section 1 {#sec:ch1 .unnumbered}
![Architecture](arch.png){#fig:arch .responsive width=80%}
[Link](#sec:ch1){#link1 .unnumbered}
"""

    result = on_page_markdown(content)

    assert "## Section 1\n" in result
    assert "![Architecture](arch.png)\n" in result
    assert "[Link](#sec:ch1)\n" in result


def test_pandoc_strip_does_not_mutate_json_data():
    """Prove that JSON data structures with braces and quotes (e.g. `{"data": {"#key": 123}}`)

    are preserved without modification, locking out false-positive attribute matching on JSON.
    """
    content = 'JSON data: `{"data": {"#key": 123}}`'
    assert on_page_markdown(content) == content


def test_pandoc_strip_preserves_non_pandoc_braces_after_links():
    """Only recognized Pandoc attributes may be removed after a link."""
    content = "Literal: [link](https://example.com){not a Pandoc attribute}"
    assert on_page_markdown(content) == content


def test_pandoc_strip_handles_nested_inline_backticks():
    """Prove that double backticks wrapping single backticks (e.g. ``foo `bar` baz {.unnumbered}``)

    are correctly matched as inline code blocks and not prematurely split, locking out backtick parsing bugs.
    """
    content = "Code: ``foo `bar` baz {.unnumbered}`` outside {.unnumbered}"
    result = on_page_markdown(content)
    assert result == "Code: ``foo `bar` baz {.unnumbered}`` outside"
