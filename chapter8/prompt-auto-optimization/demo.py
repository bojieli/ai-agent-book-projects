"""
实验 8-3：基于失败轨迹的系统提示词自动优化

一条命令跑通完整流程：
  1. 用【初始 prompt】评测 → 暴露"政策争议就转人工"的过度转接问题；
  2. 从失败轨迹生成三维诊断，保留来源案例；
  3. Coding Agent 生成候选 prompt 的最小 diff；
  4. 用边界集与保留集决定候选版本是否可灰度发布；
  5. 与人工调优版对照。

    python demo.py            # 完整运行：10 个用例 × 3 份 prompt
    python demo.py --quick    # 快速演示：每组只取 2 个用例，省时省钱
    python demo.py --help     # 查看全部命令行参数（中文说明）
"""

import argparse
import json
import os
import shutil
import sys

from evaluate import evaluate_prompt
from coding_agent import optimize_prompt
from config import get_provider, get_model
from airline_env import CASES
from learning_signal import diagnose_failures, format_learning_signal
from release_gate import build_candidate_manifest, evaluate_release_gate

GROUPS = ("holdout", "boundary")

HERE = os.path.dirname(os.path.abspath(__file__))
INITIAL_PROMPT = os.path.join(HERE, "prompts", "system_prompt.txt")
MANUAL_PROMPT = os.path.join(HERE, "prompts", "system_prompt_manual.txt")
WORKING_PROMPT = os.path.join(HERE, "runtime", "system_prompt_working.txt")

def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _pct(cn):
    c, n = cn
    return f"{c}/{n} ({100 * c / n:.0f}%)" if n else "-"


def print_table(rows):
    """rows: list of (label, holdout_tuple, boundary_tuple)"""
    print("\n" + "=" * 74)
    print("正确率对比（保留任务集 = 既有正确行为不能退化；边界案例集 = 过度转接应改善）")
    print("=" * 74)
    header = f"{'系统提示词版本':<26}{'保留任务集(holdout)':<20}{'边界案例集(boundary)':<20}"
    print(header)
    print("-" * 74)
    for label, holdout, boundary in rows:
        print(f"{label:<24}{_pct(holdout):<22}{_pct(boundary):<22}")
    print("=" * 74)


def _select_cases(limit_per_group=None, groups=GROUPS):
    """按分组筛选用例，并对每组最多取 limit_per_group 个（None 表示不限制）。"""
    picked, counts = [], {}
    for c in CASES:
        g = c["group"]
        if g not in groups:
            continue
        if limit_per_group and counts.get(g, 0) >= limit_per_group:
            continue
        picked.append(c)
        counts[g] = counts.get(g, 0) + 1
    return picked


def main(cases=None, rounds=3, output=None):
    if cases is None:
        cases = CASES
    print("#" * 74)
    print("# 实验 8-3：基于失败轨迹的系统提示词自动优化（航空客服场景）")
    print(f"# LLM 提供商: {get_provider()}   模型: {get_model()}")
    print(f"# 用例数: {len(cases)}（保留集 + 边界集）   Coding Agent 优化轮数上限: {rounds}")
    print("#" * 74)

    # ---- 准备：把初始 prompt 复制成本次运行的工作副本（Coding Agent 会改写它）----
    os.makedirs(os.path.dirname(WORKING_PROMPT), exist_ok=True)
    shutil.copyfile(INITIAL_PROMPT, WORKING_PROMPT)

    # ---- 步骤 1：评测初始 prompt ----
    print("\n【步骤 1】用初始系统提示词评测（观察是否过度转接）")
    before = evaluate_prompt(_read(INITIAL_PROMPT), label="初始 prompt", cases=cases)
    print(
        f"\n  初始结果：保留集 {_pct(before['holdout'])}，"
        f"边界集 {_pct(before['boundary'])}"
    )
    over_transfer = [
        r for r in before["results"]
        if r["group"] == "boundary" and not r["should_transfer"] and r["transferred"]
    ]
    print(f"  边界案例中出现【过度转接】的用例数：{len(over_transfer)} / "
          f"{len([r for r in before['results'] if r['group'] == 'boundary'])}")
    for r in over_transfer:
        print(f"    - {r['id']}：政策争议却直接转人工，原因『{r['transfer_reason']}』")

    # ---- 步骤 2：由失败轨迹形成学习信号 ----
    learning_signal = diagnose_failures(before)
    print("\n【步骤 2】将失败轨迹整理为三维诊断")
    print(format_learning_signal(learning_signal))

    # ---- 步骤 3：Coding Agent 生成候选 prompt ----
    print("\n【步骤 3】Coding Agent 读取诊断并生成候选系统提示词……")
    opt = optimize_prompt(WORKING_PROMPT, learning_signal, max_rounds=rounds, verbose=True)
    manifest = build_candidate_manifest(opt, learning_signal)
    print(f"\n  Coding Agent 改动说明：{opt['rationale']}")
    print("\n  ---------- 系统提示词文件 diff（真实写入磁盘）----------")
    print(opt["diff"] if opt["diff"].strip() else "  (无改动)")
    print("  --------------------------------------------------------")

    print(f"  候选补丁来源：{', '.join(manifest['source_case_ids'])}")
    print(f"  候选补丁作用域：{manifest['scope']}")

    # ---- 步骤 4：评测候选 prompt 并运行发布门槛 ----
    print("\n【步骤 4】评测候选系统提示词并运行发布门槛")
    after = evaluate_prompt(opt["after"], label="自动优化后 prompt", cases=cases)
    gate = evaluate_release_gate(before, after, manifest)
    print(f"  发布决定：{gate['decision']}")
    for check, passed in gate["checks"].items():
        print(f"    {'✓' if passed else '✗'} {check}")

    # ---- 步骤 5：对照人工调优版 ----
    print("\n【步骤 5】对照组：人工调优版系统提示词")
    manual = evaluate_prompt(_read(MANUAL_PROMPT), label="人工调优版 prompt(对照)", cases=cases)

    # ---- 步骤 6：对比表 ----
    print_table([
        ("初始 prompt(优化前)", before["holdout"], before["boundary"]),
        ("自动优化后 prompt", after["holdout"], after["boundary"]),
        ("人工调优版(对照)", manual["holdout"], manual["boundary"]),
    ])

    # ---- 结论 ----
    b_before_c, b_before_n = before["boundary"]
    b_after_c, _ = after["boundary"]
    h_before_c, _ = before["holdout"]
    h_after_c, _ = after["holdout"]
    print("\n【结论】")
    print(f"  · 边界案例集正确率：{b_before_c}/{b_before_n} → {b_after_c}/{b_before_n} "
          f"（{'提升 ✓' if b_after_c > b_before_c else '未提升'}）")
    print(f"  · 保留任务集正确率：{h_before_c} → {h_after_c} "
          f"（{'未退化 ✓' if h_after_c >= h_before_c else '退化 ✗'}）")
    print(f"\n  候选工作副本已写入：{WORKING_PROMPT}")
    print("  它不会覆盖稳定版本；只有 release_to_canary 才允许进入灰度。")

    # ---- 可选：把对比结果落盘为 JSON，便于复现与二次分析 ----
    if output:
        summary = {
            "provider": get_provider(),
            "model": get_model(),
            "rounds": rounds,
            "num_cases": len(cases),
            "learning_signal": learning_signal,
            "candidate_manifest": manifest,
            "release_gate": gate,
            "rationale": opt["rationale"],
            "diff": opt["diff"],
            "rows": [
                {"label": "初始 prompt(优化前)", "holdout": list(before["holdout"]),
                 "boundary": list(before["boundary"])},
                {"label": "自动优化后 prompt", "holdout": list(after["holdout"]),
                 "boundary": list(after["boundary"])},
                {"label": "人工调优版(对照)", "holdout": list(manual["holdout"]),
                 "boundary": list(manual["boundary"])},
            ],
        }
        os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"  对比结果已写入：{output}")


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="demo.py",
        description="实验 8-3：从失败轨迹诊断到候选补丁与发布门槛（航空客服场景）。",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "示例：\n"
            "  python demo.py                     # 完整运行：10 个用例 × 3 份 prompt\n"
            "  python demo.py --quick             # 每组只取 2 个用例，省时省钱\n"
            "  python demo.py --group boundary    # 只评测边界案例集\n"
            "  python demo.py --rounds 5 --model gpt-5.6-luna\n"
            "  python demo.py --output output/run.json  # 把对比结果写成 JSON\n"
            "  python demo.py --dry-run           # 离线：只打印配置与用例数，不调用 API"
        ),
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="快速演示模式：每组只取 2 个用例，减少 API 调用与耗时。",
    )
    parser.add_argument(
        "--limit", type=int, default=None, metavar="N",
        help="每组最多评测 N 个用例（覆盖 --quick）。",
    )
    parser.add_argument(
        "--group", choices=("holdout", "boundary", "both"), default="both",
        help="选择评测的任务集：holdout(保留集) / boundary(边界集) / both(默认，两者都跑)。",
    )
    parser.add_argument(
        "--rounds", type=int, default=3, metavar="N",
        help="Coding Agent 自动改写提示词的最大重试轮数（默认 3）。",
    )
    parser.add_argument(
        "--model", default=None, metavar="NAME",
        help="覆盖 LLM 模型名（等价于设置环境变量 LLM_MODEL，如 gpt-5.6-luna）。",
    )
    parser.add_argument(
        "--provider", choices=("openai", "moonshot", "ark"), default=None,
        help="覆盖 LLM 提供商（等价于设置环境变量 LLM_PROVIDER，默认 openai）。",
    )
    parser.add_argument(
        "--output", default=None, metavar="PATH",
        help="把优化前后 + 人工对照的对比结果写入指定 JSON 文件（如 output/run.json）。",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="离线自检：只打印解析后的配置与选中用例数，不调用任何 LLM API。",
    )
    return parser


if __name__ == "__main__":
    args = _build_parser().parse_args()

    # 命令行覆盖优先级高于环境变量：get_provider()/get_model() 均在调用时读取环境变量
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
    if args.model:
        os.environ["LLM_MODEL"] = args.model

    limit = args.limit if args.limit is not None else (2 if args.quick else None)
    groups = GROUPS if args.group == "both" else (args.group,)
    cases = _select_cases(limit, groups=groups)

    if args.dry_run:
        # 离线路径：不触发任何网络请求，仅用于验证参数解析与用例选择
        print("[dry-run] 解析后的运行配置（不调用 API）：")
        print(f"  LLM 提供商 : {get_provider()}")
        print(f"  LLM 模型   : {get_model()}")
        print(f"  优化轮数   : {args.rounds}")
        print(f"  任务集     : {args.group}")
        print(f"  选中用例数 : {len(cases)}  -> {[c['id'] for c in cases]}")
        print(f"  输出文件   : {args.output or '(不写文件)'}")
        sys.exit(0)

    try:
        main(cases=cases, rounds=args.rounds, output=args.output)
    except RuntimeError as e:
        # 例如 API Key 未设置：给出清晰的人类可读错误，而非原始 traceback
        print(f"\n[错误] {e}", file=sys.stderr)
        sys.exit(1)
