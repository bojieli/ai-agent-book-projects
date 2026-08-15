import json
import subprocess

import pytest

from evaluate_audio_quality import DIMENSIONS, OUTPUTS, PERMUTATIONS, aggregate, validate_response
from markup import parse
from tts import concat_mp3, make_silence
from voice_library import EMOTIONS, SPEEDS, STYLES, load_voice_library


def test_native_s1_nonverbal_events_not_onomatopoeia():
    segments = parse("[THINKING]好吧，[SIGH][LAUGH:small][BREATH]继续。")
    texts = [s["text"] for s in segments if s["type"] == "speech"]
    assert "(uncertain)嗯……" in texts
    assert "(sighing)" in texts
    assert "(chuckling)" in texts
    assert "(gasping)" in texts
    assert "哈哈，" not in texts and "唉——" not in texts


@pytest.mark.parametrize(
    "directory_name",
    ["speaker clips", "speaker's clips", "d'angelo's clips"],
)
def test_concat_handles_apostrophe_in_output_directory(tmp_path, directory_name):
    """FFconcat must preserve ordinary, single-quote, and multi-quote paths."""
    output_dir = tmp_path / directory_name
    output_dir.mkdir()
    parts = [output_dir / "first.mp3", output_dir / "second.mp3"]
    for part in parts:
        make_silence(100, part)

    output = output_dir / "joined.mp3"
    concat_mp3(parts, output)

    duration = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(output),
    ], text=True).strip())
    assert output.is_file()
    assert duration >= 0.18


def test_library_requires_exact_cartesian_product(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"profiles": {}}))
    with pytest.raises(ValueError, match="24"):
        load_voice_library(manifest)


def test_dimensions_are_4_by_3_by_2():
    assert len(EMOTIONS) * len(SPEEDS) * len(STYLES) == 24


def _judge_response(scores):
    return {
        "clips": {
            alias: {
                dimension: {"score": scores[alias], "reason": f"audible evidence for {alias}"}
                for dimension in DIMENSIONS
            }
            for alias in ("X", "Y", "Z")
        },
        "ranking": sorted(("X", "Y", "Z"), key=scores.get, reverse=True),
        "ranking_reason": "audible comparison",
    }


def test_quality_response_rejects_bare_scores_without_audible_evidence():
    response = _judge_response({"X": 1, "Y": 2, "Z": 3})
    response["clips"]["X"]["naturalness"]["reason"] = ""
    with pytest.raises(ValueError, match="audible evidence"):
        validate_response(response)


def test_position_balanced_aggregate_maps_aliases_back_to_configurations():
    # Each pass gives C=5, B=4, A=2 regardless of its anonymous position.
    passes = []
    score_by_name = {
        "A_no_control_markers": 2,
        "B_single_reference": 4,
        "C_24_reference_library": 5,
    }
    for permutation in PERMUTATIONS:
        mapping = dict(zip(("X", "Y", "Z"), permutation))
        scores = {alias: score_by_name[name] for alias, name in mapping.items()}
        passes.append({"alias_to_configuration": mapping, "response": _judge_response(scores)})
    result = aggregate(passes)
    assert result["aggregate_ranking"] == list(reversed(list(OUTPUTS)))
    assert result["manuscript_quality_claim_reproduced"] is True
