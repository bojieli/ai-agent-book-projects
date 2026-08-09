"""Unit tests for chapter10/book-translation/consistency_auditor.py."""

from pathlib import Path
import sys

# Ensure chapter10/book-translation is in sys.path
ch10_dir = (Path(__file__).resolve().parent.parent / "chapter10" / "book-translation").resolve()
if str(ch10_dir) not in sys.path:
    sys.path.insert(0, str(ch10_dir))

from consistency_auditor import (
    AuditReport,
    BilingualConsistencyAuditor,
    audit_translation,
)


def test_bilingual_consistency_auditor_perfect_match():
    """Test auditing a perfectly translated markdown document."""
    source_md = """# Transformer Model Overview

The transformer model relies on attention mechanisms and token embedding.
Fine-tuning reduces latency during inference.

```python
def forward(x):
    return x * 2
```

The energy formula is $E = mc^2$.
For details, see [Documentation](https://example.com/docs).
"""

    target_md = """# Transformer 模型概述

Transformer 模型依赖注意力机制和词元嵌入。
微调可以在推理过程中降低时延。

```python
def forward(x):
    return x * 2
```

能量公式为 $E = mc^2$。
更多细节参见 [文档](https://example.com/docs).
"""

    report = audit_translation(source_md, target_md, lang="zh")

    assert isinstance(report, AuditReport)
    assert report.is_consistent is True
    assert report.overall_score == 1.0
    assert report.scores["terminology"] == 1.0
    assert report.scores["code_blocks"] == 1.0
    assert report.scores["latex_formulas"] == 1.0
    assert report.scores["link_targets"] == 1.0
    assert len(report.findings) == 0


def test_bilingual_consistency_auditor_terminology_drift():
    """Test auditing when terminology is missing or translated inconsistently."""
    source_md = "The transformer uses token embedding and attention for inference."
    target_md = "该模型使用未知处理和关注度。"  # Missing 'token' (词元) and 'inference' (推理)

    auditor = BilingualConsistencyAuditor()
    report = auditor.run_audit(source_md, target_md, lang="zh")

    assert report.scores["terminology"] < 1.0
    term_findings = [f for f in report.findings if f["category"] == "terminology"]
    assert len(term_findings) > 0


def test_bilingual_consistency_auditor_code_block_mismatch():
    """Test auditing code block synchronization errors."""
    source_md = """
```python
x = 10
print(x)
```
"""
    target_md = """
```python
x = 999
print(x)
```
"""

    auditor = BilingualConsistencyAuditor()
    report = auditor.run_audit(source_md, target_md, lang="zh")

    assert report.scores["code_blocks"] < 1.0
    code_findings = [f for f in report.findings if f["category"] == "code_blocks"]
    assert len(code_findings) > 0
    assert any("desynchronized" in f["message"] for f in code_findings)


def test_bilingual_consistency_auditor_latex_formula_corruption():
    """Test auditing LaTeX formula syntax and content preservation errors."""
    source_md = "Formula: $E = mc^2$ and block $$\\\\alpha + \\\\beta = 1$$"
    target_md = "公式: $E = mc^3$ 且块 $$"

    auditor = BilingualConsistencyAuditor()
    report = auditor.run_audit(source_md, target_md, lang="zh")

    assert report.scores["latex_formulas"] < 1.0
    latex_findings = [f for f in report.findings if f["category"] == "latex_formulas"]
    assert len(latex_findings) > 0


def test_bilingual_consistency_auditor_link_target_mismatch():
    """Test auditing link target mismatches."""
    source_md = "Check [API Guide](https://api.example.com/v1)."
    target_md = "查看 [API 指南](https://api.wrong-domain.com/v1)."

    auditor = BilingualConsistencyAuditor()
    report = auditor.run_audit(source_md, target_md, lang="zh")

    assert report.scores["link_targets"] < 1.0
    link_findings = [f for f in report.findings if f["category"] == "link_targets"]
    assert len(link_findings) > 0
    assert "https://api.example.com/v1" in link_findings[0]["message"]


def test_bilingual_consistency_auditor_file_path_inputs(tmp_path):
    """Test auditing with actual file path inputs on disk."""
    src_file = tmp_path / "source.md"
    tgt_file = tmp_path / "target.md"

    src_file.write_text("The prompt improves fine-tuning.", encoding="utf-8")
    tgt_file.write_text("提示词可以改进微调。", encoding="utf-8")

    report = audit_translation(src_file, tgt_file, lang="zh")

    assert report["is_consistent"] is True
    assert report["scores"]["terminology"] == 1.0
    assert report.overall_score == 1.0


def test_bilingual_consistency_auditor_custom_glossary():
    """Test auditing with a custom terminology glossary."""
    custom_glossary = {
        "es": {
            "agent": {"canonical": "agente", "variants": ["agente"]},
            "prompt": {"canonical": "indicación", "variants": ["indicación", "prompt"]},
        }
    }

    auditor = BilingualConsistencyAuditor(glossary=custom_glossary)
    report = auditor.run_audit(
        "An agent processes the prompt.",
        "Un agente procesa la indicación.",
        lang="es",
    )

    assert report.scores["terminology"] == 1.0
    assert report.is_consistent is True


def test_bilingual_consistency_auditor_nonexistent_path_raises_error(tmp_path):
    """Test that passing a non-existent Path object raises FileNotFoundError."""
    non_existent = tmp_path / "does_not_exist.md"
    auditor = BilingualConsistencyAuditor()
    try:
        auditor.run_audit(non_existent, "Some content", lang="zh")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_bilingual_consistency_auditor_latex_formula_in_code_block():
    """Test that dollar signs in code blocks do not trigger false formula errors."""
    source_md = "Run `$ pip install pkg` for setup."
    target_md = "运行 `$ pip install pkg` 进行设置。"
    report = audit_translation(source_md, target_md, lang="zh")
    assert report.scores["latex_formulas"] == 1.0
    assert report.is_consistent is True


def test_bilingual_consistency_auditor_independent_substring_variants():
    """Test that independent usage of canonical term alongside longer variant triggers warning."""
    source_md = "The embedding concept."
    target_md = "嵌入 和 嵌入向量。"
    report = audit_translation(source_md, target_md, lang="zh")
    assert report.scores["terminology"] == 0.5
    term_findings = [f for f in report.findings if f["category"] == "terminology"]
    assert any(f["severity"] == "warning" for f in term_findings)


def test_bilingual_consistency_auditor_case_insensitive_target_matching():
    """Test that capital letters in target text (e.g. sentence start) match terms case-insensitively."""
    custom_glossary = {
        "es": {
            "agent": {"canonical": "agente", "variants": ["agente"]},
        }
    }
    auditor = BilingualConsistencyAuditor(glossary=custom_glossary)
    report = auditor.run_audit("An agent works.", "Agente trabaja.", lang="es")
    assert report.scores["terminology"] == 1.0
    assert report.is_consistent is True


def test_bilingual_consistency_auditor_unbalanced_dollars_without_source_formulas():
    """Test that unbalanced dollar signs in target document trigger error even if source has no formulas."""
    source_md = "Simple text without formula."
    target_md = "简单文本 带着 $ 不匹配定界符。"
    report = audit_translation(source_md, target_md, lang="zh")
    assert report.scores["latex_formulas"] == 0.0
    assert report.is_consistent is False
    latex_findings = [f for f in report.findings if f["category"] == "latex_formulas"]
    assert len(latex_findings) > 0
    assert "Unbalanced" in latex_findings[0]["message"]
