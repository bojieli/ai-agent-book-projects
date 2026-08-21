"""Google Gemini 原生文生图封装，带留证。

密钥只从环境变量 GEMINI_API_KEY 读取。
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from receipts import ReceiptBook, utc_now

IMAGE_MODEL = "gemini-2.5-flash-image"


def generate_image(prompt: str, out_path: Path, book: ReceiptBook, name: str) -> Path:
    """调用 Gemini 生成图片并保存为 PNG，返回路径。"""
    from google import genai

    out_path.parent.mkdir(parents=True, exist_ok=True)
    started = utc_now()
    t0 = time.time()
    status = "ok"
    resp_summary = {}
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        resp = client.models.generate_content(model=IMAGE_MODEL, contents=prompt)
        image_bytes = None
        for part in resp.candidates[0].content.parts:
            if part.inline_data is not None:
                image_bytes = part.inline_data.data
                resp_summary["mime_type"] = part.inline_data.mime_type
                break
        if image_bytes is None:
            status = "error"
            resp_summary["error"] = "响应中无图像数据"
            raise RuntimeError("Gemini 响应中无图像数据")
        out_path.write_bytes(image_bytes)
        resp_summary["image_bytes"] = len(image_bytes)
        resp_summary["saved_to"] = str(out_path)
    finally:
        ended = utc_now()
        book.record(name, provider="google-gemini",
                    endpoint="google-genai:models/generate_content",
                    model=IMAGE_MODEL,
                    request={"model": IMAGE_MODEL, "contents": prompt},
                    response=resp_summary,
                    started_utc=started, ended_utc=ended,
                    latency_ms=int((time.time() - t0) * 1000), status=status)
    return out_path
