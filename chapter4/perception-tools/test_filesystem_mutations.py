"""Safety and receipt checks for Experiment 4-1 filesystem mutations."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))

from filesystem_tools import copy_path, delete_path, move_path  # noqa: E402


def _unwrap(result) -> dict:
    return json.loads(result.text)


def test_move_copy_delete_are_real_verified_and_reversible(tmp_path, monkeypatch):
    monkeypatch.setenv("PERCEPTION_MUTATION_ROOT", str(tmp_path))
    (tmp_path / "input.txt").write_text("experiment 4-1\n", encoding="utf-8")

    copied = _unwrap(asyncio.run(copy_path("input.txt", "copied.txt")))
    assert copied["success"] is True
    assert (tmp_path / "input.txt").is_file()
    assert copied["metadata"]["pre_operation_fingerprint"] == copied["message"][
        "destination_fingerprint"
    ]

    moved = _unwrap(asyncio.run(move_path("copied.txt", "moved.txt")))
    assert moved["success"] is True
    assert not (tmp_path / "copied.txt").exists()
    assert (tmp_path / "moved.txt").is_file()

    deleted = _unwrap(asyncio.run(delete_path("moved.txt")))
    assert deleted["success"] is True
    assert deleted["message"]["reversible"] is True
    assert not (tmp_path / "moved.txt").exists()
    quarantined = tmp_path / deleted["message"]["quarantine_path"]
    assert quarantined.read_text(encoding="utf-8") == "experiment 4-1\n"
    assert deleted["metadata"]["pre_operation_fingerprint"] == deleted["message"][
        "quarantine_fingerprint"
    ]


@pytest.mark.parametrize("candidate", ["../outside.txt", "/tmp/outside.txt", "."])
def test_mutations_reject_traversal_absolute_paths_and_root(candidate, tmp_path, monkeypatch):
    monkeypatch.setenv("PERCEPTION_MUTATION_ROOT", str(tmp_path))
    (tmp_path / "safe.txt").write_text("safe", encoding="utf-8")
    receipt = _unwrap(asyncio.run(copy_path("safe.txt", candidate)))
    assert receipt["success"] is False
    assert receipt["metadata"]["error_type"] in {"PermissionError", "ValueError"}


def test_mutations_reject_symlinks_that_escape_root(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("do not touch", encoding="utf-8")
    (workspace / "escape").symlink_to(outside)
    monkeypatch.setenv("PERCEPTION_MUTATION_ROOT", str(workspace))

    receipt = _unwrap(asyncio.run(delete_path("escape")))
    assert receipt["success"] is False
    assert receipt["metadata"]["error_type"] == "PermissionError"
    assert outside.read_text(encoding="utf-8") == "do not touch"


def test_mutations_fail_closed_without_explicit_root(tmp_path, monkeypatch):
    monkeypatch.delenv("PERCEPTION_MUTATION_ROOT", raising=False)
    receipt = _unwrap(asyncio.run(delete_path("anything")))
    assert receipt["success"] is False
    assert receipt["metadata"]["error_type"] == "PermissionError"
