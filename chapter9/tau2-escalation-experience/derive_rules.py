#!/usr/bin/env python3
"""从 τ²-bench telecom 的失败轨迹中提炼可操作规则，生成"进化后"的策略补丁。

提炼由 LLM 完成，不由人手写：本实验检验的是系统能否从自身失败中产生
可用规则，而不是"人能否写出更好的提示词"。所有请求与回复原样保存。
"""
import argparse, hashlib, json, os, sys, time
from pathlib import Path
import urllib.request

ARK = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

def summarize(sim, max_errs=6):
    """把一条失败轨迹压成提炼模型能读的紧凑摘要。"""
    msgs = sim["messages"]
    calls, errs = [], []
    for m in msgs:
        for t in (m.get("tool_calls") or []):
            args = t.get("arguments") or {}
            empty = [k for k, v in args.items() if v == ""]
            calls.append({"tool": t["name"], "empty_args": empty})
        if m.get("role") == "tool" and "Error" in (m.get("content") or ""):
            errs.append((m.get("content") or "").strip()[:120])
    return {
        "task_id": sim["task_id"],
        "reward": sim["reward_info"]["reward"],
        "termination": sim.get("termination_reason"),
        "num_messages": len(msgs),
        "tool_call_sequence": [c["tool"] for c in calls][:25],
        "calls_with_empty_args": [c["tool"] for c in calls if c["empty_args"]][:10],
        "distinct_errors": sorted(set(errs))[:max_errs],
        "escalated_to_human": any(c["tool"] == "transfer_to_human_agents" for c in calls),
    }

PROMPT = """你在改进一个电信客服 Agent 的系统策略（system policy）。

下面是该 Agent 在一批任务上的**失败轨迹摘要**。当前策略中关于"何时转人工"只有两句话：

    You should transfer the user to a human agent if and only if the request cannot be
    handled within the scope of your actions.
    You should try your best to resolve the issue for the user before transferring.

请阅读失败摘要，归纳出反复出现的错误模式，并写出一段**新增**的操作性规则，
让 Agent 下次遇到同类情况时不再犯错。

要求：
1. 只输出要追加到策略中的规则条目，用英文，Markdown 无序列表，每条一行。
2. 规则必须可操作（说明"遇到什么情况、该做什么"），不要写"应当认真""尽力而为"这类无法执行的话。
3. 规则必须从摘要中的证据归纳而来，不要凭空添加摘要里没有出现的情形。
4. 不超过 10 条。不要重复已有的两句话。
5. 只输出规则列表本身，不要解释、不要标题、不要代码块围栏。

失败轨迹摘要（JSON）：
{summaries}
"""

INVENTORY_BLOCK = """
补充材料——本 Agent 实际可调用的工具，以及**只有用户能在自己设备上执行**的工具：

{inventory}

请结合这份清单判断失败原因：如果 Agent 调用了不属于它的工具，正确的做法不是
"不要再调用"，而是想清楚那个能力属于谁、应该如何取得。
"""

def call_ark(model, messages, api_key, max_tokens=1600):
    body = json.dumps({"model": model, "messages": messages,
                       "temperature": 0, "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(ARK, data=body, headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.load(r)
    return resp, time.time() - t0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="基线训练集运行结果 json")
    ap.add_argument("--model", default="doubao-seed-1-6-250615")
    ap.add_argument("--baseline-policy", default="policies/baseline_main_policy.md")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--tool-inventory", default=None,
                    help="可选：Agent/用户工具清单文件；提供后提炼器能识别工具归属")
    a = ap.parse_args()

    key = os.environ.get("ARK_API_KEY")
    if not key: sys.exit("需要 ARK_API_KEY")

    sims = json.load(open(a.run, encoding="utf-8"))["simulations"]
    failures = [s for s in sims if s["reward_info"]["reward"] == 0]
    summaries = [summarize(s) for s in failures]

    prompt = PROMPT.format(summaries=json.dumps(summaries, ensure_ascii=False, indent=1))
    inventory_used = None
    if a.tool_inventory:
        inventory_used = Path(a.tool_inventory).read_text(encoding="utf-8").strip()
        prompt += INVENTORY_BLOCK.format(inventory=inventory_used)
    messages = [{"role": "user", "content": prompt}]
    resp, elapsed = call_ark(a.model, messages, key)
    rules = resp["choices"][0]["message"]["content"].strip()
    rules = rules.replace("```markdown", "").replace("```", "").strip()

    base = Path(a.baseline_policy).read_text(encoding="utf-8")
    evolved = base.rstrip() + "\n\n## Escalation and Tool-Use Rules (learned from failed runs)\n\n" + rules + "\n"

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "derived_rules.md").write_text(rules + "\n", encoding="utf-8")
    (out / "evolved_main_policy.md").write_text(evolved, encoding="utf-8")
    json.dump({
        "source_run": a.run,
        "num_failures_analyzed": len(failures),
        "num_total_train_tasks": len(sims),
        "derivation_model": a.model,
        "tool_inventory_provided": bool(a.tool_inventory),
        "tool_inventory": inventory_used,
        "endpoint": ARK,
        "elapsed_seconds": round(elapsed, 3),
        "request_messages": messages,
        "response": resp,
        "baseline_policy_sha256": hashlib.sha256(base.encode()).hexdigest(),
        "evolved_policy_sha256": hashlib.sha256(evolved.encode()).hexdigest(),
        "baseline_policy_chars": len(base),
        "evolved_policy_chars": len(evolved),
    }, open(out / "derivation_receipt.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"提炼完成：{len(failures)} 条失败 → {len(rules.splitlines())} 行规则")
    print(f"策略 {len(base)} → {len(evolved)} 字符")
    print(rules)

if __name__ == "__main__":
    main()
