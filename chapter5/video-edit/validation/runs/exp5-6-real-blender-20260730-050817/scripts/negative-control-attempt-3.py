import bpy

# Clear existing data to start fresh
bpy.ops.wm.read_factory_settings(use_empty=True)

# Get the current scene
scene = bpy.context.scene

# Set render resolution and FPS
scene.render.resolution_x = 854
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100
scene.render.fps = 25
scene.render.fps_base = 1.0

# Set render output settings
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
scene.render.filepath = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-050817/negative_control.mp4'

# Create sequence editor
scene.sequence_editor_create()
seq_ed = scene.sequence_editor

# Input movie path
input_movie = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-050817/source.mov'

# Add video strip with trim (0.000-3.000s = 0-75 frames at 25fps)
video_strip = seq_ed.sequences.new_movie(name='Video', filepath=input_movie, channel=1, frame_start=0)
video_strip.frame_offset_start = 0  # Start at source frame 0
video_strip.frame_final_duration = 75  # 3s * 25fps = 75 frames

# Add speed effect to slow down (1.5x duration: 3s → 4.5s = 112.5 frames → 113 frames)
speed_effect = seq_ed.sequences.new_effect(name='Speed', type='SPEED', channel=2, frame_start=0, frame_end=113, seq1=video_strip)
speed_effect.speed_factor = 2/3  # Slows to 1.5x original duration

# Add audio strip from movie
audio_strip = seq_ed.sequences.new_sound(name='Audio', filepath=input_movie, channel=1, frame_start=0)
audio_strip.frame_offset_start = 0  # Match video trim start
audio_strip.frame_final_duration = 75  # Match video trim duration

# Add speed effect to audio
audio_speed = seq_ed.sequences.new_effect(name='AudioSpeed', type='SPEED', channel=2, frame_start=0, frame_end=113, seq1=audio_strip)
audio_speed.speed_factor = 2/3
audio_speed.use_audio = True

# Create subtitle background (semi-transparent dark box)
bg_strip = seq_ed.sequences.new_effect(name='SubtitleBG', type='COLOR', channel=3, frame_start=0, frame_end=113)
bg_strip.color = (0.1, 0.1, 0.1, 0.7)  # Dark gray with 70% transparency
bg_strip.align_x = 'CENTER'
bg_strip.align_y = 'BOTTOM'
bg_strip.transform.scale_x = 0.5  # Width of background box
bg_strip.transform.scale_y = 0.15  # Height of background box
bg_strip.transform.location_y = 0.03  # Position slightly above bottom edge

# Create subtitle text
text_strip = seq_ed.sequences.new_effect(name='SubtitleText', type='TEXT', channel=4, frame_start=0, frame_end=113)
text_strip.text = 'BIG BUNNY'
text_strip.align_x = 'CENTER'
text_strip.align_y = 'BOTTOM'
text_strip.font_size = 48
text_strip.color = (1.0, 1.0, 1.0)  # White text
text_strip.transform.location_y = 0.05  # Align with background box

# Set scene frame range to cover slowed duration (4.5 seconds = 112.5 frames → 113 frames)
scene.frame_start = 0
scene.frame_end = 113

# Render the animation
bpy.ops.render.render(animation=True)