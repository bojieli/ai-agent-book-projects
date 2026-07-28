"""实验 5-1：用代码生成工具提升数学解题能力

对照实验：在同一组 AIME 风格竞赛数学题上，比较
  - 【纯思维链 CoT】：只靠自然语言推理，不能执行代码；
  - 【代码辅助】：把问题形式化为 Python（sympy 符号计算、scipy 数值优化、
     numpy 矩阵），在子进程沙箱执行，返回精确结果。

两种模式跑同一个模型、同一组题、temperature=0，最后给出准确率对照表。

运行:  python demo.py                  # 跑完整对照实验（需要 API key）
       python demo.py --selfcheck      # 离线自检：只跑沙箱执行参考解，无需 API key
更多用法见  python demo.py --help
"""

import os
import re
import sys
import json
import argparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sandbox import run_python

# ---------------------------------------------------------------------------
# 配置：兼容多种可用的 OpenAI 协议 key（含通用 OpenRouter 兜底）
# ---------------------------------------------------------------------------

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def map_model_to_openrouter(model: str) -> str:
    """把直连模型名映射为 OpenRouter 上的 id（非可映射 id 统一兜底到当前廉价旗舰）。"""
    if not model or "/" in model:
        return model or "openai/gpt-5.6-luna"
    m = model.lower()
    if m.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai/" + model
    if m.startswith("claude"):
        if "haiku" in m:
            return "anthropic/claude-haiku-4.5"
        if "sonnet" in m:
            return "anthropic/claude-sonnet-4.6"
        return "anthropic/claude-opus-4.8"
    if m.startswith("gemini"):
        return "google/" + model
    # kimi / doubao / 其它非 OpenRouter 原生 id -> 统一兜底
    return "openai/gpt-5.6-luna"


def resolve_llm(api_key, base_url, model):
    """通用 OpenRouter 兜底 + gpt-5.x 优先路由，返回 (api_key, base_url, model)。

    - gpt-5.x / gpt-5.6* 且设置了 OPENROUTER_API_KEY 时优先走 OpenRouter
      （直连 OpenAI 调用 gpt-5.6 需要组织实名认证）。
    - 否则有直连 key 就保持直连不变。
    - 否则有 OPENROUTER_API_KEY 就整体改走 OpenRouter。
    - 都没有则原样返回，由调用方给出缺 key 的报错。
    """
    orkey = os.getenv("OPENROUTER_API_KEY")
    m = (model or "").lower()
    prefer_or = bool(orkey) and m.startswith("gpt-5")
    if prefer_or or (not api_key and orkey):
        return orkey, OPENROUTER_BASE_URL, map_model_to_openrouter(model)
    return api_key, base_url, model


def build_client_and_model(model_override=None):
    """根据环境变量构造 OpenAI 客户端与默认模型名。

    优先级：OPENAI_API_KEY > MOONSHOT_API_KEY > ARK_API_KEY，均缺失时走 OPENROUTER_API_KEY。
    这些服务都兼容 OpenAI 的 chat.completions + function calling 接口。
    命令行 --model 优先级最高，会覆盖环境变量推断出的默认模型。
    """
    # 延迟导入：离线自检（--selfcheck）不需要 openai，也不需要 API key。
    from openai import OpenAI

    model = os.getenv("MODEL", "gpt-5.6-luna")
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = None

    if os.getenv("OPENAI_API_KEY"):
        api_key = os.getenv("OPENAI_API_KEY")
    elif os.getenv("MOONSHOT_API_KEY"):
        api_key = os.getenv("MOONSHOT_API_KEY")
        base_url = base_url or "https://api.moonshot.cn/v1"
        model = os.getenv("MODEL", "kimi-k3")
    elif os.getenv("ARK_API_KEY"):
        api_key = os.getenv("ARK_API_KEY")
        base_url = base_url or "https://ark.cn-beijing.volces.com/api/v3"
        model = os.getenv("MODEL", "doubao-seed-1-6-250615")

    if model_override:
        model = model_override

    # 通用 OpenRouter 兜底：无直连 key（或默认走 gpt-5.x）时改走 OpenRouter。
    api_key, base_url, model = resolve_llm(api_key, base_url, model)

    if not api_key:
        raise SystemExit(
            "未找到 API key，请设置 OPENAI_API_KEY（或 MOONSHOT_API_KEY / ARK_API_KEY / OPENROUTER_API_KEY）。\n"
            "若只想验证沙箱与题库而不调用大模型，可运行：python demo.py --selfcheck"
        )

    # 加上超时与重试：避免个别 API 调用长时间挂起导致整个评测卡死。
    _kw = {"api_key": api_key, "timeout": 60.0, "max_retries": 3}
    if base_url:
        _kw["base_url"] = base_url
    client = OpenAI(**_kw)
    return client, model


# ---------------------------------------------------------------------------
# 工具定义（function calling）
# ---------------------------------------------------------------------------

RUN_PYTHON_TOOL = {
    "type": "function",
    "function": {
        "name": "run_python",
        "description": (
            "在预装 sympy/numpy/scipy 的 Python 沙箱中执行代码，用于精确的数学计算。"
            "必须用 print() 打印你想看到的结果。适合符号计算、数论枚举、"
            "多项式展开、数值求解等。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要执行的 Python 源码，用 print 输出结果。",
                }
            },
            "required": ["code"],
        },
    },
}

FINAL_INSTRUCTION = (
    "题目的答案是一个整数。请在最后单独用一行给出最终答案，格式严格为：\n"
    "FINAL ANSWER: <整数>"
)

COT_SYSTEM = (
    "你是一位数学竞赛高手。请仅用自然语言逐步推理来解题，"
    "不要编写或调用任何代码。\n" + FINAL_INSTRUCTION
)

CODE_SYSTEM = (
    "你是一位擅长用编程解题的数学竞赛高手。遇到需要计算的地方，"
    "请把问题形式化为 Python 代码，并调用 run_python 工具在沙箱中执行，"
    "用精确的计算结果替代心算。可以多次调用工具来验证。\n" + FINAL_INSTRUCTION
)


# ---------------------------------------------------------------------------
# 答案抽取
# ---------------------------------------------------------------------------

def extract_answer(text: str):
    """从模型输出中解析整数答案。优先匹配 FINAL ANSWER，退化到最后一个整数。"""
    if not text:
        return None
    m = list(re.finditer(r"FINAL ANSWER:\s*(-?\d+)", text, re.IGNORECASE))
    if m:
        return int(m[-1].group(1))
    # 退化：抓最后一个 \boxed{...} 或末尾整数
    m = list(re.finditer(r"\\boxed\{\s*(-?\d+)\s*\}", text))
    if m:
        return int(m[-1].group(1))
    nums = re.findall(r"-?\d+", text)
    return int(nums[-1]) if nums else None


# ---------------------------------------------------------------------------
# 单题求解
# ---------------------------------------------------------------------------

def solve(client, model, question, use_code, max_turns=8, verbose=False):
    """求解单题，返回 (预测整数答案, 使用的工具代码列表, 最终文本)。"""
    system = CODE_SYSTEM if use_code else COT_SYSTEM
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]
    tools = [RUN_PYTHON_TOOL] if use_code else None
    codes = []

    for _ in range(max_turns):
        # 推理模型（kimi-k3 / gpt-5 / *thinking 等）不接受 temperature=0，且需更大 max_tokens 容纳思考
        _rs = ({"temperature": 1, "max_tokens": 4096}
               if any(k in (model or "").lower() for k in ("kimi-k3", "kimi-k2.", "gpt-5", "o1", "o3", "o4", "thinking", "reasoner"))
               else {"temperature": 0})
        kwargs = dict(model=model, messages=messages, **_rs)
        if tools:
            kwargs["tools"] = tools
        resp = client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message

        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            # 必须把 assistant 的 tool_calls 消息原样加回
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            )
            for tc in tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                    code = args.get("code", "")
                except json.JSONDecodeError:
                    code = ""
                codes.append(code)
                result = run_python(code) if code else "[错误] 未提供 code"
                if verbose:
                    print("\n--- 模型生成的代码 ---\n" + code)
                    print("--- 执行结果 ---\n" + result)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )
            continue  # 继续让模型基于工具结果推理

        # 没有工具调用 → 最终回答
        return extract_answer(msg.content), codes, (msg.content or "")

    # 超过最大轮次，做最后一次强制收尾
    messages.append(
        {"role": "user", "content": "请立刻给出：FINAL ANSWER: <整数>"}
    )
    _rs = ({"temperature": 1, "max_tokens": 4096}
           if any(k in (model or "").lower() for k in ("kimi-k3", "kimi-k2.", "gpt-5", "o1", "o3", "o4", "thinking", "reasoner"))
           else {"temperature": 0})
    resp = client.chat.completions.create(
        model=model, messages=messages, **_rs
    )
    content = resp.choices[0].message.content or ""
    return extract_answer(content), codes, content


# ---------------------------------------------------------------------------
# 离线自检：只用沙箱执行题库自带的参考解，不调用任何大模型
# ---------------------------------------------------------------------------

def run_selfcheck(problems, verbose=False):
    """确定性地验证「沙箱 + 题库」这条链路，无需 API key。

    对每道题执行其 problems.json 里附带的参考解（Python 代码），
    在子进程沙箱里运行，抽取整数输出并与真值比对。既演示了
    「模型写代码 → 沙箱执行 → 按真值判分」的核心机制，也自检了题库真值本身。
    返回通过的题目数；全部通过时进程退出码为 0，否则为 1。
    """
    print("离线自检：在沙箱中执行题库参考解，并按真值判分（无需 API key）\n")
    print(f"{'题号':<5}{'考点':<26}{'真值':>7}{'沙箱输出':>10}{'':>4}")
    print("-" * 56)
    ok_count = 0
    missing = 0
    for p in problems:
        sol = p.get("solution")
        if not sol:
            missing += 1
            print(f"{p['id']:<5}{p['topic']:<26}{p['answer']:>7}{'(无参考解)':>12}")
            continue
        out = run_python(sol)
        pred = extract_answer(out)
        ok = pred == p["answer"]
        ok_count += ok
        if verbose:
            print("\n--- 参考解 ---\n" + sol)
            print("--- 沙箱输出 ---\n" + out)
        print(
            f"{p['id']:<5}{p['topic']:<26}{p['answer']:>7}{str(pred):>10}"
            f"{'✓' if ok else '✗':>4}"
        )
    n = len(problems)
    print("-" * 56)
    print(f"参考解命中真值：{ok_count}/{n}" + (f"（{missing} 题缺参考解）" if missing else ""))
    if ok_count == n:
        print("\n全部通过：沙箱可用，题库真值自洽，可放心用于打分。")
        return 0
    print("\n存在不一致：请检查上述 ✗ 题目的参考解或真值。")
    return 1


# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="demo.py",
        description="实验 5-1：代码沙箱辅助 vs 纯思维链（CoT）在 AIME 风格数学题上的准确率对照。",
        epilog=(
            "示例：\n"
            "  python demo.py                       跑完整对照实验（code 与 cot 两种模式）\n"
            "  python demo.py --selfcheck           离线自检沙箱与题库真值，无需 API key\n"
            "  python demo.py --mode code           只跑代码辅助模式\n"
            "  python demo.py --mode cot --limit 3  只跑纯 CoT 的前 3 题\n"
            "  python demo.py --model gpt-5.6        换用更强的模型\n"
            "  python demo.py --output result.json  把逐题结果写入 JSON\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["both", "code", "cot"],
        default="both",
        help="求解模式：both=两种都跑并对照（默认）；code=仅代码辅助；cot=仅纯思维链。",
    )
    parser.add_argument(
        "--problems",
        default="problems.json",
        metavar="路径",
        help="题库 JSON 路径（默认 problems.json，相对本脚本目录）。",
    )
    parser.add_argument(
        "--model",
        default=None,
        metavar="名称",
        help="覆盖模型名（默认取环境变量 MODEL，再退化到供应商默认，如 gpt-5.6-luna）。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="只跑前 N 题（省钱调试，0 表示全部）。",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="路径",
        help="把逐题结果与汇总写入指定的 JSON 文件。",
    )
    parser.add_argument(
        "--selfcheck",
        action="store_true",
        help="离线自检模式：只在沙箱中执行题库参考解并按真值判分，不调用任何大模型（无需 API key）。",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="打印模型（或参考解）生成的代码与沙箱执行结果。",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# 主流程：对照实验
# ---------------------------------------------------------------------------

def load_problems(path):
    here = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(path):
        path = os.path.join(here, path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    args = parse_args(argv)

    problems = load_problems(args.problems)
    if args.limit:
        problems = problems[: args.limit]

    # ---- 离线自检：无需 API key，确定性判分 ----
    if args.selfcheck:
        return run_selfcheck(problems, verbose=args.verbose)

    client, model = build_client_and_model(model_override=args.model)

    run_cot = args.mode in ("both", "cot")
    run_code = args.mode in ("both", "code")
    print(f"模型: {model}   题目数: {len(problems)}   模式: {args.mode}\n")

    rows = []
    cot_correct = code_correct = 0
    for p in problems:
        q, truth = p["question"], p["answer"]
        print(f"[{p['id']:>2}] {p['topic']}  (真值={truth})")

        cot_pred = code_pred = None
        cot_ok = code_ok = False
        n_calls = 0
        if run_cot:
            cot_pred, _, _ = solve(client, model, q, use_code=False, verbose=args.verbose)
            cot_ok = cot_pred == truth
            cot_correct += cot_ok
        if run_code:
            code_pred, codes, _ = solve(client, model, q, use_code=True, verbose=args.verbose)
            code_ok = code_pred == truth
            code_correct += code_ok
            n_calls = len(codes)

        parts = []
        if run_cot:
            parts.append(f"纯CoT   预测={cot_pred!s:>8}  {'✓' if cot_ok else '✗'}")
        if run_code:
            parts.append(
                f"代码辅助 预测={code_pred!s:>8}  {'✓' if code_ok else '✗'}"
                f"   (工具调用 {n_calls} 次)"
            )
        print("     " + "   |  ".join(parts))
        rows.append(
            {
                "id": p["id"],
                "topic": p["topic"],
                "answer": truth,
                "cot_pred": cot_pred,
                "cot_ok": bool(cot_ok),
                "code_pred": code_pred,
                "code_ok": bool(code_ok),
                "tool_calls": n_calls,
            }
        )

    # ---- 汇总表 ----
    n = len(problems)
    print("\n" + "=" * 78)
    print("逐题对照结果")
    print("=" * 78)
    print(f"{'题号':<5}{'考点':<26}{'真值':>7}{'CoT预测':>10}{'':>4}{'代码预测':>10}{'':>4}")
    print("-" * 78)
    for r in rows:
        cp = str(r["cot_pred"]) if run_cot else "-"
        dp = str(r["code_pred"]) if run_code else "-"
        cm = ("✓" if r["cot_ok"] else "✗") if run_cot else " "
        dm = ("✓" if r["code_ok"] else "✗") if run_code else " "
        print(
            f"{r['id']:<5}{r['topic']:<26}{r['answer']:>7}{cp:>10}{cm:>4}{dp:>10}{dm:>4}"
        )
    print("-" * 78)
    summary_line = f"{'准确率':<5}{'':<26}{'':>7}"

    def _rate_cell(correct: int, width: int) -> str:
        if n == 0:
            return f"{correct}/{n} =   N/A".rjust(width)
        return f"{correct}/{n} = {correct / n:5.0%}".rjust(width)

    if run_cot:
        summary_line += _rate_cell(cot_correct, 14)
    if run_code:
        summary_line += _rate_cell(code_correct, 18)
    print(summary_line)
    print("=" * 78)
    if n and run_cot and run_code:
        print(
            f"\n结论：纯 CoT 准确率 {cot_correct/n:.0%}，代码辅助准确率 {code_correct/n:.0%}，"
            f"提升 {(code_correct-cot_correct)/n:+.0%}。"
        )

    # ---- 可选：写出 JSON 结果 ----
    if args.output:
        summary = {
            "model": model,
            "mode": args.mode,
            "num_problems": n,
            "cot_correct": cot_correct if run_cot else None,
            "code_correct": code_correct if run_code else None,
            "rows": rows,
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\n结果已写入：{args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
