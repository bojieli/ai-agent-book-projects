import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
WEBRTC_RUN = ROOT / "validation/runs/exp10-5-webrtc-raw-20260731-v4"


def test_persisted_evidence_is_redacted_and_does_not_overclaim_voice():
    report = json.loads((ROOT / "validation/real_browser_llm_2026-07-29.json").read_text())
    timeline = json.loads((ROOT / "validation/message_timeline_2026-07-29.json").read_text())
    assert report["gates"]["real_playwright_page_and_fill"]["status"] == "pass"
    assert report["gates"]["autonomous_real_llm_tool_call"]["status"] == "pass"
    assert report["gates"]["real_pstn_call"]["status"] == "not_run"
    assert report["gates"]["real_audio_asr_tts"]["status"] == "not_run"
    assert report["gates"]["real_form_submission"]["status"] == "not_run"
    assert report["overall_status"] == "incomplete"
    collected = [e for e in timeline["events"] if e["type"] == "info_collected"]
    assert collected and all(e["payload"]["value"] == "<redacted>" for e in collected)


def test_software_gate_record_preserves_live_acceptance_blockers():
    data = json.loads((ROOT / "validation/software_gates_2026-07-29.json").read_text())
    assert data["pstn_calls_placed"] == 0
    assert data["human_audio_used"] is False
    assert all(status == "pass" for status in data["gates"].values())
    assert data["acceptance_boundary"]["real_pstn_call"] == "not_run"
    assert data["acceptance_boundary"]["real_human_asr_tts"] == "not_run"
    assert data["acceptance_boundary"]["real_external_form_submission"] == "not_run"
    assert data["acceptance_boundary"]["overall_status"] == "incomplete"


def test_latest_real_browser_llm_recheck_passes_only_safe_gates():
    data = json.loads((ROOT / "validation/real_browser_llm_recheck_2026-07-29.json").read_text())
    assert data["gates"]["real_playwright_page_and_fill"]["status"] == "pass"
    assert data["gates"]["autonomous_real_llm_tool_call"]["status"] == "pass"
    assert data["gates"]["ask_one_fill_one_concurrency"]["status"] == "pass"
    assert (
        len(data["timing_evidence"]["overlap_checks"])
        == data["timing_evidence"]["expected_overlap_count"]
        == 3
    )
    assert all(
        item["next_question_before_fill_completed"]
        for item in data["timing_evidence"]["overlap_checks"]
    )
    assert set(data["persisted_collected_values"]) == {"<redacted>"}
    assert data["pstn_calls_placed"] == data["external_form_submissions"] == 0
    assert data["human_audio_used"] is False
    assert data["gates"]["real_form_submission"]["status"] == "not_run"
    assert data["gates"]["real_pstn_call"]["status"] == "not_run"
    assert data["gates"]["real_audio_asr_tts"]["status"] == "not_run"
    assert data["overall_status"] == "incomplete"


def test_formal_webrtc_acceptance_passes_every_gate_without_pstn():
    report = json.loads((WEBRTC_RUN / "acceptance_report.json").read_text())
    receipt = json.loads((WEBRTC_RUN / "form_submission_receipt.json").read_text())
    timeline = json.loads((WEBRTC_RUN / "message_timeline.json").read_text())

    assert report["overall_status"] == "pass"
    assert all(gate["status"] == "pass" for gate in report["gates"].values())
    assert report["provider_receipts"]["decision"]["response_id"]
    assert len(report["provider_receipts"]["field_extractions"]) == 7
    assert report["result"] == {
        "filled": ["firstName", "lastName", "email", "userNumber", "gender", "address"],
        "submitted": True,
        "errors": [],
    }
    assert receipt["endpoint_scope"] == "localhost-only"
    assert receipt["submission_count"] == 1
    assert receipt["raw_values_retained"] is False

    media = report["webrtc_receipt"]
    assert media["offers"] == media["answers"] == 1
    assert media["media_recordings"] == media["asr_count"] == 7
    assert media["tts_prompt_count"] == 9
    assert media["raw_audio_retained"] is media["transcripts_retained"] is False
    assert all(item["packets"] > 0 and item["bytes"] > 0 for item in media["audio_rtp"])

    assert sum(row["type"] == "format_invalid" for row in timeline) == 1
    assert any(
        row["type"] == "question_asked" and row["payload"] == {"field": "email", "attempt": 2}
        for row in timeline
    )
    collected = [row for row in timeline if row["type"] == "info_collected"]
    assert len(collected) == 6
    assert {row["payload"]["value"] for row in collected} == {"<redacted>"}
    overlaps = report["timing_evidence"]["overlap_checks"]
    assert len(overlaps) == report["timing_evidence"]["expected_overlap_count"] == 5
    assert all(row["next_question_before_fill_completed"] for row in overlaps)


def test_formal_webrtc_manifest_hashes_runtime_and_artifacts():
    manifest = json.loads((WEBRTC_RUN / "manifest.json").read_text())
    assert manifest["schema_version"] == 2
    assert manifest["retained_evidence_validation"] == "pass"
    assert manifest["acceptance"] == {
        "overall_status": "pass",
        "gate_count": 9,
        "passed_gate_count": 9,
    }
    assert manifest["privacy"]["phone_number_required"] is False
    assert manifest["privacy"]["pstn_provider_required"] is False
    for name, expected in manifest["artifact_sha256"].items():
        assert hashlib.sha256((WEBRTC_RUN / name).read_bytes()).hexdigest() == expected
    for name, expected in manifest["input_sha256"].items():
        assert hashlib.sha256((WEBRTC_RUN / name).read_bytes()).hexdigest() == expected
    for name, expected in manifest["source_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
