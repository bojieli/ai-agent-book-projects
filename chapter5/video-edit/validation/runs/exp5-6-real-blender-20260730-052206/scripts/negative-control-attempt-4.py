import bpy
import os

# Clear existing data
bpy.ops.wm.read_factory_settings(use_empty=True)

# Get the current scene
scene = bpy.context.scene

# Set render resolution (854x480 for H.264 even width)
scene.render.resolution_x = 854
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100

# Set frame rate (25 FPS)
scene.render.fps = 25
scene.render.fps_base = 1.0

# Output settings
output_path = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-052206/negative_control.mp4'
scene.render.filepath = output_path
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H.264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.ffmpeg.audio_mixrate = 44100
scene.render.ffmpeg.audio_bitrate = 192
scene.render.use_audio = True

# Create sequence editor
scene.sequence_editor_create()
seq_ed = scene.sequence_editor

# Source movie path
source_path = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-052206/source.mov'

# Add video strip with trim (0.000-3.000s = 75 frames @25FPS)
video_strip = seq_ed.sequences.new_movie(
    name='Video',
    filepath=source_path,
    channel=1,
    frame_start=1
)
video_strip.frame_offset_start = 0  # Start at 0s of source
video_strip.frame_final_duration = 75  # Trim to 3s (75 frames)

# Add SPEED effect for slow motion (1.5x duration)
 speed_effect = seq_ed.sequences.new_effect(
    name='SpeedControl',
    type='SPEED',
    channel=2,
    frame_start=1,
    seq1=video_strip
)
speed_effect.speed_control = 'MULTIPLY'
speed_effect.speed_factor = 1/1.5  # Slow playback speed

# Extend video duration to 1.5x trimmed interval (4.5s = 112.5 frames → 113 frames)
video_strip.frame_final_duration = 113

# Configure audio strip (trim to original 3s duration)
sound_strip = None
for strip in seq_ed.sequences:
    if strip.type == 'SOUND' and strip.name.startswith('Audio'):
        sound_strip = strip
if sound_strip:
    sound_strip.frame_offset_start = 0  # Start at 0s of source audio
    sound_strip.frame_final_duration = 75  # Keep original 3s duration

# Add subtitle text strip with background box
text_strip = seq_ed.sequences.new_effect(
    name='Subtitle',
    type='TEXT',
    channel=3,
    frame_start=1,
    frame_final_duration=113
)
text_strip.text = 'BIG BUNNY'
text_strip.align_x = 'CENTER'
text_strip.align_y = 'BOTTOM'
text_strip.use_box = True
text_strip.box_color = (0, 0, 0, 0.6)  # Semi-transparent black box
text_strip.font_size = 48

# Set scene frame range to match slowed video duration
scene.frame_start = 1
scene.frame_end = 113

# Render the animation
bpy.ops.render.render(animation=True)