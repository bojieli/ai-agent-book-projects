"""实验 8-9 离线单元测试：检测器、合并去重、冲突检测、防误伤、校准、SKILL.md。"""

from __future__ import annotations

import json


from evaluate import load_eval_texts
from extract_rules import PATTERN_LIBRARY, extract_deterministic, load_pairs
from judge import calibrate, load_golden_set, proxy_judge, score_text
from rules_engine import detect_parallelism, run_detector
from skill_manager import merge_rules, prune_rules, render_skill_md, write_skill

DET = {key: spec["detector"] for key, spec in PATTERN_LIBRARY.items()}


# ---------------------------------------------------------------- 检测器命中/不命中

def test_dash_density_hit_and_miss():
    hits = run_detector("甲——乙——丙——丁——戊", DET["dash-density"])
    assert len(hits) == 4
    assert "密度" in hits[0]["detail"]
    # 一处合法补充说明：次数不足，不触发
    assert run_detector("伙伴系统——按 2 的幂分级管理——能减少碎片", DET["dash-density"]) == []


def test_not_but_hit_and_miss():
    assert run_detector("不是堆砌，而是回应；不是口号，而是行动。", DET["not-but"])
    # 单次真实对比不触发
    assert run_detector("不是不可行，而是成本太高。", DET["not-but"]) == []


def test_parallelism_hit_and_miss():
    hits = detect_parallelism("读书可以拓宽视野，读书可以沉淀心灵，读书可以启迪智慧。")
    assert len(hits) == 1 and "连续 3 个" in hits[0]["detail"]
    # 人类作者的两句对仗不触发；长度相近但不排比的散文也不触发
    assert detect_parallelism("写得慢的稿子，读者未必看得出来；写得急的稿子，读者一眼就能看出来。") == []
    assert detect_parallelism("十五块钱两荤两素，味道超出预期，老板娘说开了八年。") == []


def test_lets_start_hit_and_miss():
    assert run_detector("让我们携手并进。让我们共创辉煌。", DET["lets-start"])
    assert run_detector("让我们在评论区交流一下。", DET["lets-start"]) == []


def test_template_sequence_hit_and_miss():
    assert run_detector("首先安装，其次配置，最后启动。", DET["template-sequence"])
    assert run_detector("首先填密钥，其次确认网络。其余保持默认。", DET["template-sequence"]) == []


def test_emoji_density_hit_and_miss():
    assert run_detector("新品 🎉🎉 配色 🌈 性能 🚀 价格 💰", DET["emoji-density"])
    assert run_detector("味道超出预期 😋。这样的小店能多开几家就好了 👍。", DET["emoji-density"]) == []


def test_era_opening_hit_and_miss():
    assert run_detector("在人工智能飞速发展的今天，人人都有机会。", DET["era-opening"])
    assert run_detector("在上世纪八十年代的广州，个体户刚刚出现。", DET["era-opening"]) == []


# ---------------------------------------------------------------- 提炼与合并

def test_extract_deterministic_finds_expected_rules():
    pairs = load_pairs()
    candidates = extract_deterministic(pairs)
    ids = {c["id"] for c in candidates}
    assert {
        "rule-dash-density", "rule-not-but", "rule-parallelism", "rule-lets-start",
        "rule-template-sequence", "rule-emoji-density", "rule-era-opening",
        "rule-hollow-metaphor",
    }.issubset(ids)
    dash = next(c for c in candidates if c["id"] == "rule-dash-density")
    assert "fp-001" in dash["source_ids"]
    assert dash["status"] == "candidate"
    assert dash["bad_example"] and dash["good_example"] and dash["scope"]


def test_merge_dedupes_same_detector():
    pairs = load_pairs()
    batch1 = extract_deterministic([p for p in pairs if p["batch"] == 1])
    batch2 = extract_deterministic([p for p in pairs if p["batch"] == 2])
    rules, report1 = merge_rules([], batch1)
    count_after_1 = len(rules)
    rules, report2 = merge_rules(rules, batch2)
    # 批次 2 的模式批次 1 全部已有：只合并不新增
    assert len(rules) == count_after_1
    assert report2["added"] == [] and len(report2["merged"]) == len(batch2)
    dash = next(r for r in rules if r["id"] == "rule-dash-density")
    assert {"fp-001", "fp-008"}.issubset(set(dash["source_ids"]))


def test_merge_detects_threshold_conflict():
    existing = [{
        "id": "rule-dash-density", "name": "破折号", "definition": "d",
        "detector": {"type": "density", "pattern": "——", "min_occurrences": 3, "threshold": 6},
        "bad_example": "b", "good_example": "g", "scope": ["邮件"],
        "source_ids": ["fp-001"], "status": "active",
    }]
    candidate = dict(existing[0])
    candidate["detector"] = {"type": "density", "pattern": "——", "min_occurrences": 3, "threshold": 3}
    candidate["source_ids"] = ["fp-008"]
    rules, report = merge_rules(existing, [candidate])
    assert len(rules) == 1
    assert len(report["conflicts"]) == 1
    conflict = report["conflicts"][0]
    assert conflict["parameter"] == "threshold"
    assert rules[0]["detector"]["threshold"] == 6  # 保留现有值


def test_prune_archives_idle_and_contradicted():
    rules = [
        {"id": "rule-a", "definition": "a", "source_ids": ["fp-001"], "last_confirmed_batch": 1},
        {"id": "rule-b", "definition": "b", "source_ids": ["fp-002"], "last_confirmed_batch": 3},
        {"id": "rule-c", "definition": "c", "source_ids": ["fp-003"], "last_confirmed_batch": 3},
    ]
    active, archived = prune_rules(
        rules, current_batch=4, idle_batches=2, contradicted_ids={"rule-c"}
    )
    assert [r["id"] for r in active] == ["rule-b"]
    assert {r["id"] for r in archived} == {"rule-a", "rule-c"}
    assert "推翻" in next(r["archive_reason"] for r in archived if r["id"] == "rule-c")


# ---------------------------------------------------------------- 防误伤与检出

def _active_rules():
    pairs = load_pairs()
    rules = []
    for batch_no in (1, 2, 3):
        candidates = extract_deterministic([p for p in pairs if p["batch"] == batch_no])
        rules, _ = merge_rules(rules, candidates)
    return rules


def test_retention_set_not_harmed():
    rules = _active_rules()
    llm_judges = {r["id"]: proxy_judge(r) for r in rules if r["detector"].get("type") == "llm"}
    for item in load_eval_texts()["retention"]:
        fired = score_text(item["text"], rules, llm_judges)
        assert not fired, f"{item['id']} 被误伤：{list(fired)}"


def test_boundary_set_detected_with_expected_rules():
    rules = _active_rules()
    llm_judges = {r["id"]: proxy_judge(r) for r in rules if r["detector"].get("type") == "llm"}
    for item in load_eval_texts()["boundary"]:
        fired = score_text(item["text"], rules, llm_judges)
        expected = set(item["expected_rules"])
        assert expected & set(fired), f"{item['id']} 漏检：期望 {expected}"
        assert expected <= set(fired), f"{item['id']} 部分漏检：{expected - set(fired)}"


# ---------------------------------------------------------------- 金标集校准

def test_calibration_accepts_good_judge():
    rule = next(r for r in _active_rules() if r["id"] == "rule-hollow-metaphor")
    result = calibrate(rule, load_golden_set(), proxy_judge(rule))
    assert result["total"] == 10
    assert result["agreement"] >= 0.8
    assert result["decision"] == "activate"


def test_calibration_rejects_bad_judge():
    rule = next(r for r in _active_rules() if r["id"] == "rule-hollow-metaphor")
    result = calibrate(rule, load_golden_set(), lambda text: True)  # 全部判命中
    assert result["agreement"] < 0.8
    assert result["decision"] == "reject"


# ---------------------------------------------------------------- SKILL.md 结构

def test_skill_md_structure(tmp_path):
    rules = _active_rules()
    md = render_skill_md(rules)
    assert "## 何时加载" in md
    assert f"共 {len(rules)} 条" in md
    for rule in rules:
        assert rule["id"] in md
    for section in ("**定义**", "**坏例**", "**好例**", "**作用域**", "**检测方法**"):
        assert section in md
    path = write_skill(rules, tmp_path)
    assert path.exists()
    assert json.loads((tmp_path / "rules.json").read_text(encoding="utf-8"))[0]["id"]
