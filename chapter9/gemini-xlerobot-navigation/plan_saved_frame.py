#!/usr/bin/env python3
"""Call Gemini Robotics-ER on one saved frame without executing robot tools."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import shutil
import traceback
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

MODEL = "gemini-robotics-er-1.5-preview"
TOOLS = ("move_forward", "turn_left", "turn_right")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def annotate_frame(source: Path, target: Path, fov_degrees: float) -> None:
    image = Image.open(source).convert("RGB")
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    horizon = int(height * 0.78)
    center_x = width / 2
    for angle in range(-int(fov_degrees // 2), int(fov_degrees // 2) + 1, 10):
        x = center_x + (angle / fov_degrees) * width
        draw.line([(center_x, horizon), (x, 0)], fill=(255, 230, 0, 150), width=max(1, width // 500))
        draw.text((max(0, min(width - 36, x - 12)), 4), f"{angle:+d}°", fill=(255, 230, 0, 255))
    draw.line([(center_x, 0), (center_x, height)], fill=(255, 60, 60, 190), width=max(1, width // 350))
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="PNG")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True, help="saved RGB frame; no camera is opened")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--annotated-image", type=Path, required=True)
    parser.add_argument("--fov-degrees", type=float, default=90.0)
    parser.add_argument("--task", default="find the kitchen and go there")
    parser.add_argument("--input-source-url")
    parser.add_argument("--input-source-commit")
    parser.add_argument("--already-annotated", action="store_true", help="preserve an upstream frame that already contains an angular scale")
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error(f"image does not exist: {args.image}")
    if not 0 < args.fov_degrees <= 180 or not math.isfinite(args.fov_degrees):
        parser.error("--fov-degrees must be in (0, 180]")

    if args.already_annotated:
        args.annotated_image.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.image, args.annotated_image)
        annotation_mode = "upstream_existing"
    else:
        annotate_frame(args.image, args.annotated_image, args.fov_degrees)
        annotation_mode = "companion_overlay"
    base = {
        "schema_version": "1.0",
        "experiment_id": "9-9",
        "kind": "non_actuating_saved_frame_plan",
        "acceptance_scope": "reference_input_api_validation_only_not_navigation_evidence",
        "model": MODEL,
        "task": args.task,
        "tools_declared_but_not_executed": list(TOOLS),
        "input_image": {"path": str(args.image), "sha256": sha256(args.image)},
        "annotated_image": {"path": str(args.annotated_image), "sha256": sha256(args.annotated_image), "fov_degrees": args.fov_degrees, "annotation_mode": annotation_mode},
        "input_provenance": {"source_url": args.input_source_url, "source_commit": args.input_source_commit},
        "actuation_attempted": False,
    }
    key_alias = "GEMINI_API_KEY" if os.environ.get("GEMINI_API_KEY") else "GOOGLE_API_KEY" if os.environ.get("GOOGLE_API_KEY") else None
    if not key_alias:
        base.update({"status": "blocked", "blocker": "Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set", "api_call_attempted": False})
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        print(f"BLOCKED: wrote {args.output} sha256={sha256(args.output)}")
        return 2

    from google import genai
    from google.genai import types

    declarations = [
        types.FunctionDeclaration(
            name=name,
            description={
                "move_forward": "Move the robot forward by one safe navigation increment.",
                "turn_left": "Turn the robot left by one safe navigation increment.",
                "turn_right": "Turn the robot right by one safe navigation increment.",
            }[name],
            parameters_json_schema={"type": "object", "properties": {}, "additionalProperties": False},
        )
        for name in TOOLS
    ]
    prompt = (
        f"Task: {args.task}. Inspect this angularly annotated robot-camera frame. "
        "Choose exactly one declared navigation tool and explain the visible cue. "
        "Do not claim that any physical action has occurred."
    )
    sdk_version = importlib.metadata.version("google-genai")
    client = genai.Client(api_key=os.environ[key_alias])
    image_bytes = args.annotated_image.read_bytes()
    started_at = datetime.now(timezone.utc).isoformat()
    start = time.perf_counter()
    model_lookup = None
    try:
        model_info = client.models.get(model=MODEL)
        model_lookup = model_info.model_dump(mode="json") if hasattr(model_info, "model_dump") else {"name": getattr(model_info, "name", None)}
        response = client.models.generate_content(
            model=MODEL,
            contents=[types.Part.from_bytes(data=image_bytes, mime_type="image/png"), prompt],
            config=types.GenerateContentConfig(tools=[types.Tool(function_declarations=declarations)], temperature=0),
        )
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        base.update({
            "status": "blocked",
            "api_call_attempted": True,
            "api_key_alias_used": key_alias,
            "started_at": started_at,
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "latency_ms": round(elapsed_ms, 3),
            "google_genai_version": sdk_version,
            "model_lookup": model_lookup,
            "provider_error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()},
            "token_usage": None,
            "estimated_cost_usd": None,
            "cost_note": "No successful response; no provider-reported token usage was available.",
        })
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        print(f"BLOCKED: exact model call failed; wrote {args.output} sha256={sha256(args.output)}")
        return 2

    elapsed_ms = (time.perf_counter() - start) * 1000
    raw = response.model_dump(mode="json") if hasattr(response, "model_dump") else {"text": getattr(response, "text", None)}
    usage = getattr(response, "usage_metadata", None)
    usage_json = usage.model_dump(mode="json") if hasattr(usage, "model_dump") else None
    base.update({
        "status": "complete",
        "api_call_attempted": True,
        "api_key_alias_used": key_alias,
        "started_at": started_at,
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "latency_ms": round(elapsed_ms, 3),
        "google_genai_version": sdk_version,
        "model_lookup": model_lookup,
        "provider_model_version": getattr(response, "model_version", None),
        "token_usage": usage_json,
        "estimated_cost_usd": None,
        "cost_note": "Token usage is provider-reported above; no authoritative Robotics-ER price was encoded, so cost is not estimated.",
        "raw_response": raw,
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} sha256={sha256(args.output)}; no tool was executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
