#!/usr/bin/env python3
"""Build a revision-pinned official AIME 2024 benchmark for Experiment 5-1."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import urllib.request
from pathlib import Path

import pyarrow.parquet as parquet


DATASET = "HuggingFaceH4/aime_2024"
REVISION = "2fe88a2f1091d5048c0f36abc874fb997b3dd99a"
SOURCE_PATH = "data/train-00000-of-00001.parquet"


def download() -> bytes:
    url = f"https://huggingface.co/datasets/{DATASET}/resolve/{REVISION}/{SOURCE_PATH}?download=true"
    request = urllib.request.Request(url, headers={"User-Agent": "ai-agent-book-exp5-1/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def convert(rows):
    problems = []
    seen_ids = set()
    for row in rows:
        answer = int(row["answer"])
        if not 0 <= answer <= 999:
            raise ValueError(f"AIME answer outside 000--999: {answer}")
        source_id = int(row["id"])
        if source_id in seen_ids:
            raise ValueError(f"duplicate source id: {source_id}")
        seen_ids.add(source_id)
        problems.append({
            "id": f"aime2024-{source_id}",
            "question": row["problem"],
            "answer": answer,
            "topic": "official AIME 2024",
            "source": {
                "dataset": DATASET,
                "revision": REVISION,
                "source_id": source_id,
                "year": row["year"],
                "problem_url": row["url"],
            },
        })
    if len(problems) != 30:
        raise ValueError(f"expected 30 AIME 2024 problems, got {len(problems)}")
    return sorted(problems, key=lambda item: item["id"])


def build():
    raw = download()
    with tempfile.NamedTemporaryFile(suffix=".parquet") as handle:
        handle.write(raw)
        handle.flush()
        rows = parquet.read_table(handle.name).to_pylist()
    problems = convert(rows)
    manifest = {
        "schema_version": "1.0",
        "experiment": "5-1",
        "dataset": DATASET,
        "revision": REVISION,
        "source_path": SOURCE_PATH,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "split": "train",
        "problems": len(problems),
        "selection": "all published AIME I and AIME II 2024 problems",
        "answers": "published integer answer field; solutions are never sent to the model",
    }
    return problems, manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("aime_2024.json"))
    parser.add_argument("--manifest", type=Path, default=Path("aime_2024.manifest.json"))
    args = parser.parse_args()
    problems, manifest = build()
    args.output.write_text(json.dumps(problems, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"problems": len(problems), "revision": REVISION,
                      "output": str(args.output), "manifest": str(args.manifest)}))


if __name__ == "__main__":
    main()
