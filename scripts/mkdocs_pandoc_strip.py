"""MkDocs hook: strip Pandoc-specific attributes before rendering.

The book source uses Pandoc/LaTeX attributes that Python-Markdown does not
understand and would otherwise render as literal text:

    ## 标题 {.unnumbered}        ->  ## 标题
    ![图](x.svg){height=55%}     ->  ![图](x.svg)
    [文本](#sec:foo){.unnumbered} ->  [文本](#sec:foo)
"""
import re

_CODE_PATTERN = re.compile(r"(?P<fence>```+|~~~+|`+)([\s\S]*?)(?P=fence)")
_PANDOC_ATTR = re.compile(
    r"[ \t]*\{(?:\s*#[a-zA-Z0-9_.:-]+|\s*\.[a-zA-Z0-9_-]+|\s*[a-zA-Z0-9_-]+=[^{}]*)+\s*\}"
)


def on_page_markdown(markdown, **kwargs):
    """MkDocs hook to strip Pandoc attributes outside code blocks and inline code."""
    out = []
    last_end = 0
    for match in _CODE_PATTERN.finditer(markdown):
        start, end = match.span()
        if start > last_end:
            non_code = markdown[last_end:start]
            non_code = _PANDOC_ATTR.sub("", non_code)
            out.append(non_code)
        out.append(match.group(0))
        last_end = end
    if last_end < len(markdown):
        non_code = markdown[last_end:]
        non_code = _PANDOC_ATTR.sub("", non_code)
        out.append(non_code)
    return "".join(out)
