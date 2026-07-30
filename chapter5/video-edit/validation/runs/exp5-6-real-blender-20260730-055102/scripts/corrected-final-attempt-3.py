import bpy

INPUT_PATH = "/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-055102/source.mov"
OUTPUT_PATH = "/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-055102/final.mp4"
FPS = 25
START_SECONDS = 9.0
END_SECONDS = 12.0

# Calculate timing parameters
start_frame = int(round(START_SECONDS * FPS))
dur_frames = max(1, int(round((END_SECONDS - START_SECONDS) * FPS))))
render_dur = int(round(dur_frames * 1.5))

# Clear existing scene data
bpy.ops.sequencer.select_all(action='SELECT')
bpy.ops.sequencer.delete()
scene = bpy.context.scene

# Create sequence editor
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

# Add slowmotion effect to video
speed = se.sequences.new_effect(
    name='slowmo',
    type='SPEED',
    channel=3,
    frame_start=1,
    frame_end=1 + dur_frames,
    seq1=movie
)
speed.use_default_fade = False
speed.speed_control = 'MULTIPLY'
speed.speed_factor = 1.0 / 1.5

# Extend video duration to match slowed render time
movie.frame_final_duration = render_dur

# Add subtitle text with background box
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
text.box_color = (0.0, 0.0, 0.0, 0.6)

# Configure render settings
scene.render.resolution_x = 854
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100
scene.render.fps = FPS
scene.render.fps_base = 1.0

# Configure output format
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.filepath = OUTPUT_PATH

# Set render frame range
scene.frame_start = 1
scene.frame_end = render_dur

# Execute render
bpy.ops.render.render(animation=True)