import json
from pathlib import Path


ROOT = Path(__file__).parent


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
    data = json.loads(
        (ROOT / "validation/real_browser_llm_recheck_2026-07-29.json").read_text()
    )
    assert data["gates"]["real_playwright_page_and_fill"]["status"] == "pass"
    assert data["gates"]["autonomous_real_llm_tool_call"]["status"] == "pass"
    assert data["gates"]["ask_one_fill_one_concurrency"]["status"] == "pass"
    assert len(data["timing_evidence"]["overlap_checks"]) == data["timing_evidence"]["expected_overlap_count"] == 3
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
