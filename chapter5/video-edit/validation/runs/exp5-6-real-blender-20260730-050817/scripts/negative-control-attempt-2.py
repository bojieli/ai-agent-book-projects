import bpy
import math

# Clear default objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Set up scene
scene = bpy.context.scene

# Render settings
scene.render.resolution_x = 854
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100
scene.render.fps = 25
scene.render.fps_base = 1.0
scene.render.image_settings.file_format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.filepath = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-050817/negative_control.mp4'

# Set up Video Sequence Editor
if not scene.sequence_editor:
    scene.sequence_editor_create()
scene.sequence_editor.sequences.clear()

# Import source movie
input_path = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-050817/source.mov'
movie_strip = scene.sequence_editor.sequences.new_movie(
    name='Source',
    filepath=input_path,
    channel=1,
    frame_start=1
)
# Trim to 3 seconds (75 frames at 25fps)
movie_strip.frame_final_duration = 75

# Add speed effect (1.5x duration = 2/3 speed)
speed_strip = scene.sequence_editor.sequences.new_effect(
    name='Slow',
    type='SPEED',
    channel=2,
    frame_start=1,
    frame_end=movie_strip.frame_final_end,
    seq1=movie_strip
)
speed_strip.speed_factor = 2/3  # 3s * 1.5 = 4.5s duration

# Calculate scene frame range
slowed_frames = movie_strip.frame_final_duration / speed_strip.speed_factor
scene.frame_start = 1
scene.frame_end = math.ceil(scene.frame_start + slowed_frames - 1)

# Create sequence editor if not exists
if not scene.sequence_editor:
    scene.sequence_editor_create()

# Subtitle background (semi-transparent dark box)
color_strip = scene.sequence_editor.sequences.new_effect(
    name='SubtitleBG',
    type='COLOR',
    channel=3,
    frame_start=scene.frame_start,
    frame_end=scene.frame_end
)
color_strip.color = (0.0, 0.0, 0.0)  # Black
color_strip.alpha = 0.5  # Semi-transparent
color_strip.transform.scale_x = 0.4  # Box width
color_strip.transform.scale_y = 0.15  # Box height
color_strip.transform.translate_y = -0.4  # Bottom position
color_strip.transform.align_x = 'CENTER'  # Center horizontally

# Subtitle text
text_strip = scene.sequence_editor.sequences.new_effect(
    name='SubtitleText',
    type='TEXT',
    channel=4,
    frame_start=scene.frame_start,
    frame_end=scene.frame_end
)
text_strip.text = 'BIG BUNNY'
text_strip.align_x = 'CENTER'
text_strip.align_y = 'CENTER'
text_strip.font_size = 40
text_strip.color = (1.0, 1.0, 1.0)  # White text
text_strip.transform.translate_y = -0.4  # Match background Y position
text_strip.transform.align_x = 'CENTER'

# Render animation
bpy.ops.render.render(animation=True)