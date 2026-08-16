"""Regression test for empty evaluation windows in chapter1 RL and LLM learning agents."""

import sys
from pathlib import Path
import pytest

pytest.importorskip("openai")
pytest.importorskip("numpy")
# Add chapter1/learning-from-experience to sys.path
ch1_dir = (Path(__file__).resolve().parent.parent / "chapter1" / "learning-from-experience").resolve()
if str(ch1_dir) not in sys.path:
    sys.path.insert(0, str(ch1_dir))

from llm_agent import LLMAgent
from rl_agent import QLearningAgent


def test_rl_agent_evaluate_zero_episodes():
    agent = QLearningAgent()
    results = agent.evaluate(num_episodes=0)
    assert results["num_episodes"] == 0
    assert results["victory_rate"] == 0.0
    assert results["avg_reward"] == 0.0
    assert results["avg_length"] == 0.0
    assert results["std_reward"] == 0.0
    assert results["std_length"] == 0.0


def test_llm_agent_evaluate_zero_episodes():
    agent = LLMAgent(api_key="dummy-key")
    results = agent.evaluate(num_episodes=0)
    assert results["num_episodes"] == 0
    assert results["victory_rate"] == 0.0
    assert results["avg_reward"] == 0.0
    assert results["avg_length"] == 0.0
