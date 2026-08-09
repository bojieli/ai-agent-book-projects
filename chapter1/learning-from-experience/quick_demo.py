#!/usr/bin/env python3
"""
Quick demo showing the LLM learning process in detail.
This script runs a simplified experiment to demonstrate how LLMs learn from experience.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from game_environment import TreasureHuntGame
from llm_agent import LLMAgent


def show_game_solution():
    """Show the optimal solution to the game."""
    print("\n" + "="*70)
    print("GAME SOLUTION (for reference)")
    print("="*70)
    
    game = TreasureHuntGame()
    print(game.get_hidden_rules())
    
    print("\n📝 Optimal solution path:")
    print("1. Take rusty sword (in entrance)")
    print("2. Go east to storage")
    print("3. Take red key")
    print("4. Take magic crystal")
    print("5. Try crafting → creates silver sword")
    print("6. Go west to entrance")
    print("7. Go north to hallway (uses red key automatically)")
    print("8. Go north to guard room")
    print("9. Attack with silver sword → defeats strong guard")
    print("10. Go east to treasure room")
    print("11. Take dragon's treasure → Victory!")
    print("\n✨ Total moves: ~11-12 (optimal)")


def run_llm_demo():
    """Run a simplified LLM demo with just a few episodes."""
    print("\n" + "🤖"*35)
    print("LLM IN-CONTEXT LEARNING DEMO")
    print("🤖"*35)
    
    # Check API key
    provider = os.getenv("LLM_PROVIDER", "moonshot").lower()
    api_key = os.getenv("DASHSCOPE_API_KEY") if provider in {"dashscope", "qwen", "bailian"} else os.getenv("MOONSHOT_API_KEY")
    if not api_key and not os.getenv("OPENROUTER_API_KEY"):
        print(f"\n❌ Error: API key for provider '{provider}' not set.")
        print("Please set your Kimi API key:")
        print("  export DASHSCOPE_API_KEY='your-key-here'  # for dashscope/qwen/bailian")
        print("  export MOONSHOT_API_KEY='your-key-here'   # for moonshot/kimi")
        print("\nGet your key at: https://platform.moonshot.cn/")
        print("Or set OPENROUTER_API_KEY as a universal fallback.")
        return
    
    print("\n✅ API key found!")
    print("🧠 Initializing Kimi K3 LLM agent...")
    
    # Initialize agent
    agent = LLMAgent(
        api_key=api_key,
        model=os.getenv("MOONSHOT_MODEL", "kimi-k3"),
        provider=provider,
        temperature=0.7,
        max_experiences=30
    )
    
    print("\n📚 The LLM will play 3 episodes to learn the game")
    print("👀 Watch how it reasons and learns from each experience!\n")
    
    # Play 3 episodes
    game = TreasureHuntGame()
    
    for episode in range(3):
        print("\n" + "🎮"*35)
        print(f"EPISODE {episode + 1} of 3")
        print("🎮"*35)
        
        # Show what the LLM has learned so far
        if agent.experiences:
            print(f"\n📊 Experience Memory: {len(agent.experiences)} interactions stored")
            
            # Show some key learnings
            successful = [e for e in agent.experiences if e.success]
            if successful:
                print("✅ Successful patterns discovered:")
                for exp in successful[-3:]:
                    print(f"   • {exp.action} → reward: {exp.reward:.1f}")
            
            failed = [e for e in agent.experiences if not e.success]
            if failed and len(failed) > 5:
                print("❌ Mistakes to avoid:")
                for exp in failed[-2:]:
                    print(f"   • {exp.action} → reward: {exp.reward:.1f}")
        
        # Play episode
        reward, steps, victory = agent.play_episode(game, verbose=True)
        
        print(f"\n📈 Episode {episode + 1} Performance:")
        print(f"  • Result: {'🎉 Victory!' if victory else '💀 Failed'}")
        print(f"  • Total Reward: {reward:.2f}")
        print(f"  • Steps Taken: {steps}")
        print(f"  • Experiences Collected: {len(agent.experiences)}")
        
        if victory:
            print("\n🎊 The LLM learned to solve the game!")
            print(f"   It took {episode + 1} episodes to learn")
            print(f"   Total API calls used: {agent.api_calls}")
            break
        
        if episode < 2:
            print("\n⏳ Waiting 2 seconds before next episode...")
            import time
            time.sleep(2)
    
    # Summary
    print("\n" + "="*70)
    print("DEMO SUMMARY")
    print("="*70)
    print(f"📊 Total episodes played: {episode + 1}")
    print(f"🧠 Total experiences collected: {len(agent.experiences)}")
    print(f"🎯 Victories: {agent.victories}")
    print(f"📡 API calls made: {agent.api_calls}")
    
    if agent.victories > 0:
        print("\n✨ Key Insight:")
        print("The LLM learned to solve the game by reasoning about patterns")
        print("in just a few episodes, without any parameter updates!")
        print("Traditional RL would need thousands of episodes for the same result.")
    else:
        print("\n💡 Note: The LLM is still learning. Run more episodes to see it succeed!")


def main():
    """Main entry point."""
    print("\n" + "🎯"*35)
    print("LEARNING FROM EXPERIENCE: LLM DEMO")
    print("Replicating insights from 'The Second Half'")
    print("🎯"*35)
    
    # Show solution first
    show_game_solution()
    
    # Ask user if they want to continue
    response = input("\n▶️ Ready to see how an LLM learns this game? (y/n): ").strip().lower()
    
    if response == 'y':
        run_llm_demo()
    else:
        print("\n👋 Okay, goodbye!")


if __name__ == "__main__":
    main()
