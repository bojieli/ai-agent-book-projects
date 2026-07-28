"""Tests for the deterministic offline ReAct demonstration."""

from agent import run_offline_demo


def test_offline_demo_returns_a_complete_deterministic_trace():
    result = run_offline_demo("캐싱이 뭐야?", verbose=False)

    assert result["question"] == "캐싱이 뭐야?"
    assert [step["type"] for step in result["trace"]] == [
        "thought",
        "action",
        "observation",
        "thought",
        "action",
        "observation",
        "answer",
    ]
    assert result["answer"] == result["trace"][-1]["content"]
    assert "离线示例轨迹" in result["answer"]


def test_offline_demo_verbose_mode_prints_each_trace_step(capsys):
    result = run_offline_demo("question", verbose=True)

    output = capsys.readouterr().out
    assert output.count("💭") == 2
    assert output.count("🔧") == 2
    assert output.count("👀") == 2
    assert output.count("✅") == 1
    assert result["answer"] in output


def test_offline_demo_quiet_mode_prints_nothing(capsys):
    run_offline_demo("question", verbose=False)

    assert capsys.readouterr().out == ""
