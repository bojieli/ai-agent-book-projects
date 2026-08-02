#!/usr/bin/env python3
"""Baseline/student/teacher acceptance campaign for Experiment 7-9."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from generate_data import ANSWER_SUFFIX, extract_predicted_number, verify

BEHAVIORS = {
    "reflection": r"\b(reflect|reconsider|wait|actually|mistake|not right)\b|反思|等等|不对|重新",
    "backtracking": r"\b(backtrack|another approach|instead|alternative)\b|回溯|换一种|另一种方法",
    "verification": r"\b(verify|check|substitute|sanity check)\b|验算|检查|代回|核对",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def behavior_flags(text: str) -> dict[str, bool]:
    return {name: bool(re.search(pattern, text, re.IGNORECASE)) for name, pattern in BEHAVIORS.items()}


def exact_two_sided_sign_p_value(baseline_only: int, student_only: int) -> float:
    """Exact two-sided paired sign test over discordant binary outcomes."""
    n = baseline_only + student_only
    if n == 0:
        return 1.0
    k = min(baseline_only, student_only)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def compare_binary(baseline: dict[str, bool], student: dict[str, bool]) -> dict[str, Any]:
    ids = sorted(set(baseline) & set(student))
    both_correct = sum(baseline[i] and student[i] for i in ids)
    baseline_only = sum(baseline[i] and not student[i] for i in ids)
    student_only = sum(student[i] and not baseline[i] for i in ids)
    both_wrong = len(ids) - both_correct - baseline_only - student_only
    return {
        "paired_cases": len(ids),
        "both_correct": both_correct,
        "baseline_only": baseline_only,
        "student_only": student_only,
        "both_wrong": both_wrong,
        "exact_two_sided_p_value": exact_two_sided_sign_p_value(baseline_only, student_only),
    }


def completion_and_findings(
    *,
    problem_ids: set[str],
    baseline: dict[str, Any],
    student: dict[str, Any],
    teacher: dict[str, Any],
    paired: dict[str, Any],
    student_training_complete: bool,
    teacher_outputs_complete: bool,
) -> tuple[dict[str, bool], dict[str, Any]]:
    """Separate execution/evidence gates from potentially negative hypotheses."""
    arm_ids = [
        {str(record["id"]) for record in arm.get("records", [])}
        for arm in (baseline, student, teacher)
    ]
    completion = {
        "same_problem_ids_across_three_arms": all(ids == problem_ids for ids in arm_ids),
        "real_student_training": student_training_complete,
        "teacher_outputs_complete": teacher_outputs_complete,
        "paired_quality_comparison_complete": paired.get("paired_cases") == len(problem_ids),
        "behavior_inspection_complete": all(
            set(arm.get("behavior_rates", {})) == set(BEHAVIORS)
            for arm in (baseline, student, teacher)
        ),
    }
    completion["complete"] = all(completion.values())
    findings = {
        "student_improves_over_baseline": student["accuracy"] > baseline["accuracy"],
        "paired_improvement_significant_p_lt_0_05": paired["exact_two_sided_p_value"] < 0.05,
        "teacher_style_reflection_backtracking_or_verification_observed": any(
            student["behavior_rates"].values()
        ),
    }
    return completion, findings


def teacher_outputs(path: Path) -> dict[str, str]:
    outputs: dict[str, str] = {}
    for row in load_jsonl(path):
        if "id" in row:
            outputs[str(row["id"])] = "\n".join(
                part for part in (row.get("reasoning") or "", row.get("content") or "") if part
            )
            continue
        messages = row.get("messages") or []
        if len(messages) >= 2:
            question = str(messages[0].get("content", ""))
            outputs[question] = str(messages[1].get("content", ""))
    return outputs


def generate_local(model_name: str, questions: list[str], max_new_tokens: int) -> list[str]:
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise SystemExit("Install the full requirements.txt before local evaluation") from exc
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto",
    )
    results = []
    for question in questions:
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": question + ANSWER_SUFFIX}],
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.inference_mode():
            generated = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        results.append(tokenizer.decode(
            generated[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
        ))
    return results


def score_arm(name: str, problems: list[dict[str, Any]], outputs: list[str]) -> dict[str, Any]:
    records = []
    for problem, output in zip(problems, outputs):
        flags = behavior_flags(output)
        records.append({
            "id": problem["id"],
            "gold_answer": problem["answer"],
            "predicted_answer": extract_predicted_number(output),
            "correct": verify(output, problem["answer"]),
            "behaviors": flags,
            "output": output,
        })
    correct = sum(record["correct"] for record in records)
    return {
        "name": name,
        "cases": len(records),
        "correct": correct,
        "accuracy": correct / len(records) if records else 0.0,
        "behavior_rates": {
            behavior: sum(r["behaviors"][behavior] for r in records) / len(records)
            if records else 0.0
            for behavior in BEHAVIORS
        },
        "records": records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Experiment 7-9 paired baseline/student/teacher evaluation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--problems", type=Path, default=Path("problems.jsonl"))
    parser.add_argument("--baseline-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--student-model", required=True, help="Real checkpoint emitted by train_student.py")
    parser.add_argument("--teacher-data", type=Path, default=Path("data/raw_trajectories_aime_kimi_k3.jsonl"))
    parser.add_argument(
        "--reuse-local-arms-from",
        type=Path,
        help="Reuse retained baseline/student records from a prior evaluation; teacher data is always rescored",
    )
    parser.add_argument("--max-new-tokens", type=int, default=4096)
    parser.add_argument("--output", type=Path, default=Path("validation/experiment_7_9.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    problems = load_jsonl(args.problems)
    if not problems:
        raise SystemExit("No evaluation problems")
    student_manifest = Path(args.student_model) / "training_manifest.json"
    if not student_manifest.is_file():
        raise SystemExit(
            "student-model lacks training_manifest.json; a mechanism/demo model cannot pass Experiment 7-9"
        )

    questions = [str(problem["question"]) for problem in problems]
    reused_local_arms = None
    if args.reuse_local_arms_from:
        prior = json.loads(args.reuse_local_arms_from.read_text())
        arms = {arm.get("name"): arm for arm in prior.get("arms", [])}
        if set(arms) < {"baseline", "student"}:
            raise SystemExit("reuse source lacks retained baseline and student arms")
        baseline = arms["baseline"]
        student = arms["student"]
        reused_local_arms = {
            "path": str(args.reuse_local_arms_from),
            "sha256": sha256(args.reuse_local_arms_from),
        }
    else:
        baseline = score_arm(
            "baseline", problems, generate_local(args.baseline_model, questions, args.max_new_tokens)
        )
        student = score_arm(
            "student", problems, generate_local(args.student_model, questions, args.max_new_tokens)
        )
    cached_teacher = teacher_outputs(args.teacher_data)
    teacher_texts = [cached_teacher.get(str(p["id"]), cached_teacher.get(str(p["question"]), "")) for p in problems]
    teacher = score_arm("teacher", problems, teacher_texts)

    baseline_map = {r["id"]: r["correct"] for r in baseline["records"]}
    student_map = {r["id"]: r["correct"] for r in student["records"]}
    paired = compare_binary(baseline_map, student_map)
    baseline_accuracy = baseline["accuracy"]
    teacher_gap = max(0.0, teacher["accuracy"] - baseline_accuracy)
    recovered = (
        (student["accuracy"] - baseline_accuracy) / teacher_gap if teacher_gap > 0 else None
    )
    completion, findings = completion_and_findings(
        problem_ids={str(problem["id"]) for problem in problems},
        baseline=baseline,
        student=student,
        teacher=teacher,
        paired=paired,
        student_training_complete=json.loads(student_manifest.read_text()).get("status") == "complete",
        teacher_outputs_complete=all(bool(text) for text in teacher_texts),
    )
    payload = {
        "schema_version": 1,
        "experiment": "7-9",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "complete" if completion["complete"] else "incomplete",
        "inputs": {
            "problems": {"path": str(args.problems), "sha256": sha256(args.problems)},
            "teacher_data": {"path": str(args.teacher_data), "sha256": sha256(args.teacher_data)},
            "student_training_manifest": json.loads(student_manifest.read_text()),
            "reused_local_arms": reused_local_arms,
        },
        "models": {
            "baseline": args.baseline_model,
            "student": args.student_model,
            "teacher": "cached real API trajectories",
        },
        "paired_comparison": paired,
        "teacher_capability_recovered": recovered,
        "completion": completion,
        "findings": findings,
        "arms": [baseline, student, teacher],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "status": payload["status"],
        "accuracies": {arm["name"]: arm["accuracy"] for arm in payload["arms"]},
        "paired_p": paired["exact_two_sided_p_value"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
