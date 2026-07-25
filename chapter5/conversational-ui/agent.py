"""实验 5-11：对话式界面定制 Agent。

职责：接收一条自然语言 UI 定制需求（如"把发送按钮改成蓝色"），读取前端源码，
调用 OpenAI 让模型定位并改写相应源文件（颜色 / 字体 / 文案 / 布局 / 组件）。

设计要点
--------
- 只暴露少量"可定制文件"给模型（frontend/src 下的 App.jsx 与 theme.css），
  降低模型改错文件的概率，也让改动可控、可验证。
- 通过 function calling 的 `apply_edits` 工具，让模型返回"要整体改写的文件全文"。
  相比零散的 search/replace，整文件改写对小文件更稳定、更少破坏语法。
- 修改前先把原文件内容快照下来，改后可计算 diff、读回断言，并跑构建验证。

环境变量:
  OPENAI_API_KEY   （必填，本实验读取此项）
  OPENAI_BASE_URL  （可选，切换到兼容 OpenAI 协议的服务端点）
  MODEL            （可选，默认 gpt-5.6-luna）
  OPENROUTER_API_KEY（可选，无直连 key 时自动改走 OpenRouter 兜底）
"""

import os
import json
from pathlib import Path

from openai import OpenAI

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # dotenv 是可选依赖
    pass


# 可被 Agent 定制的前端源文件（相对 frontend/ 的路径）。
EDITABLE_FILES = [
    "src/App.jsx",
    "src/theme.css",
]


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


def build_client_and_model():
    model = os.getenv("MODEL", "gpt-5.6-luna")
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    orkey = os.getenv("OPENROUTER_API_KEY")
    # 通用 OpenRouter 兜底：无直连 key，或默认 gpt-5.x（直连需组织实名认证）时改走 OpenRouter。
    prefer_or = bool(orkey) and (model or "").lower().startswith("gpt-5")
    if prefer_or or (not api_key and orkey):
        api_key, base_url, model = orkey, OPENROUTER_BASE_URL, map_model_to_openrouter(model)
    if not api_key:
        raise SystemExit("未找到 OPENAI_API_KEY（或 OPENROUTER_API_KEY 兜底），请先在环境变量或 .env 中设置。")
    # timeout / max_retries：让偶发的网络/SSL 抖动自动重试，不至于整轮崩溃
    client_kwargs = {"api_key": api_key, "timeout": 60.0, "max_retries": 3}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)
    return client, model


APPLY_EDITS_TOOL = {
    "type": "function",
    "function": {
        "name": "apply_edits",
        "description": (
            "根据用户的界面定制需求，改写一个或多个前端源文件。"
            "只返回真正需要改动的文件；每个文件返回改写后的完整内容。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "用一句话说明本次改了什么（中文）。",
                },
                "files": {
                    "type": "array",
                    "description": "需要改写的文件列表。",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "相对 frontend/ 的文件路径，"
                                "必须是可编辑文件之一。",
                            },
                            "content": {
                                "type": "string",
                                "description": "改写后的文件完整内容。",
                            },
                        },
                        "required": ["path", "content"],
                    },
                },
            },
            "required": ["summary", "files"],
        },
    },
}


SYSTEM_PROMPT = """你是一个前端界面定制 Agent，负责把用户的自然语言 UI 需求落到 React(Vite) 源码上。

规则：
1. 只能修改用户提供的"可编辑文件"，不要新增或删除文件。
2. 优先做最小改动：改颜色/字体/间距等样式，改 theme.css；改文案/组件结构，改 App.jsx。
3. 颜色请使用明确的 CSS 颜色值（如十六进制 #2563eb）。如果用户给了具体色值，就用它。
4. 保持代码可编译：JSX/CSS 语法必须正确，不要破坏原有功能。
5. 必须调用 apply_edits 工具返回结果，files 里给出改写后的完整文件内容。
"""


def read_editable_sources(frontend_dir: Path) -> dict:
    """读取所有可编辑文件当前内容，返回 {相对路径: 内容}。"""
    sources = {}
    for rel in EDITABLE_FILES:
        p = frontend_dir / rel
        sources[rel] = p.read_text(encoding="utf-8")
    return sources


def customize(client, model, frontend_dir: Path, requirement: str) -> dict:
    """让模型针对一条自然语言需求改写源码，返回 apply_edits 的参数 dict。

    仅调用模型并解析工具参数，不落盘（写文件、验证在 demo.py 里做，便于展示 diff）。
    """
    sources = read_editable_sources(frontend_dir)

    file_blocks = "\n\n".join(
        f"===== 文件: {rel} =====\n{content}" for rel, content in sources.items()
    )
    user_prompt = (
        f"可编辑文件当前内容如下：\n\n{file_blocks}\n\n"
        f"用户的定制需求：{requirement}\n\n"
        f"请调用 apply_edits 返回需要改写的文件全文。"
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        tools=[APPLY_EDITS_TOOL],
        tool_choice={"type": "function", "function": {"name": "apply_edits"}},
        temperature=(1 if any(k in (model or "").lower()
                              for k in ("gpt-5", "o1", "o3", "o4", "thinking", "reasoner", "kimi-k3"))
                     else 0),
    )

    msg = resp.choices[0].message
    if not msg.tool_calls:
        raise RuntimeError("模型没有返回 apply_edits 工具调用。")
    raw_args = msg.tool_calls[0].function.arguments or "{}"
    try:
        args = json.loads(raw_args)
    except json.JSONDecodeError:
        # Tolerate bad apply_edits JSON; degrade to empty edits.
        args = {}

    # 安全校验：只允许改写白名单内的文件。
    files = [f for f in (args.get("files") or []) if isinstance(f, dict)]
    for f in files:
        path = f.get("path")
        if path not in EDITABLE_FILES:
            raise RuntimeError(f"模型试图修改非白名单文件：{path}")
    args["files"] = files
    return args
