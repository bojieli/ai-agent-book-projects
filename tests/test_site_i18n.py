import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from site_i18n import canonical_nav_labels


def test_canonical_nav_labels_preserves_colons_in_quoted_strings():
    """Prove that double-quoted and single-quoted nav labels containing colons

    (e.g., "第1章: Agent基础知识", 'Chapter 2: Context Engineering') are preserved in full,
    locking out catalog validation failures where nav labels are truncated at colons.
    """
    config = """
nav:
  - 首页: index.md
  - "第1章: Agent基础知识":
      - book/chapter1/index.md
      - 配套实验: chapter1/README.md
  - 'Chapter 2: Context Engineering':
      - book/chapter2/index.md
"""
    labels = canonical_nav_labels(config)

    assert "第1章: Agent基础知识" in labels
    assert "Chapter 2: Context Engineering" in labels
    assert "首页" in labels
    assert "配套实验" in labels


def test_canonical_nav_labels_unquoted():
    """Prove that unquoted nav labels without colons are correctly parsed and appended,

    locking out missing nav entry errors.
    """
    config = """
nav:
  - Overview: index.md
  - Experiments:
      - chapter1/README.md
"""
    labels = canonical_nav_labels(config)

    assert labels == ["Overview", "Experiments"]

def test_canonical_nav_labels_multiple_colons_and_escaped_quotes():
    """Prove that quoted nav labels with multiple colons and escaped quotes are properly parsed."""
    config = r"""
nav:
  - "Part 1: Chapter 2: Deep Dive: Context": index.md
  - 'Section A: Part B: Overview: Details': intro.md
  - "Chapter 1: \"Agent\" Architecture: Overview": chapter1.md
  - 'Chapter 2: \'Context\' & \'Prompts\': Details': chapter2.md
  - 'Chapter 3: ''Memory'' Management': chapter3.md
"""
    labels = canonical_nav_labels(config)
    assert "Part 1: Chapter 2: Deep Dive: Context" in labels
    assert "Section A: Part B: Overview: Details" in labels
    assert 'Chapter 1: "Agent" Architecture: Overview' in labels
    assert "Chapter 2: 'Context' & 'Prompts': Details" in labels
    assert "Chapter 3: 'Memory' Management" in labels
