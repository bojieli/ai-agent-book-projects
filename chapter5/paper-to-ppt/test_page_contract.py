import importlib.util
from pathlib import Path


spec = importlib.util.spec_from_file_location("paper_to_ppt_agents_real", Path(__file__).with_name("agents.py"))
agents = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(agents)
_slide_count = agents._slide_count
_slide_contract_issues = agents._slide_contract_issues


def deck(pages: int) -> str:
    body = ["---\ntheme: default\n---\n\n# Page 1"]
    body.extend(f"# Page {index}" for index in range(2, pages + 1))
    return "\n\n---\n\n".join(body)


def test_slide_count_matches_slidev_frontmatter_and_separators():
    assert _slide_count(deck(10)) == 10
    assert _slide_count(deck(20)) == 20
    assert _slide_count(deck(22)) == 22


def test_source_contract_requires_18_to_20_pages():
    assert _slide_contract_issues(deck(18)) == []
    assert _slide_contract_issues(deck(20)) == []
    assert "page count is 17" in _slide_contract_issues(deck(17))[0]


def test_source_contract_caps_total_bullets_per_page():
    slides = deck(18) + "\n\n- one\n- two\n- three\n- four\n- five\n"
    issues = _slide_contract_issues(slides)
    assert issues == ["page 18 has 5 bullets; maximum is 4 total"]


def test_source_contract_counts_non_markdown_fake_bullets():
    slides = deck(18) + "\n\n■ one\n▪ two\n• three\n- four\n- five\n"
    assert _slide_contract_issues(slides) == [
        "page 18 has 5 bullets; maximum is 4 total"
    ]


def test_source_contract_enforces_dedicated_bounded_figure_page():
    valid = deck(18) + (
        '\n\n## Long-Distance Attention (Figure 3)\n\n'
        '<img src="/paper_figure_3_long_distance.png" '
        'style="max-height: 460px; width: 100%; object-fit: contain;" />'
        '\n\nOne short caption.\n'
    )
    assert _slide_contract_issues(valid) == []

    oversized = valid.replace("max-height: 460px", "max-height: 650px")
    assert _slide_contract_issues(oversized) == [
        "page 18 source figure must use inline style max-height: 460px; "
        "width: 100%; object-fit: contain;"
    ]

    crowded = valid + "\n- extra point\n"
    assert _slide_contract_issues(crowded) == [
        "page 18 source figure must have only a title and at most one caption"
    ]

    wrapped_title = valid.replace(
        "## Long-Distance Attention (Figure 3)",
        "## Attention Visualization: Long-Distance Dependencies",
    )
    assert _slide_contract_issues(wrapped_title) == [
        "page 18 source figure must use one-line title: "
        "Long-Distance Attention (Figure 3)"
    ]
