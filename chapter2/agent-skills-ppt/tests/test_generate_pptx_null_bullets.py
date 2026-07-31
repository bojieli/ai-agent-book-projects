import tempfile
from pathlib import Path

from generate_pptx import build_presentation


def test_null_bullets_like_omit():
    out = Path(tempfile.mkdtemp()) / "out.pptx"
    result = build_presentation(
        {
            "title": "Demo",
            "slides": [{"title": "Slide", "bullets": None}],
        },
        str(out),
    )
    assert out.exists()
    assert result["num_slides"] == 2
    assert "Slide" in result["titles"]


def test_missing_bullets_still_works():
    out = Path(tempfile.mkdtemp()) / "out.pptx"
    result = build_presentation(
        {
            "title": "Demo",
            "slides": [{"title": "Slide"}],
        },
        str(out),
    )
    assert out.exists()
    assert result["num_slides"] == 2
