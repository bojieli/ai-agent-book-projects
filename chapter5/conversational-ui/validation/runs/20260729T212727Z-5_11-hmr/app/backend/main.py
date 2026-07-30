"""实验 5-11：对话式界面定制系统 —— FastAPI 后端。

一个最小的 chatbot 后端：前端把用户消息 POST 到 /api/chat，后端返回回复。
开发模式下用 `uvicorn main:app --reload` 启动，改动后端代码会自动 reload
（对应书中所说的"FastAPI 的热加载"）。

两种回复模式（默认保持"回声式"占位，聚焦 UI 定制这一主题）：
  - **echo（默认）**：后端把用户消息原样回显，无需任何模型 Key，开箱即用；
  - **llm（可选）**：设置模型后走真实 LLM 对话，让运行起来的 chatbot 真会说话。
    通过命令行 `--model` 或环境变量 `CHAT_MODEL` 打开，复用与 agent.py 相同的
    OPENAI_API_KEY / OPENAI_BASE_URL 配置。

启动方式（二选一，行为一致）：
  uvicorn main:app --reload --port 8000      # 书中示例：模块级 app + uvicorn 热加载
  python main.py --reload --port 8000        # 本文件自带的命令行入口（见 --help）
"""

import os
import argparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:  # dotenv 可选：让 --model 模式也能读到 .env 里的 OPENAI_API_KEY
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

app = FastAPI(title="Conversational UI Backend")

# 允许前端(Vite dev server, 5173)直接跨域访问，方便本地开发。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


def _chat_model() -> str:
    """当前回复模式：返回模型名则走真实 LLM，返回空串则为默认 echo 模式。

    从环境变量 CHAT_MODEL 读取（而非模块级常量），这样即使 `--reload` 触发的
    子进程重新 import 本模块，也能透过环境变量拿到命令行传入的模型设置。
    """
    return (os.getenv("CHAT_MODEL") or "").strip()


def _llm_reply(message: str, model: str) -> str:
    """走真实 LLM 生成回复，复用 agent.py 同款 OPENAI_* 配置。

    任何异常都降级为清晰的提示（绝不编造回复），保证前端不至于白屏。
    """
    try:
        from openai import OpenAI
    except Exception:
        return "（未安装 openai 依赖，无法启用 LLM 模式；已回退占位回复）"

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    orkey = os.getenv("OPENROUTER_API_KEY")
    # 通用 OpenRouter 兜底：无直连 key，或 gpt-5.x（直连需组织实名认证）时改走 OpenRouter。
    prefer_or = bool(orkey) and (model or "").lower().startswith("gpt-5")
    if prefer_or or (not api_key and orkey):
        api_key, base_url = orkey, "https://openrouter.ai/api/v1"
        if "/" not in model:
            model = ("openai/" + model) if model.lower().startswith(("gpt-", "o1", "o3", "o4")) else "openai/gpt-5.6-luna"
    if not api_key:
        return "（未配置 OPENAI_API_KEY 或 OPENROUTER_API_KEY，无法启用 LLM 模式；已回退占位回复）"

    client_kwargs = {"api_key": api_key, "timeout": 60.0, "max_retries": 2}
    if base_url:
        client_kwargs["base_url"] = base_url

    try:
        client = OpenAI(**client_kwargs)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个乐于助人的中文智能助手，回答简洁友好。"},
                {"role": "user", "content": message},
            ],
            temperature=(1 if any(k in (model or "").lower()
                                  for k in ("gpt-5", "o1", "o3", "o4", "thinking", "reasoner", "kimi-k3"))
                         else 0.7),
        )
        return resp.choices[0].message.content or "（模型返回了空回复）"
    except Exception as e:  # 网络/鉴权/模型名等问题都在此兜底
        return f"（调用 LLM 失败：{e}；已回退占位回复）"


@app.get("/api/health")
def health():
    model = _chat_model()
    return {"status": "ok", "mode": "llm" if model else "echo", "model": model or None}


@app.post("/api/chat")
def chat(req: ChatRequest):
    """默认回声式回复；设置 CHAT_MODEL 后走真实 LLM 对话。

    本实验聚焦"对话式 UI 定制"，后端逻辑刻意保持最小；
    如需真实客服体验，用 `python main.py --model <模型名>` 打开 LLM 模式即可。
    """
    model = _chat_model()
    if model:
        return {"reply": _llm_reply(req.message, model)}
    return {"reply": f"我收到了你的消息：{req.message}"}


# ---------------------------------------------------------------------------
# 命令行入口：让后端既能 `uvicorn main:app --reload` 启动，也能 `python main.py`
# 启动，并通过参数控制 host/port/热加载/回复模式/日志。
# ---------------------------------------------------------------------------
def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="实验 5-11：对话式界面定制系统 —— FastAPI 后端（最小 chatbot 服务）。"
        "为可对话定制的前端提供 /api/chat 载体，开发模式下配合 --reload 演示后端热加载。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="监听地址；对外可用 0.0.0.0。",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="监听端口（前端 vite.config.js 默认把 /api 代理到 8000）。",
    )
    reload_group = parser.add_mutually_exclusive_group()
    reload_group.add_argument(
        "--reload",
        dest="reload",
        action="store_true",
        default=True,
        help="开启热加载：改动后端 .py 自动重启（开发默认开启）。",
    )
    reload_group.add_argument(
        "--no-reload",
        dest="reload",
        action="store_false",
        help="关闭热加载（更接近生产运行）。",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("CHAT_MODEL") or None,
        metavar="NAME",
        help="打开真实 LLM 对话并指定模型名（如 gpt-5.6-luna）；"
        "缺省则为默认的 echo 回声模式。也可用环境变量 CHAT_MODEL 设置。",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="uvicorn 日志/输出级别。",
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="只打印生效配置(JSON)后退出，不真正监听端口（便于无网络/无端口环境下校验）。",
    )
    return parser.parse_args(argv)


def main(argv=None):
    import json

    args = parse_args(argv)

    # 把 --model 写回环境变量：这样 --reload 派生的子进程重新 import 本模块时，
    # 也能通过 CHAT_MODEL 感知到 LLM 模式（子进程不共享本函数的局部状态）。
    if args.model:
        os.environ["CHAT_MODEL"] = args.model
    else:
        os.environ.pop("CHAT_MODEL", None)

    config = {
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
        "mode": "llm" if args.model else "echo",
        "model": args.model,
        "log_level": args.log_level,
    }

    if args.print_config:
        print(json.dumps(config, ensure_ascii=False, indent=2))
        return 0

    import uvicorn

    print(
        f"启动 FastAPI 后端：http://{args.host}:{args.port}"
        f"  模式={config['mode']}"
        f"  热加载={'开' if args.reload else '关'}"
    )
    # 用 import string 才能在 --reload 下工作；从 backend/ 目录运行 `python main.py`。
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
