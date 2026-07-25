"""Shared packaging and plumbing for the ai-agent-book companion experiments.

This package exists so the repo can declare its dependencies once (see the root
``pyproject.toml``) instead of repeating them across per-project
``requirements.txt`` files.

Install what a chapter needs::

    pip install -e ".[ch1]"     # chapter 1, no GPU stack
    pip install -e ".[ch7]"     # heavy fine-tuning deps, opt in explicitly

Scope: this package holds *plumbing only* -- provider resolution, environment
loading, trace printing. The teaching code stays inside each chapter's
experiment directory, where a reader can follow it top to bottom.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
