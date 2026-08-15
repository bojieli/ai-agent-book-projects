#!/usr/bin/env python3
"""Create normal, long-pause and background-noise variants from one WAV."""

import argparse
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("output_dir", type=Path)
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=True)

duration = float(subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(args.source)
], text=True).strip())
split = duration * 0.55
normal = args.output_dir / "normal.wav"
pause = args.output_dir / "long_pause.wav"
noise = args.output_dir / "background_noise.wav"

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(args.source), "-ar", "16000", "-ac", "1", str(normal)], check=True)
filter_pause = (
    f"[0:a]atrim=0:{split},asetpts=PTS-STARTPTS[a];"
    f"[0:a]atrim={split},asetpts=PTS-STARTPTS[b];"
    "anullsrc=r=16000:cl=mono:d=0.9[s];[a][s][b]concat=n=3:v=0:a=1[out]"
)
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error", "-i", str(normal), "-filter_complex", filter_pause,
    "-map", "[out]", str(pause)
], check=True)
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error", "-i", str(normal),
    "-f", "lavfi", "-i", f"anoisesrc=color=pink:amplitude=0.12:d={duration}",
    "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:weights='1 1'[out]",
    "-map", "[out]", "-ar", "16000", "-ac", "1", str(noise)
], check=True)
print(normal)
print(pause)
print(noise)
