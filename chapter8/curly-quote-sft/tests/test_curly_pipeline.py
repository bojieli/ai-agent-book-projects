import json
from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_splits_are_nonempty_and_structured():
    for name in ("train", "eval", "boundary"):
        rows = [json.loads(x) for x in (ROOT / "data" / f"{name}.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        assert rows
        assert all({"id", "kind", "article_type", "language", "prompt", "target"} <= set(row) for row in rows)

def read(name):
    return [json.loads(x) for x in (ROOT / "data" / f"{name}.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]

def test_campaign_sizes_and_id_disjointness():
    train, evaluation, boundary = map(read, ("train", "eval", "boundary"))
    assert (len(train), len(evaluation), len(boundary)) == (1024, 256, 256)
    ids = [x["id"] for x in train + evaluation + boundary]
    assert len(ids) == len(set(ids))

def test_all_scope_kinds_have_holdout_coverage():
    expected = {"zh", "mixed", "english", "python", "javascript", "java", "go", "rust", "sql", "shell", "yaml", "markdown", "nested", "comment", "quote", "json"}
    for name in ("train", "eval", "boundary"):
        assert {x["kind"] for x in read(name)} == expected

def test_curly_targets_and_protected_regions():
    for row in read("train") + read("eval") + read("boundary"):
        if row["kind"] in {"zh", "mixed", "nested", "comment", "quote", "json"}:
            assert any(c in row["target"] for c in "“”‘’")
        if row["kind"] == "mixed":
            assert "`" in row["target"] and '{"status": "' in row["target"]
        if row["kind"] in {"python", "javascript", "java", "go", "rust", "sql", "shell", "yaml"}:
            assert "```" in row["target"] and "中文注释：显示 “" in row["target"]
        if row["kind"] == "python":
            assert "```python" in row["target"] and 'name = "' in row["target"]

def test_protected_examples_are_present():
    text = "\n".join(json.loads(x)["prompt"] for x in (ROOT / "data" / "train.jsonl").read_text(encoding="utf-8").splitlines() if x.strip())
    assert "`validate()`" in text and "```python" in text and "```javascript" in text and "```rust" in text and '"status"' in text

def test_generated_targets_do_not_contain_unresolved_placeholders():
    for row in read("train") + read("eval") + read("boundary"):
        text = row["prompt"] + row["target"]
        assert "{version}" not in text and "{status}" not in text and "{action}" not in text

def test_quality_audit_has_zero_errors():
    report = json.loads((ROOT / "validation" / "quality_audit.json").read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert report["total_errors"] == 0
