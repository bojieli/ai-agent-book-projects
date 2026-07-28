"""
视频剪辑执行层（双后端）。

书中实验 5-6 的核心是"代码生成"：Proposer Agent 生成一段调用 Blender Python API
（bpy）的脚本来完成剪辑。因此本层有两个后端：

  - blender：把剪辑计划翻译成 bpy 脚本，用 `blender --background --python` 无头渲染
             （见 blender_editor.py）——书中原方案，需安装 Blender；
  - ffmpeg ：用 ffmpeg 完成等价的裁剪/字幕/慢动作，单二进制、CI 友好，本机已验证。

apply_edit(..., backend=) 统一入口：backend="auto" 时装了 Blender 走 bpy，否则回退
ffmpeg。**无论走哪个后端，都会把 Proposer 生成的 bpy 脚本落盘（output/edit.py）**，
体现"生成 Blender Python API 代码"这一核心，便于人工核对或换机执行。

支持的操作：
  - trim      裁剪 [start, end] 片段
  - subtitle  在片段上叠加字幕
  - slowmo    慢动作（放慢到 factor 倍时长）
所有操作最终产出一个标准 mp4（H.264 + AAC）。
"""
import os

from blender_editor import blender_available, render_with_blender, write_bpy_script
from ffmpeg_utils import find_font, run


def _esc(text: str) -> str:
    """转义 drawtext/subtitles 文本中的特殊字符。"""
    return text.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")


def apply_edit(source: str, plan: dict, out_path: str,
               backend: str = "auto", script_path: str = None) -> str:
    """
    按剪辑计划 plan 生成成片。

    plan 结构（由 Proposer Agent 产出）:
      {
        "start": float,          # 目标片段起点（秒）
        "end": float,            # 目标片段终点（秒）
        "effects": [             # 可选特效列表
          {"type": "subtitle", "text": "..."},
          {"type": "slowmo", "factor": 2.0}
        ]
      }

    backend:
      "auto"    装了 blender 用 bpy，否则回退 ffmpeg（默认）。
      "blender" 强制用 Blender bpy 无头渲染（未装 blender 则报错）。
      "ffmpeg"  强制用 ffmpeg 剪辑。

    无论哪个后端，都会把 Proposer 生成的 bpy 脚本写到 script_path
    （默认 out 同目录 edit.py），作为"生成 Blender API 代码"的产物。
    返回成片路径。
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if script_path is None:
        script_path = os.path.join(os.path.dirname(out_path) or ".", "edit.py")

    # 始终产出 bpy 脚本：这正是书中"Proposer 生成 Blender 脚本"的落地产物。
    write_bpy_script(source, plan, out_path, script_path)

    use_blender = backend == "blender" or (backend == "auto" and blender_available())
    if use_blender:
        return render_with_blender(source, plan, out_path, script_path)
    if backend == "blender":  # 显式要求 Blender 却没装
        return render_with_blender(source, plan, out_path, script_path)  # 抛清晰错误
    return _apply_edit_ffmpeg(source, plan, out_path)


def _apply_edit_ffmpeg(source: str, plan: dict, out_path: str) -> str:
    """ffmpeg 后端：与 bpy 脚本等价的裁剪/字幕/慢动作，产出 H.264+AAC 的 mp4。"""
    start, end = float(plan["start"]), float(plan["end"])
    if end <= start:
        raise ValueError(f"剪辑区间非法：start={start} >= end={end}")

    effects = plan.get("effects", []) or []
    vf_chain = []          # 视频滤镜链
    af_chain = []          # 音频滤镜链
    font = find_font()

    for eff in effects:
        etype = eff.get("type")
        if etype == "subtitle":
            txt = _esc(eff.get("text", ""))
            opts = [f"text='{txt}'", "fontsize=52", "fontcolor=white",
                    "x=(w-text_w)/2", "y=h-text_h-50",
                    "box=1", "boxcolor=black@0.6", "boxborderw=16"]
            if font:
                opts.insert(0, f"fontfile={font}")
            vf_chain.append("drawtext=" + ":".join(opts))
        elif etype == "slowmo":
            factor = float(eff.get("factor", 2.0))
            if factor <= 0:
                continue
            vf_chain.append(f"setpts={factor}*PTS")
            # atempo 只支持 0.5~2.0，用 1/factor 放慢音频。
            af_chain.append(f"atempo={max(0.5, min(2.0, 1.0 / factor))}")

    cmd = ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", source]
    if vf_chain:
        cmd += ["-vf", ",".join(vf_chain)]
    if af_chain:
        cmd += ["-af", ",".join(af_chain)]
    cmd += ["-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", out_path]

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    run(cmd, desc="ffmpeg 剪辑")
    return out_path


# --------------------------------------------------------------------------- #
# Blender 后端说明
# --------------------------------------------------------------------------- #
# 真实的 Blender bpy 脚本生成与无头渲染已实现在 blender_editor.py：
#   - generate_bpy_script()：把剪辑计划翻译成一段 bpy 脚本（new_movie / 裁剪 /
#     TEXT / SPEED / render）——即书中"Proposer 生成 Blender 脚本"；
#   - render_with_blender()：用 `blender --background --python edit.py` 无头执行。
# apply_edit(backend="blender") 即走这条路径；backend="auto"（默认）在未装 Blender 时
# 回退到本文件的 ffmpeg 后端。核心的"两步 Vision 定位 + 提议者-审核者"与执行层解耦，
# 两个后端共用同一份剪辑计划（plan），agents.py / demo.py 无需为切换后端改动逻辑。
