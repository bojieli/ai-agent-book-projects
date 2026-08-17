"""Cross-trajectory Markdown experience documents for Experiment 9-2.

This module is intentionally independent of AWorld so that the learning
method can be inspected and tested offline. AWorld trajectories only need to
be converted to the small evaluated record schema used here.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Sequence


def outcome_label(score: float) -> str:
    if score >= 0.9:
        return "success"
    if score >= 0.4:
        return "partial"
    return "failure"


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "experience"


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]", text.lower()))


@dataclass(frozen=True)
class ExperienceDocument:
    task_family: str
    capabilities: tuple[str, ...]
    applies_when: tuple[str, ...]
    recommended_strategies: tuple[str, ...]
    common_pitfalls: tuple[str, ...]
    exceptions: tuple[str, ...]
    sources: tuple[str, ...]
    last_validated: str

    @property
    def document_id(self) -> str:
        return _slug(self.task_family)

    def to_markdown(self) -> str:
        def bullets(items: Sequence[str]) -> str:
            return "\n".join(f"- {item}" for item in items) if items else "- 暂无可靠结论"

        return (
            f"# {self.task_family}：可复用经验\n\n"
            f"最近验证时间：{self.last_validated}\n\n"
            "## 适用场景\n\n"
            f"{bullets(self.applies_when)}\n\n"
            "## 推荐策略\n\n"
            f"{bullets(self.recommended_strategies)}\n\n"
            "## 常见误区\n\n"
            f"{bullets(self.common_pitfalls)}\n\n"
            "## 例外条件\n\n"
            f"{bullets(self.exceptions)}\n\n"
            "## 来源轨迹\n\n"
            f"{bullets(self.sources)}\n"
        )


def build_documents(
    trajectories: Iterable[Dict[str, Any]], *, validated_on: str | None = None
) -> List[ExperienceDocument]:
    """Compare evaluated trajectories and create one document per task family.

    A strategy must be supported by at least two non-failed trajectories. A
    single lucky run is retained as evidence but not promoted to a reusable
    recommendation.
    """
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in trajectories:
        record = dict(item)
        record["outcome"] = outcome_label(float(record.get("environment_score", 0.0)))
        groups[record["task_family"]].append(record)

    documents: List[ExperienceDocument] = []
    for family, records in sorted(groups.items()):
        strategy_support: Counter[str] = Counter()
        pitfall_support: Counter[str] = Counter()
        capabilities: set[str] = set()
        applies_when: set[str] = set()
        exceptions: set[str] = set()

        for record in records:
            capabilities.update(record.get("capabilities", []))
            applies_when.update(record.get("applies_when", []))
            exceptions.update(record.get("exceptions", []))
            if record["outcome"] != "failure":
                strategy_support.update(set(record.get("observed_strategies", [])))
            if record["outcome"] != "success":
                pitfall_support.update(set(record.get("mistakes", [])))

        recommendations = tuple(
            text for text, count in strategy_support.most_common() if count >= 2
        )
        pitfalls = tuple(text for text, _ in pitfall_support.most_common())
        sources = tuple(
            f"{record['id']} ({record['outcome']}, score={float(record.get('environment_score', 0.0)):.2f})"
            for record in records
        )
        documents.append(ExperienceDocument(
            task_family=family,
            capabilities=tuple(sorted(capabilities)),
            applies_when=tuple(sorted(applies_when)) or (f"任务属于 {family}",),
            recommended_strategies=recommendations,
            common_pitfalls=pitfalls,
            exceptions=tuple(sorted(exceptions)),
            sources=sources,
            last_validated=validated_on or date.today().isoformat(),
        ))
    return documents


def write_documents(documents: Iterable[ExperienceDocument], output_dir: Path) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for document in documents:
        path = output_dir / f"{document.document_id}.md"
        path.write_text(document.to_markdown(), encoding="utf-8")
        paths.append(path)
    return paths


def retrieve_documents(
    query: str, task_family: str, documents: Sequence[ExperienceDocument], top_k: int = 1
) -> List[ExperienceDocument]:
    query_tokens = _tokens(query)

    def score(document: ExperienceDocument) -> tuple[float, str]:
        searchable = " ".join((
            document.task_family,
            *document.capabilities,
            *document.applies_when,
            *document.recommended_strategies,
        ))
        overlap = len(query_tokens & _tokens(searchable))
        family_bonus = 10.0 if document.task_family == task_family else 0.0
        return family_bonus + overlap, document.document_id

    return sorted(documents, key=score, reverse=True)[:top_k]


def _trajectory_summary(record: Dict[str, Any]) -> Dict[str, Any]:
    """The direct-single-trajectory baseline used in the experiment."""
    return {
        "id": record["id"],
        "task_family": record["task_family"],
        "text": f"{record.get('question', '')} {' '.join(record.get('observed_strategies', []))}",
        # Direct retrieval has no cross-run check: even a failed path may be
        # presented to the next agent as the action taken in that case.
        "directives": list(record.get("observed_strategies", [])),
    }


def _retrieve_summary(query: str, family: str, records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    query_tokens = _tokens(query)
    summaries = [_trajectory_summary(record) for record in records]

    def score(summary: Dict[str, Any]) -> tuple[float, str]:
        family_bonus = 10.0 if summary["task_family"] == family else 0.0
        return family_bonus + len(query_tokens & _tokens(summary["text"])), summary["id"]

    return max(summaries, key=score)


def evaluate_retrieval_baselines(
    trajectories: Sequence[Dict[str, Any]],
    documents: Sequence[ExperienceDocument],
    transfer_cases: Sequence[Dict[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """Measure transfer, context cost and negative transfer for three modes."""
    aggregates: Dict[str, Dict[str, float]] = {}
    for mode in ("no_experience", "single_trajectory_summary", "knowledge_document"):
        successes = negatives = retrieved_chars = 0
        for case in transfer_cases:
            if mode == "no_experience":
                directives: List[str] = []
                content = ""
            elif mode == "single_trajectory_summary":
                summary = _retrieve_summary(case["query"], case["task_family"], trajectories)
                directives = summary["directives"]
                content = summary["text"]
            else:
                document = retrieve_documents(case["query"], case["task_family"], documents)[0]
                directives = list(document.recommended_strategies)
                content = document.to_markdown()

            guidance = " ".join(directives).lower()
            expected = [term.lower() for term in case.get("expected_guidance", [])]
            harmful = [term.lower() for term in case.get("harmful_guidance", [])]
            successes += int(all(term in guidance for term in expected))
            negatives += int(any(term in guidance for term in harmful))
            retrieved_chars += len(content)

        count = max(1, len(transfer_cases))
        aggregates[mode] = {
            "transfer_success_rate": round(successes / count, 3),
            "negative_transfer_rate": round(negatives / count, 3),
            "average_retrieved_characters": round(retrieved_chars / count, 1),
        }
    return aggregates
