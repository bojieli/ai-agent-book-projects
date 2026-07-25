"""Slide bullets containing null must still render a PNG."""
import demo


def test_render_slide_skips_null_bullet(tmp_path, monkeypatch):
    monkeypatch.setattr(demo, "SLIDES_DIR", tmp_path)
    slide = {
        "title": "Demo Title",
        "subtitle": "Demo Subtitle",
        "bullets": ["ok", None, "also"],
    }
    path = demo.render_slide(slide, 0, 1)
    assert path.exists()
    assert path.stat().st_size > 0
    assert path == tmp_path / "slide_01.png"
