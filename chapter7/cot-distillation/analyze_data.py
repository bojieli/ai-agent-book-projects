"""统计蒸馏得到的 SFT 数据：规模、token/字符分布、思考链特征。"""

import argparse
import json
import re


def main():
    parser = argparse.ArgumentParser(description="统计 CoT 蒸馏 SFT 数据")
    parser.add_argument("--sft", default="./data/sft_cot_distill_aime.jsonl")
    parser.add_argument("--raw", default="./data/raw_trajectories_aime.jsonl")
    args = parser.parse_args()

    with open(args.sft, encoding="utf-8") as f:
        samples = [json.loads(line) for line in f if line.strip()]
    print(f"SFT 样本数：{len(samples)}")

    think_lens, answer_lens = [], []
    n_reflect = 0
    n_skipped_short = 0
    for s in samples:
        messages = s.get("messages") or []
        # Incomplete SFT rows (user-only / truncated export) must not IndexError.
        if len(messages) < 2:
            n_skipped_short += 1
            continue
        assistant_msg = messages[1]
        if not isinstance(assistant_msg, dict):
            n_skipped_short += 1
            continue
        assistant = assistant_msg.get("content")
        if not isinstance(assistant, str):
            n_skipped_short += 1
            continue
        m = re.search(r"<think>\n?(.*?)\n?</think>", assistant, re.DOTALL)
        think = m.group(1) if m else ""
        think_lens.append(len(think))
        answer_lens.append(len(assistant))
        # 教师式的反思/验算行为（实验 7-9 验收标准之一）
        if re.search(r"(验算|检查|重新|等等|不对|再算|反思|verify|check|wait)", think, re.IGNORECASE):
            n_reflect += 1

    def stats(xs, name):
        if not xs:
            print(f"{name}：无数据")
            return
        xs = sorted(xs)
        n = len(xs)
        print(f"{name}：均值 {sum(xs)/n:.0f}，中位 {xs[n//2]}，最小 {xs[0]}，最大 {xs[-1]}")

    stats(think_lens, "思考链长度（字符）")
    stats(answer_lens, "完整回答长度（字符）")
    n_scored = len(samples) - n_skipped_short
    print(f"含反思/验算行为的样本：{n_reflect}/{n_scored}")
    if n_skipped_short:
        print(f"跳过 messages 不足 2 条的样本：{n_skipped_short}")

    try:
        with open(args.raw, encoding="utf-8") as f:
            raw = [json.loads(line) for line in f if line.strip()]
        failed = [r for r in raw if not r["verified"]]
        print(f"\n原始轨迹 {len(raw)} 条，未通过验证 {len(failed)} 条：")
        for r in failed:
            pred = r["content"][-80:].replace("\n", " ") if r["content"] else "(无输出)"
            print(f"  {r['id']}: gold={r['gold_answer']}  输出末尾: …{pred}  error={r['error']}")
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    main()
