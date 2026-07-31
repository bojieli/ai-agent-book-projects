#!/usr/bin/env python3
"""Regression tests for zero-episode division guards.

Bug: train()/evaluate() divided victory counts by episode counts, so
num_episodes=0 (accepted by experiment.py's argparse) crashed with
ZeroDivisionError. Fixed by guarding the divisions and rejecting
episode counts < 1 in experiment.py's front door.
"""

import sys

import experiment
from llm_agent import LLMAgent
from rl_agent import QLearningAgent


def test_rl_train_zero_episodes_no_zero_division():
    result = QLearningAgent().train(num_episodes=0, verbose=False)
    assert result["total_episodes"] == 0
    assert result["victory_rate"] == 0.0


def test_rl_evaluate_zero_episodes_no_zero_division():
    result = QLearningAgent().evaluate(num_episodes=0)
    assert result["num_episodes"] == 0
    assert result["victory_rate"] == 0.0


def test_llm_evaluate_zero_episodes_no_zero_division():
    # Dummy key: constructing the client makes no network calls, and
    # evaluate(num_episodes=0) never reaches the API.
    agent = LLMAgent(api_key="dummy-key")
    result = agent.evaluate(num_episodes=0)
    assert result["victory_rate"] == 0.0
    assert result["avg_reward"] == 0.0
    assert result["avg_length"] == 0.0


def test_experiment_rejects_zero_episodes(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["experiment.py", "--mode", "qlearning",
                                      "--rl-episodes", "0"])
    experiment.main()  # must print an error and return before running
    assert "must all be >= 1" in capsys.readouterr().out
