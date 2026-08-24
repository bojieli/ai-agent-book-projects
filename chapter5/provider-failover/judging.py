"""判定一次恢复算不算成功。

单独放一个模块，是因为运行时判过一次之后，汇总时还要从留下的原始数据重判一次
——判定口径改了不必重跑整场活动。
"""

from __future__ import annotations

import json
import re

import tools

RESEND, PREFILL, META = "resend", "prefill", "meta"
REASONING, TEXT, TOOL_ARGS = "reasoning", "text", "tool_args"
EXPECTED_ARGS = tools.TRUNCATED_CALL_ARGS


def judge(break_point: str, strategy: str, partial: dict, result: dict,
          executed_fingerprint: str = "") -> dict:
    """``partial`` 是切断时手上那一截，``result`` 是恢复请求的产物。

    ``executed_fingerprint`` 是断点之前已经真的执行过的那次调用，恢复时再调一次
    就是重复副作用。
    """
    verdict = {"recovered": False, "json_valid": None, "args_correct": None,
               "duplicate_side_effects": 0}
    for call in result.get("tool_calls") or []:
        args = json.dumps(call.get("arguments") or {}, sort_keys=True, ensure_ascii=False)
        if f"{call.get('name')}({args})" == executed_fingerprint:
            verdict["duplicate_side_effects"] += 1

    text = result.get("text") or ""
    if break_point == TOOL_ARGS:
        if strategy == PREFILL:
            # 续写只给出后半截，要和断点处那一截拼起来才是完整参数。
            spliced = (partial.get("tool_args") or "") + text
            match = re.search(r"\{.*?\}", spliced, re.S)
            args = None
            if match:
                try:
                    args = json.loads(match.group(0))
                except json.JSONDecodeError:
                    args = None
            verdict["spliced"] = spliced[:200]
            verdict["json_valid"] = args is not None
            verdict["args_correct"] = args == EXPECTED_ARGS
            verdict["recovered"] = args is not None
        else:
            calls = result.get("tool_calls") or []
            args = calls[0].get("arguments") if calls else None
            verdict["json_valid"] = args is not None
            verdict["args_correct"] = args == EXPECTED_ARGS
            verdict["recovered"] = args is not None
    elif break_point == TEXT:
        # 整轮重发把半截丢掉重写，另外两种都是接着已有的半截往下写。
        head = "" if strategy == RESEND else (partial.get("text") or "")
        combined = head + text
        verdict["recovered"] = len(combined) > len(partial.get("text") or "") + 10
        verdict["combined_chars"] = len(combined)
        verdict["answer_correct"] = _answer_ok(combined)
    else:
        verdict["recovered"] = bool(text or result.get("tool_calls"))
    return verdict


def _answer_ok(text: str) -> bool:
    return tools.answer_is_correct(text or "")
