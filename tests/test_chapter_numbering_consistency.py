"""Regression checks for the 2.0 chapter reorganization.

The checks cover the public chapter index, build-version metadata, the issue
#907 trajectory-verifier example, and representative retained-run migrations.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CHAPTERS = {
    1: ("AI Agent 入门", 3),
    2: ("上下文工程", 10),
    3: ("用户记忆和知识库", 12),
    4: ("工具", 5),
    5: ("Coding Agent 与通用 Agent", 13),
    6: ("交互：观察与动作空间的扩展", 13),
    7: ("Agent 的评估", 13),
    8: ("模型后训练", 19),
    9: ("Agent 的持续进化", 9),
    10: ("多 Agent 协作", 6),
}

RENAMED_RUNS = (
    (
        "chapter6/streaming-speech/validation/runs/exp9-3-qwen2audio-whisper-provenance-20260730-v3",
        "chapter6/streaming-speech/validation/runs/exp6-4-qwen2audio-whisper-provenance-20260730-v3",
    ),
    (
        "chapter7/openvla-robotwin2-eval/validation/runs/exp6-12-localgpu-20260803-v1",
        "chapter7/openvla-robotwin2-eval/validation/runs/exp7-13-localgpu-20260803-v1",
    ),
    (
        "chapter8/MiniMind-pretrain/validation/runs/exp7-3-training-report-20260731-v1",
        "chapter8/MiniMind-pretrain/validation/runs/exp8-3-training-report-20260731-v1",
    ),
    (
        "chapter9/hermes-self-evolution/validation/exp8-6-hermes-gpt56luna-autonomous-20260802-v2",
        "chapter9/hermes-self-evolution/validation/exp9-8-hermes-gpt56luna-autonomous-20260802-v2",
    ),
    (
        "chapter10/autonomous-phone-registration/validation/runs/exp10-5-webrtc-raw-20260731-v4",
        "chapter10/autonomous-phone-registration/validation/runs/exp10-3-webrtc-raw-20260731-v4",
    ),
    (
        "chapter10/voice-werewolf/validation/runs/exp10-8-simulated-user-openrouter-20260803-v11",
        "chapter10/voice-werewolf/validation/runs/exp10-6-simulated-user-openrouter-20260803-v11",
    ),
)


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_public_chapter_indexes_use_the_2_0_structure():
    root_readme = read("README.md")
    zh_readme = read("docs/zh-CN/README.md")

    for document in (root_readme, zh_readme):
        assert "书稿版本已由 1.4 升级为 2.0" in document
        assert "**103 个配套实验**" in document
        for number, (title, count) in CHAPTERS.items():
            assert f"| {number} |" in document
            assert f"**{title}**" in document
            assert f"[{count}]" in document

    assert "从模态与时序两个维度扩展 Agent 的观察与动作空间" in root_readme
    assert "撤掉“轮流发言”前提" not in root_readme


def test_introduction_uses_two_parts_and_current_chapter_numbers():
    introduction = read("book/introduction.md")
    structure_figure = read("book/images/fig0-2.svg")

    assert "第一部分“如何构建 Agent”" in introduction
    assert "第二部分“如何提升 Agent 能力”" in introduction
    assert "沿四个层次展开" not in introduction
    assert "第一部分　如何构建 Agent" in structure_figure
    assert "第二部分　如何提升 Agent 能力" in structure_figure
    assert "第 6 章　交互" in structure_figure
    assert "第 7 章　Agent 的评估" in structure_figure
    assert "第 10 章　多 Agent 协作" in structure_figure


def test_book_build_metadata_uses_v2_0_everywhere():
    versioned_files = [
        ROOT / ".github/workflows/build-latest.yml",
        ROOT / "build_epub.sh",
        *ROOT.glob("book*/cover.tex"),
        *ROOT.glob("book*/build_pdf.sh"),
    ]

    assert versioned_files
    for path in versioned_files:
        content = path.read_text(encoding="utf-8")
        assert "v1.4" not in content, path
        if "cover.tex" == path.name or "build_pdf.sh" == path.name:
            assert "v2.0" in content, path


def test_issue_907_verifier_and_runner_use_experiment_9_1():
    verifier = read("chapter9/trajectory-verifier/verifier.py")
    demo = read("chapter9/trajectory-verifier/demo.py")

    assert "Experiment 9-1" in verifier
    assert "Experiment 8-1" not in verifier
    assert "Experiment 9-1" in demo
    assert (ROOT / "chapter9/trajectory-verifier/run_experiment_9_1.py").is_file()
    assert not (ROOT / "chapter9/trajectory-verifier/run_experiment_8_1.py").exists()


def test_representative_retained_runs_use_current_identifiers():
    for old_path, current_path in RENAMED_RUNS:
        assert not (ROOT / old_path).exists(), old_path
        assert (ROOT / current_path).exists(), current_path


def test_chapter_overviews_do_not_link_obsolete_run_ids():
    forbidden = {
        "chapter6/README.md": ("chapter9/", "exp9-"),
        "chapter7/README.md": ("exp6-", "chapter6/"),
        "chapter8/README.md": ("chapter7/", "exp7-"),
        "chapter10/README.md": (
            "exp10-5-webrtc",
            "exp10-4-talkact",
            "exp10-6-real-receipts",
            "exp10-7-qwen",
            "exp10-8-simulated-user",
        ),
    }

    for path, fragments in forbidden.items():
        content = read(path)
        for fragment in fragments:
            assert fragment not in content, (path, fragment)
