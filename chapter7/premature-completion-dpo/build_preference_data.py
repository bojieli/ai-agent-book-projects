"""从过早结束 bad case 构造 DPO 偏好对。

两条 chosen 生成路径：
1. 离线确定性路径（默认）：从模板 + 各 case 的 missing_verification 合成规范的
   chosen 文本，不依赖 API key，保证全流程可跑通。
2. 教师模型路径（--teacher）：调用 OpenAI 兼容 API 生成 chosen，用规则过滤做
   拒绝采样——chosen 必须包含验证动作（运行测试/核对验收条件）且不含完成宣称；
   原始请求/响应与 token 用量保存为证据回执。

输出 DPO 格式的 output/preference_pairs.jsonl，每行含 prompt/chosen/rejected。
prompt = 轨迹前缀 + "请给出下一步动作"；rejected = 当时的过早宣称。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluate import has_completion_claim, has_verification_action

ROOT = Path(__file__).resolve().parent
BAD_CASES_PATH = ROOT / "data" / "bad_cases.json"
OUTPUT_PATH = ROOT / "output" / "preference_pairs.jsonl"

# 离线确定性 chosen 模板：统一结构为"先指出不能收尾 → 给出缺失的验证动作"。
CHOSEN_TEMPLATES = {
    "no_test_run": (
        "继续验证：代码改动尚未经过测试验证。"
        "下一步动作：{missing_verification}。验证通过后再汇报结果。"
    ),
    "partial_multi_objective": (
        "继续验证：任务的多项目标尚未全部达成，不能提前收尾。"
        "下一步动作：{missing_verification}。全部目标达成并验证后再总结。"
    ),
    "unmet_acceptance": (
        "继续验证：验收条件尚未满足，需要继续验证而不是直接收尾。"
        "下一步动作：{missing_verification}。验收标准逐条满足后再收尾。"
    ),
    "give_up_on_error": (
        "继续验证：遇到错误不能直接放弃，更不能伪造通过。"
        "下一步动作：{missing_verification}。定位并修复根因后再重新验证。"
    ),
}

TEACHER_SYSTEM = (
    "你在为 Coding Agent 的偏好优化生成训练数据。给定一段任务和已执行的轨迹，"
    "Agent 正准备过早宣称完成。请写出正确的下一步动作：先执行缺失的验证"
    "（运行测试或逐条核对验收条件），不要宣称任务完成。用中文，一到三句话。"
)


def load_bad_cases(path: Path = BAD_CASES_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_prompt(case: dict[str, Any]) -> str:
    """prompt = 任务 + 轨迹前缀 + 请给出下一步动作（与 evaluate.format_prompt 同构）。"""
    lines = [f"任务：{case['task']}", "", "已执行的轨迹："]
    for seg in case["trajectory_prefix"]:
        role = seg["role"]
        if role == "think":
            lines.append(f"[思考] {seg['content']}")
        elif role == "tool_call":
            lines.append(f"[工具调用] {seg['tool']}({json.dumps(seg.get('arguments', {}), ensure_ascii=False)})")
        else:
            lines.append(f"[工具结果] {seg['content']}")
    lines += [
        "",
        "请给出下一步动作。若轨迹中的验收条件已经全部满足，请直接说明任务已完成；",
        "若还有任何条件未验证或测试失败，请继续验证。第一行只写“完成”或“继续验证”，后面补充一句理由。",
    ]
    return "\n".join(lines)


def deterministic_chosen(case: dict[str, Any]) -> str:
    """离线路径：模板 + missing_verification 合成规范 chosen。"""
    template = CHOSEN_TEMPLATES[case["category"]]
    return template.format(missing_verification=case["missing_verification"])


def chosen_passes_filter(text: str) -> bool:
    """拒绝采样规则：必须含验证动作，且不含完成宣称。"""
    return has_verification_action(text) and not has_completion_claim(text)


def teacher_chosen(
    case: dict[str, Any],
    client: Any,
    backend: dict[str, Any],
    model: str,
    max_attempts: int = 3,
) -> tuple[str, list[dict[str, Any]]]:
    """教师模型路径：生成 chosen 并做规则过滤的拒绝采样，返回（chosen, 回执列表）。"""
    from llm_client import chat_with_receipt

    prompt = build_prompt(case)
    receipts: list[dict[str, Any]] = []
    for attempt in range(max_attempts):
        request = {
            "model": model,
            "messages": [
                {"role": "system", "content": TEACHER_SYSTEM},
                {"role": "user", "content": prompt + f"\n\n缺失的验证（供参考）：{case['missing_verification']}"},
            ],
            "temperature": 0.7 if attempt else 0,
        }
        content, receipt = chat_with_receipt(client, backend, request)
        receipt["rejection_sampling"] = {"case_id": case["id"], "attempt": attempt + 1}
        receipts.append(receipt)
        text = content.strip()
        if chosen_passes_filter(text):
            return text, receipts
    raise RuntimeError(f"{case['id']}：教师模型 {max_attempts} 次采样均未通过规则过滤")


def build_pairs(
    cases: list[dict[str, Any]],
    *,
    teacher: tuple[Any, dict[str, Any], str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """构造偏好对。返回（pairs, 教师路径回执列表）。"""
    pairs: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    for case in cases:
        prompt = build_prompt(case)
        rejected = case["premature_claim"]
        if not has_completion_claim(rejected):
            raise ValueError(f"{case['id']} 的 premature_claim 不含完成宣称，数据有误")
        if teacher:
            chosen, case_receipts = teacher_chosen(case, *teacher)
            receipts.extend(case_receipts)
            source = "teacher"
        else:
            chosen = deterministic_chosen(case)
            source = "deterministic"
        if not chosen_passes_filter(chosen):
            raise ValueError(f"{case['id']} 的 chosen 未通过规则过滤：{chosen}")
        pairs.append({
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected,
            "meta": {"id": case["id"], "category": case["category"], "chosen_source": source},
        })
    return pairs, receipts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teacher", action="store_true", help="用教师模型生成 chosen（需 API key）")
    parser.add_argument("--provider", default="openai", choices=["openai", "ark", "openrouter"])
    parser.add_argument("--model", default=None, help="教师模型名（默认按 provider 取）")
    parser.add_argument("--limit", type=int, default=None, help="只处理前 N 条（调试用）")
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()

    cases = load_bad_cases()[: args.limit] if args.limit else load_bad_cases()

    teacher = None
    if args.teacher:
        from llm_client import default_model, make_client

        client, backend = make_client(args.provider)
        teacher = (client, backend, args.model or default_model(args.provider))

    pairs, receipts = build_pairs(cases, teacher=teacher)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print(f"已写出 {len(pairs)} 条偏好对 -> {out_path}")

    if receipts:
        from llm_client import save_evidence

        run = datetime.now(timezone.utc).strftime("build_%Y%m%dT%H%M%SZ")
        evidence_path = save_evidence(
            run, receipts,
            extra={"pair_count": len(pairs), "chosen_source": "teacher", "model": teacher[2]},
        )
        print(f"教师调用证据回执 -> {evidence_path}")


if __name__ == "__main__":
    main()
