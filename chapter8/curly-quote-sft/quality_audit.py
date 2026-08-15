"""Deterministic quality gate for the scope-sensitive synthetic corpus.

This is the machine-checkable part of the manual audit: a reviewer samples
rows from each language/type stratum, while this gate rejects malformed or
ambiguous targets before they reach SFT.
"""
from __future__ import annotations

import json, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMMENT_PREFIX = {
    "python": "#", "javascript": "//", "java": "//", "go": "//",
    "rust": "//", "sql": "--", "shell": "#", "yaml": "#",
}


def rows(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def check_row(row):
    errors = []
    text = row["prompt"] + row["target"]
    if re.search(r"\{(?:version|status|action|word|literal|quote_literal|english|method)\}", text):
        errors.append("unresolved_template")
    if row["kind"] in COMMENT_PREFIX:
        fence = re.search(r"```([A-Za-z]+)\n(.*?)```", row["target"], re.S)
        if not fence:
            errors.append("missing_code_fence")
        else:
            language = row["kind"]
            prefix = COMMENT_PREFIX[language]
            code_lines = fence.group(2).splitlines()
            source_fence = re.search(r"```([A-Za-z]+)\n(.*?)```", row["prompt"], re.S)
            source_lines = source_fence.group(2).splitlines() if source_fence else []
            for src, tgt in zip(source_lines, code_lines):
                if src.lstrip().startswith(prefix):
                    if '"' in tgt or not any(c in tgt for c in "“”‘’"):
                        errors.append("comment_not_curly")
                elif src != tgt:
                    errors.append("non_comment_code_changed")
    return errors


def main():
    report = {"splits": {}, "total_rows": 0, "total_errors": 0}
    for split in ("train", "eval", "boundary"):
        counts = Counter()
        checked = 0
        for row in rows(ROOT / "data" / f"{split}.jsonl"):
            checked += 1
            counts.update(check_row(row))
        report["splits"][split] = {"rows": checked, "errors": dict(counts)}
        report["total_rows"] += checked
        report["total_errors"] += sum(counts.values())
    report["status"] = "pass" if report["total_errors"] == 0 else "fail"
    out = ROOT / "validation" / "quality_audit.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
