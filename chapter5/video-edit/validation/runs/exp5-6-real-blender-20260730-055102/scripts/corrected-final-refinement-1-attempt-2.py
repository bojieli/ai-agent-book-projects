import bpy

# Configuration
INPUT_PATH = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-055102/source.mov'
OUTPUT_PATH = '/Users/boj/book/ai-agent-book/chapter5/video-edit/validation/runs/exp5-6-real-blender-20260730-055102/final.mp4'
FPS = 25
START_SECONDS = 9.250
END_SECONDS = 11.000
RENDER_SIZE = (854, 480)

# Calculate timing
start_frame = int(round(START_SECONDS * FPS))
dur_frames = max(1, int(round((END_SECONDS - START_SECONDS) * FPS)))
render_dur = int(round(dur_frames * 1.5))

# Setup scene
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = render_dur

# Clear default objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create sequence editor
se = scene.sequence_editor_create()

# Add movie strip
movie = se.sequences.new_movie(
    name='clip',
    filepath=INPUT_PATH,
    channel=1,
    frame_start=1 - start_frame
)
movie.frame_offset_start = start_frame
movie.frame_final_duration = dur_frames

# Add sound strip
sound = se.sequences.new_sound(
    name='audio',
    filepath=INPUT_PATH,
    channel=2,
    frame_start=1 - start_frame
)
sound.frame_offset_start = start_frame
sound.frame_final_duration = dur_frames

# Add speed effect to movie
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
movie.frame_final_duration = render_dur

# Add subtitle text
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

# Render settings
scene.render.resolution_x = RENDER_SIZE[0]
scene.render.resolution_y = RENDER_SIZE[1]
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.filepath = OUTPUT_PATH

# Render animation
bpy.ops.render.render(animation=True)