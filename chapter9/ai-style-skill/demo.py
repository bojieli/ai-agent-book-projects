#!/usr/bin/env python3
"""实验 8-9 离线教学演示：模糊反馈 → 可检查规则 → Skill → 防膨胀/防误伤。

全程离线、确定性，不需要 API key：

    python demo.py
"""

from __future__ import annotations

from evaluate import evaluate_rules, load_eval_texts
from extract_rules import extract_deterministic, load_pairs
from judge import calibrate, load_golden_set, proxy_judge
from rewrite_demo import SAMPLE_TEXT, rewrite_deterministic
from skill_manager import merge_rules, prune_rules, write_skill


def main() -> int:
    pairs = load_pairs()

    print("=" * 70)
    print("第 1 步：收集用户纠正（before/after 对）")
    print("=" * 70)
    sample = pairs[0]
    print(f"[{sample['id']}｜{sample['scene']}] 用户说：{sample['correction']}")
    print(f"  before：{sample['before']}")
    print(f"  after ：{sample['after']}")
    print(f"\n共收集 {len(pairs)} 条反馈，按到达时间分成 3 批。")

    print("\n" + "=" * 70)
    print("第 2 步：逐批提炼候选规则并合并（防膨胀的关键）")
    print("=" * 70)
    rules = []
    for batch_no in (1, 2, 3):
        batch_pairs = [p for p in pairs if p["batch"] == batch_no]
        candidates = extract_deterministic(batch_pairs)
        rules, report = merge_rules(rules, candidates)
        new_sources = {sid for c in candidates for sid in c["source_ids"]}
        for rule in rules:
            if set(rule.get("source_ids", [])) & new_sources:
                rule["last_confirmed_batch"] = batch_no
        print(f"批次 {batch_no}：提炼候选 {len(candidates)} 条 → "
              f"新增规则 {len(report['added'])} 条，合并进已有规则 {len(report['merged'])} 条，"
              f"当前共 {len(rules)} 条")
    print("\n合并后的规则清单：")
    for rule in rules:
        print(f"  {rule['id']}（来源 {len(rule['source_ids'])} 条反馈，"
              f"作用域：{'、'.join(rule['scope'])}）")
    print("注意：相同检测模式的候选被合并，规则数不会随反馈条数线性膨胀。")

    print("\n" + "=" * 70)
    print("第 3 步：llm 类规则上线前先校准（金标集一致率门槛 0.8）")
    print("=" * 70)
    golden_set = load_golden_set()
    active = []
    for rule in rules:
        if rule["detector"].get("type") == "llm":
            result = calibrate(rule, golden_set, proxy_judge(rule))
            print(f"  {rule['id']}：一致率 {result['agree']}/{result['total']}"
                  f" = {result['agreement']:.2f} → {result['decision']}"
                  f"（{result['note']}）")
            if result["decision"] == "activate":
                rule["status"] = "active"
                active.append(rule)
            else:
                rule["status"] = "rejected"
        else:
            rule["status"] = "active"
            active.append(rule)
    print("离线路径用确定性代理 judge 演示校准机制；真实验收请跑"
          " run_experiment_8_9.py --provider ... 用真实 LLM judge。")

    print("\n" + "=" * 70)
    print("第 4 步：prune——长期未触发或被推翻的规则归档")
    print("=" * 70)
    kept, archived = prune_rules(active, current_batch=3)
    print(f"  本批无规则达到归档条件（存活 {len(kept)} 条，归档 {len(archived)} 条）。")
    print("  机制见 skill_manager.prune_rules：连续 2 批无新证据、或被评估证据推翻的规则")
    print("  会移出 SKILL.md，归档到 skill/archive/。")

    print("\n" + "=" * 70)
    print("第 5 步：生成 Skill 并评估（防误伤）")
    print("=" * 70)
    skill_path = write_skill(kept)
    print(f"  已生成 {skill_path}")
    eval_texts = load_eval_texts()
    llm_judges = {r["id"]: proxy_judge(r) for r in kept if r["detector"].get("type") == "llm"}
    metrics = evaluate_rules(kept, eval_texts, llm_judges)
    print(f"  boundary 检出率：{metrics['boundary_detected']}/{metrics['boundary_total']}"
          f"（带明显 AI 味的文本应被检出）")
    print(f"  retention 误伤率：{metrics['retention_harmed']}/{metrics['retention_total']}"
          f"（合法使用这些模式的好文本不应被误伤）")

    print("\n" + "=" * 70)
    print("第 6 步：按 Skill 改写一段 AI 味文本（确定性路径）")
    print("=" * 70)
    result = rewrite_deterministic(SAMPLE_TEXT, kept)
    print("原文：", result["original"])
    for s in result["suggestions"]:
        print(f"  [{s['rule_name']}] {len(s['hits'])} 处命中 → {s['suggestion']}")
    print("参考改写：", result["reference_rewrite"])

    print("\n演示完成。真实 LLM 路径："
          "python run_experiment_8_9.py --provider ark --model doubao-seed-1-6-250615")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
