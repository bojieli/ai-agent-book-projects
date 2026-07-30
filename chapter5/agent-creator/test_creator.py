from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from creator import (
    AgentCreator,
    ResolvedBackend,
    SCRATCH_FILE_GROUPS,
    _usage_cost,
    load_protocol,
)
from validator import _audit_case, _structural_check


def response(payload):
    message = SimpleNamespace(content=json.dumps(payload))
    usage = SimpleNamespace(prompt_tokens=100, completion_tokens=200)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


class FakeCompletions:
    def __init__(self, payload):
        self.payload = payload

    def create(self, **_kwargs):
        return response(self.payload)


class SequenceCompletions:
    def __init__(self, payloads):
        self.payloads = iter(payloads)

    def create(self, **_kwargs):
        payload = next(self.payloads)
        if isinstance(payload, str):
            message = SimpleNamespace(content=payload)
            usage = SimpleNamespace(prompt_tokens=10, completion_tokens=20)
            return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)
        return response(payload)


def fake_client(payload):
    return SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(payload)))


def sequence_client(payloads):
    return SimpleNamespace(chat=SimpleNamespace(completions=SequenceCompletions(payloads)))


def template_payload():
    return {
        "specialization": {
            "name": "test-agent",
            "role": "Evaluate required test checks from supplied evidence.",
            "sample_task": "evaluate the checks",
            "tool_name": "evaluate_test_checks",
            "tool_description": "Evaluate every supplied test check.",
            "record_noun": "test check",
            "records_argument": "checks",
            "identifier_field": "id",
            "required_field": "required",
            "status_field": "outcome",
            "evidence_field": "evidence",
            "passing_values": ["passed"],
            "approved_label": "APPROVED",
            "rejected_label": "REFUSED",
            "remediation_by_status": {"failed": "Fix and rerun the check."},
            "default_remediation": "Resolve the check and attach passing evidence.",
        }
    }


def scratch_blueprint():
    return {
        "name": "release-agent",
        "sample_task": "evaluate supplied release gates",
        "design": {
            "tool_name": "evaluate_gates",
            "records_argument": "gates",
            "identifier_field": "id",
            "required_field": "required",
            "status_field": "outcome",
            "evidence_field": "evidence",
            "passing_value": "passed",
            "agent_contract": "bounded standard tool loop",
            "dispatcher_contract": "evaluate every required gate",
            "cli_contract": "accept --task and --model and print JSON",
            "test_contract": "test refusal and tool message preservation",
        },
    }


def test_staged_scratch_generation_collects_every_file_and_call(tmp_path: Path):
    group_payloads = [
        {
            "files": {
                path: ('{"tools": []}' if path == "tools.json" else "content")
                for path in group
            }
        }
        for group in SCRATCH_FILE_GROUPS
    ]
    creator = AgentCreator(
        sequence_client([scratch_blueprint(), *group_payloads]), "test-model"
    )

    blueprint, files, stats = creator._generate_scratch_files(
        "make a release agent", tmp_path / "scratch-checkpoint"
    )

    assert blueprint["design"]["tool_name"] == "evaluate_gates"
    assert set(files) == {path for group in SCRATCH_FILE_GROUPS for path in group}
    assert stats.model_calls == 1 + len(SCRATCH_FILE_GROUPS)
    assert stats.prompt_tokens == 100 * (1 + len(SCRATCH_FILE_GROUPS))
    assert stats.completion_tokens == 200 * (1 + len(SCRATCH_FILE_GROUPS))


def test_scratch_creation_recovers_only_empty_staging_directory(tmp_path: Path):
    output = tmp_path / "scratch"
    output.mkdir()
    group_payloads = [
        {
            "files": {
                path: ('{"tools": []}' if path == "tools.json" else "content")
                for path in group
            }
        }
        for group in SCRATCH_FILE_GROUPS
    ]
    creator = AgentCreator(
        sequence_client([scratch_blueprint(), *group_payloads]), "test-model"
    )
    creator._repair_until_deterministic = lambda **kwargs: kwargs["stats"]

    stats = creator.create_from_scratch("make a release agent", output)

    assert stats.strategy == "scratch"
    assert (output / "generation.json").is_file()


def test_scratch_creation_preserves_nonempty_existing_output(tmp_path: Path):
    output = tmp_path / "scratch"
    output.mkdir()
    (output / "user-file.txt").write_text("preserve", encoding="utf-8")
    creator = AgentCreator(fake_client({}), "test-model")

    with pytest.raises(FileExistsError):
        creator.create_from_scratch("make a release agent", output)

    assert (output / "user-file.txt").read_text(encoding="utf-8") == "preserve"


def test_template_mode_copies_core_and_applies_specialization(tmp_path: Path):
    creator = AgentCreator(fake_client(template_payload()), "test-model")
    output = tmp_path / "agent"
    stats = creator.create_from_template("make a test agent", output)
    assert stats.strategy == "template"
    assert (output / "agent.py").is_file()
    assert (output / "tests/test_contract.py").is_file()
    assert "Never invent a registration ID" in (output / "system_prompt.md").read_text()
    assert json.loads((output / "domain_spec.json").read_text())["records_argument"] == "checks"


def test_normalizes_bare_tool_array():
    raw = {"tools.json": json.dumps([{"type": "function", "function": {"name": "x"}}])}
    normalized = AgentCreator._normalize_files(raw)
    assert json.loads(normalized["tools.json"])["tools"][0]["function"]["name"] == "x"


def test_ask_retries_truncated_json_and_accounts_for_both_real_calls():
    creator = AgentCreator(
        sequence_client(['{"specialization":{"name":"unterminated', template_payload()]),
        "test-model",
    )

    payload, stats = creator._ask("return a specialization")

    assert payload == template_payload()
    assert stats.model_calls == 2
    assert stats.prompt_tokens == 110
    assert stats.completion_tokens == 220


def test_rejects_path_traversal(tmp_path: Path):
    with pytest.raises(ValueError, match="disallowed"):
        AgentCreator._safe_files({"files": {"../escape.py": "bad"}}, {"domain_spec.json"})


def test_safe_files_accepts_direct_allowlisted_mapping_and_structured_json():
    files = AgentCreator._safe_files(
        {
            "domain_tools.py": "def evaluate():\n    return True\n",
            "tools.json": {"tools": []},
        },
        {"domain_tools.py", "tools.json"},
    )

    assert files["domain_tools.py"].startswith("def evaluate")
    assert json.loads(files["tools.json"]) == {"tools": []}


@pytest.mark.parametrize("wrapper", ["artifacts", "outputs", "generated_files"])
def test_safe_files_accepts_one_known_wrapper_without_relaxing_paths(wrapper: str):
    files = AgentCreator._safe_files(
        {wrapper: {"domain_tools.py": "def evaluate():\n    return True\n"}},
        {"domain_tools.py"},
    )
    assert set(files) == {"domain_tools.py"}

    with pytest.raises(ValueError, match="disallowed"):
        AgentCreator._safe_files(
            {wrapper: {"../escape.py": "bad"}}, {"domain_tools.py"}
        )


def test_safe_files_does_not_treat_arbitrary_payload_as_file_mapping():
    with pytest.raises(ValueError, match="files object"):
        AgentCreator._safe_files(
            {"name": "not-a-file-envelope", "domain_tools.py": "content"},
            {"domain_tools.py"},
        )


def test_resolved_backend_aliases_real_endpoint_for_generated_agents():
    backend = ResolvedBackend(
        provider="moonshot",
        client=object(),
        model="kimi-k3",
        api_key="test-key-not-a-secret",
        base_url="https://api.moonshot.cn/v1",
    )
    env = backend.generated_agent_env()
    assert env["OPENAI_API_KEY"] == "test-key-not-a-secret"
    assert env["OPENAI_BASE_URL"] == "https://api.moonshot.cn/v1"
    assert env["OPENAI_MODEL"] == "kimi-k3"
    assert env["OPENROUTER_API_KEY"] == ""


def test_structural_gate_requires_common_live_cli(tmp_path: Path):
    root = tmp_path / "generated"
    root.mkdir()
    for relative in (
        "agent.py", "domain_tools.py", "system_prompt.md", "requirements.txt"
    ):
        (root / relative).write_text("", encoding="utf-8")
    (root / "main.py").write_text(
        "import argparse\nparser = argparse.ArgumentParser()\n"
        "parser.add_argument('--facts')\n",
        encoding="utf-8",
    )
    (root / "tools.json").write_text('{"tools": []}', encoding="utf-8")
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_contract.py").write_text("def test_placeholder(): pass\n", encoding="utf-8")

    ok, errors = _structural_check(root)

    assert ok is False
    assert "main.py must implement the common live CLI option --task" in errors
    assert "main.py must implement the common live CLI option --model" in errors


def test_frozen_protocol_has_three_common_cases_and_native_pricing():
    protocol, digest = load_protocol()

    assert len(digest) == 64
    assert [case["kind"] for case in protocol["live_cases"]].count("basic_task") == 2
    assert [case["kind"] for case in protocol["live_cases"]].count("multi_turn_state") == 1
    assert protocol["backend_requirement"]["model"] == "kimi-k3"
    assert protocol["backend_requirement"]["pricing"]["currency"] == "CNY"


def test_native_cost_uses_observed_cached_split():
    protocol, _digest = load_protocol()
    cost = _usage_cost(
        {
            "prompt_tokens": 1000,
            "cached_prompt_tokens": 400,
            "completion_tokens": 100,
            "requests": 2,
        },
        protocol["backend_requirement"]["pricing"],
    )

    assert cost["uncached_prompt_tokens"] == 600
    assert cost["cost"] == pytest.approx(0.0228)
    assert cost["currency"] == "CNY"


def test_case_audit_requires_matching_tool_protocol_history_usage_and_evidence():
    case = {
        "id": "stateful",
        "kind": "multi_turn_state",
        "history": [
            {"role": "user", "content": "Remember Mei-Lin."},
            {"role": "assistant", "content": "Remembered Mei-Lin."},
        ],
        "task": "Evaluate rollback_drill.",
        "expected": {
            "decision": "REFUSED",
            "failed_ids": ["rollback_drill"],
            "evidence": ["too slow"],
            "answer_substrings": ["REFUSED", "rollback_drill"],
            "forbidden_answer_substrings": ["APPROVED"],
            "context_markers": ["Mei-Lin"],
        },
    }
    result = {
        "ok": True,
        "answer": "REFUSED for rollback_drill. Owner Mei-Lin must rerun it.",
        "messages": [
            {"role": "system", "content": "system"},
            *case["history"],
            {"role": "user", "content": case["task"]},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {"name": "evaluate", "arguments": "{}"},
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call-1",
                "content": json.dumps(
                    {
                        "decision": "REFUSED",
                        "failed": "rollback_drill",
                        "evidence": "too slow",
                    }
                ),
            },
            {"role": "assistant", "content": "REFUSED"},
        ],
        "usage": {
            "prompt_tokens": 100,
            "cached_prompt_tokens": 0,
            "completion_tokens": 20,
            "requests": 2,
        },
    }

    audit = _audit_case(
        case,
        process_ok=True,
        result=result,
        elapsed_s=1.0,
        extra_env={"OPENAI_API_KEY": "credential-not-in-evidence"},
    )

    assert audit["passed"] is True
    assert audit["score"] == audit["max_score"]
