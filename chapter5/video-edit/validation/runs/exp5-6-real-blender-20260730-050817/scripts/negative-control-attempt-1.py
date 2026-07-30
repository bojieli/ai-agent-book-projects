import bpy

# Clear default objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Set up scene and sequence editor
scene = bpy.context.scene
scene.sequence_editor = scene.sequence_editor_create()
se = scene.sequence_editor

# File paths
input_path = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-050817/source.mov'
output_path = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-050817/negative_control.mp4'

# Video parameters
source_fps = 25
trim_start_sec = 0.0
trim_end_sec = 3.0
trim_duration_sec = trim_end_sec - trim_start_sec
trim_duration_frames = int(trim_duration_sec * source_fps)  # 75 frames
output_duration_sec = trim_duration_sec * 1.5  # 4.5 seconds
output_duration_frames = int(output_duration_sec * source_fps)  # 113 frames (rounded up from 112.5)

speed_factor = trim_duration_sec / output_duration_sec  # 0.666...

# Add video strip
video_strip = se.sequences.new_movie(
    name='Video',
    filepath=input_path,
    channel=2,
    frame_start=1
)
video_strip.frame_offset_start = 0  # Start at 0s of source
video_strip.frame_final_duration = trim_duration_frames  # Trim to 3 seconds

# Add audio strip
audio_strip = se.sequences.new_sound(
    name='Audio',
    filepath=input_path,
    channel=1,
    frame_start=1
)
audio_strip.frame_offset_start = 0
audio_strip.frame_final_duration = trim_duration_frames

# Add speed effect to video
speed_video = se.sequences.new_effect(
    name='Speed_Video',
    type='SPEED',
    channel=3,
    frame_start=1,
    seq1=video_strip
)
speed_video.speed_factor = speed_factor
 speed_video.frame_final_duration = output_duration_frames

# Add speed effect to audio
speed_audio = se.sequences.new_effect(
    name='Speed_Audio',
    type='SPEED',
    channel=2,
    frame_start=1,
    seq1=audio_strip
)
speed_audio.speed_factor = speed_factor
 speed_audio.frame_final_duration = output_duration_frames

# Add subtitle text strip
text_strip = se.sequences.new_effect(
    name='Subtitle',
    type='TEXT',
    channel=4,
    frame_start=1,
    frame_end=1 + output_duration_frames - 1
)
text_strip.text = 'BIG BUNNY'
text_strip.align_x = 'CENTER'
text_strip.align_y = 'BOTTOM'
text_strip.font_size = 48
text_strip.color = (1.0, 1.0, 1.0, 1.0)  # White text

# Subtitle background box
text_strip.use_box = True
text_strip.box_color = (0.0, 0.0, 0.0, 0.5)  # Semi-transparent black
text_strip.box_margin_left = 10
text_strip.box_margin_right = 10
text_strip.box_margin_top = 10
text_strip.box_margin_bottom = 10

# Render settings
scene.render.resolution_x = 854
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100
scene.render.fps = source_fps
scene.render.fps_base = 1.0

# Output format settings
scene.render.image_settings.file_format = 'MPEG4'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H.264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.ffmpeg.audio_bitrate = 192
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
scene.render.filepath = output_path

# Set scene frame range
scene.frame_start = 1
scene.frame_end = output_duration_frames

# Render animation
bpy.ops.render.render(animation=True)