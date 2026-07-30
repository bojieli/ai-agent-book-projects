#!/usr/bin/env python3
"""Build the frozen Experiment 5-2 test set from the named Hugging Face dataset.

The manuscript explicitly names K-and-K/perturbed-knights-and-knaves.  This
builder downloads a revision-pinned, stratified sample from every test
perturbation and every 2--8-person difficulty cell.  It retains source identity
and hashes and independently checks every published label with the local
python-constraint implementation before writing the benchmark JSON.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import random
import urllib.request
from pathlib import Path
from typing import Any

from csp_solver import solve_labeled


DATASET = "K-and-K/perturbed-knights-and-knaves"
REVISION = "bc7ee75a15ee8196ccbdb7df3ab46284340412e2"
LICENSE = "CC-BY-NC-SA-4.0"
PERTURBATIONS = (
    "perturbed_leaf",
    "perturbed_statement",
    "reorder_statement",
    "random_pair",
    "uncommon_name",
    "flip_role",
)


def _source_path(perturbation: str, people: int) -> str:
    return f"test/{perturbation}/people{people}_num100.jsonl"


def _download(path: str) -> bytes:
    url = (
        "https://huggingface.co/datasets/"
        f"{DATASET}/resolve/{REVISION}/{path}?download=true"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "ai-agent-book-exp5-2/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def convert_expression(node: Any, names: list[str]) -> list[Any]:
    """Convert the dataset's published tuple AST into the lab's JSON DSL."""
    if not isinstance(node, tuple) or not node:
        raise ValueError(f"invalid statement AST node: {node!r}")
    tag = node[0]
    if tag in {"lying", "telling-truth"}:
        if len(node) != 2 or not isinstance(node[1], int):
            raise ValueError(f"invalid identity node: {node!r}")
        role = "knave" if tag == "lying" else "knight"
        return ["is", names[node[1]], role]
    if tag == "not" and len(node) == 2:
        return ["not", convert_expression(node[1], names)]
    binary = {"and": "and", "or": "or", "->": "implies", "<=>": "iff"}
    if tag in binary and len(node) == 3:
        return [
            binary[tag],
            convert_expression(node[1], names),
            convert_expression(node[2], names),
        ]
    raise ValueError(f"unsupported statement AST node: {node!r}")


def convert_row(
    row: dict[str, Any], *, perturbation: str, people: int, source_path: str,
    source_sha256: str, source_row: int,
) -> dict[str, Any]:
    names = list(row["names"])
    if len(names) != people:
        raise ValueError(f"row {source_row}: expected {people} names, got {len(names)}")
    statements = ast.literal_eval(row["statements"])
    if not isinstance(statements, tuple) or len(statements) != len(names):
        raise ValueError(f"row {source_row}: statement count does not match names")
    structs = {
        speaker: convert_expression(statement, names)
        for speaker, statement in zip(names, statements)
    }
    gold = {
        name: ("knight" if truth else "knave")
        for name, truth in zip(names, row["solution"])
    }
    independently_solved = solve_labeled(names, structs)
    if len(independently_solved) != 1 or independently_solved[0] != gold:
        raise ValueError(
            f"row {source_row}: published label failed independent CSP check: "
            f"gold={gold!r}, solved={independently_solved!r}"
        )
    return {
        "id": f"{perturbation}-p{people}-r{source_row:03d}",
        "num_people": people,
        "names": names,
        "description": row["quiz"],
        "solution": gold,
        "statements_struct": structs,
        "source": {
            "dataset": DATASET,
            "revision": REVISION,
            "license": LICENSE,
            "config": "test",
            "split": perturbation,
            "path": source_path,
            "file_sha256": source_sha256,
            "row": source_row,
            "dataset_index": row.get("index"),
        },
    }


def build(*, per_cell: int, seed: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not 1 <= per_cell <= 100:
        raise ValueError("per_cell must be between 1 and 100")
    puzzles: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    for perturbation in PERTURBATIONS:
        for people in range(2, 9):
            path = _source_path(perturbation, people)
            raw = _download(path)
            sha256 = hashlib.sha256(raw).hexdigest()
            rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
            if len(rows) < per_cell:
                raise ValueError(
                    f"{path}: only {len(rows)} published rows, cannot sample {per_cell}"
                )
            cell_seed = int.from_bytes(
                hashlib.sha256(f"{seed}:{path}".encode()).digest()[:8], "big"
            )
            indices = sorted(random.Random(cell_seed).sample(range(len(rows)), per_cell))
            for index in indices:
                puzzles.append(convert_row(
                    rows[index], perturbation=perturbation, people=people,
                    source_path=path, source_sha256=sha256, source_row=index,
                ))
            files.append({
                "path": path,
                "sha256": sha256,
                "published_rows": len(rows),
                "sampled_rows": indices,
            })
    manifest = {
        "schema_version": "1.0",
        "experiment": "5-2",
        "dataset": DATASET,
        "revision": REVISION,
        "license": LICENSE,
        "sampling": {
            "split": "test",
            "perturbations": list(PERTURBATIONS),
            "people": list(range(2, 9)),
            "per_cell": per_cell,
            "seed": seed,
            "cells": len(PERTURBATIONS) * 7,
            "total": len(puzzles),
        },
        "source_files": files,
        "label_validation": "all rows independently solved with python-constraint",
    }
    return puzzles, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-cell", type=int, default=2)
    parser.add_argument("--seed", type=int, default=512)
    parser.add_argument("--output", type=Path, default=Path("hf_test_stratified_84.json"))
    parser.add_argument("--manifest", type=Path, default=Path("hf_test_stratified_84.manifest.json"))
    args = parser.parse_args()
    puzzles, manifest = build(per_cell=args.per_cell, seed=args.seed)
    args.output.write_text(json.dumps(puzzles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output), "manifest": str(args.manifest),
        "puzzles": len(puzzles), "revision": REVISION,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
