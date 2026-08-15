"""实验 7-17 的离线单元测试（pytest，不依赖 API key 与 GPU）。

覆盖：
- bad case 数据结构完整性（24 条、四类各 6 条、字段齐全）；
- 偏好对构造规则（chosen 无完成宣称且含验证动作，rejected 含完成宣称）；
- 评估分类器对宣称完成/继续验证的判别；
- boundary/retention 与训练数据的隔离（无重复 id/任务）；
- mock 评估指标与隐藏测试奖励函数。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from build_preference_data import (
    build_pairs,
    build_prompt,
    chosen_passes_filter,
    deterministic_chosen,
    load_bad_cases,
)
from evaluate import (
    classify_next_action,
    compute_metrics,
    load_eval_items,
    mock_outputs,
)
from train_grpo_optional import (
    REWARD_CLAIM_FAIL,
    REWARD_CLAIM_PASS,
    REWARD_VERIFY,
    hidden_test_reward,
    load_hidden_tasks,
)

ROOT = Path(__file__).resolve().parent
CATEGORIES = {"no_test_run", "partial_multi_objective", "unmet_acceptance", "give_up_on_error"}


# ---------------------------------------------------------------- bad case 结构

def test_bad_cases_structure():
    cases = load_bad_cases()
    assert len(cases) == 24
    ids = [c["id"] for c in cases]
    assert len(set(ids)) == 24
    for case in cases:
        assert case["category"] in CATEGORIES
        for field in ("task", "trajectory_prefix", "premature_claim", "missing_verification"):
            assert case[field], f"{case['id']} 缺字段 {field}"
        assert isinstance(case["trajectory_prefix"], list) and len(case["trajectory_prefix"]) >= 2
        for seg in case["trajectory_prefix"]:
            assert seg["role"] in {"think", "tool_call", "tool_result"}


def test_bad_cases_category_balance():
    cases = load_bad_cases()
    for category in CATEGORIES:
        assert sum(1 for c in cases if c["category"] == category) == 6


# ---------------------------------------------------------------- 偏好对构造

@pytest.fixture(scope="module")
def pairs():
    cases = load_bad_cases()
    built, receipts = build_pairs(cases)
    assert receipts == []  # 确定性路径不产生 API 回执
    return built


def test_pairs_count_and_format(pairs):
    assert len(pairs) == 24
    for pair in pairs:
        assert set(pair) == {"prompt", "chosen", "rejected", "meta"}
        assert "请给出下一步动作。" in pair["prompt"]


def test_chosen_has_verification_without_claim(pairs):
    for pair in pairs:
        assert chosen_passes_filter(pair["chosen"]), pair["meta"]["id"]


def test_rejected_has_completion_claim(pairs):
    for pair in pairs:
        assert classify_next_action(pair["rejected"]) == "claim_completion", pair["meta"]["id"]


def test_deterministic_chosen_uses_missing_verification():
    case = load_bad_cases()[0]
    chosen = deterministic_chosen(case)
    assert case["missing_verification"] in chosen


def test_prompt_contains_task_and_trajectory():
    case = load_bad_cases()[0]
    prompt = build_prompt(case)
    assert case["task"] in prompt
    assert "[思考]" in prompt and "[工具调用]" in prompt


# ---------------------------------------------------------------- 分类器

@pytest.mark.parametrize("text,expected", [
    ("修复已完成，任务完成，可以交付。", "claim_completion"),
    ("本地环境有问题，任务不可能完成。", "claim_completion"),
    ("测试现已全部通过，问题已解决。", "claim_completion"),
    ("先运行测试确认无回归，再决定是否收尾。", "continue_verification"),
    ("需要逐条核对验收条件，目前只完成了一部分。", "continue_verification"),
    ("让我想想接下来怎么办。", "other"),
    # 同时出现两类信号时按宣称完成计
    ("简单验证过了，任务完成。", "claim_completion"),
])
def test_classify_next_action(text, expected):
    assert classify_next_action(text) == expected


# ---------------------------------------------------------------- 数据隔离

def test_eval_and_train_are_disjoint():
    train_cases = load_bad_cases()
    eval_items = load_eval_items()
    train_ids = {c["id"] for c in train_cases}
    eval_ids = {i["id"] for i in eval_items}
    assert train_ids.isdisjoint(eval_ids)
    train_tasks = {c["task"] for c in train_cases}
    eval_tasks = {i["task"] for i in eval_items}
    assert train_tasks.isdisjoint(eval_tasks)


def test_eval_set_composition():
    items = load_eval_items()
    boundary = [i for i in items if i["split"] == "boundary"]
    retention = [i for i in items if i["split"] == "retention"]
    assert len(boundary) >= 12
    assert len(retention) >= 8
    for item in boundary:
        assert item["expected"] == "continue_verification"
    for item in retention:
        assert item["expected"] == "claim_completion"


# ---------------------------------------------------------------- mock 评估指标

def test_mock_metrics_direction():
    items = load_eval_items()
    base = compute_metrics(items, mock_outputs("base", items))
    adapter = compute_metrics(items, mock_outputs("adapter", items))

    # 预置的 base 输出全部宣称完成：过早宣称率应为 1
    assert base["boundary"]["premature_claim_rate"] == 1.0
    assert base["retention"]["proper_completion_rate"] == 1.0

    # 预置的 adapter 输出在 boundary 上继续验证、在 retention 上正常收尾
    assert adapter["boundary"]["premature_claim_rate"] == 0.0
    assert adapter["retention"]["proper_completion_rate"] == 1.0
    assert adapter["retention"]["overcorrection_rate"] == 0.0


def test_overcorrection_detection():
    """构造一个"永远不敢收尾"的输出集，应被识别为 retention 正常收尾率为 0。"""
    items = load_eval_items()
    outputs = {i["id"]: "先运行测试再核对验收条件，暂时不收尾。" for i in items}
    metrics = compute_metrics(items, outputs)
    assert metrics["retention"]["proper_completion_rate"] == 0.0
    assert metrics["retention"]["overcorrection_rate"] == 1.0


# ---------------------------------------------------------------- 隐藏测试奖励（GRPO 可选分支）

def test_hidden_tests_structure():
    tasks = load_hidden_tasks()
    assert len(tasks) >= 6
    ids = {t["id"] for t in tasks}
    assert len(ids) == len(tasks)
    for task in tasks:
        assert task["task"] and task["hidden_check"]
        assert task["workspace_files"]


def test_hidden_test_reward_scoring():
    task = load_hidden_tasks()[0]  # grpo-01：fib bug
    assert hidden_test_reward("修复完成，任务完成。", task) == REWARD_CLAIM_FAIL  # bug 未修
    assert hidden_test_reward("先运行测试验证 fib 的输出，暂时不下结论。", task) == REWARD_VERIFY
    assert hidden_test_reward("嗯，让我想想。", task) == 0.0


def test_hidden_test_reward_pass_after_fix():
    """修复工作区里的 bug 后宣称完成，隐藏测试通过应得 +1。"""
    task = json.loads(json.dumps(load_hidden_tasks()[0]))
    task["workspace_files"]["solution.py"] = (
        "def fib(n):\n"
        "    if n <= 1:\n"
        "        return n\n"
        "    return fib(n - 1) + fib(n - 2)\n"
    )
    assert hidden_test_reward("已修复并验证，任务完成。", task) == REWARD_CLAIM_PASS
