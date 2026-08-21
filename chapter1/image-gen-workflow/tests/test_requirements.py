"""需求清单的两类对照设计（离线）。"""

from main import ALL_ROUTES, REQUIREMENTS


def test_every_requirement_has_category():
    for r in REQUIREMENTS:
        assert r["id"] and r["text"]
        assert r["category"] in ("specific", "broad"), r["id"]


def test_both_categories_present():
    cats = {r["category"] for r in REQUIREMENTS}
    assert cats == {"specific", "broad"}


def test_all_routes_include_native_models():
    """三条路线中应包含两条原生路线（Nano Banana 2 和 GPT-Image 2）及一条工作流路线。"""
    assert "workflow" in ALL_ROUTES
    assert "native" in ALL_ROUTES       # Nano Banana 2 = gemini-3-pro-image
    assert "native_gptimage" in ALL_ROUTES   # GPT-Image 2 = gpt-image-2


def test_book_main_case_text():
    by_id = {r["id"]: r for r in REQUIREMENTS}
    assert by_id["agi-programmer"]["text"] == "帮我画一个 AGI 实现以后程序员的工作场景"
