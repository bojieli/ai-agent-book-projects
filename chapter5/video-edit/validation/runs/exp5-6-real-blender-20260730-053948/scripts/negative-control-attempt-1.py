import bpy

# Configuration
INPUT_PATH = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-053948/source.mov'
OUTPUT_PATH = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-053948/negative_control.mp4'
START_SECONDS = 0.000
END_SECONDS = 3.000
FPS = 25

# Calculate timing parameters
start_frame = int(round(START_SECONDS * FPS))
dur_frames = max(1, int(round((END_SECONDS - START_SECONDS) * FPS)))
render_dur = int(round(dur_frames * 1.5))

# Initialize scene
scene = bpy.context.scene
scene.sequence_editor_clear()

# Render settings
scene.render.resolution_x = 854
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100
scene.render.fps = FPS
scene.render.fps_base = 1.0
scene.render.filepath = OUTPUT_PATH
scene.render.image_settings.file_format = 'MPEG4'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'

# Video Sequence Editor setup
se = scene.sequence_editor_create()

# Add movie and audio strips
movie = se.sequences.new_movie(
    name='clip',
    filepath=INPUT_PATH,
    channel=1,
    frame_start=1 - start_frame
)
sound = se.sequences.new_sound(
    name='audio',
    filepath=INPUT_PATH,
    channel=2,
    frame_start=1 - start_frame
)

# Set trim for both media strips
for strip in (movie, sound):
    strip.frame_offset_start = start_frame
    strip.frame_final_duration = dur_frames

# Add speed effect for slow motion
speed = se.sequences.new_effect(
    name='slowmo',
    type='SPEED',
    channel=3,
    frame_start=1,
    frame_end=1 + dur_frames,
    seq1=movie
)
speed.speed_control = 'MULTIPLY'
speed.speed_factor = 1 / 1.5
speed.use_default_fade = False

# Extend movie strip to match render duration
movie.frame_final_duration = render_dur

# Add subtitle text strip
text = se.sequences.new_effect(
    name='subtitle',
    type='TEXT',
    channel=4,
    frame_start=1,
    frame_end=1 + render_dur
)
text.text = 'BIG BUNNY'
text.location = (0.5, 0.12)
text.align_x = 'CENTER'
text.align_y = 'BOTTOM'
text.use_box = True
text.box_color = (0, 0, 0, 0.6)

# Set render frame range
scene.frame_start = 1
scene.frame_end = render_dur

# Render animation
bpy.ops.render.render(animation=True)