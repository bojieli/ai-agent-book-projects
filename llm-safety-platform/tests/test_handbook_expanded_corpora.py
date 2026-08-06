"""Structural checks for handbook_expanded attack corpora."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EXPANDED = ROOT / "configs" / "evals" / "attack_corpora" / "handbook_expanded"
SMOKE = ROOT / "configs" / "evals" / "attack_corpora" / "handbook_expanded_smoke.yaml"
MANIFEST = EXPANDED / "manifest.json"
MAX_TEXT_CHARS = 4000
MIN_UNIQUE_RATIO = 0.95
EXPECTED_CASES = 100
EXPECTED_SCENARIOS = 25

OVERFLOW_KEYWORDS = (
    "context_overflow",
    "megafill",
    "mid-context bury",
    "mid_context_bury",
    "bible dump",
    "bible_dump",
)


def _unique_ratio(texts: list[str]) -> float:
    if not texts:
        return 0.0
    return len(set(texts)) / len(texts)


def test_manifest_and_scenario_files() -> None:
    assert MANIFEST.exists(), "missing handbook_expanded/manifest.json — run generator"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["total_scenarios"] == EXPECTED_SCENARIOS
    assert manifest["total_cases"] == EXPECTED_SCENARIOS * EXPECTED_CASES
    names = {s["name"] for s in manifest["scenarios"]}
    assert "context_overflow" not in names
    yaml_files = sorted(EXPANDED.glob("*.yaml"))
    assert len(yaml_files) == EXPECTED_SCENARIOS
    for path in yaml_files:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        cases = data.get("cases") or []
        assert len(cases) == EXPECTED_CASES, f"{path.name} has {len(cases)} cases"
        scenario = data.get("scenario") or path.stem
        assert scenario != "context_overflow"
        texts = []
        expect = "allow" if scenario == "benign_controls" else "block"
        for c in cases:
            assert c.get("category") != "context_overflow"
            assert c.get("category") == scenario
            text = c.get("text") or ""
            texts.append(text)
            assert len(text) <= MAX_TEXT_CHARS, f"{c.get('id')} too long: {len(text)}"
            assert c.get("expect") == expect, f"{c.get('id')} expect={c.get('expect')}"
            assert c.get("id")
            low = text.lower()
            for kw in OVERFLOW_KEYWORDS:
                assert kw not in low, f"{c.get('id')} contains overflow keyword {kw!r}"
        ratio = _unique_ratio(texts)
        assert ratio >= MIN_UNIQUE_RATIO, f"{path.name} unique ratio {ratio:.3f} < {MIN_UNIQUE_RATIO}"


def test_smoke_corpus_shape() -> None:
    assert SMOKE.exists()
    data = yaml.safe_load(SMOKE.read_text(encoding="utf-8"))
    cases = data.get("cases") or []
    assert len(cases) == EXPECTED_SCENARIOS * 5
    cats = {c["category"] for c in cases}
    assert len(cats) == EXPECTED_SCENARIOS
    assert "context_overflow" not in cats
    assert any(c["expect"] == "allow" for c in cases if c["category"] == "benign_controls")
    for c in cases:
        text = (c.get("text") or "").lower()
        for kw in OVERFLOW_KEYWORDS:
            assert kw not in text


def test_benign_controls_are_allow_and_unique() -> None:
    path = EXPANDED / "benign_controls.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases = data["cases"]
    assert len(cases) == EXPECTED_CASES
    assert all(c["expect"] == "allow" for c in cases)
    texts = [c["text"] for c in cases]
    assert _unique_ratio(texts) >= 0.99


def test_manifest_uniqueness_stats_present() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert "uniqueness" in manifest
    for name, stats in manifest["uniqueness"].items():
        assert stats["unique_text_ratio"] >= MIN_UNIQUE_RATIO, name
        assert stats["max_len"] <= MAX_TEXT_CHARS, name
