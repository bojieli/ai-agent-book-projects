from pathlib import Path

from prepare_official_skill import PROTOCOL
from validate_official_run import (
    collect_kimi_metadata,
    collect_tool_calls,
    parse_stream,
    sha256,
)


def test_protocol_pins_exact_manuscript_workflow():
    assert PROTOCOL["runtime"]["official_skill_repository"] == "https://github.com/anthropics/skills.git"
    assert len(PROTOCOL["runtime"]["official_skill_revision"]) == 40
    assert PROTOCOL["output"]["minimum_slides"] == 10
    assert PROTOCOL["output"]["maximum_slides"] == 15
    assert PROTOCOL["output"]["minimum_paper_visuals"] == 3


def test_protocol_records_runtime_agnostic_acceptance_policy():
    policy = PROTOCOL["runtime"]["acceptance_policy"].lower()
    assert "runtime-agnostic" in policy
    kimi = PROTOCOL["runtime"]["alternate_runtimes"]["kimi"]
    assert kimi["binary"] == "kimi"
    assert kimi["skills_flag"] == "--skills-dir"


def test_sha256_reads_binary(tmp_path: Path):
    artifact = tmp_path / "x.bin"
    artifact.write_bytes(b"experiment-2-6")
    assert len(sha256(artifact)) == 64


def test_collect_tool_calls_parses_kimi_stream(tmp_path: Path):
    stream = tmp_path / "kimi_stream.jsonl"
    stream.write_text(
        '{"role":"assistant","tool_calls":[{"type":"function","id":"t1",'
        '"function":{"name":"Skill","arguments":"{\\"skill\\":\\"pptx\\"}"}}]}\n'
        '{"role":"tool","tool_call_id":"t1","content":"Skill \\"pptx\\" loaded inline."}\n'
        '{"role":"assistant","content":"done"}\n',
        encoding="utf-8",
    )
    events, _ = parse_stream(stream)
    calls = collect_tool_calls(events)
    assert calls == [{"name": "Skill", "arguments": '{"skill":"pptx"}'}]


def test_collect_kimi_metadata(tmp_path: Path):
    (tmp_path / "kimi_stream.jsonl").write_text(
        '{"role":"assistant","tool_calls":[{"type":"function","id":"t1",'
        '"function":{"name":"Read","arguments":"{\\"path\\":\\"x.md\\"}"}}]}\n'
        '{"role":"assistant","content":"final answer"}\n'
        '{"role":"meta","type":"session.resume_hint","session_id":"s1"}\n',
        encoding="utf-8",
    )
    (tmp_path / "kimi_exit.json").write_text('{"return_code": 0}', encoding="utf-8")
    (tmp_path / "runtime.json").write_text(
        '{"runtime": "kimi", "model_alias": "kimi-code/k3"}', encoding="utf-8"
    )
    events, _ = parse_stream(tmp_path / "kimi_stream.jsonl")
    metadata = collect_kimi_metadata(events, tmp_path)
    assert metadata["return_code"] == 0
    assert metadata["model_alias"] == "kimi-code/k3"
    assert metadata["num_tool_calls"] == 1
    assert metadata["tool_names"] == ["Read"]
    assert metadata["session_id"] == "s1"
    assert metadata["final_response"] == "final answer"
