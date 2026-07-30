import bpy
import math

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# File paths
input_path = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-052206/source.mov'
output_path = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-052206/negative_control.mp4'

# Scene setup
scene = bpy.context.scene

# Render settings
scene.render.fps = 25
scene.render.fps_base = 1.0
scene.render.resolution_x = 854
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100

# Output format settings
scene.render.image_settings.file_format = 'MPEG4'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.filepath = output_path

# VSE setup
scene.sequence_editor_create()
seq_ed = scene.sequence_editor

# Add video strip
video_strip = seq_ed.sequences.new_movie(
    name='Video',
    filepath=input_path,
    frame_start=0,
    channel=1
)
video_strip.frame_final_duration = 75  # 3s * 25fps

# Add speed effect (1.5x slowdown)
original_duration = 75
new_duration = math.ceil(original_duration * 1.5)  # 113 frames (4.52s)
speed_strip = seq_ed.sequences.new_effect(
    name='SpeedControl',
    type='SPEED',
    channel=2,
    frame_start=0,
    frame_end=new_duration,
    seq1=video_strip
)
speed_strip.speed_control = 'MULTIPLY'
speed_strip.speed_factor = 1/1.5

# Add audio strip
audio_strip = seq_ed.sequences.new_sound(
    name='Audio',
    filepath=input_path,
    frame_start=0,
    channel=3
)
audio_strip.frame_final_duration = 75  # Keep original audio duration

# Add subtitle text strip
text_strip = seq_ed.sequences.new_effect(
    name='Subtitle',
    type='TEXT',
    channel=4,
    frame_start=0,
    frame_end=new_duration
)
text_strip.text = 'BIG BUNNY'
text_strip.align_x = 'CENTER'
text_strip.align_y = 'BOTTOM'
text_strip.font_size = 48
text_strip.use_box = True
text_strip.box_color = (0, 0, 0, 0.6)  # Semi-transparent black box

# Set render frame range
scene.frame_start = 1
scene.frame_end = new_duration

# Render animation
bpy.ops.render.render(animation=True)