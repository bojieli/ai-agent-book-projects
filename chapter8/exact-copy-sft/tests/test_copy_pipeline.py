import json
from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_splits_are_nonempty_and_structured():
    for name in ("train", "eval", "boundary"):
        rows = [json.loads(x) for x in (ROOT / "data" / f"{name}.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        assert rows
        assert all({"id", "kind", "language", "article_type", "source", "prompt", "target"} <= set(row) for row in rows)

def read(name):
    return [json.loads(x) for x in (ROOT / "data" / f"{name}.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]

def test_campaign_sizes_and_id_disjointness():
    train, evaluation, boundary = map(read, ("train", "eval", "boundary"))
    assert (len(train), len(evaluation), len(boundary)) == (1024, 256, 256)
    ids = [x["id"] for x in train + evaluation + boundary]
    assert len(ids) == len(set(ids))

def test_eval_ids_do_not_overlap_train_ids():
    train = {json.loads(x)["id"] for x in (ROOT / "data" / "train.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}
    eval_ids = {json.loads(x)["id"] for x in (ROOT / "data" / "eval.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}
    assert train.isdisjoint(eval_ids)

def test_sources_are_unique_across_all_splits():
    rows = read("train") + read("eval") + read("boundary")
    sources = [x["source"] for x in rows]
    assert len(sources) == len(set(sources))

def test_tool_targets_are_valid_json_and_direct_targets_are_exact():
    for row in read("train") + read("eval") + read("boundary"):
        if row["kind"] == "tool_json":
            parsed = json.loads(row["target"])
            assert parsed["old_string"] == row["source"]
        else:
            assert row["target"] == row["source"]

def test_special_character_cases_are_present():
    rows = read("train")
    assert any("\n" in x["source"] for x in rows)
    assert any("\\n" in x["source"] for x in rows)
    assert any("\u200b" in x["source"] for x in rows)
    assert any("中" in x["source"] for x in rows)

def test_tokenizer_audit_covers_multiple_open_tokenizers():
    report = json.loads((ROOT / "validation" / "tokenizer_audit.json").read_text(encoding="utf-8"))
    assert report["probe_count"] == 512
    assert len(report["tokenizers"]) >= 3
    assert all("roundtrip_rate" in value and "mean_tokens" in value for value in report["tokenizers"].values())
