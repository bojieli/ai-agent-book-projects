#!/usr/bin/env python3
"""Live three-paradigm comparison for Chapter 4 Experiment 4-2.

The PNG chart and the PDF page containing that chart are each submitted to the
same two questions through native vision, local text extraction followed by a
text-only model, and an agent that decides whether to invoke a vision tool.
Every provider call is checkpointed immediately and later copied into the
immutable campaign receipts.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

PROJECT_DIR = Path(__file__).resolve().parent
CHAPTER_DIR = PROJECT_DIR.parent
sys.path.insert(0, str(CHAPTER_DIR))

from experiment_utils import ChatRecorder, jsonable, sha256_file, write_campaign_evidence  # noqa: E402

ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3"
MOONSHOT_ENDPOINT = "https://api.moonshot.cn/v1"
SEED = 37
QUESTIONS = [
    {
        "id": "highest",
        "question": "Which quarter had the highest revenue, and what was the exact value?",
        "expected": "Q4, $180M",
        "required_patterns": [r"\bQ4\b", r"(?:\$\s*)?180\s*M"],
    },
    {
        "id": "lowest_gap",
        "question": "Which quarter had the lowest revenue, what was its value, and by how much did Q4 exceed it?",
        "expected": "Q3, $95M; Q4 exceeded it by $85M",
        "required_patterns": [r"\bQ3\b", r"(?:\$\s*)?95\s*M", r"(?:\$\s*)?85\s*M"],
    },
]
TOOL = {
    "type": "function",
    "function": {
        "name": "inspect_visual",
        "description": "Inspect the original chart or PDF page when exact visual, spatial, or numeric evidence is needed.",
        "parameters": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    },
}


class CheckpointRecorder(ChatRecorder):
    def __init__(self, *args: Any, checkpoint: Path, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.checkpoint = checkpoint
        self.checkpoint.parent.mkdir(parents=True, exist_ok=True)

    def create(self, *, purpose: str, **request: Any) -> Any:
        try:
            return super().create(purpose=purpose, **request)
        finally:
            self.checkpoint.write_text(
                json.dumps(self.calls, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )


def data_url(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def local_extract(kind: str, original: Path) -> tuple[str, dict[str, Any]]:
    started = time.perf_counter()
    if kind == "png":
        command = ["tesseract", str(original), "stdout", "--psm", "6"]
    else:
        command = ["pdftotext", "-layout", str(original), "-"]
    proc = subprocess.run(command, text=True, capture_output=True, check=True)
    return proc.stdout.strip(), {
        "command": command,
        "stderr": proc.stderr,
        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
    }


def render_pdf(pdf: Path, output: Path) -> None:
    prefix = output.with_suffix("")
    subprocess.run(
        ["pdftoppm", "-png", "-singlefile", "-r", "180", str(pdf), str(prefix)],
        check=True,
        capture_output=True,
        text=True,
    )


def answer_text(recorder: CheckpointRecorder, model: str, context: str, question: str, purpose: str) -> str:
    response = recorder.create(
        purpose=purpose,
        model=model,
        seed=SEED,
        temperature=0,
        messages=[
            {"role": "system", "content": "Answer only from the extracted text. If it lacks the exact visual evidence, say that it is unavailable."},
            {"role": "user", "content": f"Extracted text:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return response.choices[0].message.content or ""


def answer_vision(recorder: CheckpointRecorder, model: str, image: Path, question: str, purpose: str) -> str:
    response = recorder.create(
        purpose=purpose,
        model=model,
        seed=SEED,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Read the chart carefully. {question} Give exact values and concise supporting visual evidence."},
                    {"type": "image_url", "image_url": {"url": data_url(image)}},
                ],
            }
        ],
    )
    return response.choices[0].message.content or ""


def answer_with_tool(
    recorder: CheckpointRecorder,
    model: str,
    extracted: str,
    image: Path,
    question: str,
    artifact_id: str,
) -> tuple[str, dict[str, Any]]:
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are given a cheap text extraction and one visual-inspection tool. "
                "Call inspect_visual whenever exact chart values or spatial associations are not explicitly established by the text."
            ),
        },
        {"role": "user", "content": f"Extracted text:\n{extracted}\n\nQuestion: {question}"},
    ]
    decision = recorder.create(
        purpose=f"tool-decision:{artifact_id}",
        model=model,
        seed=SEED,
        temperature=0,
        messages=messages,
        tools=[TOOL],
        tool_choice="auto",
    )
    message = decision.choices[0].message
    calls = list(message.tool_calls or [])
    trace: dict[str, Any] = {"tool_selected": bool(calls), "decision": jsonable(message), "executions": []}
    if not calls:
        return message.content or "", trace

    messages.append(message.model_dump(exclude_none=True))
    for call in calls:
        arguments = json.loads(call.function.arguments or "{}")
        tool_question = arguments.get("question") or question
        result = answer_vision(
            recorder,
            model,
            image,
            tool_question,
            f"tool-vision:{artifact_id}:{call.id}",
        )
        trace["executions"].append(
            {"tool_call_id": call.id, "name": call.function.name, "arguments": arguments, "result": result}
        )
        messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    final = recorder.create(
        purpose=f"tool-final:{artifact_id}",
        model=model,
        seed=SEED,
        temperature=0,
        messages=messages,
        tools=[TOOL],
        tool_choice="none",
    )
    return final.choices[0].message.content or "", trace


def exact_correct(answer: str, patterns: list[str]) -> bool:
    return all(re.search(pattern, answer, flags=re.IGNORECASE) for pattern in patterns)


def judge_answers(recorder: CheckpointRecorder, model: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payload = [
        {"id": row["id"], "question": row["question"], "reference": row["expected"], "answer": row["answer"]}
        for row in rows
    ]
    response = recorder.create(
        purpose="external-answer-judge",
        model=model,
        seed=SEED,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Independently judge chart QA answers. Return JSON {items:[{id,correct,score,reason}]}. "
                    "Score 1 only if every requested quarter/value/difference matches the reference; otherwise 0."
                ),
            },
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    )
    return json.loads(response.choices[0].message.content)["items"]


def tool_version(command: list[str]) -> str:
    proc = subprocess.run(command, text=True, capture_output=True)
    return (proc.stdout or proc.stderr).splitlines()[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Experiment 4-2 live multimodal campaign")
    parser.add_argument("--model", default=os.getenv("ARK_MODEL", "doubao-seed-1-6-250615"))
    parser.add_argument("--judge-model", default=os.getenv("MULTIMODAL_JUDGE_MODEL", "moonshot-v1-8k"))
    args = parser.parse_args()
    ark_key = os.getenv("ARK_API_KEY") or os.getenv("DOUBAO_API_KEY")
    moonshot_key = os.getenv("MOONSHOT_API_KEY")
    if not ark_key or not moonshot_key:
        raise RuntimeError("ARK_API_KEY and MOONSHOT_API_KEY are required")

    checkpoint_dir = PROJECT_DIR / "validation" / "checkpoints"
    checkpoint_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    ark = CheckpointRecorder(
        OpenAI(api_key=ark_key, base_url=ARK_ENDPOINT, timeout=120, max_retries=3),
        "volcengine-ark",
        ARK_ENDPOINT,
        checkpoint=checkpoint_dir / f"{checkpoint_id}-ark.json",
    )
    judge = CheckpointRecorder(
        OpenAI(api_key=moonshot_key, base_url=MOONSHOT_ENDPOINT, timeout=120, max_retries=3),
        "moonshot",
        MOONSHOT_ENDPOINT,
        checkpoint=checkpoint_dir / f"{checkpoint_id}-judge.json",
    )

    chart = PROJECT_DIR / "test_files" / "sample_chart.png"
    pdf = PROJECT_DIR / "test_files" / "sample_report.pdf"
    if not chart.exists() or not pdf.exists():
        subprocess.run([sys.executable, str(PROJECT_DIR / "create_sample.py")], cwd=PROJECT_DIR, check=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        rendered_pdf = Path(temp_dir) / "sample_report_page.png"
        render_pdf(pdf, rendered_pdf)
        artifacts = [
            ("png", chart, chart),
            ("pdf", pdf, rendered_pdf),
        ]
        rows: list[dict[str, Any]] = []
        artifact_records = []
        for kind, original, visual in artifacts:
            extracted, extraction_receipt = local_extract(kind, original)
            artifact_records.append(
                {
                    "kind": kind,
                    "source_path": str(original),
                    "source_sha256": sha256_file(original),
                    "visual_input": str(visual),
                    "visual_sha256": sha256_file(visual),
                    "extracted_text": extracted,
                    "extraction": extraction_receipt,
                }
            )
            for spec in QUESTIONS:
                base = {
                    "artifact": kind,
                    "question_id": spec["id"],
                    "question": spec["question"],
                    "expected": spec["expected"],
                }
                started = time.perf_counter()
                native = answer_vision(ark, args.model, visual, spec["question"], f"native:{kind}:{spec['id']}")
                rows.append(
                    {
                        **base,
                        "id": f"{kind}:native:{spec['id']}",
                        "paradigm": "native-multimodal",
                        "answer": native,
                        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                        "exact_correct": exact_correct(native, spec["required_patterns"]),
                    }
                )
                started = time.perf_counter()
                text_answer = answer_text(
                    ark, args.model, extracted, spec["question"], f"extract-text:{kind}:{spec['id']}"
                )
                rows.append(
                    {
                        **base,
                        "id": f"{kind}:extract:{spec['id']}",
                        "paradigm": "extract-to-text",
                        "answer": text_answer,
                        "latency_ms": round(extraction_receipt["latency_ms"] + (time.perf_counter() - started) * 1000, 3),
                        "exact_correct": exact_correct(text_answer, spec["required_patterns"]),
                    }
                )
                started = time.perf_counter()
                tool_answer, tool_trace = answer_with_tool(
                    ark, args.model, extracted, visual, spec["question"], f"{kind}:{spec['id']}"
                )
                rows.append(
                    {
                        **base,
                        "id": f"{kind}:tool:{spec['id']}",
                        "paradigm": "tool-on-demand",
                        "answer": tool_answer,
                        "latency_ms": round(extraction_receipt["latency_ms"] + (time.perf_counter() - started) * 1000, 3),
                        "exact_correct": exact_correct(tool_answer, spec["required_patterns"]),
                        "tool_trace": tool_trace,
                    }
                )

        judgements = judge_answers(judge, args.judge_model, rows)
        judged = {item["id"]: item for item in judgements}
        for row in rows:
            row["external_judge"] = judged[row["id"]]
        summary: dict[str, Any] = {}
        for paradigm in ("native-multimodal", "extract-to-text", "tool-on-demand"):
            selected = [row for row in rows if row["paradigm"] == paradigm]
            summary[paradigm] = {
                "cases": len(selected),
                "exact_accuracy": sum(row["exact_correct"] for row in selected) / len(selected),
                "judge_accuracy": sum(bool(row["external_judge"]["correct"]) for row in selected) / len(selected),
                "mean_latency_ms": sum(row["latency_ms"] for row in selected) / len(selected),
            }

        pdf_text = next(item["extracted_text"] for item in artifact_records if item["kind"] == "pdf")
        tool_rows = [row for row in rows if row["paradigm"] == "tool-on-demand"]
        acceptance = {
            "same_two_questions_all_paradigms_and_artifacts": len(rows) == 12,
            "png_and_pdf_used": {row["artifact"] for row in rows} == {"png", "pdf"},
            "chart_answers_absent_from_pdf_body_text": not any(
                value in pdf_text.lower() for value in ("$180", "180m", "$95", "95m", "$85", "85m")
            ),
            "real_native_vision_calls": len([call for call in ark.calls if call["purpose"].startswith("native:")]) == 4,
            "tool_selected_on_demand": all(row["tool_trace"]["tool_selected"] for row in tool_rows),
            "real_tool_vision_calls": len([call for call in ark.calls if call["purpose"].startswith("tool-vision:")]) >= 4,
            "external_moonshot_judge": len(judge.calls) == 1 and len(judgements) == len(rows),
            "all_calls_checkpointed": (checkpoint_dir / f"{checkpoint_id}-ark.json").exists()
            and (checkpoint_dir / f"{checkpoint_id}-judge.json").exists(),
        }
        evidence = {
            "status": "passed" if all(acceptance.values()) else "failed",
            "providers": {
                "vision_answerer": {"provider": "Volcengine Ark", "endpoint": ARK_ENDPOINT, "model": args.model, "seed": SEED},
                "judge": {"provider": "Moonshot", "endpoint": MOONSHOT_ENDPOINT, "model": args.judge_model, "seed": SEED},
            },
            "local_tools": {
                "tesseract": tool_version(["tesseract", "--version"]),
                "pdftotext": tool_version(["pdftotext", "-v"]),
                "pdftoppm": tool_version(["pdftoppm", "-v"]),
            },
            "artifacts": artifact_records,
            "questions": QUESTIONS,
            "results": rows,
            "summary": summary,
            "acceptance": acceptance,
            "checkpoint_files": [str(ark.checkpoint), str(judge.checkpoint)],
        }
        manifest = write_campaign_evidence(
            PROJECT_DIR,
            "4-2",
            evidence,
            receipts=ark.calls + judge.calls,
            input_paths=[__file__, PROJECT_DIR / "create_sample.py", chart, pdf],
        )
    print(json.dumps(summary, indent=2))
    print(json.dumps(acceptance, indent=2))
    print(f"evidence: {manifest['run_dir']}")
    return 0 if all(acceptance.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
