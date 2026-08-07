"""离线端到端教学演示（实验 7-17）。

不依赖 API key、不依赖 GPU，演示完整链路：
1. 从过早结束 bad case 构造 DPO 偏好对（离线确定性路径）；
2. 展示 2 条样例偏好对；
3. 用 --mock 评估演示指标计算（base vs adapter 的预置样例输出）；
4. 打印全流程摘要与真实训练所需的后续步骤。
"""

from __future__ import annotations

import json

from build_preference_data import build_pairs, load_bad_cases
from evaluate import compute_metrics, load_eval_items, mock_outputs


def main() -> None:
    print("=" * 60)
    print("实验 7-17：过早结束的 DPO 修复 —— 离线端到端演示")
    print("=" * 60)

    # 第一步：构造偏好对（确定性路径，无 API）
    cases = load_bad_cases()
    pairs, _ = build_pairs(cases)
    print(f"\n[1] 从 {len(cases)} 条 bad case 构造出 {len(pairs)} 条 DPO 偏好对")

    # 第二步：展示样例
    print("\n[2] 样例偏好对（前 2 条）：")
    for pair in pairs[:2]:
        meta = pair["meta"]
        print(f"\n  --- {meta['id']}（{meta['category']}）---")
        print("  prompt（截断）:")
        print("    " + pair["prompt"].splitlines()[0])
        print(f"  chosen  : {pair['chosen']}")
        print(f"  rejected: {pair['rejected']}")

    # 第三步：mock 评估演示指标计算
    items = load_eval_items()
    print(f"\n[3] 评估集：boundary {sum(1 for i in items if i['split'] == 'boundary')} 条，"
          f"retention {sum(1 for i in items if i['split'] == 'retention')} 条（与训练数据隔离）")
    for variant in ("base", "adapter"):
        metrics = compute_metrics(items, mock_outputs(variant, items))
        b, r = metrics["boundary"], metrics["retention"]
        print(f"  [{variant:7s}] boundary 过早宣称率 {b['premature_claim_rate']:.0%}"
              f" | retention 正常收尾率 {r['proper_completion_rate']:.0%}"
              f" | 过度矫正率 {r['overcorrection_rate']:.0%}")

    # 第四步：摘要
    print("\n[4] 全流程摘要：")
    print("  离线已演示：bad case -> 偏好对构造 -> 评估指标口径")
    print("  真实链路待执行（需 GPU / API key）：")
    print("    python build_preference_data.py --teacher --provider ark   # 教师模型生成 chosen")
    print("    python train_dpo.py                                         # 单卡 LoRA DPO 训练")
    print("    python evaluate.py --base-only                              # 基线评估")
    print("    python evaluate.py                                          # base vs base+adapter 对比")
    print("    python train_grpo_optional.py                               # 可选 RL 分支")
    print("\n训练后的预期：boundary 过早宣称率应下降，retention 正常收尾率应保持；")
    print("实际数字需在真实训练与评估运行后填入，不预先编造。")


if __name__ == "__main__":
    main()
