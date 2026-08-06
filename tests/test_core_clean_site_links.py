import pytest
import tempfile
from pathlib import Path

from scripts.clean_site_files import rendered_links, linked_json_files, clean


def test_rendered_links_extracts_src_and_href_from_all_asset_tags():
    html_text = """
<script src="config.json"></script>
<link href="style.json" rel="stylesheet">
<iframe src="frame.json"></iframe>
<audio src="audio.json"></audio>
<video src="video.json"></video>
<source src="source.json">
<embed src="embed.json">
<a href="link.json">Link</a>
<img src="image.png">
"""
    links = rendered_links(html_text)
    assert "config.json" in links
    assert "style.json" in links
    assert "frame.json" in links
    assert "audio.json" in links
    assert "video.json" in links
    assert "source.json" in links
    assert "embed.json" in links
    assert "link.json" in links
    assert "image.png" in links


def test_linked_json_files_finds_script_and_iframe_linked_jsons():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        md_file = root / "index.md"
        json_file1 = root / "data1.json"
        json_file2 = root / "data2.json"
        json_unlinked = root / "unlinked.json"

        md_file.write_text('<script src="data1.json"></script>\n<iframe src="data2.json"></iframe>', encoding="utf-8")
        json_file1.write_text("{}", encoding="utf-8")
        json_file2.write_text("{}", encoding="utf-8")
        json_unlinked.write_text("{}", encoding="utf-8")

        linked = linked_json_files(root)
        assert json_file1.resolve() in linked
        assert json_file2.resolve() in linked
        assert json_unlinked.resolve() not in linked


def test_clean_preserves_script_linked_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        md_file = root / "page.md"
        json_file = root / "app.json"
        stale_file = root / "stale.other"

        md_file.write_text('<script src="app.json"></script>', encoding="utf-8")
        json_file.write_text("{}", encoding="utf-8")
        stale_file.write_text("stale", encoding="utf-8")

        clean(root)

        assert md_file.exists()
        assert json_file.exists()
        assert not stale_file.exists()
