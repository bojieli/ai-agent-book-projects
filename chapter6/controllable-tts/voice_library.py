"""24-file Fish Audio S1 reference-voice library and its builder."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from itertools import product
from pathlib import Path
from typing import Any

EMOTIONS = {
    "neutral": "calm",
    "happy": "happy",
    "frustrated": "frustrated",
    "thinking": "uncertain",
}
SPEEDS = {"normal": 1.0, "fast": 1.25, "slow": 0.8}
STYLES = {"formal": "confident", "casual": "relaxed"}

HERE = Path(__file__).parent
DEFAULT_LIBRARY_DIR = HERE / "reference_audio"
DEFAULT_MANIFEST = DEFAULT_LIBRARY_DIR / "manifest.json"


def profile_key(emotion: str, speed: str, style: str) -> str:
    return f"{emotion}_{speed}_{style}"


def reference_script(emotion: str, speed: str, style: str) -> tuple[str, str]:
    """Return S1-native synthesis text and the literal spoken transcript."""
    scripts = {
        ("formal", "slow"): "您好，我正在核对信息，请稍等。",
        ("formal", "normal"): "您好，我已收到您的请求，现在为您核对详细信息。",
        ("formal", "fast"): "您好，我已经收到您的请求，现在马上为您核对所有详细信息，请稍等片刻。",
        ("casual", "slow"): "你好呀，我正在帮你看看，稍等。",
        ("casual", "normal"): "你好呀，我收到你的请求啦，现在帮你看看具体情况。",
        ("casual", "fast"): "你好呀，我已经收到你的请求啦，现在马上帮你看看全部具体情况，稍等一下。",
    }
    spoken = scripts[(style, speed)]
    native = f"({EMOTIONS[emotion]})({STYLES[style]}){spoken}"
    return native, spoken


def _duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def build_reference_library(
    api_key: str,
    base_reference_id: str,
    output_dir: Path = DEFAULT_LIBRARY_DIR,
) -> dict[str, Any]:
    """Use Fish S1 to render 24 same-speaker, different-prosody references."""
    from fish_audio_sdk import Prosody, Session, TTSRequest

    output_dir.mkdir(parents=True, exist_ok=True)
    session = Session(api_key)
    profiles: dict[str, Any] = {}
    for emotion, speed, style in product(EMOTIONS, SPEEDS, STYLES):
        key = profile_key(emotion, speed, style)
        native_text, transcript = reference_script(emotion, speed, style)
        path = output_dir / f"{key}.mp3"
        request = TTSRequest(
            text=native_text,
            reference_id=base_reference_id,
            format="mp3",
            prosody=Prosody(speed=SPEEDS[speed], volume=0),
        )
        path.write_bytes(b"".join(session.tts(request, backend="s1")))
        profiles[key] = {
            "emotion": emotion,
            "speed": speed,
            "style": style,
            "path": path.name,
            "transcript": transcript,
            "s1_reference_prompt": native_text,
            "duration_seconds": round(_duration(path), 3),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    manifest = {
        "backend": "s1",
        "source_reference_id": base_reference_id,
        "dimensions": {"emotion": list(EMOTIONS), "speed": list(SPEEDS), "style": list(STYLES)},
        "profiles": profiles,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def load_voice_library(manifest_path: str | Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    path = Path(manifest_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Fish reference library not found: {path}. Run build_reference_library.py first."
        )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    profiles = manifest.get("profiles", {})
    if len(profiles) != 24:
        raise ValueError(f"Reference library must contain 24 profiles, found {len(profiles)}")
    for key, profile in profiles.items():
        audio = path.parent / profile["path"]
        if not audio.is_file() or hashlib.sha256(audio.read_bytes()).hexdigest() != profile["sha256"]:
            raise ValueError(f"Missing or modified reference audio for {key}: {audio}")
        profile["absolute_path"] = str(audio)
    return manifest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build the 4×3×2 Fish Audio S1 reference library")
    parser.add_argument("--base-reference-id", default=os.getenv("FISH_BASE_REFERENCE_ID"), required=False)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_LIBRARY_DIR)
    args = parser.parse_args()
    if not os.getenv("FISH_API_KEY") or not args.base_reference_id:
        parser.error("Set FISH_API_KEY and FISH_BASE_REFERENCE_ID (a voice you are authorized to use)")
    result = build_reference_library(os.environ["FISH_API_KEY"], args.base_reference_id, args.output_dir)
    print(f"Built {len(result['profiles'])} real Fish S1 reference clips in {args.output_dir}")
