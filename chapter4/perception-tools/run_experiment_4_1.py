#!/usr/bin/env python3
"""Run Experiment 4-1 through the real perception MCP stdio transport.

The campaign exercises every sub-capability explicitly named by the manuscript.
It creates small local documents/media as deterministic inputs, uses live public
endpoints for network observations, confines mutation tools to a fresh fixture
workspace, and stores credential-safe receipts.  Missing private credentials
produce a blocked campaign; they can never satisfy acceptance.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any

from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
PROTOCOL_PATH = HERE / "experiment_protocol.json"
SERVER_PATH = HERE / "src" / "main.py"
VALIDATION_ROOT = HERE / "validation" / "experiment_4_1"

CASE_TO_TOOL = {
    "web_search": "web_search",
    "knowledge_base_search": "knowledge_base_search",
    "download": "download",
    "webpage_reader": "webpage_reader",
    "document_reader_pdf": "document_reader",
    "document_reader_docx": "document_reader",
    "document_reader_pptx": "document_reader",
    "image_ocr": "image_ocr",
    "image_analyze": "image_analyze",
    "audio_transcribe": "audio_transcribe",
    "video_parser": "video_parser",
    "video_analyze": "video_analyze",
    "file_reader": "file_reader",
    "grep": "grep",
    "directory_list": "directory_list",
    "filesystem_copy": "filesystem_copy",
    "filesystem_move": "filesystem_move",
    "filesystem_delete": "filesystem_delete",
    "reject_parent_traversal": "filesystem_copy",
    "reject_absolute_path": "filesystem_delete",
    "reject_escaping_symlink": "filesystem_delete",
    "weather": "weather",
    "yfinance_quote": "yfinance_quote",
    "currency_converter": "currency_converter",
    "wikipedia_search": "wikipedia_search",
    "arxiv_search": "arxiv_search",
    "calendar_events": "calendar_events",
    "notion_search": "notion_search",
}

PROVENANCE = {
    "web_search": {"backend": "duckduckgo-live-search", "origin": "live-api"},
    "knowledge_base_search": {"backend": "local-knowledge-files", "origin": "local-filesystem"},
    "download": {"backend": "tls-http-download", "origin": "live-api"},
    "webpage_reader": {"backend": "tls-http-beautifulsoup", "origin": "live-api"},
    "document_reader": {"backend": "format-aware-local-parser", "origin": "local-process"},
    "image_ocr": {"backend": "local-tesseract-ocr", "origin": "local-process"},
    "image_analyze": {"backend": "configured-vision-api", "origin": "live-api"},
    "audio_transcribe": {"backend": "local-whisper-or-openai", "origin": "local-process"},
    "video_parser": {"backend": "local-opencv", "origin": "local-process"},
    "video_analyze": {"backend": "opencv-and-configured-vision-api", "origin": "live-api"},
    "file_reader": {"backend": "local-filesystem", "origin": "local-filesystem"},
    "grep": {"backend": "local-regex-filesystem-search", "origin": "local-filesystem"},
    "directory_list": {"backend": "local-filesystem", "origin": "local-filesystem"},
    "filesystem_copy": {"backend": "workspace-confined-copy", "origin": "local-filesystem"},
    "filesystem_move": {"backend": "workspace-confined-rename", "origin": "local-filesystem"},
    "filesystem_delete": {"backend": "workspace-confined-quarantine", "origin": "local-filesystem"},
    "weather": {"backend": "open-meteo", "origin": "live-api"},
    "yfinance_quote": {"backend": "yahoo-finance-yfinance", "origin": "live-api"},
    "currency_converter": {"backend": "live-exchange-rate-api", "origin": "live-api"},
    "wikipedia_search": {"backend": "mediawiki", "origin": "live-api"},
    "arxiv_search": {"backend": "export.arxiv.org", "origin": "live-api"},
    "calendar_events": {"backend": "google-calendar-api", "origin": "private-live-api"},
    "notion_search": {"backend": "notion-api", "origin": "private-live-api"},
}

SIMULATION_PATTERN = re.compile(r"\b(mock(?:ed)?|placeholder|synthetic|simulat(?:ed|ion))\b", re.I)
MARKER = "PERCEPTION-EXPERIMENT-4-1-VERIFIED"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def file_receipt(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": sha256_bytes(data)}


def command_receipt(command: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=120)
    receipt = {
        "executable": command[0],
        "arguments": command[1:],
        "returncode": result.returncode,
        "stdout_sha256": sha256_bytes(result.stdout.encode()),
        "stderr_sha256": sha256_bytes(result.stderr.encode()),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    if result.returncode != 0:
        raise RuntimeError(f"fixture command failed: {receipt}")
    return receipt


def prepare_fixtures(campaign_dir: Path) -> dict[str, Any]:
    """Create small deterministic inputs with real document/media encoders."""
    fixtures = campaign_dir / "fixtures"
    knowledge = fixtures / "knowledge"
    documents = fixtures / "documents"
    media = fixtures / "media"
    downloads = fixtures / "downloads"
    mutation = fixtures / "mutation_workspace"
    for directory in (knowledge, documents, media, downloads, mutation / "nested"):
        directory.mkdir(parents=True, exist_ok=True)

    note = knowledge / "mcp-notes.md"
    note.write_text(
        f"# Experiment 4-1\n\n{MARKER}\nThe Model Context Protocol connects agents to perception tools.\n",
        encoding="utf-8",
    )
    (mutation / "seed.txt").write_text(f"{MARKER}\n", encoding="utf-8")
    (mutation / "nested" / "entry.txt").write_text("directory browse fixture\n", encoding="utf-8")

    outside_witness = fixtures / "outside-witness.txt"
    outside_witness.write_text("OUTSIDE-WITNESS-MUST-REMAIN\n", encoding="utf-8")
    (mutation / "escape-link").symlink_to(outside_witness)

    from reportlab.pdfgen import canvas

    pdf = documents / "sample.pdf"
    report = canvas.Canvas(str(pdf))
    report.drawString(72, 760, f"Experiment 4-1 PDF {MARKER}")
    report.save()

    from docx import Document

    docx = documents / "sample.docx"
    document = Document()
    document.add_heading("Experiment 4-1 DOCX", level=1)
    document.add_paragraph(MARKER)
    document.save(docx)

    from pptx import Presentation

    pptx = documents / "sample.pptx"
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[1])
    slide.shapes.title.text = "Experiment 4-1 PPTX"
    slide.placeholders[1].text = MARKER
    presentation.save(pptx)

    from PIL import Image, ImageDraw, ImageFont

    image = media / "ocr-source.png"
    canvas_image = Image.new("RGB", (1200, 360), "white")
    draw = ImageDraw.Draw(canvas_image)
    font_candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    font_path = next((path for path in font_candidates if path.is_file()), None)
    font = ImageFont.truetype(str(font_path), 54) if font_path else ImageFont.load_default()
    draw.text((45, 70), "EXPERIMENT 4-1", fill="black", font=font)
    draw.text((45, 170), "PERCEPTION TOOLS VERIFIED", fill="black", font=font)
    canvas_image.save(image)

    audio_aiff = media / "spoken-marker.aiff"
    if not shutil.which("say"):
        raise RuntimeError("macOS say executable is required for the speech fixture")
    say_receipt = command_receipt([
        "say", "-v", "Samantha", "-r", "150", "-o", str(audio_aiff),
        "Experiment four one. Perception tools verified.",
    ])

    video = media / "visual-marker.mp4"
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is required for the video fixture")
    ffmpeg_receipt = command_receipt([
        "ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(image),
        "-t", "1.5", "-r", "3", "-pix_fmt", "yuv420p", str(video),
    ])

    paths = {
        "fixtures": fixtures,
        "knowledge": knowledge,
        "note": note,
        "pdf": pdf,
        "docx": docx,
        "pptx": pptx,
        "image": image,
        "audio": audio_aiff,
        "video": video,
        "downloads": downloads,
        "mutation": mutation,
        "outside_witness": outside_witness,
    }
    receipt = {
        "marker": MARKER,
        "paths": {name: str(path) for name, path in paths.items()},
        "files": [
            file_receipt(path)
            for path in (note, pdf, docx, pptx, image, audio_aiff, video, outside_witness)
        ],
        "generators": {"say": say_receipt, "ffmpeg": ffmpeg_receipt},
    }
    write_json(campaign_dir / "fixture_receipt.json", receipt)
    return paths


def credential_preflight() -> dict[str, Any]:
    token_path = Path("~/.perception-tools/google_token.pickle").expanduser()
    return {
        "secret_values_recorded": False,
        "google_calendar": {
            "token_file_exists": token_path.is_file(),
            "token_file_bytes": token_path.stat().st_size if token_path.is_file() else 0,
            "oauth_credentials_sdk_importable": importlib.util.find_spec("google.oauth2.credentials") is not None,
            "calendar_sdk_importable": importlib.util.find_spec("googleapiclient.discovery") is not None,
        },
        "notion": {
            "api_key_present": bool(os.environ.get("NOTION_API_KEY")),
            "sdk_importable": importlib.util.find_spec("notion_client") is not None,
        },
        "multimodal": {
            "openai_key_present": bool(os.environ.get("OPENAI_API_KEY")),
            "openrouter_key_present": bool(os.environ.get("OPENROUTER_API_KEY")),
            "gemini_key_present": bool(os.environ.get("GEMINI_API_KEY")),
            "dashscope_key_present": bool(os.environ.get("DASHSCOPE_API_KEY")),
            "local_whisper_importable": importlib.util.find_spec("whisper") is not None,
            "pytesseract_importable": importlib.util.find_spec("pytesseract") is not None,
            "tesseract_executable_present": bool(shutil.which("tesseract")),
            "ffmpeg_executable_present": bool(shutil.which("ffmpeg")),
        },
    }


def _parse_text(text: str) -> Any:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def unwrap_mcp_result(result: Any) -> Any:
    structured = getattr(result, "structuredContent", None)
    if structured is None:
        structured = getattr(result, "structured_content", None)
    if structured:
        return structured
    texts = [getattr(item, "text", None) for item in getattr(result, "content", [])]
    texts = [text for text in texts if isinstance(text, str)]
    if len(texts) == 1:
        return _parse_text(texts[0])
    return [_parse_text(text) for text in texts]


def _action_message(payload: Any) -> Any:
    if isinstance(payload, dict):
        return payload.get("message", payload.get("data"))
    return None


def _action_metadata(payload: Any) -> dict[str, Any]:
    return payload.get("metadata", {}) if isinstance(payload, dict) else {}


def _declared_simulation_markers(payload: Any) -> list[str]:
    """Scan provenance-like fields, not arbitrary fetched page text."""
    markers: list[str] = []

    def visit(value: Any, key: str = "") -> None:
        if isinstance(value, dict):
            for child_key, child in value.items():
                if child_key.lower() in {"backend", "provider", "method", "source", "origin"}:
                    match = SIMULATION_PATTERN.search(str(child))
                    if match:
                        markers.append(match.group(0).lower())
                if child_key.lower() in {"metadata", "provenance"}:
                    visit(child, child_key)

    visit(payload)
    return sorted(set(markers))


def _error_type(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    metadata = payload.get("metadata")
    if isinstance(metadata, dict) and metadata.get("error_type"):
        return str(metadata["error_type"])
    return str(payload.get("error_type")) if payload.get("error_type") else None


def _tool_success(payload: Any, mcp_is_error: bool) -> bool:
    return not mcp_is_error and isinstance(payload, dict) and payload.get("success") is True


def substantive_observation(case: str, payload: Any, paths: dict[str, Path]) -> bool:
    if not isinstance(payload, dict) or payload.get("success") is not True:
        return False
    message = _action_message(payload)
    metadata = _action_metadata(payload)
    if case == "web_search":
        return isinstance(message, dict) and bool(message.get("results"))
    if case == "knowledge_base_search":
        return isinstance(message, dict) and bool(message.get("results"))
    if case == "download":
        target = paths["downloads"] / "iana-example.html"
        return target.is_file() and target.stat().st_size > 100 and metadata.get("file_size_bytes") == target.stat().st_size
    if case == "webpage_reader":
        return isinstance(message, dict) and bool(message.get("title")) and message.get("text_length", 0) > 50
    if case.startswith("document_reader_"):
        expected = case.rsplit("_", 1)[1]
        return isinstance(message, dict) and message.get("file_type") == expected and message.get("text_length", 0) > 10
    if case == "image_ocr":
        text = str(message.get("extracted_text", "")) if isinstance(message, dict) else ""
        return len(text.strip()) > 10 and "EXPERIMENT" in text.upper()
    if case == "image_analyze":
        return isinstance(message, dict) and len(str(message.get("analysis", "")).strip()) > 20
    if case == "audio_transcribe":
        return isinstance(message, dict) and len(str(message.get("transcription", "")).strip()) > 5
    if case == "video_parser":
        return isinstance(message, dict) and message.get("duration_seconds", 0) > 0 and message.get("frame_count", 0) > 0
    if case == "video_analyze":
        return isinstance(message, dict) and message.get("frames_analyzed", 0) >= 1 and len(str(message.get("combined_analysis", ""))) > 20
    if case == "file_reader":
        return isinstance(message, dict) and MARKER in str(message.get("content", ""))
    if case == "grep":
        return isinstance(message, dict) and message.get("total_found", 0) >= 1
    if case == "directory_list":
        return isinstance(message, list) and any(row.get("name") == "seed.txt" for row in message if isinstance(row, dict))
    if case in {"filesystem_copy", "filesystem_move"}:
        return (
            isinstance(message, dict)
            and message.get("destination_fingerprint") == metadata.get("pre_operation_fingerprint")
            and message.get("destination_fingerprint", {}).get("bytes", 0) > 0
        )
    if case == "filesystem_delete":
        return (
            isinstance(message, dict)
            and message.get("reversible") is True
            and message.get("path_exists_after") is False
            and message.get("quarantine_fingerprint") == metadata.get("pre_operation_fingerprint")
        )
    if case == "weather":
        return isinstance(message, dict) and message.get("temperature") is not None
    if case == "yfinance_quote":
        return isinstance(message, dict) and message.get("symbol") == "AAPL" and message.get("current_price") is not None
    if case == "currency_converter":
        return isinstance(message, dict) and message.get("converted_amount") is not None and message.get("exchange_rate") is not None
    if case == "wikipedia_search":
        return isinstance(message, dict) and bool(message.get("title")) and bool(message.get("summary"))
    if case == "arxiv_search":
        return isinstance(message, dict) and bool(message.get("papers"))
    if case in {"calendar_events", "notion_search"}:
        return isinstance(message, dict) and isinstance(message.get("count"), int)
    return False


async def call_case(
    client: Client,
    case: str,
    arguments: dict[str, Any],
    paths: dict[str, Path],
) -> dict[str, Any]:
    tool = CASE_TO_TOOL[case]
    started = time.perf_counter()
    try:
        result = await client.call_tool(tool, arguments=arguments)
        payload = unwrap_mcp_result(result)
        mcp_is_error = bool(getattr(result, "isError", False) or getattr(result, "is_error", False))
        success = _tool_success(payload, mcp_is_error)
        receipt = {
            "case": case,
            "tool": tool,
            "arguments": arguments,
            "arguments_sha256": sha256_bytes(canonical_json(arguments).encode()),
            "transport": "mcp-stdio",
            "mcp_result_is_error": mcp_is_error,
            "success": success,
            "substantive_observation": substantive_observation(case, payload, paths),
            "backend_provenance": PROVENANCE[tool],
            "simulation_markers": _declared_simulation_markers(payload),
            "error_type": _error_type(payload),
            "payload": payload,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
    except Exception as exc:
        receipt = {
            "case": case,
            "tool": tool,
            "arguments": arguments,
            "arguments_sha256": sha256_bytes(canonical_json(arguments).encode()),
            "transport": "mcp-stdio",
            "mcp_result_is_error": True,
            "success": False,
            "substantive_observation": False,
            "backend_provenance": PROVENANCE[tool],
            "simulation_markers": [],
            "error_type": type(exc).__name__,
            "payload": {"success": False, "error": str(exc)},
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
    return receipt


def credential_blocked(receipt: dict[str, Any]) -> bool:
    error_type = str(receipt.get("error_type") or "").lower()
    payload_text = canonical_json(receipt.get("payload", {})).lower()
    markers = [
        "missing_credentials", "missing_library", "not configured", "api key not configured",
        "invalid credentials", "unauthorized", "authentication", "insufficient_quota",
        "exceeded your current quota", "user not found", "401",
    ]
    return error_type in {"missing_credentials", "missing_library"} or any(marker in payload_text for marker in markers)


def valid_success(receipt: dict[str, Any]) -> bool:
    return (
        receipt.get("transport") == "mcp-stdio"
        and receipt.get("mcp_result_is_error") is False
        and receipt.get("success") is True
        and receipt.get("substantive_observation") is True
        and receipt.get("simulation_markers") == []
        and receipt.get("backend_provenance", {}).get("origin") in {
            "live-api", "private-live-api", "local-filesystem", "local-process"
        }
    )


def derive_acceptance(
    protocol: dict[str, Any],
    catalog: dict[str, Any],
    receipts: list[dict[str, Any]],
    *,
    outside_witness_unchanged: bool,
) -> dict[str, Any]:
    by_case = {receipt.get("case"): receipt for receipt in receipts}
    required_tools = {CASE_TO_TOOL[case]
                      for category in protocol["categories"].values()
                      for case in category.get("required_cases", []) + category.get("required_safety_cases", [])}
    category_results: dict[str, Any] = {}
    for name, category in protocol["categories"].items():
        required = category.get("required_cases", [])
        missing = [case for case in required if case not in by_case]
        invalid = [case for case in required if case in by_case and not valid_success(by_case[case])]
        if not missing and not invalid:
            status = "passed"
        elif category.get("credential_blocking_allowed") and not missing and invalid and all(
            credential_blocked(by_case[case]) for case in invalid
        ):
            status = "blocked"
        else:
            status = "failed"
        category_results[name] = {
            "status": status,
            "required_cases": required,
            "missing_cases": missing,
            "invalid_cases": invalid,
        }

    safety_cases = protocol["categories"]["filesystem"]["required_safety_cases"]
    safety_rejected = all(
        case in by_case
        and by_case[case].get("success") is False
        and by_case[case].get("mcp_result_is_error") is False
        and by_case[case].get("error_type") == "PermissionError"
        for case in safety_cases
    ) and outside_witness_unchanged
    filesystem_hashes = all(
        valid_success(by_case[case]) for case in (
            "filesystem_copy", "filesystem_move", "filesystem_delete"
        )
    ) if all(case in by_case for case in (
        "filesystem_copy", "filesystem_move", "filesystem_delete"
    )) else False
    if not safety_rejected or not filesystem_hashes:
        category_results["filesystem"]["status"] = "failed"

    gates = {
        "catalog_from_real_mcp": (
            catalog.get("transport") == "mcp-stdio"
            and catalog.get("tools_list_received") is True
            and catalog.get("protocol_version") == "2026-07-28"
            and str(catalog.get("mcp_sdk_version", "")).split(".", 1)[0] == "2"
            and catalog.get("tool_count") == catalog.get("unique_tool_count")
            and catalog.get("tool_count", 0) >= 120
        ),
        "catalog_contains_all_required_tools": required_tools <= set(catalog.get("tool_names", [])),
        "search_category_passed": category_results["search"]["status"] == "passed",
        "multimodal_category_passed": category_results["multimodal"]["status"] == "passed",
        "filesystem_category_passed": category_results["filesystem"]["status"] == "passed",
        "public_data_category_passed": category_results["public_data"]["status"] == "passed",
        "private_data_category_passed": category_results["private_data"]["status"] == "passed",
        "filesystem_pre_post_hashes_verified": filesystem_hashes,
        "filesystem_isolation_probes_rejected": safety_rejected,
        "all_successes_substantive_and_non_simulated": all(
            valid_success(receipt) for receipt in receipts if receipt.get("success") is True
        ),
        "exact_case_set_recorded": set(by_case) == {
            case for category in protocol["categories"].values()
            for case in category.get("required_cases", []) + category.get("required_safety_cases", [])
        },
    }
    if all(gates.values()):
        status = "passed"
    elif (
        any(category["status"] == "blocked" for category in category_results.values())
        and all(category["status"] in {"passed", "blocked"}
                for category in category_results.values())
        and all(
            value for gate, value in gates.items()
            if not gate.endswith("_category_passed")
        )
    ):
        status = "blocked"
    else:
        status = "failed"
    return {"status": status, "gates": gates, "categories": category_results}


def build_manifest(campaign_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    files = []
    for path in sorted(campaign_dir.rglob("*")):
        if path.name == "manifest.json":
            continue
        if path.is_symlink():
            data = os.readlink(path).encode("utf-8")
            kind = "symlink-target"
        elif path.is_file():
            data = path.read_bytes()
            kind = "file"
        else:
            continue
        files.append({
            "path": str(path.relative_to(campaign_dir)),
            "kind": kind,
            "bytes": len(data),
            "sha256": sha256_bytes(data),
        })
    return {
        "experiment": "4-1",
        "campaign_id": summary.get("campaign_id"),
        "status": summary.get("status"),
        "official_complete": summary.get("status") == "passed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "files": files,
    }


async def run(campaign_id: str | None = None) -> Path:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    campaign_id = campaign_id or "real_mcp_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    campaign_dir = VALIDATION_ROOT / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=False)
    write_json(campaign_dir / "protocol.json", protocol)
    paths = prepare_fixtures(campaign_dir)
    preflight = credential_preflight()
    write_json(campaign_dir / "credential_preflight.json", preflight)

    outside_before = file_receipt(paths["outside_witness"])
    server_env = os.environ.copy()
    server_env["PERCEPTION_MUTATION_ROOT"] = str(paths["mutation"])
    if server_env.get("DASHSCOPE_API_KEY"):
        server_env["PERCEPTION_VISION_PROVIDER"] = "dashscope"
        server_env["PERCEPTION_VISION_MODEL"] = "qwen-vl-max"
    elif server_env.get("GEMINI_API_KEY"):
        server_env["PERCEPTION_VISION_PROVIDER"] = "gemini"
        server_env["PERCEPTION_VISION_MODEL"] = "gemini-2.5-flash"
    else:
        server_env.setdefault("PERCEPTION_VISION_MODEL", "gpt-4o-mini")
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        env=server_env,
    )
    receipts: list[dict[str, Any]] = []
    async with Client(stdio_client(parameters)) as client:
        listed = await client.list_tools()
        schemas = [tool.model_dump(by_alias=True, exclude_none=True, mode="json") for tool in listed.tools]
        names = [schema["name"] for schema in schemas]
        server_info = client.server_info
        catalog = {
            "transport": "mcp-stdio",
            "tools_list_received": True,
            "mcp_sdk_version": package_version("mcp"),
            "protocol_version": client.protocol_version,
            "server_name": server_info.name if server_info else None,
            "server_version": server_info.version if server_info else None,
            "tool_count": len(names),
            "unique_tool_count": len(set(names)),
            "tool_names": names,
            "schemas_sha256": sha256_bytes(canonical_json(schemas).encode()),
            "schemas": schemas,
        }
        write_json(campaign_dir / "catalog_receipt.json", catalog)

        calls = [
            ("web_search", {"query": "Model Context Protocol official specification", "num_results": 3}),
            ("knowledge_base_search", {"query": MARKER, "knowledge_base_path": str(paths["knowledge"]), "top_k": 3}),
            ("download", {"url": "https://www.iana.org/help/example-domains", "output_path": str(paths["downloads"] / "iana-example.html"), "timeout": 60}),
            ("webpage_reader", {"url": "https://example.com", "extract_text": True, "extract_links": True}),
            ("document_reader_pdf", {"file_path": str(paths["pdf"])}),
            ("document_reader_docx", {"file_path": str(paths["docx"])}),
            ("document_reader_pptx", {"file_path": str(paths["pptx"])}),
            ("image_ocr", {"image_path": str(paths["image"]), "language": "eng"}),
            ("image_analyze", {"image_path": str(paths["image"]), "prompt": "Read the prominent text and describe the simple image."}),
            ("audio_transcribe", {"file_path": str(paths["audio"]), "model_size": "tiny", "language": "en"}),
            ("video_parser", {"video_path": str(paths["video"]), "extract_frames": False}),
            ("video_analyze", {"video_path": str(paths["video"]), "num_frames": 1, "prompt": "Read the text shown in this frame."}),
            ("file_reader", {"file_path": str(paths["note"]), "max_length": 2000}),
            ("grep", {"pattern": MARKER, "directory": str(paths["knowledge"]), "file_pattern": "*.md", "max_results": 10}),
            ("directory_list", {"query": str(paths["mutation"]), "options_json": "{\"limit\": 20}"}),
            ("filesystem_copy", {"source_path": "seed.txt", "destination_path": "copied.txt"}),
            ("filesystem_move", {"source_path": "copied.txt", "destination_path": "moved.txt"}),
            ("filesystem_delete", {"path": "moved.txt"}),
            ("reject_parent_traversal", {"source_path": "seed.txt", "destination_path": "../escaped.txt"}),
            ("reject_absolute_path", {"path": "/tmp"}),
            ("reject_escaping_symlink", {"path": "escape-link"}),
            ("weather", {"location": "Singapore"}),
            ("yfinance_quote", {"symbol": "AAPL"}),
            ("currency_converter", {"amount": 10, "from_currency": "USD", "to_currency": "SGD"}),
            ("wikipedia_search", {"query": "Model Context Protocol", "language": "en", "sentences": 3}),
            ("arxiv_search", {"query": "agentic artificial intelligence", "max_results": 2, "sort_by": "relevance"}),
            ("calendar_events", {"calendar_id": "primary", "max_results": 5}),
            ("notion_search", {"query": "Experiment 4-1", "page_size": 5}),
        ]
        for case, arguments in calls:
            receipt = await call_case(client, case, arguments, paths)
            receipts.append(receipt)
            write_json(campaign_dir / "receipts" / f"{len(receipts):02d}_{case}.json", receipt)

    outside_after = file_receipt(paths["outside_witness"])
    outside_unchanged = outside_before == outside_after
    acceptance = derive_acceptance(
        protocol,
        catalog,
        receipts,
        outside_witness_unchanged=outside_unchanged,
    )
    summary = {
        "experiment": "4-1",
        "campaign_id": campaign_id,
        "status": acceptance["status"],
        "official_complete": acceptance["status"] == "passed",
        "acceptance": acceptance,
        "receipt_count": len(receipts),
        "successful_cases": [row["case"] for row in receipts if row["success"]],
        "failed_or_blocked_cases": [row["case"] for row in receipts if not row["success"]],
        "outside_witness_unchanged": outside_unchanged,
        "credential_preflight": preflight,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(campaign_dir / "summary.json", summary)
    write_json(campaign_dir / "manifest.json", build_manifest(campaign_dir, summary))
    write_json(VALIDATION_ROOT / "latest.json", {
        "experiment": "4-1", "campaign_id": campaign_id,
        "status": summary["status"], "official_complete": summary["official_complete"],
        "manifest": str((campaign_dir / "manifest.json").relative_to(HERE)),
        "manifest_sha256": sha256_bytes((campaign_dir / "manifest.json").read_bytes()),
    })
    return campaign_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-id")
    args = parser.parse_args()
    campaign = asyncio.run(run(args.campaign_id))
    summary = json.loads((campaign / "summary.json").read_text(encoding="utf-8"))
    print(json.dumps({"campaign": str(campaign), "status": summary["status"]}, indent=2))
    return 0 if summary["status"] in {"passed", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
