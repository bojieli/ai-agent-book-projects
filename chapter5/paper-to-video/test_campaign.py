import json
from pathlib import Path

import campaign


def test_protocol_is_exact_twelve_page_five_to_fifteen_minute_contract():
    protocol = json.loads(campaign.PROTOCOL_PATH.read_text())
    assert len(protocol["source"]["selected_pages"]) == 12
    assert protocol["acceptance"]["duration_seconds_min"] == 300
    assert protocol["acceptance"]["duration_seconds_max"] == 900
    assert protocol["providers"]["tts"]["name"] == "Fish Audio"


def test_slide_sections_map_to_rendered_pages():
    protocol = json.loads(campaign.PROTOCOL_PATH.read_text())
    markdown = (campaign.HERE / protocol["source"]["slide_markdown"]).resolve()
    sections = campaign.slide_sections(markdown.read_text())
    assert len(sections) == 22
    assert "Attention Is All You Need" in sections[0]
    assert "Long-Distance Dependencies" in sections[17]


def test_parse_json_content_accepts_fenced_provider_result():
    assert campaign.parse_json_content('```json\n{"visual_alignment": 5}\n```')["visual_alignment"] == 5


def test_selected_source_images_exist_and_are_distinct():
    protocol = json.loads(campaign.PROTOCOL_PATH.read_text())
    rendered = (campaign.HERE / protocol["source"]["rendered_slides"]).resolve()
    paths = [rendered / f"{page}.png" for page in protocol["source"]["selected_pages"]]
    assert all(path.stat().st_size > 10_000 for path in paths)
    assert len({campaign.sha256_file(path) for path in paths}) == 12
