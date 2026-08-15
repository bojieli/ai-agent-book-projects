"""
Quick start demo - minimal example to get started quickly
"""
from elo_rating import EloRatingSystem


def demo_basic_elo():
    """Demonstrate basic Elo rating calculation with synthetic data."""
    
    print("="*60)
    print("Quick Start: Elo Rating System Demo")
    print("="*60)
    print()
    
    # Initialize Elo system
    elo = EloRatingSystem(initial_rating=1000.0, k_factor=32.0)
    
    # Simulate some matches
    matches = [
        ("GPT-4", "Claude-v1", "GPT-4"),
        ("GPT-4", "Llama-2", "GPT-4"),
        ("Claude-v1", "Llama-2", "Claude-v1"),
        ("GPT-4", "Claude-v1", "tie"),
        ("Llama-2", "Gemini", "Gemini"),
        ("GPT-4", "Gemini", "GPT-4"),
        ("Claude-v1", "Gemini", "Claude-v1"),
        ("GPT-4", "Llama-2", "GPT-4"),
        ("Claude-v1", "Llama-2", "Claude-v1"),
        ("Gemini", "Llama-2", "Gemini"),
    ]
    
    print("Processing matches:")
    print("-" * 60)
    for i, (model_a, model_b, winner) in enumerate(matches, 1):
        old_rating_a = elo.get_rating(model_a)
        old_rating_b = elo.get_rating(model_b)

        # update_ratings expects 'model_a' / 'model_b' / 'tie', not the
        # winning model's name (anything unrecognized is scored as a tie).
        outcome = ("model_a" if winner == model_a
                   else "model_b" if winner == model_b else "tie")
        new_rating_a, new_rating_b = elo.update_ratings(model_a, model_b, outcome)
        
        print(f"Match {i}: {model_a} vs {model_b} -> {winner} wins")
        print(f"  {model_a}: {old_rating_a:.1f} → {new_rating_a:.1f} ({new_rating_a-old_rating_a:+.1f})")
        print(f"  {model_b}: {old_rating_b:.1f} → {new_rating_b:.1f} ({new_rating_b-old_rating_b:+.1f})")
        print()
    
    # Show final leaderboard
    print("=" * 60)
    print("Final Leaderboard:")
    print("=" * 60)
    leaderboard = elo.get_leaderboard()
    for rank, (model, rating, matches, wins) in enumerate(leaderboard, 1):
        win_rate = (wins / matches * 100) if matches > 0 else 0
        print(f"{rank}. {model:15s} - Rating: {rating:7.1f} | "
              f"Matches: {matches:2d} | Wins: {wins:4.1f} | Win Rate: {win_rate:5.1f}%")
    
    print()
    
    # Show win probability predictions
    print("=" * 60)
    print("Win Probability Predictions:")
    print("=" * 60)
    
    models = [m[0] for m in leaderboard]
    for i, model_a in enumerate(models):
        for model_b in models[i+1:]:
            prob = elo.calculate_win_probability(model_a, model_b)
            print(f"{model_a} vs {model_b}: {prob*100:.1f}% - {(1-prob)*100:.1f}%")
    
    print()
    print("=" * 60)
    print("Demo complete! Check main.py for full analysis with real data.")
    print("=" * 60)


if __name__ == "__main__":
    demo_basic_elo()

