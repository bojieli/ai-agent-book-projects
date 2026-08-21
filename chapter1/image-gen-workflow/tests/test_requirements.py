"""需求清单的两类对照设计（离线）。"""

from main import GPT_IMAGE_REQUIREMENT_ID, REQUIREMENTS


def test_every_requirement_has_category():
    for r in REQUIREMENTS:
        assert r["id"] and r["text"]
        assert r["category"] in ("specific", "broad"), r["id"]


def test_both_categories_present():
    cats = {r["category"] for r in REQUIREMENTS}
    assert cats == {"specific", "broad"}


def test_gpt_image_main_case_is_broad():
    by_id = {r["id"]: r for r in REQUIREMENTS}
    assert GPT_IMAGE_REQUIREMENT_ID in by_id
    assert by_id[GPT_IMAGE_REQUIREMENT_ID]["category"] == "broad"


def test_book_main_case_text():
    by_id = {r["id"]: r for r in REQUIREMENTS}
    assert by_id["agi-programmer"]["text"] == "帮我画一个 AGI 实现以后程序员的工作场景"
