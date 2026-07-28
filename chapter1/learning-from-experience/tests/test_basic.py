#!/usr/bin/env python3
"""
Basic test to verify all components work correctly.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_game_environment():
    """Test that the game environment works."""
    print("Testing game environment...")
    from game_environment import TreasureHuntGame
    
    game = TreasureHuntGame(seed=42)
    
    # Test initial state
    state = game.get_state_description()
    assert "entrance" in state.lower()
    print("  ✓ Game initialization works")
    
    # Test actions
    actions = game.get_available_actions()
    assert len(actions) > 0
    print("  ✓ Actions generation works")
    
    # Test action execution
    feedback, reward, done = game.execute_action("look around")
    assert isinstance(feedback, str)
    assert isinstance(reward, float)
    assert isinstance(done, bool)
    print("  ✓ Action execution works")
    
    # Test reset
    game.reset()
    assert game.moves == 0
    print("  ✓ Game reset works")
    
    print("✅ Game environment tests passed!\n")


def test_rl_agent():
    """Test that the RL agent works."""
    print("Testing RL agent...")
    from game_environment import TreasureHuntGame
    from rl_agent import QLearningAgent
    
    game = TreasureHuntGame(seed=42)
    agent = QLearningAgent()
    
    # Test action selection
    action = agent.choose_action(game, training=True)
    assert isinstance(action, str)
    print("  ✓ Action selection works")
    
    # Test Q-value update
    state = agent._get_state_hash(game)
    feedback, reward, done = game.execute_action(action)
    next_state = agent._get_state_hash(game)
    next_actions = game.get_available_actions()
    
    agent.update_q_value(state, action, reward, next_state, next_actions, done)
    print("  ✓ Q-value update works")
    
    # Test training (just 10 episodes for speed)
    results = agent.train(num_episodes=10, verbose=False)
    assert "total_episodes" in results
    print("  ✓ Training works")
    
    print("✅ RL agent tests passed!\n")


def test_llm_agent():
    """Test that the LLM agent works (without API calls)."""
    print("Testing LLM agent structure...")
    from game_environment import TreasureHuntGame
    from llm_agent import LLMAgent, GameExperience
    
    # Test experience storage
    exp = GameExperience(
        state_description="test state",
        action="test action",
        feedback="test feedback",
        reward=1.0,
        success=True
    )
    assert exp.action == "test action"
    print("  ✓ Experience dataclass works")
    
    # Test context building (without API)
    try:
        # This will fail without API key, but we can test the structure
        agent = LLMAgent(api_key="dummy-key-for-testing")
        
        game = TreasureHuntGame()
        state = game.get_state_description()
        actions = game.get_available_actions()
        
        context = agent._build_context(state, actions)
        assert "treasure hunt" in context.lower()
        print("  ✓ Context building works")
        
        # Test experience update
        agent.update_experience(state, "test action", "test feedback", 1.0)
        assert len(agent.experiences) == 1
        print("  ✓ Experience storage works")
        
    except ValueError as e:
        if "MOONSHOT_API_KEY" in str(e):
            print("  ⚠ LLM agent requires API key for full testing")
        else:
            raise
    
    print("✅ LLM agent structure tests passed!\n")


def test_experiment_runner():
    """Test that the experiment runner works."""
    print("Testing experiment runner...")
    from experiment import ExperimentRunner
    
    runner = ExperimentRunner(results_dir="test_results")
    assert runner.results_dir.exists()
    print("  ✓ Experiment runner initialization works")
    
    # Clean up test directory
    import shutil
    if runner.results_dir.exists():
        shutil.rmtree(runner.results_dir)
    
    print("✅ Experiment runner tests passed!\n")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("RUNNING BASIC TESTS")
    print("="*60 + "\n")
    
    try:
        test_game_environment()
        test_rl_agent()
        test_llm_agent()
        test_experiment_runner()
        
        print("="*60)
        print("ALL TESTS PASSED! ✅")
        print("="*60)
        print("\nThe experiment is ready to run.")
        print("To run the full experiment: python experiment.py")
        print("To play interactively: python demo.py")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
