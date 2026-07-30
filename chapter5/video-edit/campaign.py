"""Real-media, real-Vision, real-Blender acceptance campaign for Experiment 5-6."""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI


ROOT = Path(__file__).resolve().parent
VALIDATION = ROOT / "validation"
SOURCE_CACHE = VALIDATION / "source_cache" / "big-buck-bunny-trailer-480p.mov"
SOURCE_URL = "https://download.blender.org/peach/trailer/trailer_480p.mov"
SOURCE_SHA256 = "36801b74638c12be9aa587e93cd18edfc9bc51a1c089ab2a19ee42beed9f497d"
BLENDER = Path("/Applications/Blender.app/Contents/MacOS/Blender")
GROUND_TRUTH = {"start": 9.08, "end": 11.20}
TARGET = (
    "the single continuous shot showing the large white rabbit walking alone in a sunny green "
    "meadow, after the ONE BIG RABBIT title and before the THREE RODENTS title"
)
REQUEST = (
    "Cut out the shot of the large white rabbit walking alone in the sunny meadow, slow it to "
    "1.5x duration, and add the subtitle BIG BUNNY along the bottom."
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if re.search(r"\b(?:sk|gh[opusr])-[A-Za-z0-9_-]{12,}\b", text):
        raise ValueError(f"credential-shaped value in {path}")
    path.write_text(text, encoding="utf-8")


def _probe(path: Path) -> dict[str, Any]:
    process = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration,size,format_name:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
            "-of", "json", str(path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return json.loads(process.stdout)


def _extract(source: Path, timestamp: float, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{timestamp:.3f}",
            "-i", str(source), "-frames:v", "1", "-vf", "scale=640:-2", "-y", str(output),
        ],
        check=True,
    )
    if not output.is_file():
        raise RuntimeError(f"ffmpeg produced no frame at {timestamp:.3f}s: {source}")


def _frame_set(source: Path, timestamps: list[float], directory: Path) -> list[dict[str, Any]]:
    result = []
    for timestamp in timestamps:
        # PNG avoids the local ffmpeg build's strict MJPEG full-range rejection
        # on the trailer's final credits frame while preserving the exact pixels.
        path = directory / f"frame-{timestamp:06.2f}.png"
        _extract(source, timestamp, path)
        result.append(
            {
                "timestamp_s": timestamp,
                "path": str(path),
                "sha256": _sha(path),
                "bytes": path.stat().st_size,
            }
        )
    return result


class Backend:
    def __init__(self, provider: str):
        if provider == "ark":
            key = os.environ.get("ARK_API_KEY")
            self.endpoint = os.environ.get("ARK_BASE_URL") or "https://ark.cn-beijing.volces.com/api/v3"
            self.model = os.environ.get("ARK_MODEL") or "doubao-seed-1-6-250615"
        elif provider == "moonshot":
            key = os.environ.get("MOONSHOT_API_KEY") or os.environ.get("KIMI_API_KEY")
            self.endpoint = os.environ.get("MOONSHOT_BASE_URL") or "https://api.moonshot.cn/v1"
            self.model = os.environ.get("KIMI_MODEL") or "kimi-k3"
        else:
            key = os.environ.get("OPENAI_API_KEY")
            self.endpoint = os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
            self.model = os.environ.get("OPENAI_MODEL") or "gpt-5.6-luna"
        if not key:
            raise RuntimeError(f"missing credential for {provider}")
        self.provider = provider
        self.receipt_checkpoint: Path | None = None
        self.client = OpenAI(api_key=key, base_url=self.endpoint, timeout=240, max_retries=0)


def _json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("model response must be an object")
    return value


def _call(
    backend: Backend,
    *,
    purpose: str,
    messages: list[dict[str, Any]],
    receipt_messages: list[dict[str, Any]],
    receipts: list[dict[str, Any]],
    max_tokens: int,
) -> dict[str, Any]:
    request: dict[str, Any] = {
        "model": backend.model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    started = time.perf_counter()
    response = backend.client.chat.completions.create(**request)
    latency = round(time.perf_counter() - started, 3)
    content = response.choices[0].message.content or ""
    usage = response.usage
    receipts.append(
        {
            "purpose": purpose,
            "provider": backend.provider,
            "endpoint": backend.endpoint,
            "request": {
                "model": backend.model,
                "messages": receipt_messages,
                "temperature": 0,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            },
            "response": {
                "id": response.id,
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
                "content": content,
            },
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            },
            "latency_s": latency,
        }
    )
    if backend.receipt_checkpoint is not None:
        _write_json(backend.receipt_checkpoint, {"calls": receipts})
    return _json_object(content)


def _vision(
    backend: Backend,
    *,
    purpose: str,
    prompt: str,
    frames: list[dict[str, Any]],
    receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    summarized: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for frame in frames:
        path = Path(frame["path"])
        content.append({"type": "text", "text": f"timestamp={frame['timestamp_s']:.2f}s"})
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii"),
                    "detail": "low",
                },
            }
        )
        summarized.append({"type": "text", "text": f"timestamp={frame['timestamp_s']:.2f}s"})
        summarized.append(
            {
                "type": "image_artifact",
                "path": frame["path"],
                "sha256": frame["sha256"],
                "bytes": frame["bytes"],
            }
        )
    return _call(
        backend,
        purpose=purpose,
        messages=[{"role": "user", "content": content}],
        receipt_messages=[{"role": "user", "content": summarized}],
        receipts=receipts,
        max_tokens=700,
    )


def _bounds(value: dict[str, Any], duration: float) -> tuple[float, float]:
    start = float(value["start"])
    end = float(value["end"])
    if not (0 <= start < end <= duration):
        raise ValueError(f"invalid model interval [{start}, {end}] for duration {duration}")
    return start, end


def _script_is_safe(code: str, source: Path, output: Path) -> None:
    tree = ast.parse(code)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    if "bpy" not in imports:
        raise ValueError("generated script does not import bpy")
    forbidden_imports = {"subprocess", "socket", "requests", "urllib", "http", "ftplib"}
    if imports & forbidden_imports:
        raise ValueError(f"generated script imports forbidden modules: {sorted(imports & forbidden_imports)}")
    forbidden_calls = {"eval", "exec", "compile", "__import__", "system", "popen", "remove", "unlink", "rmtree"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = ""
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name.casefold() in forbidden_calls:
                raise ValueError(f"generated script calls forbidden function: {name}")
    if str(source.resolve()) not in code or str(output.resolve()) not in code:
        raise ValueError("generated script does not pin the supplied input and output paths")
    required_markers = ("new_movie", "frame_offset_start", "new_effect", "TEXT", "SPEED", "render")
    missing = [marker for marker in required_markers if marker not in code]
    if missing:
        raise ValueError(f"generated script omits requested Blender API operations: {missing}")


def _render_model_script(
    backend: Backend,
    *,
    label: str,
    source: Path,
    output: Path,
    start: float,
    end: float,
    scripts: Path,
    logs: Path,
    receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    prompt = f"""Generate a complete Blender 4.3 Python script for this video edit.

Input movie: {source.resolve()}
Output MP4: {output.resolve()}
Source FPS: 25
Source size: 853x480; render at 854x480 (one-pixel even-width pad required by H.264)
Trim interval: [{start:.3f}, {end:.3f}] seconds
Effects: slow playback so output duration is 1.5 times the trimmed interval; add bottom-centered subtitle BIG BUNNY with a visible semi-transparent dark box.

Requirements:
- Use bpy and Blender's Video Sequence Editor, including new_movie, new_sound when available, frame_offset_start/frame_final_duration, a SPEED effect, and a TEXT effect.
- Render exactly 854x480 at 25 fps through Blender to MPEG-4 H.264 with AAC audio.
- Set the scene frame range to the slowed duration and call bpy.ops.render.render(animation=True).
- Create only the requested output. Do not invoke ffmpeg, subprocesses, a shell, the network, or read credentials.
- Use APIs available in Blender 4.3 (scene.sequence_editor_create().sequences).
- In Blender 4.3, SpeedControlSequence has no use_audio property. Never read or assign use_audio, and do not apply a SPEED effect to the sound strip. A valid movie slow-motion pattern is speed_control='MULTIPLY', speed_factor=1/1.5, and extending the movie/render duration; the sound strip may remain normally trimmed.
- For the subtitle background, prefer the TEXT strip's use_box=True and box_color=(0,0,0,0.6); do not assume a COLOR strip has text-layout properties.

Use this real-Blender-4.3-validated timing pattern, substituting the supplied paths and interval but preserving the timing relationships exactly:
```
FPS = 25
start_frame = int(round(START_SECONDS * FPS))
dur_frames = max(1, int(round((END_SECONDS - START_SECONDS) * FPS)))
render_dur = int(round(dur_frames * 1.5))
se = scene.sequence_editor_create()
movie = se.sequences.new_movie(name='clip', filepath=INPUT_PATH, channel=1,
                               frame_start=1 - start_frame)
sound = se.sequences.new_sound(name='audio', filepath=INPUT_PATH, channel=2,
                               frame_start=1 - start_frame)
for strip in (movie, sound):
    strip.frame_offset_start = start_frame
    strip.frame_final_duration = dur_frames
speed = se.sequences.new_effect(name='slowmo', type='SPEED', channel=3,
                                frame_start=1, frame_end=1 + dur_frames, seq1=movie)
speed.use_default_fade = False
speed.speed_control = 'MULTIPLY'
speed.speed_factor = 1.0 / 1.5
movie.frame_final_duration = render_dur
text = se.sequences.new_effect(name='subtitle', type='TEXT', channel=4,
                               frame_start=1, frame_end=1 + render_dur)
text.text = 'BIG BUNNY'; text.location = (0.5, 0.12)
text.align_x = 'CENTER'; text.align_y = 'BOTTOM'
text.use_box = True; text.box_color = (0.0, 0.0, 0.0, 0.6)
scene.frame_start = 1; scene.frame_end = render_dur
```
This pattern was executed against Blender 4.3.2 and visibly retained the requested source frames through the whole slowed output. Do not replace its negative source-strip frame_start with frame_start=1: frame_offset_start would then move the visible strip later and render black frames.

Return one JSON object only: {{"code":"complete executable Python source"}}.
"""
    feedback = ""
    attempts: list[dict[str, Any]] = []
    for attempt in range(1, 7):
        payload = _call(
            backend,
            purpose=f"blender_script_{label}_attempt_{attempt}",
            messages=[
                {"role": "system", "content": "You are a Blender VSE engineer. Return one JSON object only."},
                {"role": "user", "content": prompt + (f"\nPrior executable feedback:\n{feedback}" if feedback else "")},
            ],
            receipt_messages=[
                {"role": "system", "content": "You are a Blender VSE engineer. Return one JSON object only."},
                {"role": "user", "content": prompt + (f"\nPrior executable feedback:\n{feedback}" if feedback else "")},
            ],
            receipts=receipts,
            max_tokens=7000,
        )
        code = payload.get("code")
        script_path = scripts / f"{label}-attempt-{attempt}.py"
        if not isinstance(code, str):
            feedback = "Response lacked a string code field."
            attempts.append({"attempt": attempt, "accepted": False, "error": feedback})
            continue
        script_path.write_text(code, encoding="utf-8")
        try:
            _script_is_safe(code, source, output)
        except (SyntaxError, ValueError) as exc:
            feedback = f"Static safety/API validation failed: {type(exc).__name__}: {exc}"
            attempts.append({"attempt": attempt, "script": str(script_path), "accepted": False, "error": feedback})
            continue
        if output.exists():
            output.unlink()
        started = time.perf_counter()
        process = subprocess.run(
            [str(BLENDER), "--background", "--python", str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300,
        )
        latency = round(time.perf_counter() - started, 3)
        log_path = logs / f"{label}-attempt-{attempt}.log"
        log_path.write_text(process.stdout, encoding="utf-8")
        accepted = (
            process.returncode == 0
            and "Traceback (most recent call last)" not in process.stdout
            and output.is_file()
            and output.stat().st_size > 1000
        )
        attempt_record = {
                "attempt": attempt,
                "script": str(script_path),
                "script_sha256": _sha(script_path),
                "blender_log": str(log_path),
                "blender_log_sha256": _sha(log_path),
                "blender_exit_code": process.returncode,
                "blender_latency_s": latency,
                "accepted": accepted,
        }
        if not accepted and output.is_file():
            partial_output = logs / f"{label}-attempt-{attempt}.partial.mp4"
            output.replace(partial_output)
            attempt_record["partial_output"] = str(partial_output)
            attempt_record["partial_output_sha256"] = _sha(partial_output)
        attempts.append(attempt_record)
        if accepted:
            return {"attempts": attempts, "accepted_script": str(script_path), "output": str(output)}
        feedback = (
            f"Blender exit={process.returncode}; output_exists={output.exists()}. "
            "Tail of real Blender log:\n" + "\n".join(process.stdout.splitlines()[-30:])
        )
    raise RuntimeError(f"model never generated an executable Blender script for {label}: {attempts}")


def _review(
    backend: Backend,
    *,
    purpose: str,
    clip: Path,
    directory: Path,
    receipts: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    duration = float(_probe(clip)["format"]["duration"])
    timestamps = sorted({round(min(0.35, duration / 5), 3), round(duration / 2, 3), round(max(0.0, duration - 0.35), 3)})
    frames = _frame_set(clip, timestamps, directory)
    prompt = f"""Independently review these actual rendered keyframes against this edit request:
{REQUEST}

The target source shot is: {TARGET}.
Judge the pixels, not filenames or claims. Return JSON exactly with:
{{"pass":boolean,"target_present":boolean,"irrelevant_content_present":boolean,
  "subtitle_visible":boolean,"feedback":"specific evidence from the frames"}}.
Pass only if all frames show the intended large white rabbit meadow shot without title cards or unrelated scenes and the BIG BUNNY subtitle is visibly overlaid near the bottom.
"""
    result = _vision(backend, purpose=purpose, prompt=prompt, frames=frames, receipts=receipts)
    for key in ("pass", "target_present", "irrelevant_content_present", "subtitle_visible"):
        if not isinstance(result.get(key), bool):
            raise ValueError(f"review response lacks boolean {key}")
    return result, frames


def _refine_boundaries(
    backend: Backend,
    *,
    source: Path,
    duration: float,
    start: float,
    end: float,
    reviewer_feedback: str,
    round_number: int,
    directory: Path,
    receipts: list[dict[str, Any]],
) -> tuple[float, float, dict[str, Any], list[dict[str, Any]]]:
    """Ask Vision to tighten a rejected edit using dense source-frame evidence.

    Ground-truth annotations are deliberately not supplied here: the next edit
    must be driven by the independent review and actual source pixels.
    """
    lo = max(0.0, start - 1.0)
    hi = min(duration, end + 1.0)
    first_tick = math.ceil(lo * 4)
    last_tick = math.floor(hi * 4)
    timestamps = [tick / 4 for tick in range(first_tick, last_tick + 1)]
    frames = _frame_set(source, timestamps, directory)
    prompt = f"""A rendered video edit was rejected by an independent pixel reviewer.
Target shot: {TARGET}
Prior attempted source interval: [{start:.3f}, {end:.3f}] seconds
Reviewer feedback: {reviewer_feedback}

These are dense 0.25-second frames from the source around both attempted boundaries.
Using only the timestamped pixels and the reviewer feedback, return the maximal safe
continuous interval containing the intended rabbit-meadow shot while excluding every
neighboring title card or unrelated shot. It is better to trim a fraction of a second
of the target than include even one title-card frame.
Return JSON exactly as {{"start":seconds,"end":seconds,"reason":"visual boundary evidence"}}.
"""
    result = _vision(
        backend,
        purpose=f"reviewer_driven_quarter_second_boundary_refinement_{round_number}",
        prompt=prompt,
        frames=frames,
        receipts=receipts,
    )
    refined_start, refined_end = _bounds(result, duration)
    return refined_start, refined_end, result, frames


def run(provider: str, run_id: str) -> dict[str, Any]:
    run_dir = VALIDATION / "runs" / run_id
    if run_dir.exists():
        raise FileExistsError(run_dir)
    run_dir.mkdir(parents=True)
    if not SOURCE_CACHE.is_file() or _sha(SOURCE_CACHE) != SOURCE_SHA256:
        raise RuntimeError("pinned source cache missing or hash mismatch")
    if not BLENDER.is_file():
        raise RuntimeError(f"real Blender binary not found: {BLENDER}")
    source = run_dir / "source.mov"
    shutil.copy2(SOURCE_CACHE, source)
    source_probe = _probe(source)
    duration = float(source_probe["format"]["duration"])
    backend = Backend(provider)
    receipts: list[dict[str, Any]] = []
    backend.receipt_checkpoint = run_dir / "provider_receipts.checkpoint.json"
    frames_dir = run_dir / "frames"
    scripts_dir = run_dir / "scripts"
    logs_dir = run_dir / "blender_logs"
    scripts_dir.mkdir()
    logs_dir.mkdir()

    source_evidence = {
        "url": SOURCE_URL,
        "title": "Big Buck Bunny trailer (Blender Foundation Peach Open Movie Project)",
        "license": "Creative Commons Attribution 3.0",
        "license_url": "https://creativecommons.org/licenses/by/3.0/",
        "sha256": _sha(source),
        "probe": source_probe,
        "naturally_occurring_scenes": True,
        "ground_truth": {
            **GROUND_TRUTH,
            "target": TARGET,
            "method": "Human-labeled target shot bounded by ffmpeg scene-change frames; source inspection found transitions at 9.08 and 11.20 seconds.",
            "ffmpeg_scene_threshold": 0.35,
        },
    }
    _write_json(run_dir / "source_evidence.json", source_evidence)

    # Container audio extends slightly beyond the last decodable video frame;
    # stay 1.5 s inside format duration for the final sparse sample.
    coarse_times = [0.0, 10.0, 20.0, 30.0, round(duration - 1.5, 3)]
    coarse_frames = _frame_set(source, coarse_times, frames_dir / "coarse")
    coarse_prompt = f"""These are frames from one contiguous real trailer sampled about every 10 seconds.
Locate this target: {TARGET}.
Return JSON {{"start":seconds,"end":seconds,"reason":"visual evidence"}} with a rough continuous interval. Use timestamps and visual content only."""
    coarse = _vision(
        backend,
        purpose="coarse_10_second_visual_localization",
        prompt=coarse_prompt,
        frames=coarse_frames,
        receipts=receipts,
    )
    coarse_start, coarse_end = _bounds(coarse, duration)
    midpoint = (coarse_start + coarse_end) / 2
    fine_lo = max(0, math.floor(midpoint - 10))
    fine_hi = min(duration, math.ceil(midpoint + 10))
    fine_times = [float(value) for value in range(int(fine_lo), int(math.floor(fine_hi)) + 1)]
    fine_frames = _frame_set(source, fine_times, frames_dir / "fine")
    fine_prompt = f"""These are one-second samples from the narrowed window [{fine_lo:.1f}, {fine_hi:.1f}] seconds of the same real trailer.
Precisely locate the boundaries of this one continuous target shot: {TARGET}.
Return JSON {{"start":seconds,"end":seconds,"reason":"visual boundary evidence"}}. The answer may interpolate between adjacent one-second samples; do not include either neighboring title card."""
    fine = _vision(
        backend,
        purpose="fine_1_second_visual_localization",
        prompt=fine_prompt,
        frames=fine_frames,
        receipts=receipts,
    )
    start, end = _bounds(fine, duration)
    localization = {
        "request": REQUEST,
        "target": TARGET,
        "coarse_interval_s": 10,
        "coarse_frames": coarse_frames,
        "coarse_result": coarse,
        "fine_interval_s": 1,
        "fine_window": [fine_lo, fine_hi],
        "fine_frames": fine_frames,
        "fine_result": fine,
        "ground_truth": GROUND_TRUTH,
        "start_error_s": round(abs(start - GROUND_TRUTH["start"]), 3),
        "end_error_s": round(abs(end - GROUND_TRUTH["end"]), 3),
    }
    _write_json(run_dir / "localization.json", localization)

    negative_output = run_dir / "negative_control.mp4"
    negative_render = _render_model_script(
        backend,
        label="negative-control",
        source=source,
        output=negative_output,
        start=0.0,
        end=3.0,
        scripts=scripts_dir,
        logs=logs_dir,
        receipts=receipts,
    )
    negative_review, negative_frames = _review(
        backend,
        purpose="review_negative_control_rendered_pixels",
        clip=negative_output,
        directory=frames_dir / "negative-review",
        receipts=receipts,
    )
    correction_triggered = negative_review["pass"] is False
    if not correction_triggered:
        raise RuntimeError("independent reviewer failed to reject the obvious wrong-shot negative control")

    final_output = run_dir / "final.mp4"
    final_render = _render_model_script(
        backend,
        label="corrected-final",
        source=source,
        output=final_output,
        start=start,
        end=end,
        scripts=scripts_dir,
        logs=logs_dir,
        receipts=receipts,
    )
    final_review, final_frames = _review(
        backend,
        purpose="review_corrected_final_rendered_pixels",
        clip=final_output,
        directory=frames_dir / "final-review",
        receipts=receipts,
    )
    correction_rounds: list[dict[str, Any]] = [
        {
            "round": 0,
            "kind": "initial_fine_localization",
            "plan": {"start": start, "end": end, "effects": ["slowmo:1.5", "subtitle:BIG BUNNY"]},
            "render": final_render,
            "review": final_review,
            "frames": final_frames,
        }
    ]
    # A reviewer rejection is actionable evidence, not merely a failed gate.
    # Densely inspect the real source pixels, ask Vision to tighten the interval,
    # then generate and execute a fresh Blender script before reviewing again.
    for refinement_round in range(1, 4):
        if final_review["pass"]:
            break
        prior_start, prior_end = start, end
        start, end, refinement, refinement_frames = _refine_boundaries(
            backend,
            source=source,
            duration=duration,
            start=prior_start,
            end=prior_end,
            reviewer_feedback=str(final_review.get("feedback") or ""),
            round_number=refinement_round,
            directory=frames_dir / f"boundary-refinement-{refinement_round}",
            receipts=receipts,
        )
        final_render = _render_model_script(
            backend,
            label=f"corrected-final-refinement-{refinement_round}",
            source=source,
            output=final_output,
            start=start,
            end=end,
            scripts=scripts_dir,
            logs=logs_dir,
            receipts=receipts,
        )
        final_review, final_frames = _review(
            backend,
            purpose=f"review_corrected_final_refinement_{refinement_round}_rendered_pixels",
            clip=final_output,
            directory=frames_dir / f"final-review-refinement-{refinement_round}",
            receipts=receipts,
        )
        correction_rounds.append(
            {
                "round": refinement_round,
                "kind": "reviewer_driven_quarter_second_refinement",
                "prior_interval": [prior_start, prior_end],
                "source_frames": refinement_frames,
                "refinement": refinement,
                "plan": {"start": start, "end": end, "effects": ["slowmo:1.5", "subtitle:BIG BUNNY"]},
                "render": final_render,
                "review": final_review,
                "frames": final_frames,
            }
        )
    localization["reviewer_driven_refinements"] = [
        {
            "round": item["round"],
            "prior_interval": item["prior_interval"],
            "source_frames": item["source_frames"],
            "result": item["refinement"],
        }
        for item in correction_rounds[1:]
    ]
    localization["final_interval"] = [start, end]
    localization["final_start_error_s"] = round(abs(start - GROUND_TRUTH["start"]), 3)
    localization["final_end_error_s"] = round(abs(end - GROUND_TRUTH["end"]), 3)
    _write_json(run_dir / "localization.json", localization)
    final_probe = _probe(final_output)
    output_duration = float(final_probe["format"]["duration"])
    expected_duration = (end - start) * 1.5
    blender_version = subprocess.run(
        [str(BLENDER), "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    ).stdout
    (run_dir / "blender_version.txt").write_text(blender_version, encoding="utf-8")
    _write_json(
        run_dir / "review.json",
        {
            "negative_control": {
                "plan": {"start": 0.0, "end": 3.0, "effects": ["slowmo:1.5", "subtitle:BIG BUNNY"]},
                "render": negative_render,
                "review": negative_review,
                "frames": negative_frames,
            },
            "correction_triggered": correction_triggered,
            "correction_rounds": correction_rounds,
            "corrected_final": {
                "plan": {"start": start, "end": end, "effects": ["slowmo:1.5", "subtitle:BIG BUNNY"]},
                "render": final_render,
                "review": final_review,
                "frames": final_frames,
                "probe": final_probe,
                "expected_slowed_duration_s": expected_duration,
                "observed_duration_s": output_duration,
            },
        },
    )
    _write_json(run_dir / "provider_receipts.json", {"calls": receipts})

    video_streams = [stream for stream in final_probe["streams"] if stream.get("codec_type") == "video"]
    gates = {
        "pinned_real_public_multiscene_source": source_evidence["sha256"] == SOURCE_SHA256,
        "coarse_real_vision_about_10_seconds": len(coarse_frames) >= 4 and bool(coarse.get("reason")),
        "fine_real_vision_every_1_second": len(fine_frames) >= 10 and all(
            abs(b["timestamp_s"] - a["timestamp_s"] - 1.0) < 1e-6 for a, b in zip(fine_frames, fine_frames[1:])
        ),
        "start_boundary_error_le_3s": localization["final_start_error_s"] <= 3.0,
        "end_boundary_error_le_3s": localization["final_end_error_s"] <= 3.0,
        "model_generated_blender_python": all(
            Path(item["accepted_script"]).is_file()
            for item in [negative_render, *[round_["render"] for round_ in correction_rounds]]
        ),
        "actual_blender_execution": all(
            any(attempt.get("accepted") and attempt.get("blender_exit_code") == 0 for attempt in item["attempts"])
            for item in [negative_render, *[round_["render"] for round_ in correction_rounds]]
        ),
        "reviewer_rejected_bad_edit": negative_review["pass"] is False and negative_review["target_present"] is False,
        "reviewer_triggered_correction": correction_triggered,
        "reviewer_accepted_corrected_pixels": final_review["pass"] is True and final_review["target_present"] is True,
        "subtitle_visually_verified": final_review["subtitle_visible"] is True,
        "slow_motion_duration_verified": abs(output_duration - expected_duration) <= 0.8,
        "final_format_and_quality": bool(video_streams)
        and video_streams[0].get("codec_name") == "h264"
        and int(video_streams[0].get("width") or 0) == 854
        and int(video_streams[0].get("height") or 0) == 480,
        "raw_receipts_usage_latency_complete": all(
            call.get("response")
            and call.get("latency_s") is not None
            and call.get("usage", {}).get("prompt_tokens") is not None
            and call.get("usage", {}).get("completion_tokens") is not None
            for call in receipts
        ),
    }
    official_complete = all(gates.values())
    artifacts = {
        str(path.relative_to(run_dir)): {"sha256": _sha(path), "bytes": path.stat().st_size}
        for path in sorted(run_dir.rglob("*"))
        if path.is_file()
    }
    manifest = {
        "schema_version": "1.0",
        "experiment": "5-6",
        "run_id": run_id,
        "generated_at_utc": _utc(),
        "provider": backend.provider,
        "model": backend.model,
        "source_url": SOURCE_URL,
        "source_sha256": SOURCE_SHA256,
        "blender_binary": str(BLENDER),
        "blender_version": blender_version.splitlines()[0],
        "localization": {
            "predicted": [start, end],
            "ground_truth": [GROUND_TRUTH["start"], GROUND_TRUTH["end"]],
            "errors_s": [localization["final_start_error_s"], localization["final_end_error_s"]],
            "reviewer_driven_refinement_rounds": len(correction_rounds) - 1,
        },
        "final_video": {"path": "final.mp4", "sha256": _sha(final_output), "probe": final_probe},
        "model_call_count": len(receipts),
        "gates": gates,
        "artifacts": artifacts,
        "official_complete": official_complete,
    }
    _write_json(run_dir / "manifest.json", manifest)
    if not official_complete:
        raise RuntimeError("Experiment 5-6 acceptance gates failed: " + json.dumps(gates))
    _write_json(
        VALIDATION / "latest.json",
        {
            "experiment": "5-6",
            "run_id": run_id,
            "manifest": str((run_dir / "manifest.json").relative_to(ROOT)),
            "manifest_sha256": _sha(run_dir / "manifest.json"),
            "official_complete": True,
        },
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=("ark", "moonshot", "openai"), default="ark")
    parser.add_argument("--run-id", default=f"exp5-6-real-blender-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    args = parser.parse_args()
    print(json.dumps(run(args.provider, args.run_id), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
