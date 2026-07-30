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


def test_cached_json_call_retries_and_preserves_malformed_receipt(tmp_path):
    class Message:
        def __init__(self, content):
            self.content = content

    class Choice:
        def __init__(self, content):
            self.message = Message(content)

    class Response:
        def __init__(self, content, request_id):
            self.choices = [Choice(content)]
            self.raw = {
                "id": request_id,
                "model": "real-model",
                "usage": {"total_tokens": 4},
                "choices": [{"message": {"content": content}}],
            }

        def model_dump(self, mode="json"):
            return self.raw

    class Completions:
        def __init__(self):
            self.calls = 0

        def create(self, **_kwargs):
            self.calls += 1
            if self.calls == 1:
                return Response("not json", "failed-real-call")
            return Response('{"narration":"valid"}', "accepted-real-call")

    class Client:
        def __init__(self):
            self.chat = type("Chat", (), {"completions": Completions()})()

    destination = tmp_path / "receipt.json"
    client = Client()
    parsed, receipt = campaign.cached_json_call(
        destination,
        client,
        provider="real-provider",
        model="real-model",
        messages=[{"role": "user", "content": "return JSON"}],
        max_tokens=20,
    )

    assert parsed == {"narration": "valid"}
    assert receipt["json_attempt"] == 2
    assert client.chat.completions.calls == 2
    failure = json.loads(
        (tmp_path / "receipt.failed-attempts.json").read_text(encoding="utf-8")
    )
    assert failure["attempts"][0]["receipt"]["response"]["id"] == "failed-real-call"
