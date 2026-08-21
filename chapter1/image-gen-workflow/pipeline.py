"""
实验 1-4 的三条路线实现。

工作流路线（workflow）：改写节点（Kimi kimi-k3）→ 生图节点（通义万相 wan2.2-t2i-flash）
原生路线（native）：Gemini 3 Pro Image（Nano Banana 2）直接出图，一次调用
原生路线 GPT-Image 2（native_gptimage）：OpenAI gpt-image-2 直接出图，一次调用

每次真实 API 调用都产生一条 call record（模型名、请求参数、响应 ID、
用量、时间戳、耗时），绝不记录密钥。
"""

import base64
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

from config import Config

# ---------------------------------------------------------------------------
# 改写节点
# ---------------------------------------------------------------------------

REWRITE_SYSTEM_PROMPT = """\
你是 Stable Diffusion 风格的文生图提示词专家。用户会给你一句口语化的中文需求，
你需要把它改写成经典文生图模型（如 Stable Diffusion / FLUX）能消化的提示词。

要求：
1. prompt 字段：逗号分隔的英文 tag，先主体后细节，包含质量词
   （如 masterpiece, best quality, highly detailed），必要时包含画风、构图、光线、情绪词。
2. negative_prompt 字段：逗号分隔的英文负面提示词（如 lowres, bad anatomy, blurry, watermark, text 等）。
3. style_notes 字段：一句中文，说明你这次改写做了哪些关键增补/取舍。
4. 只输出一个 JSON 对象，不要输出任何其他文字。格式：
{"prompt": "...", "negative_prompt": "...", "style_notes": "..."}
"""


def parse_rewrite_output(text: str) -> Dict[str, str]:
    """把改写节点的原始输出解析为 {prompt, negative_prompt, style_notes}。

    容忍 ```json 代码围栏和前后多余文字；结构不合法时抛 ValueError。
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("改写输出为空")

    cleaned = text.strip()
    if cleaned.startswith("```"):
        # 去掉首行围栏与结尾围栏
        lines = cleaned.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    decoder = json.JSONDecoder()
    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"改写输出中没有 JSON 对象: {cleaned[:100]!r}")
    try:
        obj, _ = decoder.raw_decode(cleaned[start:])
    except json.JSONDecodeError as e:
        raise ValueError(f"改写输出不是合法 JSON: {e}") from e

    if not isinstance(obj, dict):
        raise ValueError("改写输出的 JSON 不是对象")
    prompt = obj.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("改写输出缺少非空的 prompt 字段")
    negative = obj.get("negative_prompt", "")
    if not isinstance(negative, str):
        raise ValueError("negative_prompt 字段必须是字符串")
    notes = obj.get("style_notes", "")
    if not isinstance(notes, str):
        raise ValueError("style_notes 字段必须是字符串")
    return {
        "prompt": prompt.strip(),
        "negative_prompt": negative.strip(),
        "style_notes": notes.strip(),
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_call_record(provider: str, model: str, endpoint: str) -> Dict[str, Any]:
    return {
        "call_id": uuid.uuid4().hex[:12],
        "provider": provider,
        "model": model,
        "endpoint": endpoint,
        "started_at": _utc_now(),
        "finished_at": None,
        "latency_ms": None,
        "status": "ok",
        "request": {},
        "response_id": None,
        "usage": {},
        "error": None,
    }


def _finish(record: Dict[str, Any], t0: float) -> Dict[str, Any]:
    record["finished_at"] = _utc_now()
    record["latency_ms"] = round((time.monotonic() - t0) * 1000, 1)
    return record


def rewrite_prompt(requirement: str) -> Tuple[Dict[str, str], Dict[str, Any]]:
    """工作流路线节点 1：用 Kimi 把口语化需求改写为 SD 风格提示词。"""
    from openai import OpenAI

    record = _new_call_record(
        provider="moonshot",
        model=Config.REWRITE_MODEL,
        endpoint=f"{Config.KIMI_BASE_URL}/chat/completions",
    )
    record["request"] = {
        "messages": [
            {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
            {"role": "user", "content": requirement},
        ],
        # kimi-k3 只允许 temperature=1（默认值），显式传其他值会被 400 拒绝
    }
    t0 = time.monotonic()
    try:
        client = OpenAI(api_key=Config.KIMI_API_KEY, base_url=Config.KIMI_BASE_URL)
        resp = client.chat.completions.create(
            model=Config.REWRITE_MODEL,
            messages=record["request"]["messages"],
        )
        record["response_id"] = resp.id
        record["usage"] = resp.usage.model_dump() if resp.usage else {}
        raw = resp.choices[0].message.content or ""
        record["raw_output"] = raw
        return parse_rewrite_output(raw), _finish(record, t0)
    except Exception as e:  # 记录失败同样留证
        record["status"] = "error"
        record["error"] = f"{type(e).__name__}: {e}"
        _finish(record, t0)
        raise RuntimeError(f"改写节点调用失败: {e}") from e


# ---------------------------------------------------------------------------
# 工作流路线节点 2：DashScope 通义万相（异步任务）
# ---------------------------------------------------------------------------


def generate_image_wanx(
    prompt: str, negative_prompt: str = ""
) -> Tuple[bytes, str, List[Dict[str, Any]]]:
    """提交万相文生图异步任务并轮询取图。返回 (图片字节, mime, call records)。"""
    headers = {
        "Authorization": f"Bearer {Config.DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    submit_url = f"{Config.DASHSCOPE_BASE_URL}/services/aigc/text2image/image-synthesis"

    submit = _new_call_record("dashscope", Config.WANX_MODEL, submit_url)
    submit["request"] = {
        "input": {"prompt": prompt, "negative_prompt": negative_prompt},
        "parameters": {"size": Config.WANX_SIZE, "n": 1},
    }
    t0 = time.monotonic()
    try:
        r = requests.post(
            submit_url,
            headers=headers,
            json={"model": Config.WANX_MODEL, **submit["request"]},
            timeout=60,
        )
        body = r.json()
        submit["response_id"] = body.get("request_id")
        if r.status_code != 200 or "output" not in body:
            raise RuntimeError(f"任务提交失败 HTTP {r.status_code}: {body}")
        task_id = body["output"]["task_id"]
        submit["task_id"] = task_id
        _finish(submit, t0)
    except Exception as e:
        submit["status"] = "error"
        submit["error"] = f"{type(e).__name__}: {e}"
        _finish(submit, t0)
        raise

    poll_url = f"{Config.DASHSCOPE_BASE_URL}/tasks/{task_id}"
    poll = _new_call_record("dashscope", Config.WANX_MODEL, poll_url)
    poll["task_id"] = task_id
    t0 = time.monotonic()
    deadline = t0 + Config.TASK_POLL_TIMEOUT
    try:
        while True:
            time.sleep(Config.TASK_POLL_INTERVAL)
            r = requests.get(poll_url, headers=headers, timeout=30)
            body = r.json()
            status = body.get("output", {}).get("task_status")
            if status == "SUCCEEDED":
                break
            if status in ("FAILED", "CANCELED"):
                raise RuntimeError(f"任务失败: {body}")
            if time.monotonic() > deadline:
                raise TimeoutError(f"轮询超时（{Config.TASK_POLL_TIMEOUT}s），最后状态 {status}")
        poll["response_id"] = body.get("request_id")
        poll["usage"] = body.get("usage", {})
        poll["task_metrics"] = {
            k: body["output"].get(k)
            for k in ("submit_time", "scheduled_time", "end_time")
        }
        result = body["output"]["results"][0]
        image_url = result["url"]
        poll["actual_prompt"] = result.get("actual_prompt")
        _finish(poll, t0)
    except Exception as e:
        poll["status"] = "error"
        poll["error"] = f"{type(e).__name__}: {e}"
        _finish(poll, t0)
        raise

    dl = _new_call_record("dashscope", Config.WANX_MODEL, image_url.split("?")[0])
    t0 = time.monotonic()
    r = requests.get(image_url, timeout=60)
    r.raise_for_status()
    mime = r.headers.get("Content-Type", "image/png").split(";")[0]
    dl["response_bytes"] = len(r.content)
    _finish(dl, t0)
    return r.content, mime, [submit, poll, dl]


# ---------------------------------------------------------------------------
# 原生路线：Gemini 3 Pro Image（Nano Banana 2）原生图像生成
# ---------------------------------------------------------------------------


def generate_image_gemini(
    requirement: str,
) -> Tuple[bytes, str, Dict[str, Any], Optional[str]]:
    """把口语化需求原样发给 Gemini 3 Pro Image（Nano Banana 2），一次调用直接出图。

    返回 (图片字节, mime, call record, 模型附带文本)。
    """
    from google import genai
    from google.genai import types

    record = _new_call_record(
        provider="google",
        model=Config.GEMINI_IMAGE_MODEL,
        endpoint="google-genai: models.generate_content",
    )
    record["request"] = {
        "contents": requirement,
        "config": {"response_modalities": ["IMAGE"]},
    }
    t0 = time.monotonic()
    try:
        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        resp = client.models.generate_content(
            model=Config.GEMINI_IMAGE_MODEL,
            contents=requirement,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )
        record["response_id"] = getattr(resp, "response_id", None)
        if resp.usage_metadata:
            record["usage"] = {
                "prompt_tokens": resp.usage_metadata.prompt_token_count,
                "candidates_tokens": resp.usage_metadata.candidates_token_count,
                "total_tokens": resp.usage_metadata.total_token_count,
            }
        image_bytes, mime, text = None, None, None
        for cand in resp.candidates or []:
            content = getattr(cand, "content", None)
            if not content:
                continue
            for part in content.parts or []:
                if getattr(part, "inline_data", None) and part.inline_data.data:
                    raw = part.inline_data.data
                    image_bytes = (
                        base64.b64decode(raw) if isinstance(raw, str) else bytes(raw)
                    )
                    mime = part.inline_data.mime_type or "image/png"
                elif getattr(part, "text", None):
                    text = part.text
        if image_bytes is None:
            raise RuntimeError(f"响应中没有图片部分（text={text!r}）")
        _finish(record, t0)
        return image_bytes, mime, record, text
    except Exception as e:
        record["status"] = "error"
        record["error"] = f"{type(e).__name__}: {e}"
        _finish(record, t0)
        raise RuntimeError(f"原生路线调用失败: {e}") from e


# ---------------------------------------------------------------------------
# 原生路线 B：OpenAI GPT-Image 2
# ---------------------------------------------------------------------------


def generate_image_gpt_image(
    requirement: str,
) -> Tuple[bytes, str, Dict[str, Any]]:
    """把口语化需求原样发给 OpenAI 图像接口。返回 (图片字节, mime, call record)。"""
    from openai import OpenAI

    record = _new_call_record(
        provider="openai",
        model=Config.GPT_IMAGE_MODEL,
        endpoint=f"{Config.OPENAI_BASE_URL}/images/generations",
    )
    record["request"] = {"prompt": requirement, "size": "1024x1024", "n": 1}
    t0 = time.monotonic()
    try:
        client = OpenAI(
            api_key=Config.OPENAI_API_KEY, base_url=Config.OPENAI_BASE_URL
        )
        resp = client.images.generate(
            model=Config.GPT_IMAGE_MODEL,
            prompt=requirement,
            size="1024x1024",
            n=1,
        )
        record["response_id"] = str(getattr(resp, "created", "")) or None
        if getattr(resp, "usage", None):
            record["usage"] = resp.usage.model_dump()
        datum = resp.data[0]
        if getattr(datum, "b64_json", None):
            image_bytes = base64.b64decode(datum.b64_json)
        elif getattr(datum, "url", None):
            dl = requests.get(datum.url, timeout=60)
            dl.raise_for_status()
            image_bytes = dl.content
        else:
            raise RuntimeError("响应中既没有 b64_json 也没有 url")
        _finish(record, t0)
        return image_bytes, "image/png", record
    except Exception as e:
        record["status"] = "error"
        record["error"] = f"{type(e).__name__}: {e}"
        _finish(record, t0)
        raise RuntimeError(f"GPT-Image 原生路线调用失败: {e}") from e


# ---------------------------------------------------------------------------
# 三条路线的编排
# ---------------------------------------------------------------------------


def run_workflow_route(requirement: str) -> Dict[str, Any]:
    """工作流路线：改写 → 生图。返回 run 记录（含各节点 call records）。"""
    nodes: List[Dict[str, Any]] = []

    rewrite, rec = rewrite_prompt(requirement)
    nodes.append({"node": "rewrite", "call": rec, "output": rewrite})

    image_bytes, mime, recs = generate_image_wanx(
        rewrite["prompt"], rewrite["negative_prompt"]
    )
    nodes.append(
        {
            "node": "image_generate",
            "calls": recs,
            "output": {
                "prompt_used": rewrite["prompt"],
                "negative_prompt_used": rewrite["negative_prompt"],
            },
        }
    )
    return {
        "route": "workflow",
        "rewrite": rewrite,
        "image_bytes": image_bytes,
        "mime": mime,
        "nodes": nodes,
        "error": None,
    }


def run_native_route(requirement: str) -> Dict[str, Any]:
    """原生路线：一次调用直接出图。"""
    image_bytes, mime, rec, text = generate_image_gemini(requirement)
    return {
        "route": "native",
        "rewrite": None,
        "image_bytes": image_bytes,
        "mime": mime,
        "nodes": [{"node": "native_generate", "call": rec, "output": {"text": text}}],
        "error": None,
    }


def run_native_gpt_image_route(requirement: str) -> Dict[str, Any]:
    """原生路线 B：GPT-Image 2（gpt-image-2）一次调用直接出图。"""
    image_bytes, mime, rec = generate_image_gpt_image(requirement)
    return {
        "route": "native_gptimage",
        "rewrite": None,
        "image_bytes": image_bytes,
        "mime": mime,
        "nodes": [{"node": "native_generate", "call": rec, "output": {"text": None}}],
        "error": None,
    }


ROUTE_RUNNERS = {
    "workflow": run_workflow_route,
    "native": run_native_route,
    "native_gptimage": run_native_gpt_image_route,
}
