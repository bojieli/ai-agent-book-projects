import bpy

# Clear existing objects to start fresh
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Configuration paths and parameters
INPUT_MOVIE = "/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-052206/source.mov"
OUTPUT_MP4 = "/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-052206/negative_control.mp4"
SOURCE_FPS = 25
TRIM_DURATION_SECONDS = 3.0
SLOW_FACTOR = 1.5
RENDER_RESOLUTION = (854, 480)

# Calculate frame values
trim_frames = int(TRIM_DURATION_SECONDS * SOURCE_FPS)
slowed_frames = int(trim_frames * SLOW_FACTOR)
scene = bpy.context.scene

# Create sequence editor
seq_ed = scene.sequence_editor_create()

# Add movie strip with trim
movie_strip = seq_ed.sequences.new_movie(
    name="SourceVideo",
    filepath=INPUT_MOVIE,
    channel=1,
    frame_start=1
)
movie_strip.frame_offset_start = 0  # Start at beginning of source
movie_strip.frame_final_duration = trim_frames  # Trim to 3 seconds

# Locate and trim audio strip (auto-created with movie)
sound_strip = None
for strip in seq_ed.sequences:
    if strip.type == 'SOUND' and strip.channel == 2 and strip.frame_start == 1:
        sound_strip = strip
if sound_strip:
    sound_strip.frame_final_duration = trim_frames  # Keep audio at original speed

# Add speed effect to video (slow motion)
speed_strip = seq_ed.sequences.new_effect(
    name="SlowMotion",
    type='SPEED',
    channel=3,
    frame_start=1,
    frame_end=1 + slowed_frames - 1,
    target=movie_strip
)
speed_strip.speed_control = 'MULTIPLY'
speed_strip.speed_factor = 1 / SLOW_FACTOR  # 1/1.5 speed factor

# Add subtitle text strip with background box
text_strip = seq_ed.sequences.new_text(
    name="Subtitle",
    text="BIG BUNNY",
    channel=4,
    frame_start=1,
    frame_end=1 + slowed_frames - 1
)
text_strip.align_x = 'CENTER'
text_strip.align_y = 'BOTTOM'
text_strip.use_box = True
text_strip.box_color = (0.0, 0.0, 0.0, 0.6)  # Black semi-transparent box
text_strip.font_size = 48  # Visible size for 854x480 resolution

# Configure render settings
scene.render.resolution_x = RENDER_RESOLUTION[0]
scene.render.resolution_y = RENDER_RESOLUTION[1]
scene.render.resolution_percentage = 100
scene.render.fps = SOURCE_FPS
scene.render.fps_base = 1.0
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.filepath = OUTPUT_MP4

# Set render frame range
scene.frame_start = 1
scene.frame_end = 1 + slowed_frames - 1

# Execute render
bpy.ops.render.render(animation=True)