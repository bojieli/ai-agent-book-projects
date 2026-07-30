"""
Blender Python API（bpy）剪辑执行层 —— 实验 5-6 的核心。

书中方案强调"代码生成"：Proposer Agent 不去点 GUI，而是**生成一段调用
Blender Python API 的脚本**，每个编辑操作（导入 / 裁剪 / 字幕 / 变速 / 渲染）
对应一个清晰的函数调用，再用 `blender --background --python edit.py` 无头执行。

本模块两个出口：
  generate_bpy_script(source, plan, out_video) -> str
      纯字符串生成，**不依赖 bpy**，任何机器都能产出这段脚本（体现代码生成能力，
      可人工核对，或拷到装了 Blender 的机器上执行）。
  render_with_blender(source, plan, out_video, script_path) -> str
      若本机 `blender` 可执行，写出脚本并无头渲染产出成片；否则抛错由调用方回退。

裁剪基于 Blender 视频序列编辑器（VSE）：new_movie / new_sound 导入素材，
frame_offset_start + frame_final_duration 完成裁剪，TEXT / SPEED 特效条叠加，
FFMPEG(H.264+AAC) 容器渲染。API 面向 Blender 3.x / 4.x。
"""
import os
import shutil
import subprocess


def blender_available() -> bool:
    """本机是否有 blender 可执行文件（决定 backend=auto 时走 Blender 还是 ffmpeg）。"""
    return shutil.which("blender") is not None


# 生成的 bpy 脚本模板。占位符全部通过 repr() 注入，保证是合法的 Python 字面量。
_BPY_TEMPLATE = '''"""
本文件由 blender_editor.generate_bpy_script() 自动生成（实验 5-6）。
执行：blender --background --python edit.py
它把一条剪辑计划翻译成 Blender 视频序列编辑器（VSE）的 API 调用序列。
"""
import os
import bpy

SRC = {src}
OUT = {out}
FPS = {fps}
START = {start}       # 目标片段起点（秒）
END = {end}           # 目标片段终点（秒）
SUBTITLE = {subtitle} # None 或字幕文本
SLOWMO = {slowmo}     # None 或放慢倍率（factor>1 表示放慢 factor 倍）

scene = bpy.context.scene
scene.render.fps = FPS
scene.render.fps_base = 1.0

# 清掉可能存在的旧序列，保证幂等
if scene.sequence_editor:
    bpy.ops.sequencer.select_all(action='SELECT')
    bpy.ops.sequencer.delete()
se = scene.sequence_editor_create()

start_frame = int(round(START * FPS))
dur_frames = max(1, int(round((END - START) * FPS)))

# 1) 导入影片 + 音轨（new_sound 在无音轨素材上会抛 RuntimeError，忽略即可）
movie = se.sequences.new_movie(name="clip", filepath=SRC, channel=1, frame_start=1)
try:
    sound = se.sequences.new_sound(name="audio", filepath=SRC, channel=2, frame_start=1)
except RuntimeError:
    sound = None

# 2) 裁剪 [START, END]：偏移掉片头，再固定成片时长
for strip in (movie, sound):
    if strip is None:
        continue
    strip.frame_offset_start = start_frame
    strip.frame_final_duration = dur_frames

top_channel = 3

# 3) 慢动作：SPEED 特效条（MULTIPLY 模式，speed_factor = 1/倍率）
if SLOWMO:
    speed = se.sequences.new_effect(
        name="slowmo", type='SPEED', channel=top_channel,
        frame_start=1, frame_end=1 + dur_frames, seq1=movie,
    )
    speed.use_default_fade = False
    speed.speed_control = 'MULTIPLY'
    speed.speed_factor = 1.0 / SLOWMO
    top_channel += 1
    # 放慢后成片总帧数按倍率拉长
    render_dur = int(round(dur_frames * SLOWMO))
    movie.frame_final_duration = render_dur
else:
    render_dur = dur_frames

# 4) 字幕：TEXT 特效条，底部居中带半透明底框
if SUBTITLE:
    txt = se.sequences.new_effect(
        name="subtitle", type='TEXT', channel=top_channel,
        frame_start=1, frame_end=1 + render_dur,
    )
    txt.text = SUBTITLE
    txt.font_size = 100
    txt.location = (0.5, 0.12)
    txt.align_x = 'CENTER'
    txt.align_y = 'BOTTOM'
    txt.use_box = True
    txt.box_color = (0.0, 0.0, 0.0, 0.6)

# 5) 渲染范围 + 输出为 mp4(H.264+AAC)
scene.frame_start = 1
scene.frame_end = render_dur

r = scene.render
r.image_settings.file_format = 'FFMPEG'
r.ffmpeg.format = 'MPEG4'
r.ffmpeg.codec = 'H264'
r.ffmpeg.audio_codec = 'AAC'
r.filepath = OUT
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)

bpy.ops.render.render(animation=True)
print("BLENDER_RENDER_DONE", OUT)
'''


def _plan_fields(plan: dict):
    """从剪辑计划里抽出 bpy 脚本需要的字段。"""
    start, end = float(plan["start"]), float(plan["end"])
    if end <= start:
        raise ValueError(f"剪辑区间非法：start={start} >= end={end}")
    effects = plan.get("effects", []) or []
    subtitle = None
    slowmo = None
    for eff in effects:
        etype = eff.get("type")
        if etype == "subtitle":
            subtitle = eff.get("text", "")
        elif etype == "slowmo":
            # Skip null factor like non-positive.
            raw = eff.get("factor", 2.0)
            if raw is None:
                continue
            factor = float(raw)
            if factor <= 0:
                continue
            slowmo = factor
    return start, end, subtitle, slowmo


def generate_bpy_script(source: str, plan: dict, out_video: str, fps: int = 30) -> str:
    """把剪辑计划渲染成一段可执行的 Blender Python(bpy) 脚本文本（不依赖 bpy）。"""
    start, end, subtitle, slowmo = _plan_fields(plan)
    return _BPY_TEMPLATE.format(
        src=repr(os.path.abspath(source)),
        out=repr(os.path.abspath(out_video)),
        fps=int(fps),
        start=repr(start),
        end=repr(end),
        subtitle=repr(subtitle),
        slowmo=repr(slowmo),
    )


def write_bpy_script(source: str, plan: dict, out_video: str,
                     script_path: str, fps: int = 30) -> str:
    """生成 bpy 脚本并落盘（无论用哪个后端都会产出，作为代码生成产物）。"""
    script = generate_bpy_script(source, plan, out_video, fps=fps)
    os.makedirs(os.path.dirname(script_path) or ".", exist_ok=True)
    with open(script_path, "w") as f:
        f.write(script)
    return script_path


def render_with_blender(source: str, plan: dict, out_video: str,
                        script_path: str, fps: int = 30) -> str:
    """写出 bpy 脚本并用 `blender --background --python` 无头执行，产出成片。"""
    if not blender_available():
        raise RuntimeError(
            "指定用 Blender 后端，但未找到 blender 可执行文件。\n"
            "  安装后确保 `blender --version` 可用：https://www.blender.org/download/\n"
            "  或改用 --backend ffmpeg。"
        )
    write_bpy_script(source, plan, out_video, script_path, fps=fps)
    os.makedirs(os.path.dirname(out_video) or ".", exist_ok=True)
    proc = subprocess.run(
        ["blender", "--background", "--python", script_path],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 or not os.path.exists(out_video):
        tail = "\n".join(proc.stderr.strip().splitlines()[-12:])
        raise RuntimeError(
            f"Blender 渲染失败（exit={proc.returncode}）：\n{tail}\n"
            f"  可人工检查生成的脚本：{script_path}"
        )
    return out_video


if __name__ == "__main__":
    # 零依赖自检：打印一段"含裁剪 + 字幕"的示例 bpy 脚本（可 py_compile 校验其语法）。
    demo_plan = {
        "start": 16.0,
        "end": 28.0,
        "effects": [{"type": "subtitle", "text": "SURFING"}],
    }
    print("# blender available:", blender_available())
    print("# ---- generated edit.py ----")
    print(generate_bpy_script("output/source.mp4", demo_plan, "output/final.mp4"))
