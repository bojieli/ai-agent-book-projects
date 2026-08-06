from __future__ import annotations

import json
import sys
from types import SimpleNamespace

from provider_adapter import ReceiptRecorder, install


class Response(dict):
    def to_dict_recursive(self):
        return dict(self)


def test_recorder_materializes_zero_call_checkpoint(tmp_path):
    receipt = tmp_path / "nested" / "empty.jsonl"
    recorder = ReceiptRecorder()
    recorder.set_path(receipt)
    assert receipt.is_file()
    assert receipt.read_bytes() == b""


def test_adapter_overrides_legacy_models_and_compacts_embeddings(tmp_path, monkeypatch):
    calls = []

    class ChatCompletion:
        @classmethod
        def create(cls, **kwargs):
            calls.append(("chat", kwargs))
            return Response(
                id="chat-id",
                model=kwargs["model"],
                choices=[{"message": {"content": "ok"}}],
                usage={"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
            )

    class Completion:
        @classmethod
        def create(cls, **kwargs):
            raise AssertionError("legacy completion endpoint should not be called")

    class Embedding:
        @classmethod
        def create(cls, **kwargs):
            calls.append(("embedding", kwargs))
            return Response(
                id="embedding-id",
                model=kwargs["model"],
                data=[{"index": 0, "object": "embedding", "embedding": [0.1, 0.2]}],
                usage={"prompt_tokens": 1, "total_tokens": 1},
            )

    fake_openai = SimpleNamespace(
        api_key=None,
        api_base=None,
        ChatCompletion=ChatCompletion,
        Completion=Completion,
        Embedding=Embedding,
    )
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    receipt = tmp_path / "calls.jsonl"
    install(
        api_key="test-key-not-retained",
        api_base="https://example.invalid/v1",
        chat_model="current-chat",
        embedding_model="current-embedding",
        receipt_path=receipt,
    )

    chat = fake_openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[])
    completion = fake_openai.Completion.create(model="text-davinci-003", prompt="hello")
    embedding = fake_openai.Embedding.create(model="text-embedding-ada-002", input=["x"])

    assert chat["id"] == "chat-id"
    assert completion.choices[0].text == "ok"
    assert embedding["data"][0]["embedding"] == [0.1, 0.2]
    assert [call[1]["model"] for call in calls] == [
        "current-chat",
        "current-chat",
        "current-embedding",
    ]
    assert all(call[1]["request_timeout"] == 90 for call in calls)
    rows = [json.loads(line) for line in receipt.read_text().splitlines()]
    assert len(rows) == 3
    assert all(row["success"] for row in rows)
    compact = rows[-1]["response"]["data"][0]
    assert compact["embedding_dimensions"] == 2
    assert "embedding" not in compact
    assert "test-key-not-retained" not in receipt.read_text()


def test_adapter_retries_transient_connection_and_records_one_logical_call(
    tmp_path, monkeypatch
):
    attempts = 0

    class APIConnectionError(Exception):
        pass

    class ChatCompletion:
        @classmethod
        def create(cls, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise APIConnectionError("connection closed")
            return Response(
                id="retry-success",
                model=kwargs["model"],
                choices=[{"message": {"content": "ok"}}],
                usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            )

    class Completion:
        @classmethod
        def create(cls, **kwargs):
            raise AssertionError("legacy completion endpoint should not be called")

    class Embedding:
        @classmethod
        def create(cls, **kwargs):
            raise AssertionError("embedding endpoint should not be called")

    fake_openai = SimpleNamespace(
        api_key=None,
        api_base=None,
        ChatCompletion=ChatCompletion,
        Completion=Completion,
        Embedding=Embedding,
    )
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    monkeypatch.setattr("provider_adapter.time.sleep", lambda _: None)
    receipt = tmp_path / "retry.jsonl"
    install(
        api_key="test-key-not-retained",
        api_base="https://example.invalid/v1",
        chat_model="current-chat",
        embedding_model="current-embedding",
        receipt_path=receipt,
    )

    response = fake_openai.ChatCompletion.create(model="legacy", messages=[])
    rows = [json.loads(line) for line in receipt.read_text().splitlines()]
    assert response["id"] == "retry-success"
    assert attempts == 2
    assert len(rows) == 1
    assert rows[0]["success"] is True
    assert rows[0]["transport_retries"] == [
        {
            "attempt": 1,
            "type": "APIConnectionError",
            "message": "connection closed",
        }
    ]
