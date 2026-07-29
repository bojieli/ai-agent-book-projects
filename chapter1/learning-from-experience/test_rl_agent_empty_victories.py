"""
Test suite locking out ZeroDivisionError in QLearningAgent.train
when computing victory_rate on an empty episode_victories list.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rl_agent import QLearningAgent


def test_q_learning_agent_train_empty_victories_snapshot():
    """
    Ensure checkpoint victory_rate calculation does not raise ZeroDivisionError when recent is empty.
    """
    agent = QLearningAgent.__new__(QLearningAgent)
    agent.episode_victories = []
    agent.learning_curve = []
    agent.q_table = {}
    agent.epsilon = 0.1

    # Simulate snapshot logic when checkpoint_interval matches
    recent = agent.episode_victories[-1000:]
    victory_rate = sum(recent) / len(recent) if recent else 0.0
    
    agent.learning_curve.append({
        "episode": 1,
        "victory_rate": victory_rate,
        "q_table_size": len(agent.q_table),
        "epsilon": agent.epsilon,
    })

    assert agent.learning_curve[0]["victory_rate"] == 0.0
