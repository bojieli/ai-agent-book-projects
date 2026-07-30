import bpy
import os

# Clear default objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Set up scene
scene = bpy.context.scene
scene.render.fps = 25
scene.render.fps_base = 1.0
scene.render.resolution_x = 854
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100

# Configure output settings
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.ffmpeg.audio_bitrate = 192
output_path = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-052206/negative_control.mp4'
scene.render.filepath = output_path

# Create sequence editor
scene.sequence_editor_create()
sequences = scene.sequence_editor.sequences

# Import source movie and sound
source_path = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-052206/source.mov'
movie_strip = sequences.new_movie(name='SourceMovie', filepath=source_path, channel=1, frame_start=0)

sound_strip = None
for strip in sequences:
    if strip.type == 'SOUND' and strip.name.startswith('SourceMovie'):
        sound_strip = strip
        break
if not sound_strip:
    sound_strip = sequences.new_sound(name='SourceAudio', filepath=source_path, channel=2, frame_start=0)

# Trim to 3-second interval (75 frames at 25fps)
trim_frames = 75  # 3.0s * 25fps
movie_strip.frame_start = 0
movie_strip.frame_final_duration = trim_frames
sound_strip.frame_start = 0
sound_strip.frame_final_duration = trim_frames

# Apply speed effect (1.5x slowdown = 4.5s output)
speed_strip = sequences.new_effect(
    name='SpeedControl',
    type='SPEED',
    channel=2,
    frame_start=0,
    frame_end=113,  # 75 frames * 1.5 = 112.5 → 113 frames
    seq1=movie_strip,
    seq2=None
)
speed_strip.speed_control = 'MULTIPLY'
speed_strip.speed_factor = 1/1.5

# Set scene frame range
duration_frames = 113  # 4.5s * 25fps = 112.5 → 113 frames
scene.frame_start = 0
scene.frame_end = duration_frames

# Add subtitle with background box
text_strip = sequences.new_effect(
    name='Subtitle',
    type='TEXT',
    channel=3,
    frame_start=0,
    frame_end=duration_frames,
    seq1=None,
    seq2=None
)
text_strip.text = 'BIG BUNNY'
text_strip.align_x = 'CENTER'
text_strip.align_y = 'BOTTOM'
text_strip.use_box = True
text_strip.box_color = (0.0, 0.0, 0.0, 0.6)
text_strip.font_size = 48

# Render animation
bpy.ops.render.render(animation=True)