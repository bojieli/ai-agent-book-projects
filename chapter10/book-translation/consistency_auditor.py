"""Bilingual Consistency Auditor module for translated technical Markdown documentation.

Audits domain terminology mapping, code block synchronization (matching book/ source),
LaTeX formula syntax preservation, and link targets across translated Markdown files.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union


# Default bilingual terminology glossary for AI/ML technical documentation
DEFAULT_GLOSSARY: Dict[str, Dict[str, Any]] = {
    "zh": {
        "token": {"canonical": "词元", "variants": ["词元", "令牌", "标记"]},
        "embedding": {"canonical": "嵌入", "variants": ["嵌入", "词向量", "向量表示", "嵌入向量"]},
        "prompt": {"canonical": "提示词", "variants": ["提示词", "提示语", "提示"]},
        "inference": {"canonical": "推理", "variants": ["推理", "推断"]},
        "latency": {"canonical": "时延", "variants": ["时延", "延迟", "延时"]},
        "attention": {"canonical": "注意力", "variants": ["注意力", "关注度"]},
        "transformer": {"canonical": "Transformer", "variants": ["Transformer", "变换器", "转换器"]},
        "fine-tuning": {"canonical": "微调", "variants": ["微调", "精调"]},
        "agent": {"canonical": "智能体", "variants": ["智能体", "代理"]},
        "retrieval": {"canonical": "检索", "variants": ["检索", "取回"]},
        "vector database": {"canonical": "向量数据库", "variants": ["向量数据库", "矢量数据库"]},
        "context window": {"canonical": "上下文窗口", "variants": ["上下文窗口", "语境窗口"]},
        "hallucination": {"canonical": "幻觉", "variants": ["幻觉"]},
        "quantization": {"canonical": "量化", "variants": ["量化"]},
    }
}


@dataclass
class AuditFinding:
    """Represents a single audit finding or issue."""

    category: str  # "terminology", "code_blocks", "latex_formulas", "link_targets"
    severity: str  # "error", "warning", "info"
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


class AuditReport(dict):
    """Structured audit report containing findings and consistency scores.

    Supports both dictionary access (report["scores"]) and attribute access (report.scores).
    """

    def __init__(
        self,
        findings: List[Dict[str, Any]],
        scores: Dict[str, float],
        overall_score: float,
        is_consistent: bool,
    ):
        super().__init__(
            findings=findings,
            scores=scores,
            overall_score=overall_score,
            is_consistent=is_consistent,
        )
        self.findings = findings
        self.scores = scores
        self.overall_score = overall_score
        self.is_consistent = is_consistent

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'AuditReport' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class BilingualConsistencyAuditor:
    """Auditor for checking consistency between source and translated technical Markdown files."""

    def __init__(self, glossary: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None):
        """Initialize the auditor with optional custom glossary."""
        self.glossary = glossary or DEFAULT_GLOSSARY

    def audit_translation(
        self,
        source_file: Union[str, Path],
        target_file: Union[str, Path],
        lang: str = "zh",
    ) -> AuditReport:
        """Audit entrypoint to check translation consistency."""
        return self.run_audit(source_file, target_file, lang)

    def run_audit(
        self,
        source_file: Union[str, Path],
        target_file: Union[str, Path],
        lang: str = "zh",
    ) -> AuditReport:
        """Run all consistency checks on the given source and target content."""
        source_text = self._load_content(source_file)
        target_text = self._load_content(target_file)

        findings: List[AuditFinding] = []

        term_score, term_findings = self._audit_terminology(source_text, target_text, lang)
        findings.extend(term_findings)

        code_score, code_findings = self._audit_code_blocks(source_text, target_text)
        findings.extend(code_findings)

        latex_score, latex_findings = self._audit_latex_formulas(source_text, target_text)
        findings.extend(latex_findings)

        link_score, link_findings = self._audit_link_targets(source_text, target_text)
        findings.extend(link_findings)

        scores = {
            "terminology": round(term_score, 4),
            "code_blocks": round(code_score, 4),
            "latex_formulas": round(latex_score, 4),
            "link_targets": round(link_score, 4),
            "overall": round(
                (term_score + code_score + latex_score + link_score) / 4.0, 4
            ),
        }

        overall_score = scores["overall"]
        has_critical_error = any(f.severity == "error" for f in findings)
        is_consistent = (overall_score >= 0.90) and not has_critical_error

        finding_dicts = [f.to_dict() for f in findings]
        return AuditReport(
            findings=finding_dicts,
            scores=scores,
            overall_score=overall_score,
            is_consistent=is_consistent,
        )

    def _load_content(self, file_or_content: Union[str, Path]) -> str:
        """Load text content from path if existing file, else return as string."""
        if isinstance(file_or_content, Path):
            if file_or_content.is_file():
                return file_or_content.read_text(encoding="utf-8")
            raise FileNotFoundError(f"Source or target file not found: {file_or_content}")
        if isinstance(file_or_content, str):
            p = Path(file_or_content)
            try:
                if p.is_file():
                    return p.read_text(encoding="utf-8")
            except (OSError, ValueError):
                pass
            # Only treat as a file path (and raise) if it looks like a path
            # AND the file doesn't exist. A single-line string ending in ".md"
            # that isn't an actual file is content, not a missing path.
            if "\n" not in file_or_content:
                looks_like_path = (
                    file_or_content.startswith(("./", "../", "/"))
                    or (" " not in file_or_content and ("/" in file_or_content or "\\" in file_or_content))
                )
                if looks_like_path:
                    raise FileNotFoundError(f"Source or target file not found: {file_or_content}")
            return file_or_content
        return str(file_or_content)

    def _strip_code(self, text: str) -> str:
        """Remove code blocks and inline code from text before terminology check."""
        text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
        text = re.sub(r"`[^`]*`", " ", text)
        return text

    def _audit_terminology(
        self, source_text: str, target_text: str, lang: str
    ) -> Tuple[float, List[AuditFinding]]:
        """Audit domain terminology mapping consistency."""
        findings: List[AuditFinding] = []
        lang_glossary = self.glossary.get(lang, {})
        if not lang_glossary:
            return 1.0, findings

        prose_source = self._strip_code(source_text)
        prose_target = self._strip_code(target_text)

        checked_terms = 0
        consistent_terms = 0

        for term_en, spec in lang_glossary.items():
            pattern = r"\b" + re.escape(term_en) + r"\b"
            if not re.search(pattern, prose_source, flags=re.IGNORECASE):
                continue
            checked_terms += 1
            canonical = spec.get("canonical", "")
            variants = spec.get("variants", [canonical])

            matched_variants = []
            occupied_spans: List[Tuple[int, int]] = []
            unique_variants = list(dict.fromkeys(variants))
            for v in sorted(unique_variants, key=len, reverse=True):
                v_pattern = re.compile(re.escape(v), re.IGNORECASE)
                found_v = False
                for match in v_pattern.finditer(prose_target):
                    m_start, m_end = match.span()
                    if not any(m_start < end and start < m_end for start, end in occupied_spans):
                        occupied_spans.append((m_start, m_end))
                        found_v = True
                if found_v:
                    matched_variants.append(v)

            if not matched_variants:
                findings.append(
                    AuditFinding(
                        category="terminology",
                        severity="error",
                        message=f"Missing translation for domain term '{term_en}'. Expected canonical: '{canonical}'.",
                        details={
                            "term_en": term_en,
                            "expected_canonical": canonical,
                            "variants": variants,
                        },
                    )
                )
            elif len(matched_variants) > 1:
                findings.append(
                    AuditFinding(
                        category="terminology",
                        severity="warning",
                        message=f"Inconsistent terminology translation for '{term_en}'. Found variants: {matched_variants}.",
                        details={
                            "term_en": term_en,
                            "found_variants": matched_variants,
                            "canonical": canonical,
                        },
                    )
                )
                consistent_terms += 0.5
            elif canonical in matched_variants or any(canonical.lower() == m.lower() for m in matched_variants):
                consistent_terms += 1.0
            else:
                findings.append(
                    AuditFinding(
                        category="terminology",
                        severity="info",
                        message=f"Term '{term_en}' translated as non-canonical variant '{matched_variants[0]}'. Canonical is '{canonical}'.",
                        details={
                            "term_en": term_en,
                            "found_variant": matched_variants[0],
                            "canonical": canonical,
                        },
                    )
                )
                consistent_terms += 0.8

        if checked_terms == 0:
            return 1.0, findings

        score = consistent_terms / checked_terms
        return score, findings

    def _audit_code_blocks(
        self, source_text: str, target_text: str
    ) -> Tuple[float, List[AuditFinding]]:
        """Audit code block synchronization matching source."""
        findings: List[AuditFinding] = []

        code_block_regex = re.compile(r"```([a-zA-Z0-9_\-+]*)\n(.*?)```", re.DOTALL)
        source_blocks = code_block_regex.findall(source_text)
        target_blocks = code_block_regex.findall(target_text)

        if len(source_blocks) != len(target_blocks):
            findings.append(
                AuditFinding(
                    category="code_blocks",
                    severity="error",
                    message=f"Code block count mismatch: source has {len(source_blocks)}, target has {len(target_blocks)}.",
                    details={
                        "source_count": len(source_blocks),
                        "target_count": len(target_blocks),
                    },
                )
            )

        if not source_blocks:
            # Target blocks with no source counterpart already produced a count
            # mismatch finding above, so score them as a miss rather than a pass.
            return 0.0 if target_blocks else 1.0, findings

        matches = 0
        min_blocks = min(len(source_blocks), len(target_blocks))

        for idx in range(min_blocks):
            src_lang, src_code = source_blocks[idx]
            tgt_lang, tgt_code = target_blocks[idx]

            src_lang_norm = src_lang.strip().lower()
            tgt_lang_norm = tgt_lang.strip().lower()

            if src_lang_norm != tgt_lang_norm:
                findings.append(
                    AuditFinding(
                        category="code_blocks",
                        severity="warning",
                        message=f"Code block {idx + 1} language tag mismatch: '{src_lang}' vs '{tgt_lang}'.",
                        details={
                            "block_index": idx + 1,
                            "source_lang": src_lang,
                            "target_lang": tgt_lang,
                        },
                    )
                )

            src_lines = [line.strip() for line in src_code.strip().splitlines() if line.strip()]
            tgt_lines = [line.strip() for line in tgt_code.strip().splitlines() if line.strip()]

            if src_lines == tgt_lines:
                matches += 1
            else:
                findings.append(
                    AuditFinding(
                        category="code_blocks",
                        severity="error",
                        message=f"Code block {idx + 1} content modified or desynchronized from source.",
                        details={
                            "block_index": idx + 1,
                            "source_line_count": len(src_lines),
                            "target_line_count": len(tgt_lines),
                        },
                    )
                )

        score = matches / len(source_blocks)
        return score, findings

    def _audit_latex_formulas(
        self, source_text: str, target_text: str
    ) -> Tuple[float, List[AuditFinding]]:
        """Audit LaTeX formula syntax preservation."""
        findings: List[AuditFinding] = []

        source_text = self._strip_code(source_text)
        target_text = self._strip_code(target_text)

        # Count only dollar signs that are actual LaTeX delimiters, not
        # currency symbols or dollar signs in prose. We do this by counting
        # the dollars consumed by the block and inline regexes below.
        block_latex_regex = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
        inline_latex_regex = re.compile(r"(?<!\$)\$([^\$\n]+)\$(?!\$)")

        src_blocks = block_latex_regex.findall(source_text)
        tgt_blocks = block_latex_regex.findall(target_text)

        src_no_blocks = block_latex_regex.sub(" ", source_text)
        tgt_no_blocks = block_latex_regex.sub(" ", target_text)

        src_inlines = inline_latex_regex.findall(src_no_blocks)
        tgt_inlines = inline_latex_regex.findall(tgt_no_blocks)

        # Count formula-related dollars: 2 per block formula, 2 per inline
        formula_dollars = (len(tgt_blocks) + len(tgt_inlines)) * 2
        # Remaining dollars after removing matched formulas are non-formula.
        # Strip currency-style $ (followed by a digit) before counting —
        # "$5" in prose is not a LaTeX delimiter.
        remaining = inline_latex_regex.sub(" ", tgt_no_blocks)
        remaining = re.sub(r"\$(?=\d)", " ", remaining)
        leftover_dollars = remaining.count("$")
        unbalanced = leftover_dollars % 2 != 0
        if unbalanced:
            findings.append(
                AuditFinding(
                    category="latex_formulas",
                    severity="error",
                    message="Unbalanced '$' delimiters found in target document.",
                    details={"dollar_count": formula_dollars + leftover_dollars},
                )
            )

        all_src_formulas = [f.strip() for f in src_blocks + src_inlines]
        all_tgt_formulas = [f.strip() for f in tgt_blocks + tgt_inlines]

        if not all_src_formulas:
            score = 0.0 if unbalanced else 1.0
            return score, findings

        matched = 0
        tgt_formula_set = set(all_tgt_formulas)

        for formula in all_src_formulas:
            if formula in tgt_formula_set:
                matched += 1
            else:
                findings.append(
                    AuditFinding(
                        category="latex_formulas",
                        severity="error",
                        message=f"LaTeX formula missing or altered: '${formula}$'.",
                        details={"formula": formula},
                    )
                )

        score = matched / len(all_src_formulas)
        return score, findings

    def _audit_link_targets(
        self, source_text: str, target_text: str
    ) -> Tuple[float, List[AuditFinding]]:
        """Audit link targets across translated Markdown files."""
        findings: List[AuditFinding] = []

        link_regex = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        ref_link_regex = re.compile(r"^\[([^\]]+)\]:\s*(\S+)", re.MULTILINE)

        src_links = link_regex.findall(source_text) + ref_link_regex.findall(source_text)
        tgt_links = link_regex.findall(target_text) + ref_link_regex.findall(target_text)

        src_targets = [target.strip() for _, target in src_links]
        tgt_targets = set(target.strip() for _, target in tgt_links)

        if not src_targets:
            if tgt_targets:
                for target in tgt_targets:
                    findings.append(
                        AuditFinding(
                            category="link_targets",
                            severity="error",
                            message=f"Extra link target in target document: '{target}'.",
                            details={"target": target},
                        )
                    )
                return 0.0, findings
            return 1.0, findings

        matched = 0
        for target in src_targets:
            if target in tgt_targets:
                matched += 1
            else:
                findings.append(
                    AuditFinding(
                        category="link_targets",
                        severity="error",
                        message=f"Link target missing or corrupted: '{target}'.",
                        details={"target": target},
                    )
                )

        score = matched / len(src_targets)
        return score, findings


def audit_translation(
    source_file: Union[str, Path],
    target_file: Union[str, Path],
    lang: str = "zh",
) -> AuditReport:
    """Standalone module-level entrypoint for auditing translation consistency."""
    return BilingualConsistencyAuditor().run_audit(source_file, target_file, lang)
