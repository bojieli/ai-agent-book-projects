import bpy

# Clear existing data
bpy.ops.wm.read_factory_settings(use_empty=True)

# Get the scene
scene = bpy.context.scene

# Set render resolution and FPS
scene.render.resolution_x = 854
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100
scene.render.fps = 25
scene.render.fps_base = 1.0

# Set output settings
output_path = "/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-052206/negative_control.mp4"
scene.render.filepath = output_path
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'

# Create sequence editor
seq_ed = scene.sequence_editor_create()

# Import movie strip
movie_path = "/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-052206/source.mov"
movie_strip = seq_ed.sequences.new_movie(
    name="SourceMovie",
    filepath=movie_path,
    channel=1,
    frame_start=0
)

# Trim movie to [0.000, 3.000] seconds (75 frames at 25 FPS)
movie_strip.frame_offset_start = 0
movie_strip.frame_final_duration = 75

# Add speed control effect
speed_strip = seq_ed.sequences.new_effect(
    name="SpeedControl",
    type='SPEED',
    channel=2,
    frame_start=0,
    frame_end=movie_strip.frame_start + movie_strip.frame_final_duration,
    seq1=movie_strip
)
speed_strip.speed_control = 'MULTIPLY'
speed_strip.speed_factor = 1 / 1.5  # Slow down by 1.5x

# Find sound strip and trim it
sound_strip = None
for strip in seq_ed.sequences:
    if strip.type == 'SOUND' and strip.frame_start == movie_strip.frame_start:
        sound_strip = strip
        break
if sound_strip:
    sound_strip.frame_offset_start = 0
    sound_strip.frame_final_duration = 75  # Keep sound at normal duration

# Calculate render duration: 3s * 1.5 = 4.5s = 112.5 frames → 113 frames (0-112)
scene.frame_start = 0
scene.frame_end = 113  # 113 frames total

# Add subtitle text strip
text_strip = seq_ed.sequences.new_effect(
    name="Subtitle",
    type='TEXT',
    channel=3,
    frame_start=0,
    frame_end=scene.frame_end
)
text_strip.text = "BIG BUNNY"
text_strip.align_x = 'CENTER'
text_strip.align_y = 'BOTTOM'
text_strip.font_size = 48
text_strip.color = (1, 1, 1, 1)  # White text
text_strip.use_box = True
text_strip.box_color = (0, 0, 0, 0.6)  # Dark semi-transparent box

# Render animation
scene.render.engine = 'BLENDER_EEVEE'
bpy.ops.render.render(animation=True)