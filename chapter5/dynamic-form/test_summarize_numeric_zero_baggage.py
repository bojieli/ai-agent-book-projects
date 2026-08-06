import importlib.util
from pathlib import Path

_demo_path = Path(__file__).parent / "demo.py"
_spec = importlib.util.spec_from_file_location("dynamic_form_demo", _demo_path)
_demo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_demo)
summarize_offline = _demo.summarize_offline


def test_summarize_offline_handles_numeric_zero_baggage():
    """Prove summarize_offline treats numeric 0 baggage count as no free baggage.

    When submitted form data contains integer 0 (e.g. from JSON deserialization or
    Python API callers), summarize_offline must format "，无免费托运" rather than
    "，免费托运 0 件".
    """
    submitted = {
        "departure_city": "北京",
        "destination_city": "上海",
        "departure_date": "2026-08-10",
        "cabin_class": "economy",
        "baggage_count": 0,
    }
    summary = summarize_offline(submitted)
    assert summary == (
        "已收到您的订票信息：北京 → 上海，出发日期 2026-08-10。\n"
        "行程类型：单程。\n"
        "舱位：经济舱，无免费托运。\n"
        "正在为您检索航班..."
    )
    assert "，无免费托运" in summary
    assert "免费托运 0 件" not in summary


def test_summarize_offline_handles_string_zero_baggage():
    """Prove summarize_offline treats string '0' baggage count as no free baggage."""
    submitted = {
        "departure_city": "北京",
        "destination_city": "上海",
        "departure_date": "2026-08-10",
        "cabin_class": "economy",
        "baggage_count": "0",
    }
    summary = summarize_offline(submitted)
    assert "，无免费托运" in summary
    assert "免费托运 0 件" not in summary


def test_summarize_offline_handles_positive_baggage():
    """Prove summarize_offline formats positive baggage count correctly."""
    submitted = {
        "departure_city": "北京",
        "destination_city": "上海",
        "departure_date": "2026-08-10",
        "cabin_class": "economy",
        "baggage_count": 1,
    }
    summary = summarize_offline(submitted)
    assert "，免费托运 1 件" in summary
