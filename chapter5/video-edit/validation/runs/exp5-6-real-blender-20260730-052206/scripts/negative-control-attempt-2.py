import bpy

# Clear existing data
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# Scene settings
scene.render.resolution_x = 854
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100
scene.render.fps = 25
scene.render.fps_base = 1.0

# Create sequence editor
if not scene.sequence_editor:
    scene.sequence_editor_create()
seq_ed = scene.sequence_editor
sequences = seq_ed.sequences

# File paths
input_movie = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-052206/source.mov'
output_mp4 = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-052206/negative_control.mp4'

# Add movie strip (3 seconds = 75 frames at 25fps)
mov_strip = sequences.new_movie(
    name='SourceMovie',
    filepath=input_movie,
    frame_start=1,
    channel=1
)
mov_strip.frame_offset_start = 0
mov_strip.frame_final_duration = 75  # 3s * 25fps

# Locate and trim sound strip
sound_strip = next((s for s in sequences if s.type == 'SOUND' and s.frame_start == mov_strip.frame_start), None)
if sound_strip:
    sound_strip.frame_final_duration = 75  # Keep original audio duration

# Add speed effect (1.5x slowdown)
speed_strip = sequences.new_effect(
    name='SlowMotion',
    type='SPEED',
    frame_start=1,
    channel=2,
    input_1=mov_strip
)
speed_strip.speed_control = 'MULTIPLY'
speed_strip.speed_factor = 1 / 1.5

# Calculate slowed duration (4.5s = 112.5 frames → 113 frames)
slowed_frames = int(4.5 * 25) + 1
scene.frame_start = 1
scene.frame_end = slowed_frames

# Add subtitle text strip
text_strip = sequences.new_effect(
    name='Subtitle',
    type='TEXT',
    frame_start=1,
    frame_end=scene.frame_end,
    channel=3
)
text_strip.text = 'BIG BUNNY'
text_strip.align_x = 'CENTER'
text_strip.align_y = 'BOTTOM'
text_strip.use_box = True
text_strip.box_color = (0, 0, 0, 0.6)
text_strip.font_size = 48

# Render settings
scene.render.filepath = output_mp4
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'

# Render animation
bpy.ops.render.render(animation=True)