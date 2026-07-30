"""Canonical real-API paper-to-lecture-video campaign for Experiment 5-5."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "experiment_protocol.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def run(command: list[str]) -> str:
    process = subprocess.run(command, text=True, capture_output=True)
    if process.returncode:
        raise RuntimeError(f"command failed ({process.returncode}): {' '.join(command)}\n{process.stderr}")
    return process.stdout


def probe(path: Path) -> dict[str, Any]:
    return json.loads(run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)
    ]))


def duration(probe_result: dict[str, Any]) -> float:
    return float(probe_result["format"]["duration"])


def parse_json_content(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("provider response did not contain a JSON object")
    value = json.loads(text[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError("provider response was not a JSON object")
    return value


def cached_json_call(
    path: Path,
    client: OpenAI,
    *,
    provider: str,
    model: str,
    messages: list[dict[str, Any]],
    max_tokens: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    signature = sha256_bytes(json.dumps({
        "provider": provider, "model": model, "messages": messages,
    }, ensure_ascii=False, sort_keys=True).encode())
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached.get("signature") != signature:
            raise RuntimeError(f"cached provider-call signature mismatch: {path}")
        return cached["parsed"], cached["receipt"]
    failed_attempts: list[dict[str, Any]] = []
    for attempt in range(1, 4):
        started = time.perf_counter()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=1,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        raw = response.model_dump(mode="json")
        receipt = {
            "provider": provider,
            "request": {"model": model, "messages": messages, "temperature": 1, "max_tokens": max_tokens, "response_format": {"type": "json_object"}},
            "response": raw,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "json_attempt": attempt,
        }
        try:
            parsed = parse_json_content(response.choices[0].message.content or "")
        except (ValueError, json.JSONDecodeError) as exc:
            # Providers occasionally ignore response_format or truncate an
            # object. Preserve the real failed receipt and retry the API; do
            # not fabricate a narration or visual judgment to fill the page.
            failed_attempts.append({"error": str(exc), "receipt": receipt})
            atomic_json(
                path.with_name(path.stem + ".failed-attempts.json"),
                {"signature": signature, "attempts": failed_attempts},
            )
            if attempt == 3:
                raise RuntimeError(
                    f"provider returned malformed JSON three times: {path}"
                ) from exc
            continue
        atomic_json(path, {"signature": signature, "parsed": parsed, "receipt": receipt})
        return parsed, receipt
    raise AssertionError("unreachable JSON retry loop")


def slide_sections(markdown: str) -> list[str]:
    parts = markdown.split("\n---\n")
    return [part.strip() for part in parts if "#" in part and "theme:" not in part]


def image_data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/png;base64,{encoded}"


def provider_receipt_valid(receipt: dict[str, Any], expected_model: str) -> bool:
    response = receipt.get("response") or {}
    usage = response.get("usage") or {}
    return bool(response.get("id") and response.get("model") == expected_model and usage.get("total_tokens") is not None)


def narration_prompt(section: str, page_index: int, total: int, feedback: str | None) -> str:
    return f"""你是一位严谨而自然的中文技术讲师，正在讲解论文 Attention Is All You Need。
这是第 {page_index}/{total} 页。下面给出该页真实 Slidev 源码：
<slide>\n{section}\n</slide>
请写一段 180–240 个中文字符左右的口语讲解。必须满足：
1. 用引导性叙事解释“为什么”和“它与前后页的关系”，不能逐条照读幻灯片；
2. 明确指向当前屏幕上的可见元素（标题、公式、表格、数值或图片）；有图片/表格/公式时必须说出观众该看哪里；
3. 不虚构源码中没有的数值或结论；开头/结尾与页序匹配；
4. 只返回 JSON：{{"narration":"...","visual_references":["..."]}}。
{('上一轮独立视觉审核反馈：' + feedback + '。请修正。') if feedback else ''}"""


def judge_prompt(narration: str, section: str) -> str:
    return f"""你是独立的讲解视频视觉审核员。图片是当前真实幻灯片；源码和旁白如下。
<slide_source>\n{section}\n</slide_source>
<narration>\n{narration}\n</narration>
请只按图片中实际可见内容审核：
- visual_alignment: 1–5，旁白是否准确呼应可见标题/公式/表格/图片；
- guiding_narrative: 1–5，是否是讲解而非逐条复述；
- factual_fidelity: 1–5，是否无虚构；
- visible_elements_referenced: 列出旁白确实提到的可见元素；
- issues: 具体问题列表。
只返回 JSON 对象。"""


def synthesize_fish(text: str, reference_id: str, output: Path) -> dict[str, Any]:
    from fish_audio_sdk import Session, TTSRequest

    started = time.perf_counter()
    request = TTSRequest(text=text, reference_id=reference_id, format="mp3")
    audio = b"".join(Session(os.environ["FISH_API_KEY"]).tts(request, backend="s1"))
    if len(audio) < 1024:
        raise RuntimeError("Fish Audio returned empty or implausibly small audio")
    output.write_bytes(audio)
    return {
        "provider": "Fish Audio",
        "model": "s1",
        "request": {
            "text_sha256": sha256_bytes(text.encode()),
            "text_characters": len(text),
            "reference_id_sha256": sha256_bytes(reference_id.encode()),
            "format": "mp3",
        },
        "response_artifact": {
            "path": output.name,
            "sha256": sha256_file(output),
            "bytes": output.stat().st_size,
        },
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def make_segment(slide: Path, audio: Path, output: Path, audio_duration: float) -> None:
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(slide),
        "-i", str(audio), "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-r", "30", "-vf", "scale=1280:720", "-c:a", "aac", "-b:a", "192k",
        "-t", f"{audio_duration:.6f}", "-movflags", "+faststart", str(output),
    ])


def process_page(
    run_dir: Path,
    narration_client: OpenAI,
    vision_client: OpenAI,
    protocol: dict[str, Any],
    page_number: int,
    source_page: int,
    slide: Path,
    section: str,
    reference_id: str,
) -> dict[str, Any]:
    cache = run_dir / "provider_calls"
    cache.mkdir(exist_ok=True)
    max_rounds = int(protocol["acceptance"]["maximum_generation_review_rounds"])
    narration_model = protocol["providers"]["narration"]["model"]
    vision_model = protocol["providers"]["independent_visual_reviewer"]["model"]
    attempts = []
    feedback = None
    selected = None
    for attempt in range(1, max_rounds + 1):
        messages = [{"role": "user", "content": narration_prompt(section, page_number, protocol["acceptance"]["pages"], feedback)}]
        generated, narration_receipt = cached_json_call(
            cache / f"page-{page_number:02d}-narration-{attempt}.json", narration_client,
            provider="Moonshot", model=narration_model, messages=messages, max_tokens=1200,
        )
        narration = str(generated.get("narration") or "").strip()
        if not narration:
            raise RuntimeError(f"empty narration on page {page_number}, attempt {attempt}")
        judge_messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": judge_prompt(narration, section)},
                {"type": "image_url", "image_url": {"url": image_data_url(slide)}},
            ],
        }]
        judged, judge_receipt = cached_json_call(
            cache / f"page-{page_number:02d}-vision-{attempt}.json", vision_client,
            provider="DashScope", model=vision_model, messages=judge_messages, max_tokens=1200,
        )
        scores = {
            name: int(judged.get(name, 0) or 0)
            for name in ("visual_alignment", "guiding_narrative", "factual_fidelity")
        }
        current = {
            "attempt": attempt,
            "narration": narration,
            "visual_references": generated.get("visual_references") or [],
            "judge": judged,
            "scores": scores,
            "narration_receipt": narration_receipt,
            "vision_receipt": judge_receipt,
        }
        attempts.append(current)
        if min(scores.values()) >= int(protocol["acceptance"]["minimum_visual_alignment_score"]):
            selected = current
            break
        feedback = json.dumps(judged.get("issues") or judged, ensure_ascii=False)
    if selected is None:
        selected = max(attempts, key=lambda item: min(item["scores"].values()))

    audio = run_dir / "audio" / f"page-{page_number:02d}.mp3"
    audio.parent.mkdir(exist_ok=True)
    tts_receipt_path = run_dir / "provider_calls" / f"page-{page_number:02d}-fish-tts.json"
    expected_text_hash = sha256_bytes(selected["narration"].encode())
    if tts_receipt_path.exists() and audio.exists():
        tts_receipt = json.loads(tts_receipt_path.read_text(encoding="utf-8"))
        if (
            tts_receipt["request"]["text_sha256"] != expected_text_hash
            or tts_receipt["response_artifact"]["sha256"] != sha256_file(audio)
        ):
            raise RuntimeError(f"Fish TTS checkpoint mismatch for page {page_number}")
    else:
        tts_receipt = synthesize_fish(selected["narration"], reference_id, audio)
        atomic_json(tts_receipt_path, tts_receipt)
    audio_probe = probe(audio)
    audio_duration = duration(audio_probe)
    segment = run_dir / "segments" / f"page-{page_number:02d}.mp4"
    segment.parent.mkdir(exist_ok=True)
    make_segment(slide, audio, segment, audio_duration)
    segment_probe = probe(segment)
    segment_duration = duration(segment_probe)
    return {
        "page": page_number,
        "source_page": source_page,
        "slide": {"path": str(slide.relative_to(run_dir)), "sha256": sha256_file(slide), "bytes": slide.stat().st_size},
        "section_sha256": sha256_bytes(section.encode()),
        "selected_attempt": selected["attempt"],
        "narration": selected["narration"],
        "narration_characters": len(selected["narration"]),
        "visual_references": selected["visual_references"],
        "review": selected["judge"],
        "scores": selected["scores"],
        "attempts": attempts,
        "tts_receipt": tts_receipt,
        "audio": {"path": str(audio.relative_to(run_dir)), "sha256": sha256_file(audio), "bytes": audio.stat().st_size, "seconds": audio_duration, "probe": audio_probe},
        "segment": {"path": str(segment.relative_to(run_dir)), "sha256": sha256_file(segment), "bytes": segment.stat().st_size, "seconds": segment_duration, "probe": segment_probe},
        "av_delta_seconds": abs(segment_duration - audio_duration),
    }


def concat_segments(run_dir: Path, pages: list[dict[str, Any]], output: Path) -> None:
    listing = run_dir / "segments" / "concat.txt"
    listing.write_text("".join(
        f"file '{(run_dir / page['segment']['path']).resolve()}'\n" for page in pages
    ), encoding="utf-8")
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
        "-c", "copy", "-movflags", "+faststart", str(output),
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    load_dotenv(HERE / ".env")
    required = ("MOONSHOT_API_KEY", "DASHSCOPE_API_KEY", "FISH_API_KEY")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"missing required real-provider credentials: {missing}")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe are required")

    protocol_bytes = PROTOCOL_PATH.read_bytes()
    protocol = json.loads(protocol_bytes)
    protocol_hash = sha256_bytes(protocol_bytes)
    run_dir = (args.output or HERE / "validation" / "runs" / f"exp5-5-real-{datetime.now().strftime('%Y%m%d-%H%M%S')}").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    protocol_copy = run_dir / "experiment_protocol.json"
    if protocol_copy.exists() and protocol_copy.read_bytes() != protocol_bytes:
        raise RuntimeError("run directory has a different frozen protocol")
    protocol_copy.write_bytes(protocol_bytes)

    source_spec = protocol["source"]
    paper = (HERE / source_spec["paper"]).resolve()
    markdown_path = (HERE / source_spec["slide_markdown"]).resolve()
    rendered = (HERE / source_spec["rendered_slides"]).resolve()
    for path in (paper, markdown_path, rendered):
        if not path.exists():
            raise RuntimeError(f"required Experiment 5-4 source is missing: {path}")
    sections = slide_sections(markdown_path.read_text(encoding="utf-8"))
    selected_pages = [int(value) for value in source_spec["selected_pages"]]
    if len(selected_pages) != int(protocol["acceptance"]["pages"]):
        raise RuntimeError("selected page count differs from protocol")
    slides_dir = run_dir / "slides"
    slides_dir.mkdir(exist_ok=True)
    page_inputs = []
    for page_number, source_page in enumerate(selected_pages, 1):
        source_image = rendered / f"{source_page}.png"
        copied = slides_dir / f"page-{page_number:02d}-source-{source_page:02d}.png"
        if not copied.exists():
            shutil.copy2(source_image, copied)
        elif sha256_file(copied) != sha256_file(source_image):
            raise RuntimeError(f"copied slide mutated: {copied}")
        page_inputs.append((page_number, source_page, copied, sections[source_page - 1]))

    voice_manifest_path = (HERE / protocol["providers"]["tts"]["authorized_reference_manifest"]).resolve()
    voice_manifest = json.loads(voice_manifest_path.read_text(encoding="utf-8"))
    reference_id = str(voice_manifest.get("source_reference_id") or "")
    if not reference_id:
        raise RuntimeError("authorized Fish voice manifest has no source_reference_id")
    narration_provider = protocol["providers"]["narration"]
    vision_provider = protocol["providers"]["independent_visual_reviewer"]
    narration_client = OpenAI(api_key=os.environ["MOONSHOT_API_KEY"], base_url=narration_provider["endpoint"], timeout=180, max_retries=3)
    vision_client = OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"], base_url=vision_provider["endpoint"], timeout=180, max_retries=3)

    page_results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                process_page, run_dir, narration_client, vision_client, protocol,
                page_number, source_page, slide, section, reference_id,
            ): page_number
            for page_number, source_page, slide, section in page_inputs
        }
        for future in as_completed(futures):
            page = futures[future]
            result = future.result()
            page_results.append(result)
            print(f"page {page}/12 complete: {result['audio']['seconds']:.2f}s", flush=True)
    page_results.sort(key=lambda item: item["page"])
    final_video = run_dir / "lecture.mp4"
    concat_segments(run_dir, page_results, final_video)
    video_probe = probe(final_video)
    video_duration = duration(video_probe)
    audio_total = sum(page["audio"]["seconds"] for page in page_results)
    streams = video_probe["streams"]
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    min_score = int(protocol["acceptance"]["minimum_visual_alignment_score"])
    acceptance = {
        "real_paper_and_experiment_5_4_slides": len(paper.read_bytes()) > 1_000_000 and len(page_results) == 12,
        "twelve_selected_real_rendered_pages": len({page["slide"]["sha256"] for page in page_results}) == 12,
        "live_narration_provider_receipts": all(
            provider_receipt_valid(attempt["narration_receipt"], narration_provider["model"])
            for page in page_results for attempt in page["attempts"]
        ),
        "independent_live_vision_review_receipts": all(
            provider_receipt_valid(attempt["vision_receipt"], vision_provider["model"])
            for page in page_results for attempt in page["attempts"]
        ),
        "visual_narrative_alignment": all(min(page["scores"].values()) >= min_score for page in page_results),
        "real_fish_s1_audio_each_page": all(
            page["tts_receipt"]["provider"] == "Fish Audio"
            and page["tts_receipt"]["model"] == "s1"
            and page["audio"]["bytes"] > 1024
            for page in page_results
        ),
        "per_page_display_matches_audio": all(
            page["av_delta_seconds"] <= float(protocol["acceptance"]["per_page_av_alignment_tolerance_seconds"])
            for page in page_results
        ),
        "duration_5_to_15_minutes": float(protocol["acceptance"]["duration_seconds_min"]) <= video_duration <= float(protocol["acceptance"]["duration_seconds_max"]),
        "final_duration_matches_page_audio": abs(video_duration - audio_total) <= float(protocol["acceptance"]["final_duration_tolerance_seconds"]),
        "h264_video_and_aac_audio": bool(video_streams and audio_streams) and video_streams[0]["codec_name"] == "h264" and audio_streams[0]["codec_name"] == "aac",
        "raw_artifact_hashes": all(page["audio"]["sha256"] and page["segment"]["sha256"] and page["slide"]["sha256"] for page in page_results),
    }
    acceptance["passed"] = all(acceptance.values())
    evidence = {
        "experiment_id": "5-5",
        "status": "passed" if acceptance["passed"] else "partial",
        "created_at": utc_now(),
        "protocol_sha256": protocol_hash,
        "source": {
            "paper": str(paper), "paper_sha256": sha256_file(paper), "paper_bytes": paper.stat().st_size,
            "slide_markdown": str(markdown_path), "slide_markdown_sha256": sha256_file(markdown_path),
            "selected_source_pages": selected_pages,
            "voice_manifest_sha256": sha256_file(voice_manifest_path),
            "authorized_reference_id_sha256": sha256_bytes(reference_id.encode()),
        },
        "scope": {"pages": len(page_results), "narration_and_review_attempts": sum(len(page["attempts"]) for page in page_results)},
        "summary": {"audio_seconds_sum": audio_total, "video_seconds": video_duration, "minutes": video_duration / 60, "max_av_delta_seconds": max(page["av_delta_seconds"] for page in page_results)},
        "acceptance": acceptance,
        "pages": page_results,
        "final_video": {"path": final_video.name, "sha256": sha256_file(final_video), "bytes": final_video.stat().st_size, "probe": video_probe},
    }
    comparison = run_dir / "comparison.json"
    atomic_json(comparison, evidence)
    artifacts = {
        str(path.relative_to(run_dir)): {"sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in sorted(item for item in run_dir.rglob("*") if item.is_file() and item.name != "manifest.json")
    }
    manifest = {
        "experiment_id": "5-5", "status": evidence["status"], "acceptance": acceptance,
        "comparison_sha256": sha256_file(comparison), "artifacts": artifacts,
    }
    manifest_path = run_dir / "manifest.json"
    atomic_json(manifest_path, manifest)
    atomic_json(HERE / "validation" / "latest.json", {
        "experiment_id": "5-5", "status": evidence["status"],
        "run_dir": str(run_dir.relative_to(HERE)), "manifest_sha256": sha256_file(manifest_path),
    })
    print(json.dumps({"status": evidence["status"], "summary": evidence["summary"], "acceptance": acceptance}, ensure_ascii=False, indent=2))
    return 0 if acceptance["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
