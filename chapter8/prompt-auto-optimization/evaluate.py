"""
评测器：给定一份 system prompt，在用例集上运行 Agent 并判定每个用例是否被"正确处理"。

判定规则（结合确定性规则 + LLM-as-judge）：
- 用例标注了 should_transfer（正确行为是否应转接人工）。
- 若 should_transfer=True：  正确 ⇔ Agent 确实转接了。
- 若 should_transfer=False： 正确 ⇔ Agent 没有转接，且 LLM 裁判确认它按 rubric 妥善处理了请求
                             （即真的解释了政策 / 办理了业务，而不是敷衍或答非所问）。
  之所以对"不转接"再加一道 LLM 裁判，是为了防止 Agent 只是"没转接但也没好好处理"蒙混过关。
"""

import json
from config import get_client, get_model, get_temperature
from airline_env import run_agent


def _judge_handled(user_message: str, rubric: str, agent_reply: str) -> bool:
    """LLM-as-judge：Agent 没转接的情况下，是否按 rubric 妥善处理了请求。"""
    client = get_client()
    model = get_model()
    prompt = f"""你是严格的客服质检员。请判断客服 Agent 的回复是否妥善处理了乘客请求。

【乘客请求】
{user_message}

【合格标准(rubric)】
{rubric}

【Agent 的回复】
{agent_reply}

请只输出一个 JSON：{{"handled": true 或 false, "reason": "简短理由"}}
其中 handled=true 表示 Agent 的回复实质满足了合格标准。"""
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=get_temperature(),
        response_format={"type": "json_object"},
    )
    try:
        verdict = json.loads(resp.choices[0].message.content)
        return bool(verdict.get("handled", False))
    except (json.JSONDecodeError, TypeError):
        return False


def evaluate_case(system_prompt: str, case: dict, verbose: bool = False) -> dict:
    """评测单个用例，返回结果 dict。"""
    result = run_agent(system_prompt, case["user"])
    transferred = result["transferred"]
    should_transfer = case["should_transfer"]

    handled = None
    if should_transfer:
        correct = transferred
        note = "应转接：" + ("已转接 ✓" if transferred else "未转接 ✗")
    else:
        if transferred:
            correct = False
            note = "不应转接：却转接了 ✗（过度转接）"
        else:
            handled = _judge_handled(case["user"], case["rubric"], result["final_text"])
            correct = handled
            note = "不应转接：未转接且妥善处理 ✓" if handled else "不应转接：未转接但处理不当 ✗"

    out = {
        "id": case["id"],
        "group": case["group"],
        "correct": correct,
        "transferred": transferred,
        "should_transfer": should_transfer,
        "note": note,
        "final_text": result["final_text"],
        "transfer_reason": result["transfer_reason"],
        "tool_calls": result["tool_calls"],
        "handled": handled,
    }
    if verbose:
        icon = "✓" if correct else "✗"
        print(f"  [{icon}] {case['id']:<16} {note}")
        if transferred:
            print(f"        转接原因: {result['transfer_reason']}")
        else:
            preview = (result["final_text"] or "").replace("\n", " ")[:80]
            print(f"        回复: {preview}...")
    return out


def evaluate_prompt(system_prompt: str, label: str = "", verbose: bool = True, cases=None) -> dict:
    """在全部用例上评测一份 prompt，返回分组正确率与明细。

    cases 为 None 时评测全部用例；也可传入用例子集（如 --quick 模式）以控制成本。
    """
    from airline_env import CASES

    if cases is None:
        cases = CASES

    if verbose and label:
        print(f"\n>>> 评测 [{label}]")
    results = []
    for case in cases:
        results.append(evaluate_case(system_prompt, case, verbose=verbose))

    def _acc(group):
        rows = [r for r in results if r["group"] == group]
        n = len(rows)
        c = sum(1 for r in rows if r["correct"])
        return c, n

    holdout_c, holdout_n = _acc("holdout")
    boundary_c, boundary_n = _acc("boundary")
    return {
        "label": label,
        "holdout": (holdout_c, holdout_n),
        "boundary": (boundary_c, boundary_n),
        "results": results,
    }
