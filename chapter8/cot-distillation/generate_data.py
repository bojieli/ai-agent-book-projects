"""
CoT 蒸馏数据采集脚本（实验 7-9 配套代码）

方法（对应书中实验 7-9 的三步流程之第一步"采集轨迹"）：
  1. 从 problems.jsonl 读取带标准答案的数学题（规则可验证的任务分布）；
  2. 通过 OpenRouter 调用前沿教师模型（默认 Claude），开启 reasoning 获取
     完整"思考 + 答案"轨迹（Claude 4 系列返回的是 summarized thinking——由另一个
     模型对原始思维链做的高保真摘要，原始思维链只存在于加密的 signature 字段中）；
  3. 用规则验证器核对最终答案，只把答对的轨迹写成 SFT 训练数据
     （"问题 → <think>思考</think> + 最终答案" 的 messages 格式）。

注意：本实验只使用各厂商官方 API 的 reasoning/thinking 能力获取思维链，
不涉及任何绕过厂商安全机制的手段。原始轨迹（含未通过验证的）保存在
raw_trajectories.jsonl，便于分析教师的错误模式。
"""

import argparse
import asyncio
import json
import os
import re
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI

ANSWER_SUFFIX = "\n\n请一步步推理，并在最后一行用「Final Answer: 数值」的格式给出最终答案（只写数值，不带单位）。"

def load_problems(path: str) -> list[dict]:
    problems = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                problems.append(json.loads(line))
    return problems


def load_jsonl(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl_atomic(path: str | Path, rows: list[dict]) -> None:
    """Replace a JSONL file without exposing a partially rewritten dataset."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def records_in_problem_order(problems: list[dict], records_by_id: dict[str, dict]) -> list[dict]:
    """Return canonical problem order while retaining any legacy extra records."""
    known_ids = [str(problem["id"]) for problem in problems]
    rows = [records_by_id[problem_id] for problem_id in known_ids if problem_id in records_by_id]
    rows.extend(record for problem_id, record in records_by_id.items() if problem_id not in known_ids)
    return rows


def extract_predicted_number(text: str) -> Optional[float]:
    """从模型输出中解析最终答案数值。优先匹配 Final Answer 标记，否则取最后一个数字。"""
    m = re.findall(r"Final Answer[:：]\s*(-?[\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
    if not m:
        m = re.findall(r"-?[\d,]+(?:\.\d+)?", text)
    if not m:
        return None
    try:
        return float(m[-1].replace(",", ""))
    except ValueError:
        return None


def verify(text: str, gold: float, tol: float = 1e-6) -> bool:
    """规则验证器：核对最终答案是否与标准答案一致。"""
    pred = extract_predicted_number(text)
    if pred is None:
        return False
    return abs(pred - float(gold)) <= tol * max(1.0, abs(float(gold)))


def get_reasoning(message) -> str:
    """从返回的 message 中提取思维链。

    依次尝试：OpenRouter 的 reasoning / reasoning_details 字段，
    以及 Moonshot、DeepSeek 等原生 API 的 reasoning_content 字段。
    """
    reasoning = getattr(message, "reasoning", None)
    if reasoning:
        return reasoning
    reasoning_content = getattr(message, "reasoning_content", None)
    if reasoning_content:
        return reasoning_content
    details = getattr(message, "reasoning_details", None) or []
    parts = []
    for d in details:
        if isinstance(d, dict):
            parts.append(d.get("text") or d.get("summary") or "")
        else:
            parts.append(getattr(d, "text", None) or getattr(d, "summary", None) or "")
    return "\n".join(p for p in parts if p)


def reasoning_extra_body(base_url: str, effort: str, max_tokens: int) -> dict:
    """Build the provider-specific reasoning control without silently ignoring it."""
    if effort:
        if "api.moonshot.cn" in base_url:
            # Moonshot's native OpenAI-compatible endpoint accepts the same
            # top-level control used by the Experiment 7-8 Kimi campaign.
            return {"reasoning_effort": effort}
        return {"reasoning": {"effort": effort}}
    if max_tokens:
        return {"reasoning": {"max_tokens": max_tokens}}
    return {}


async def distill_one(client: AsyncOpenAI, problem: dict, args, semaphore) -> dict:
    """对单道题调用教师模型，返回完整轨迹记录。"""
    record = {
        "id": problem["id"],
        "question": problem["question"],
        "gold_answer": problem["answer"],
        "model": args.model,
        "content": None,
        "reasoning": None,
        "verified": False,
        "usage": None,
        "error": None,
        "attempts": [],
    }
    async with semaphore:
        for attempt in range(args.max_retries + 1):
            try:
                kwargs = {}
                reasoning_body = reasoning_extra_body(
                    args.base_url, args.reasoning_effort, args.reasoning_max_tokens
                )
                if reasoning_body:
                    kwargs["extra_body"] = reasoning_body
                resp = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=args.model,
                        messages=[{"role": "user", "content": problem["question"] + args.answer_suffix}],
                        max_tokens=args.max_tokens,
                        # 重试时升温换取不同轨迹；Kimi K3 等锁定 temperature=1 的模型除外
                        temperature=args.temperature + (0.2 * attempt if args.temperature < 1.0 else 0),
                        **kwargs,
                    ),
                    timeout=args.request_timeout,  # 硬超时：防止半开连接挂死
                )
                msg = resp.choices[0].message
                record["content"] = msg.content or ""
                record["reasoning"] = get_reasoning(msg)
                record["usage"] = resp.usage.model_dump() if resp.usage else None
                record["verified"] = verify(record["content"], problem["answer"])
                record["error"] = None
                record["attempts"].append({
                    "attempt": attempt,
                    "content": record["content"],
                    "reasoning": record["reasoning"],
                    "usage": record["usage"],
                    "verified": record["verified"],
                    "error": None,
                })
                if record["verified"]:
                    break
            except Exception as e:
                record["error"] = f"attempt {attempt}: {type(e).__name__}: {e}"
                record["attempts"].append({
                    "attempt": attempt,
                    "content": None,
                    "reasoning": None,
                    "usage": None,
                    "verified": False,
                    "error": record["error"],
                })
        status = "OK" if record["verified"] else ("ERR" if record["error"] else "WRONG")
        print(f"  [{status}] {record['id']}", flush=True)
        return record


def to_sft_sample(record: dict) -> dict:
    """把验证通过的轨迹转成 SFT 训练样本（messages 格式，思考包在 <think> 标签里）。"""
    if record["reasoning"]:
        assistant = f"<think>\n{record['reasoning'].strip()}\n</think>\n\n{record['content'].strip()}"
    else:
        assistant = record["content"].strip()
    return {
        "messages": [
            {"role": "user", "content": record["question"]},
            {"role": "assistant", "content": assistant},
        ]
    }


async def main():
    parser = argparse.ArgumentParser(
        description="用前沿云模型（经 OpenRouter）蒸馏 CoT 轨迹，生成 SFT 数据",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", default="./problems.jsonl", help="题目文件（JSONL，含 question/answer）")
    parser.add_argument("--sft_output", default="./data/sft_cot_distill.jsonl", help="SFT 训练数据输出路径")
    parser.add_argument("--raw_output", default="./data/raw_trajectories.jsonl", help="原始轨迹（含失败样本）输出路径")
    parser.add_argument("--model", default="anthropic/claude-opus-4.8", help="教师模型 ID")
    parser.add_argument("--base_url", default="https://openrouter.ai/api/v1", help="OpenAI 兼容 API 端点")
    parser.add_argument("--api_key_env", default="OPENROUTER_API_KEY", help="存放 API Key 的环境变量名")
    parser.add_argument("--reasoning_effort", default="",
                        help="OpenRouter 风格 reasoning effort（如 high/medium/low；设置后优先于 --reasoning_max_tokens，"
                             "用于 Claude Opus 4.8 等只支持自适应思考的模型）")
    parser.add_argument("--reasoning_max_tokens", type=int, default=4096,
                        help="思维链最大 token 数（OpenRouter 风格 reasoning 参数；0 = 不传该参数，"
                             "用于 Moonshot/DeepSeek 等默认返回 reasoning_content 的原生 API）")
    parser.add_argument("--max_problems", type=int, default=0, help="最多处理多少题（0 = 全部，调试用）")
    parser.add_argument(
        "--problem-id",
        action="append",
        default=[],
        help="只运行指定题目 ID；可重复传入。用于定点重试而不重跑整套题",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="保留 raw_output 中已验证记录，只重试缺失或未验证题目，并原子更新数据集",
    )
    parser.add_argument("--concurrency", type=int, default=8, help="并发请求数")
    parser.add_argument("--temperature", type=float, default=0.3, help="采样温度")
    parser.add_argument("--max_tokens", type=int, default=8192, help="单条回复最大 token 数（须大于 reasoning tokens）")
    parser.add_argument("--max_retries", type=int, default=1, help="失败/出错后的最大重试次数")
    parser.add_argument("--request_timeout", type=float, default=600, help="单次请求超时（秒），超时后按失败重试")
    parser.add_argument("--answer_suffix", default=ANSWER_SUFFIX, help="附加在题目后的作答格式要求")
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise SystemExit(f"请先设置环境变量 {args.api_key_env}")

    all_problems = load_problems(args.input)
    problem_ids = {str(problem["id"]) for problem in all_problems}
    requested_ids = set(args.problem_id)
    unknown_ids = sorted(requested_ids - problem_ids)
    if unknown_ids:
        raise SystemExit(f"未知题目 ID: {', '.join(unknown_ids)}")
    problems = [
        problem for problem in all_problems
        if not requested_ids or str(problem["id"]) in requested_ids
    ]
    if args.max_problems:
        problems = problems[: args.max_problems]

    existing_rows = load_jsonl(args.raw_output) if args.resume else []
    records_by_id = {
        str(record["id"]): record for record in existing_rows if record.get("id") is not None
    }
    pending = [
        problem for problem in problems
        if not records_by_id.get(str(problem["id"]), {}).get("verified", False)
    ]
    print(
        f"选中 {len(problems)} 道题，待运行 {len(pending)} 道，"
        f"教师模型：{args.model} @ {args.base_url}"
    )

    client = AsyncOpenAI(base_url=args.base_url, api_key=api_key, timeout=args.request_timeout)
    semaphore = asyncio.Semaphore(args.concurrency)

    # 每题完成后原子替换：中断最多损失当前请求，不会破坏已有数据集。
    run_records = []
    tasks = [distill_one(client, p, args, semaphore) for p in pending]
    for coro in asyncio.as_completed(tasks):
        record = await coro
        previous = records_by_id.get(str(record["id"]))
        if previous and not previous.get("verified", False):
            prior_failures = list(previous.get("prior_failures") or [])
            prior_failures.append({
                "model": previous.get("model"),
                "verified": False,
                "error": previous.get("error"),
                "usage": previous.get("usage"),
            })
            record["prior_failures"] = prior_failures
        records_by_id[str(record["id"])] = record
        run_records.append(record)
        write_jsonl_atomic(
            args.raw_output,
            records_in_problem_order(all_problems, records_by_id),
        )

    records = records_in_problem_order(all_problems, records_by_id)
    write_jsonl_atomic(args.raw_output, records)
    passed = [record for record in records if record.get("verified", False)]
    write_jsonl_atomic(args.sft_output, [to_sft_sample(record) for record in passed])

    total_in = sum((r["usage"] or {}).get("prompt_tokens", 0) for r in run_records)
    total_out = sum((r["usage"] or {}).get("completion_tokens", 0) for r in run_records)
    n_err = sum(1 for r in run_records if r["error"])
    print(f"\n{'=' * 50}")
    # Empty problems JSONL yields zero records; avoid ZeroDivisionError on the rate.
    pass_rate = (len(passed) / len(records) * 100) if records else 0.0
    print(f"数据集验证通过：{len(passed)}/{len(records)}（{pass_rate:.1f}%）")
    print(
        f"本次请求：{len(run_records)}  API 最终出错：{n_err}  "
        f"无思维链返回：{sum(1 for r in run_records if not r['reasoning'])}"
    )
    print(f"本次 Token 消耗：输入 {total_in}，输出 {total_out}")
    print(f"SFT 数据已写入：{args.sft_output}")
    print(f"原始轨迹已写入：{args.raw_output}")


if __name__ == "__main__":
    asyncio.run(main())
