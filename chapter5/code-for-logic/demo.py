#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验 5-2：用代码生成工具提升逻辑思考能力

对比在三种模式下求解「骑士与无赖」(Knights & Knaves) 谜题的准确率：

  1) 纯思考(pure)      —— LLM 仅靠自然语言链式推理直接给出答案；
  2) 代码辅助(code)    —— LLM 配备 Code Interpreter(预装 python-constraint)，
                          把谜题形式化为约束满足问题(CSP)，调用求解器搜索答案；
  3) 约束求解(solver)  —— 【离线，无需 API】直接用 python-constraint 求解结构化
                          陈述，作为确定性基线(理论上 100% 正确)。

结论预期：约束求解把逻辑推理外包给确定性求解器，准确率应达 90%+，
且显著高于纯思考模式(纯思考在多人、含计数/自指的谜题上容易出错)。

用法：
    # 离线约束求解基线(不花钱、不联网，演示核心论点)：
    python demo.py --mode solver

    # LLM 对照实验(需要 OPENAI_API_KEY)：
    export OPENAI_API_KEY=your-openai-api-key
    python demo.py                       # 默认 both：跑 纯思考 vs 代码辅助 全部题目
    python demo.py --mode pure           # 只跑纯思考
    python demo.py --limit 4             # 只跑前 4 题(省钱冒烟测试)
    python demo.py --max-people 3        # 只跑不超过 3 人的谜题(按难度筛选)
    python demo.py --model gpt-4o-mini    # 指定模型(默认 gpt-4o-mini)
    python demo.py --puzzles my.json     # 换一份谜题数据集
"""
import argparse
import datetime as dt
import json
import math
import os
import re
import sys
import time
from pathlib import Path

from csp_solver import solve_labeled
from sandbox import run_python

# ---- 读取 .env(如果存在)。避免额外依赖，手写一个极简解析器。----
def _load_dotenv(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

MODEL = os.environ.get("MODEL", "gpt-4o-mini")
PROVIDER = "unknown"

# --- 通用 OpenRouter 兜底：无直连 key 时自动改走 OpenRouter ---
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
    return "openai/gpt-5.6-luna"


def build_client_and_model(provider="auto"):
    """构造 OpenAI 客户端并返回 (client, model)。

    - 有 OPENAI_API_KEY：直连（默认模型 gpt-4o-mini 是普通 gpt id，可直连 OpenAI）。
      仅当模型是 gpt-5.x 且同时设置了 OPENROUTER_API_KEY 时才优先走 OpenRouter
      （直连 gpt-5.x 需组织实名认证）。
    - 无 OPENAI_API_KEY 但有 OPENROUTER_API_KEY：整体改走 OpenRouter。
    """
    from openai import OpenAI
    global MODEL, PROVIDER
    choices = {
        "ollama": ("ollama", os.environ.get(
            "OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"
        ), MODEL),
        "openai": (os.environ.get("OPENAI_API_KEY"),
                   os.environ.get("OPENAI_BASE_URL"), MODEL),
        "openrouter": (os.environ.get("OPENROUTER_API_KEY"),
                       OPENROUTER_BASE_URL, map_model_to_openrouter(MODEL)),
        "moonshot": (os.environ.get("MOONSHOT_API_KEY"),
                     "https://api.moonshot.cn/v1", MODEL),
        "ark": (os.environ.get("ARK_API_KEY"),
                "https://ark.cn-beijing.volces.com/api/v3", MODEL),
    }
    if provider == "auto":
        provider = next(
            (name for name in ("openai", "openrouter", "moonshot", "ark")
             if choices[name][0]),
            "openai",
        )
    if provider not in choices:
        raise ValueError(f"unsupported provider: {provider}")
    api_key, base_url, MODEL = choices[provider]
    if not api_key:
        raise SystemExit(f"错误：provider={provider} 缺少对应 API key")
    PROVIDER = provider
    kw = {"api_key": api_key, "timeout": 180.0, "max_retries": 5}
    if base_url:
        kw["base_url"] = base_url
    return OpenAI(**kw), MODEL


def _reasoning(model: str) -> bool:
    """推理模型（gpt-5 / o 系列 / *thinking 等）不接受 temperature=0。"""
    return any(k in (model or "").lower()
               for k in ("gpt-5", "o1", "o3", "o4", "thinking", "reasoner", "kimi-k3"))

# run_python 工具的 function calling 定义
TOOLS = [{
    "type": "function",
    "function": {
        "name": "run_python",
        "description": (
            "在预装了 python-constraint 库的沙箱中执行 Python 代码，返回 stdout/stderr。"
            "用它把逻辑谜题建模为约束满足问题并求解。记得用 print() 打印结果。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "要执行的完整 Python 代码"}
            },
            "required": ["code"],
        },
    },
}]

ANSWER_HINT = (
    '推理结束后，请在最后单独用一行输出 JSON 形式的最终答案，'
    '键为每个居民的名字，值为 "knight" 或 "knave"，例如：'
    '{"A": "knight", "B": "knave"}'
)

PURE_SYSTEM = (
    "你是逻辑推理专家。在「骑士与无赖」谜题中，骑士永远说真话，无赖永远说假话。"
    "请仅凭自己的推理，逐步分析每位居民的身份，找出满足所有陈述的唯一解。\n" + ANSWER_HINT
)

CODE_SYSTEM = (
    "你是逻辑推理专家，擅长把谜题转化为形式化约束并用代码求解。"
    "在「骑士与无赖」谜题中，骑士永远说真话，无赖永远说假话。\n"
    "请务必使用 run_python 工具，用 python-constraint 库把谜题建模为约束满足问题(CSP)来求解。\n\n"
    "【最关键的建模规则】不要把某人的陈述直接当成事实约束！"
    "正确做法是对每位居民 X 加一条【双条件(等价)约束】：\n"
    "    X 的布尔值  ==  (X 那句话在语义上为真)\n"
    "含义：X 是骑士(True) 当且仅当 他的话为真；X 是无赖(False) 当且仅当 他的话为假。\n"
    "这条规则对每一句话都适用，包括计数类('恰好有两个骑士')和自指类('我和 B 同类')的陈述——"
    "都要写成 `X == (那句话的真值表达式)`，绝不能把 `(那句话的真值表达式)` 单独当作硬约束。\n\n"
    "示例(设 True=骑士)：\n"
    "    from constraint import Problem\n"
    "    p = Problem()\n"
    "    for name in ['A','B','C']:\n"
    "        p.addVariable(name, [True, False])\n"
    "    # A 说'我们中恰好有一个骑士'  ->  A == ( (A+B+C)==1 )\n"
    "    p.addConstraint(lambda a,b,c: a == ((a+b+c)==1), ['A','B','C'])\n"
    "    # B 说'C 是无赖'             ->  B == (not C)\n"
    "    p.addConstraint(lambda b,c: b == (not c), ['B','C'])\n"
    "    # C 说'我和 A 是同一类人'     ->  C == (C == A)\n"
    "    p.addConstraint(lambda a,c: c == (c == a), ['A','C'])\n"
    "    for s in p.getSolutions():\n"
    "        print({k:('knight' if v else 'knave') for k,v in s.items()})\n\n"
    "步骤：1) 每人一个布尔变量；2) 每句话写成上面的双条件约束；"
    "3) 调用 getSolutions() 枚举所有解并 print。\n"
    "最终答案必须严格采用求解器打印出的解，不要用自己的直觉去推翻它。"
    "若求解器输出为空，说明约束建错了(很可能漏了双条件)，请检查并重跑。\n" + ANSWER_HINT
)


def parse_answer(text, names):
    """从模型输出里提取最后一个形如 {name: knight/knave} 的 JSON 答案。"""
    norm = {
        "knight": "knight",
        "knave": "knave",
        "骑士": "knight",
        "无赖": "knave",
        "true": "knight",
        "false": "knave",
        "1": "knight",
        "0": "knave",
    }
    # 找出所有 {...} 片段，从后往前尝试解析
    for m in reversed(list(re.finditer(r"\{[^{}]*\}", text))):
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            try:
                import ast
                obj = ast.literal_eval(m.group(0))
            except (SyntaxError, ValueError):
                continue
        if not isinstance(obj, dict):
            continue
        got = {}
        for n in names:
            if n not in obj:
                break
            v = str(obj[n]).strip().lower()
            v = norm.get(v, norm.get(str(obj[n]).strip(), None))
            if v is None:
                break
            got[n] = v
        else:
            return got
    return None


def call_model(client, system, user, use_tools):
    """Run one trajectory and retain credential-free provider receipts."""
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": user}]
    codes = []
    receipts = []
    for turn in range(8):  # 最多 8 轮，防止无限循环
        kwargs = (dict(model=MODEL, messages=messages, temperature=1, max_tokens=8192)
                  if _reasoning(MODEL)
                  else dict(model=MODEL, messages=messages, temperature=0))
        if use_tools:
            kwargs.update(
                tools=TOOLS,
                tool_choice="required" if not codes else "auto",
            )
        resp = client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        usage = getattr(resp, "usage", None)
        receipts.append({
            "turn": turn + 1,
            "response_id": getattr(resp, "id", None),
            "response_model": getattr(resp, "model", None),
            "finish_reason": getattr(resp.choices[0], "finish_reason", None),
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
                "cached_prompt_tokens": getattr(
                    getattr(usage, "prompt_tokens_details", None),
                    "cached_tokens", None,
                ),
            },
            "tool_calls": len(getattr(msg, "tool_calls", None) or []),
        })
        if use_tools and msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                try:
                    code = json.loads(tc.function.arguments).get("code", "")
                except json.JSONDecodeError:
                    code = ""
                codes.append(code)
                result = run_python(code)
                messages.append({"role": "tool", "tool_call_id": tc.id,
                                 "content": result})
            continue
        return msg.content or "", codes, receipts
    return "", codes, receipts


def run_mode(client, puzzles, mode, existing=None, checkpoint=None):
    """跑一种 LLM 模式(pure/code)，返回逐题记录列表。"""
    system = CODE_SYSTEM if mode == "code" else PURE_SYSTEM
    existing_by_id = {
        record["id"]: record for record in (existing or [])
        if record.get("id")
    }
    records = []
    for p in puzzles:
        previous = existing_by_id.get(p["id"])
        if (
            previous
            and not previous.get("provider_error")
            and previous.get("provider_receipts")
            and (mode != "code" or previous.get("codes"))
        ):
            record = previous
        else:
            started = time.monotonic()
            try:
                text, codes, receipts = call_model(
                    client, system, p["description"], mode == "code"
                )
                pred = parse_answer(text, p["names"])
                record = dict(
                    id=p["id"], num=p["num_people"], pred=pred,
                    gold=p["solution"], correct=pred == p["solution"],
                    source=p.get("source"), codes=codes, text=text,
                    used_python_constraint=any(
                        re.search(r"(^|\s)(from|import)\s+constraint\b", code)
                        for code in codes
                    ),
                    duration_s=round(time.monotonic() - started, 3),
                    provider_receipts=receipts,
                    provider_error=None,
                )
            except Exception as exc:
                record = dict(
                    id=p["id"], num=p["num_people"], pred=None,
                    gold=p["solution"], correct=False,
                    source=p.get("source"), codes=[], text="",
                    used_python_constraint=False,
                    duration_s=round(time.monotonic() - started, 3),
                    provider_receipts=[],
                    provider_error=f"{type(exc).__name__}: {exc}",
                )
        records.append(record)
        if checkpoint:
            checkpoint(mode, records)
        pred = record.get("pred")
        correct = bool(record.get("correct"))
        mark = "✓" if correct else "✗"
        print(f"  [{mode:6}] {p['id']} ({p['num_people']}人) {mark}  "
              f"预测={pred}")
    return records


def run_solver(puzzles):
    """离线约束求解模式：直接用 python-constraint 求解结构化陈述，无需 LLM/API。"""
    records = []
    for p in puzzles:
        struct = p.get("statements_struct")
        if not struct:
            sys.exit(f"错误：谜题 {p['id']} 缺少 statements_struct 字段，"
                     "请用新版 build_puzzles.py 重新生成 puzzles.json。")
        sols = solve_labeled(p["names"], struct)
        pred = sols[0] if len(sols) == 1 else None
        correct = pred == p["solution"]
        records.append(dict(id=p["id"], num=p["num_people"], pred=pred,
                            gold=p["solution"], correct=correct,
                            codes=[], text="", num_solutions=len(sols)))
        mark = "✓" if correct else "✗"
        print(f"  [solver] {p['id']} ({p['num_people']}人) {mark}  "
              f"解数={len(sols)}  预测={pred}")
    return records


LABELS = {"pure": "纯思考", "code": "代码辅助", "solver": "约束求解"}


def _wilson(successes, total, z=1.959963984540054):
    if total <= 0:
        return [None, None]
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [center - half, center + half]


def paired_statistics(pure, code):
    """Preregistered paired accuracy analysis (exact McNemar/binomial test)."""
    if [r["id"] for r in pure] != [r["id"] for r in code]:
        raise ValueError("paired modes do not contain the same ordered task ids")
    pure_only = sum(a["correct"] and not b["correct"] for a, b in zip(pure, code))
    code_only = sum(not a["correct"] and b["correct"] for a, b in zip(pure, code))
    discordant = pure_only + code_only
    if discordant:
        tail = sum(math.comb(discordant, i) for i in range(min(pure_only, code_only) + 1))
        p_value = min(1.0, 2 * tail / (2 ** discordant))
    else:
        p_value = 1.0
    code_ok = sum(r["correct"] for r in code)
    pure_ok = sum(r["correct"] for r in pure)
    code_accuracy = code_ok / len(code)
    pure_accuracy = pure_ok / len(pure)
    library_rate = sum(r["used_python_constraint"] for r in code) / len(code)
    return {
        "test": "two-sided exact McNemar/binomial test on discordant pairs",
        "n": len(code),
        "contingency": {"pure_only": pure_only, "code_only": code_only,
                        "discordant": discordant},
        "pure_accuracy": pure_accuracy,
        "code_accuracy": code_accuracy,
        "accuracy_delta": code_accuracy - pure_accuracy,
        "code_accuracy_wilson_95": _wilson(code_ok, len(code)),
        "p_value": p_value,
        "python_constraint_tool_use_rate": library_rate,
        "acceptance": {
            "code_accuracy_over_90_percent": code_accuracy > 0.90,
            "code_significantly_higher_than_pure": (
                code_accuracy > pure_accuracy and p_value < 0.05
            ),
            "all_code_trajectories_used_python_constraint": library_rate == 1.0,
        },
    }


def campaign_completion(results, puzzles, manifest, mode):
    """Check exact protocol execution without requiring a positive result."""
    expected_ids = [puzzle["id"] for puzzle in puzzles]
    manifest_exact = bool(
        manifest
        and manifest.get("dataset") == "K-and-K/perturbed-knights-and-knaves"
        and manifest.get("revision")
        == "bc7ee75a15ee8196ccbdb7df3ab46284340412e2"
        and (manifest.get("sampling") or {}).get("total") == 84
        and (manifest.get("sampling") or {}).get("cells") == 42
        and (manifest.get("sampling") or {}).get("per_cell") == 2
        and len(manifest.get("source_files") or []) == 42
        and manifest.get("label_validation")
        == "all rows independently solved with python-constraint"
    )
    exact_coverage = (
        len(expected_ids) == 84 and len(set(expected_ids)) == 84
    )
    errors = []
    arm_checks = {}
    for arm in ("pure", "code"):
        records = results.get(arm) or []
        arm_errors = [
            {"id": record.get("id"), "error": record.get("provider_error")}
            for record in records if record.get("provider_error")
        ]
        errors.extend({"arm": arm, **error} for error in arm_errors)
        arm_checks[f"all_{arm}_trajectories_complete"] = (
            len(records) == 84
            and [record.get("id") for record in records] == expected_ids
            and not arm_errors
            and all(record.get("provider_receipts") for record in records)
        )
    code_records = results.get("code") or []
    checks = {
        "mode_is_full_paired_campaign": mode == "both",
        "exact_pinned_stratified_dataset_manifest": manifest_exact,
        "all_84_unique_tasks_present": exact_coverage,
        **arm_checks,
        "zero_provider_errors": not errors,
        "every_code_trajectory_used_python_constraint": (
            len(code_records) == 84
            and all(record.get("used_python_constraint") for record in code_records)
        ),
    }
    return {
        "status": "complete" if all(checks.values()) else "incomplete",
        "checks": checks,
        "provider_errors": errors,
        "expected_tasks_per_arm": 84,
    }


def print_table(columns, puzzles):
    """打印多列准确率对比表。columns = [(mode, records), ...]，顺序即列顺序。"""
    accs = {m: sum(r["correct"] for r in recs) / len(recs) for m, recs in columns}
    header = f"{'题号':<8}{'人数':<6}" + "".join(f"{LABELS[m]:<10}" for m, _ in columns)
    print("\n" + "=" * 60)
    print("准确率对比表")
    print("=" * 60)
    print(header)
    print("-" * 60)
    n = len(puzzles)
    for i in range(n):
        row = f"{puzzles[i]['id']:<8}{puzzles[i]['num_people']:<6}"
        for _, recs in columns:
            row += f"{('✓' if recs[i]['correct'] else '✗'):<10}"
        print(row)
    print("-" * 60)
    tail = f"{'准确率':<8}{'':<6}" + "".join(
        f"{accs[m]*100:>6.1f}%   " for m, _ in columns)
    print(tail)
    print("=" * 60)
    for m, recs in columns:
        n_ok = sum(r["correct"] for r in recs)
        print(f"{LABELS[m]:<6} 准确率: {accs[m]*100:5.1f}%  ({n_ok}/{len(recs)})")
    # 若同时有 solver/code 与 pure，报告提升幅度
    baseline = next((m for m in ("pure",) if m in accs), None)
    best = next((m for m in ("solver", "code") if m in accs), None)
    if baseline and best and best != baseline:
        print(f"提升({LABELS[best]} - {LABELS[baseline]}): "
              f"{(accs[best]-accs[baseline])*100:+.1f} 个百分点")


def main():
    global MODEL
    ap = argparse.ArgumentParser(
        description="实验 5-2：对比纯思考 / 代码辅助 / 约束求解 三种模式求解"
                    "「骑士与无赖」逻辑谜题的准确率",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    ap.add_argument("--mode", choices=["both", "pure", "code", "solver"],
                    default="both",
                    help="运行模式：both=纯思考+代码辅助(默认)；pure=仅纯思考；"
                         "code=仅代码辅助；solver=离线约束求解基线(无需 API)")
    ap.add_argument("--model", default=MODEL,
                    help=f"LLM 模型名(默认 {MODEL}；solver 模式忽略)")
    ap.add_argument(
        "--provider",
        choices=["auto", "ollama", "openai", "openrouter", "moonshot", "ark"],
        default="auto",
        help="explicit API provider; recorded in the saved evidence",
    )
    ap.add_argument("--limit", type=int, default=0,
                    help="只跑前 N 题(0=全部)")
    ap.add_argument("--min-people", type=int, default=0,
                    help="只跑居民数 >= 该值的谜题(按难度筛选，0=不限)")
    ap.add_argument("--max-people", type=int, default=0,
                    help="只跑居民数 <= 该值的谜题(按难度筛选，0=不限)")
    ap.add_argument("--puzzles", default="puzzles.json",
                    help="谜题数据集路径(默认 puzzles.json)")
    ap.add_argument("--output", default="last_run.json",
                    help="逐题完整记录的输出路径(默认 last_run.json)")
    ap.add_argument(
        "--manifest", default=None,
        help="optional dataset manifest; defaults to the matching .manifest.json",
    )
    ap.add_argument(
        "--resume", action="store_true",
        help="resume successful per-arm rows from OUTPUT.checkpoint.json",
    )
    args = ap.parse_args()
    MODEL = args.model

    with open(args.puzzles, encoding="utf-8") as f:
        puzzles = json.load(f)
    if args.min_people:
        puzzles = [p for p in puzzles if p["num_people"] >= args.min_people]
    if args.max_people:
        puzzles = [p for p in puzzles if p["num_people"] <= args.max_people]
    if args.limit:
        puzzles = puzzles[:args.limit]
    if not puzzles:
        sys.exit("错误：筛选后没有任何谜题，请放宽 --min-people/--max-people/--limit。")

    # solver 模式完全离线，不需要 API；其余模式需要 OPENAI_API_KEY。
    llm_modes = {"both": ["pure", "code"], "pure": ["pure"],
                 "code": ["code"], "solver": []}[args.mode]
    results = {}
    checkpoint_path = Path(str(args.output) + ".checkpoint.json")
    resumed_results = {}
    if args.resume and checkpoint_path.is_file():
        prior = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if prior.get("provider") != args.provider or prior.get("model") != MODEL:
            raise ValueError("resume rejected: provider/model changed")
        if prior.get("puzzle_ids") != [puzzle["id"] for puzzle in puzzles]:
            raise ValueError("resume rejected: selected puzzle set changed")
        resumed_results = prior.get("results") or {}

    checkpoint_results = {
        arm: list(records) for arm, records in resumed_results.items()
    }

    def persist_checkpoint(arm, records):
        checkpoint_results[arm] = list(records)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text(json.dumps({
            "schema_version": "1.0", "experiment": "5-2",
            "provider": args.provider, "model": MODEL,
            "puzzle_ids": [puzzle["id"] for puzzle in puzzles],
            "results": checkpoint_results,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.mode == "solver":
        print(f"离线约束求解基线    题目数：{len(puzzles)}\n")
        print("== 约束求解(solver，离线) ==")
        results["solver"] = run_solver(puzzles)
    else:
        client, MODEL = build_client_and_model(args.provider)
        print(f"供应商：{PROVIDER}    模型：{MODEL}    题目数：{len(puzzles)}    模式：{args.mode}\n")
        for m in llm_modes:
            print(f"== {LABELS[m]}({m}) ==")
            results[m] = run_mode(
                client, puzzles, m,
                existing=resumed_results.get(m),
                checkpoint=persist_checkpoint,
            )
            print()

    # ---- 准确率对比表(按 pure -> code -> solver 的固定列序) ----
    columns = [(m, results[m]) for m in ["pure", "code", "solver"] if m in results]
    print_table(columns, puzzles)

    # ---- 展示一题的约束建模代码与求解结果 ----
    code_recs = results.get("code")
    if code_recs:
        sample = next((r for r in code_recs if r["correct"] and r["codes"]), None)
        if sample:
            print("\n" + "=" * 60)
            print(f"示例：{sample['id']} 的约束建模代码(模型生成)")
            print("=" * 60)
            print(sample["codes"][0])
            print("-- 求解 & 最终答案 --")
            print(f"预测={sample['pred']}  真值={sample['gold']}")

    # 保存完整记录，便于复盘
    puzzle_path = Path(args.puzzles)
    manifest_path = (
        Path(args.manifest) if args.manifest
        else puzzle_path.with_name(puzzle_path.stem + ".manifest.json")
    )
    manifest = None
    manifest_sha256 = None
    if manifest_path.is_file():
        import hashlib
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    payload = dict(
        schema_version="2.0",
        experiment="5-2",
        generated_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        provider=PROVIDER,
        model=MODEL,
        mode=args.mode,
        tasks=len(puzzles),
        dataset_manifest=manifest,
        dataset_manifest_sha256=manifest_sha256,
    )
    for m, recs in results.items():
        payload[m] = recs
        payload[f"{m}_acc"] = sum(r["correct"] for r in recs) / len(recs)
    if "pure" in results and "code" in results:
        payload["paired_analysis"] = paired_statistics(results["pure"], results["code"])
    payload["completion"] = campaign_completion(
        results, puzzles, manifest, args.mode
    )
    payload["official_complete"] = payload["completion"]["status"] == "complete"
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\n完整逐题记录已保存到 {args.output}")


if __name__ == "__main__":
    main()
