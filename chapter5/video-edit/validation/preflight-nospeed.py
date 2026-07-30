"""
本文件由 blender_editor.generate_bpy_script() 自动生成（实验 5-6）。
执行：blender --background --python edit.py
它把一条剪辑计划翻译成 Blender 视频序列编辑器（VSE）的 API 调用序列。
"""
import os
import bpy

SRC = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/source_cache/big-buck-bunny-trailer-480p.mov'
OUT = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/preflight-nospeed.mp4'
FPS = 25
START = 9.0       # 目标片段起点（秒）
END = 11.0           # 目标片段终点（秒）
SUBTITLE = 'BIG BUNNY' # None 或字幕文本
SLOWMO = None     # None 或放慢倍率（factor>1 表示放慢 factor 倍）

scene = bpy.context.scene
scene.render.fps = FPS
scene.render.fps_base = 1.0
scene.render.resolution_x = 854
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100

# 清掉可能存在的旧序列，保证幂等
if scene.sequence_editor:
    bpy.ops.sequencer.select_all(action='SELECT')
    bpy.ops.sequencer.delete()
se = scene.sequence_editor_create()

start_frame = int(round(START * FPS))
dur_frames = max(1, int(round((END - START) * FPS)))

# 1) 导入影片 + 音轨（new_sound 在无音轨素材上会抛 RuntimeError，忽略即可）
movie = se.sequences.new_movie(name="clip", filepath=SRC, channel=1, frame_start=1 - start_frame)
try:
    sound = se.sequences.new_sound(name="audio", filepath=SRC, channel=2, frame_start=1 - start_frame)
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
