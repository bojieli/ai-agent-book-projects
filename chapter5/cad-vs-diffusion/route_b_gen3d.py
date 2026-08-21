"""路线 B：3D 生成模型（混元 Hunyuan3D-2.1 公共 Hugging Face Space）。

Hunyuan3D-2.1 官方 Space 只暴露 image-to-3D 端点（/shape_generation），
因此 text-to-3D 按业界标准做法走两段式：
  文本规格 → Gemini 文生图（零件产品图）→ Hunyuan3D-2.1 图生 3D（GLB）。
公共 Space 无需密钥，但可能排队/限流/失败——全部如实留证。
"""
from __future__ import annotations

import shutil
import time
from pathlib import Path

from receipts import ReceiptBook, utc_now

HF_SPACE = "tencent/Hunyuan3D-2.1"

FLANGE_IMAGE_PROMPT_M5 = (
    "产品照片：一个金属法兰盘，扁平圆柱体，端面上有 4 个均匀分布的圆形通孔，"
    "孔位于一个同心圆上。外径 80mm，厚度 10mm，孔径 5.5mm，孔位圆直径 60mm。"
    "纯色背景，正视略俯视角度，工业零件写实风格"
)
FLANGE_IMAGE_PROMPT_M6 = FLANGE_IMAGE_PROMPT_M5.replace("孔径 5.5mm", "孔径 6.5mm")


def hunyuan_image_to_3d(image_path: Path, out_glb: Path, book: ReceiptBook,
                        name: str) -> Path:
    """调用 Hunyuan3D-2.1 公共 Space 的 /shape_generation，保存 GLB。

    排队、限流、失败均抛异常前留证，由调用方决定是否降级。
    """
    from gradio_client import Client, handle_file

    out_glb.parent.mkdir(parents=True, exist_ok=True)
    started = utc_now()
    t0 = time.time()
    status = "ok"
    resp_summary = {}
    params = {
        "image": str(image_path),
        "steps": 30, "guidance_scale": 5.0, "seed": 1234,
        "octree_resolution": 256, "check_box_rembg": True,
        "num_chunks": 8000, "randomize_seed": False,
    }
    try:
        client = Client(HF_SPACE)
        result = client.predict(
            handle_file(str(image_path)),
            None, None, None, None,          # 多视图留空
            params["steps"], params["guidance_scale"], params["seed"],
            params["octree_resolution"], params["check_box_rembg"],
            params["num_chunks"], params["randomize_seed"],
            api_name="/shape_generation",
        )
        glb_src = result[0]
        # gradio File 组件可能返回 {'value': path, '__type__': 'update'} 或 FileData dict
        if isinstance(glb_src, dict):
            glb_src = glb_src.get("value") or glb_src.get("path") or glb_src.get("url")
        resp_summary["mesh_stats"] = result[2] if len(result) > 2 else None
        resp_summary["space_file"] = str(glb_src)
        shutil.copy(glb_src, out_glb)
        resp_summary["saved_to"] = str(out_glb)
    except Exception as e:
        status = "error"
        resp_summary["error"] = repr(e)
        raise
    finally:
        ended = utc_now()
        book.record(name, provider="huggingface-space",
                    endpoint=f"{HF_SPACE}:/shape_generation",
                    model="Hunyuan3D-2.1",
                    request=params,
                    response=resp_summary,
                    started_utc=started, ended_utc=ended,
                    latency_ms=int((time.time() - t0) * 1000), status=status)
    return out_glb
