import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import agents

from run_official_experiment import (
    DIMENSIONS,
    campaign_fingerprint,
    judge_chapter,
    load_checkpoint,
    markdown_fidelity,
    restore_arm,
    serialize_arm,
    split_translation_units,
    validate_judge_response,
    write_json_atomic,
)

from agents import TokenTracker


def test_markdown_fidelity_checks_exact_code_images_and_links():
    source = "# T\n\n![diagram](images/a.svg)\n\n[docs](https://example.test)\n\n```py\nx = 1\n```\n"
    same = "# 标题\n\n![图](images/a.svg)\n\n[文档](https://example.test)\n\n```py\nx = 1\n```\n"
    changed = same.replace("x = 1", "x = 2")
    result = markdown_fidelity(source, same)
    assert result["fenced_code"]["exact_payload_sequence_preserved"] is True
    assert result["images"]["exact_target_sequence_preserved"] is True
    assert result["links"]["exact_target_sequence_preserved"] is True
    assert markdown_fidelity(source, changed)["fenced_code"]["exact_payload_sequence_preserved"] is False


def test_judge_requires_evidence_for_every_dimension():
    payload = {
        "variants": {
            alias: {
                dimension: {"score": 4, "evidence": "specific passage"}
                for dimension in DIMENSIONS
            }
            for alias in ("X", "Y")
        },
        "preferred": "X",
        "preference_evidence": "X preserves a named claim",
    }
    assert validate_judge_response(payload)["preferred"] == "X"
    payload["variants"]["Y"]["accuracy"]["evidence"] = ""
    with pytest.raises(ValueError, match="non-empty"):
        validate_judge_response(payload)


def test_judge_losslessly_repairs_ark_preference_fields_nested_in_variants():
    payload = {
        "variants": {
            **{
                alias: {
                    dimension: {"score": 4, "evidence": "specific passage"}
                    for dimension in DIMENSIONS
                }
                for alias in ("X", "Y")
            },
            "preferred": "Y",
            "preference_evidence": "Y preserves a named claim.",
        }
    }
    normalized = validate_judge_response(payload)
    assert set(normalized["variants"]) == {"X", "Y"}
    assert normalized["preferred"] == "Y"
    assert normalized["schema_repairs"]


def test_translation_unit_split_never_changes_source_or_cuts_fences():
    text = "# Chapter 1\n\n" + ("paragraph words\n\n" * 20) + "```py\n\nvalue = 1\n\n```\n"
    units, mapping = split_translation_units({"Chapter 1": text}, max_characters=80)
    assert "".join(units[name] for name in mapping["Chapter 1"]) == text
    assert sum(part.count("```") for part in units.values()) == 2
    assert all(part.count("```") in (0, 2) for part in units.values())


def test_arm_and_judge_checkpoints_round_trip(tmp_path):
    tracker = TokenTracker()
    tracker.record("Translation", 10, 4, "part")
    arm = {"mode": "x", "translations": {"part": "译文"}, "tracker": tracker}
    serialized = serialize_arm(arm)
    restored = restore_arm(serialized, __import__("agents"))
    assert restored["translations"] == arm["translations"]
    assert restored["tracker"].calls == tracker.calls

    fingerprint = campaign_fingerprint(
        {"chapter": "source"}, {"chapter [Part 1/1]": "source"}, "provider", "model"
    )
    path = tmp_path / "checkpoint.json"
    write_json_atomic(path, {"campaign_fingerprint": fingerprint, "value": [1, 2]})
    assert load_checkpoint(path, fingerprint) == [1, 2]
    with pytest.raises(RuntimeError):
        load_checkpoint(path, "different")


def test_single_agent_progress_resumes_without_replaying_prefix(tmp_path, monkeypatch):
    monkeypatch.setattr(agents, "get_client", lambda: object())
    calls = []

    def fail_second(client, tracker, agent, messages, json_mode=False, note=""):
        calls.append(note)
        if note.endswith("Part 2/2]"):
            tracker.record(agent, 3, 0, note, outcome="empty_response")
            raise RuntimeError("provider returned empty")
        tracker.record(agent, 3, 2, note)
        return "第一部分"

    monkeypatch.setattr(agents, "llm_chat", fail_second)
    chapters = {
        "Chapter 1 [Part 1/2]": "source one",
        "Chapter 1 [Part 2/2]": "source two",
    }
    with pytest.raises(RuntimeError, match="empty"):
        agents.run_single_agent(chapters, str(tmp_path))
    assert calls == ["翻译 Chapter 1 [Part 1/2]", "翻译 Chapter 1 [Part 2/2]"]

    resumed_calls = []

    def finish_second(client, tracker, agent, messages, json_mode=False, note=""):
        resumed_calls.append(note)
        assert any(message.get("content") == "第一部分" for message in messages)
        tracker.record(agent, 5, 2, note)
        return "第二部分"

    monkeypatch.setattr(agents, "llm_chat", finish_second)
    result = agents.run_single_agent(chapters, str(tmp_path))
    assert resumed_calls == ["翻译 Chapter 1 [Part 2/2]"]
    assert result["translations"] == {
        "Chapter 1 [Part 1/2]": "第一部分",
        "Chapter 1 [Part 2/2]": "第二部分",
    }


def test_ark_translation_disables_reasoning_only_responses():
    assert agents._provider_request_options("Volcengine ARK") == {
        "max_tokens": 12_000,
        "extra_body": {"thinking": {"type": "disabled"}},
    }
    assert "extra_body" not in agents._provider_request_options("Mistral API")


def test_judge_retries_schema_failure_and_persists_raw_receipt(tmp_path):
    valid = {
        "variants": {
            alias: {
                dimension: {"score": 4, "evidence": f"{alias} {dimension} evidence"}
                for dimension in DIMENSIONS
            }
            for alias in ("X", "Y")
        },
        "preferred": "tie",
        "preference_evidence": "The variants are equivalent on the quoted evidence.",
    }
    contents = [json.dumps({"variants": {}}), json.dumps(valid)]

    class Completions:
        def create(self, **kwargs):
            content = contents.pop(0)
            return SimpleNamespace(
                id=f"response-{len(contents)}",
                model="judge-model",
                created=1,
                choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
                usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            )

    client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    receipt = tmp_path / "receipt.json"
    result, usage = judge_chapter(
        client, "judge-model", "source", "translation x", "translation y",
        receipt_path=receipt,
    )
    saved = json.loads(receipt.read_text(encoding="utf-8"))
    assert result["preferred"] == "tie"
    assert usage["attempt_count"] == 2
    assert usage["prompt_tokens"] == 20
    assert [row["validation"]["valid"] for row in saved["attempts"]] == [False, True]
    assert saved["attempts"][1]["request"]["messages"][-1]["role"] == "user"
    assert saved["attempts"][1]["request_kind"] == "schema_repair"
    assert "formatting repair, not a new evaluation" in (
        saved["attempts"][1]["request"]["messages"][0]["content"]
    )


def test_canonical_evidence_latest_pointer_and_all_declared_hashes_match():
    here = Path(__file__).parent
    repo = here.parents[1]
    latest_path = here / "validation" / "latest.json"
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    evidence_path = here / latest["evidence"]
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert latest["status"] == "complete"
    assert evidence["experiment_execution_complete"] is True
    assert all(evidence["acceptance_gates"].values())
    assert latest["evidence_sha256"] == hashlib.sha256(evidence_path.read_bytes()).hexdigest()

    groups = (
        "current_acceptance_sources_sha256",
        "arm_and_judge_checkpoints_sha256",
        "reassembled_translation_outputs_sha256",
        "raw_judge_receipts_sha256",
        "negative_provenance_sha256",
    )
    declarations = {
        relative: digest
        for group in groups
        for relative, digest in evidence["provenance"][group].items()
    }
    assert len(declarations) == 37
    assert all(
        (repo / relative).is_file()
        and hashlib.sha256((repo / relative).read_bytes()).hexdigest() == digest
        for relative, digest in declarations.items()
    )

    for title, relative in evidence["source_book"]["paths"].items():
        assert hashlib.sha256((repo / relative).read_bytes()).hexdigest() == (
            evidence["source_book"]["sha256"][title]
        )
