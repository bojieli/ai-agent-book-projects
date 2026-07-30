from pathlib import Path

from prepare_official_skill import PROTOCOL
from validate_official_run import sha256


def test_protocol_pins_exact_manuscript_workflow():
    assert PROTOCOL["runtime"]["official_skill_repository"] == "https://github.com/anthropics/skills.git"
    assert len(PROTOCOL["runtime"]["official_skill_revision"]) == 40
    assert PROTOCOL["output"]["minimum_slides"] == 10
    assert PROTOCOL["output"]["maximum_slides"] == 15
    assert PROTOCOL["output"]["minimum_paper_visuals"] == 3


def test_sha256_reads_binary(tmp_path: Path):
    artifact = tmp_path / "x.bin"
    artifact.write_bytes(b"experiment-2-6")
    assert len(sha256(artifact)) == 64
