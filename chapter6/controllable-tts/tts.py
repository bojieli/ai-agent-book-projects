"""Fish Audio S1 zero-shot cloning execution layer."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from voice_library import DEFAULT_MANIFEST, load_voice_library, profile_key

MODEL = "s1"


def _session():
    from fish_audio_sdk import Session

    key = os.getenv("FISH_API_KEY")
    if not key:
        raise RuntimeError("Fish S1 synthesis requires FISH_API_KEY")
    return Session(key)


def synth_speech(
    text: str,
    emotion: str,
    speed: str,
    style: str,
    emphasis: bool,
    out_path: str | Path,
    *,
    voice_library: dict[str, Any],
) -> dict[str, Any]:
    """Clone from the selected real reference clip using Fish S1."""
    from fish_audio_sdk import Prosody, ReferenceAudio, TTSRequest

    key = profile_key(emotion, speed, style)
    profile = voice_library["profiles"][key]
    reference_path = Path(profile["absolute_path"])
    # S1 supports native parentheses markers, including real non-verbal sounds.
    fish_text = f"(emphasis){text}" if emphasis else text
    request = TTSRequest(
        text=fish_text,
        references=[ReferenceAudio(audio=reference_path.read_bytes(), text=profile["transcript"])],
        format="mp3",
        prosody=Prosody(speed=1.0, volume=0),
    )
    Path(out_path).write_bytes(b"".join(_session().tts(request, backend=MODEL)))
    return {
        "model": MODEL,
        "provider": "Fish Audio",
        "profile": key,
        "reference_path": reference_path.name,
        "reference_sha256": profile["sha256"],
        "fish_text": fish_text,
    }


def synth_direct_reference(text: str, reference_id: str, out_path: str | Path) -> dict[str, Any]:
    """Fish S1 without the 24-clip control library (configuration A)."""
    from fish_audio_sdk import TTSRequest

    request = TTSRequest(text=text, reference_id=reference_id, format="mp3")
    Path(out_path).write_bytes(b"".join(_session().tts(request, backend=MODEL)))
    return {"provider": "Fish Audio", "model": MODEL, "reference_id": reference_id}


def make_silence(ms: int, out_path: str | Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", f"{ms / 1000:.3f}", "-q:a", "9", str(out_path)],
        check=True,
    )


def concat_mp3(parts: list[Path], out_path: str | Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
        for part in parts:
            escaped = part.resolve().as_posix().replace("'", "'\\''")
            handle.write(f"file '{escaped}'\n")
        list_path = handle.name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", list_path,
             "-ar", "44100", "-ac", "1", "-b:a", "128k", str(out_path)],
            check=True,
        )
    finally:
        os.unlink(list_path)


def synthesize_segments(
    segments,
    out_path,
    workdir,
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST,
):
    if not segments:
        raise ValueError("No speech segments to synthesize")
    library = load_voice_library(manifest_path)
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    parts, info = [], []
    for index, segment in enumerate(segments):
        path = workdir / f"segment_{index:02d}.mp3"
        if segment["type"] == "silence":
            make_silence(segment["ms"], path)
            meta = {"type": "silence", "ms": segment["ms"]}
        else:
            meta = synth_speech(
                segment["text"], segment["emotion"], segment["speed"], segment["style"],
                segment.get("emphasis", False), path, voice_library=library,
            )
            meta.update(type="speech", text=segment["text"])
        parts.append(path)
        info.append(meta)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    if len(parts) == 1:
        Path(out_path).write_bytes(parts[0].read_bytes())
    else:
        concat_mp3(parts, out_path)
    return info
