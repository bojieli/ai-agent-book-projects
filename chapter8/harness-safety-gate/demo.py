"""实验 8-8 离线教学入口：诊断 → 候选 → 模型外验证 → 发布决定。

单候选演示，不调用任何 API。验收入口是 run_experiment_8_8.py。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evolution import (
    diagnose,
    generate_candidate,
    release_manifest,
    validate_candidate,
    write_candidate,
)


ROOT = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser(description="实验 8-8：用户反馈触发的确认门禁")
    parser.add_argument("--generator", choices=("deterministic", "llm"), default="deterministic")
    parser.add_argument("--model", help="真实 LLM 模型；默认取 ARK_MODEL 或 gpt-4o-mini")
    args = parser.parse_args()

    trajectories = json.loads((ROOT / "failure_trajectories.json").read_text(encoding="utf-8"))
    boundary_cases = json.loads((ROOT / "boundary_cases.json").read_text(encoding="utf-8"))
    retention_cases = json.loads((ROOT / "retention_cases.json").read_text(encoding="utf-8"))
    stable_path = ROOT / "stable" / "tool_dispatcher.py"
    stable_source = stable_path.read_text(encoding="utf-8")

    diagnosis = diagnose(trajectories)
    if args.generator == "llm":
        from llm_generator import generate_with_openai
        candidate = generate_with_openai(stable_source, diagnosis, args.model)
    else:
        candidate = generate_candidate(stable_source, diagnosis)
    checks = validate_candidate(candidate["source"], boundary_cases, retention_cases)
    manifest = release_manifest(stable_source, candidate, diagnosis, checks)

    write_candidate(candidate["source"], ROOT / "output" / "candidate" / "confirmation_gate.py")
    (ROOT / "output" / "release_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"实验 8-8：用户反馈触发的高风险操作确认门禁（generator={args.generator}）\n")
    print("诊断目标:", diagnosis["target"])
    print("失败簇:")
    for pattern in diagnosis["patterns"]:
        signals = "/".join(pattern["signals"])
        print(f"  - {pattern['cluster_id']} (支持度 {pattern['cross_trajectory_support']}, 信号: {signals})")
    print("来源轨迹:", ", ".join(diagnosis["source_case_ids"]))
    print("\n接入 diff（提案，不改动 stable/）:\n")
    print(candidate["integration_diff"])
    print("检查:", checks)
    print("发布决定:", manifest["decision"])
    print("stable/ 未被改动:", stable_path.read_text(encoding="utf-8") == stable_source)
    print("回滚版本:", manifest["rollback_version"])


if __name__ == "__main__":
    main()
