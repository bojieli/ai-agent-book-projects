import importlib.util
from pathlib import Path


spec = importlib.util.spec_from_file_location("paper_to_ppt_agents_real", Path(__file__).with_name("agents.py"))
agents = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(agents)
_slide_count = agents._slide_count


def deck(pages: int) -> str:
    body = ["---\ntheme: default\n---\n\n# Page 1"]
    body.extend(f"# Page {index}" for index in range(2, pages + 1))
    return "\n\n---\n\n".join(body)


def test_slide_count_matches_slidev_frontmatter_and_separators():
    assert _slide_count(deck(10)) == 10
    assert _slide_count(deck(20)) == 20
    assert _slide_count(deck(22)) == 22
