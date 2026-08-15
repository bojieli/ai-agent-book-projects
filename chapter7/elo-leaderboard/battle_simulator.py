"""
Synthetic pairwise battle generator (offline).

Generates head-to-head "battle" outcomes from a set of known latent skill
scores, so the whole battles -> Elo -> leaderboard pipeline can be demonstrated
end-to-end without downloading the 2GB Chatbot Arena dataset or calling any API.

Because the ground-truth skills are known, the recovered Elo leaderboard can be
checked against them: the ranking should match, which validates the
implementation. Ties are produced with a configurable probability to exercise
the tie-handling paths in both the online Elo and Bradley-Terry code.
"""
import random
from typing import Dict, List, Optional


# Default roster with plausible latent skills (in Elo points). The exact numbers
# are only used to *generate* battles; the experiment then tries to recover them.
DEFAULT_TRUE_SKILLS: Dict[str, float] = {
    "gpt-4": 1250.0,
    "claude-3-opus": 1225.0,
    "gemini-1.5-pro": 1180.0,
    "llama-3-70b": 1120.0,
    "mixtral-8x7b": 1075.0,
    "gpt-3.5-turbo": 1035.0,
    "llama-2-13b": 980.0,
    "vicuna-13b": 935.0,
}


def expected_score(rating_a: float, rating_b: float,
                   base: float = 10.0, scale: float = 400.0) -> float:
    """Bradley-Terry / Elo win probability of A against B."""
    return 1.0 / (1.0 + base ** ((rating_b - rating_a) / scale))


def simulate_battles(true_skills: Dict[str, float],
                     num_battles: int,
                     tie_prob: float = 0.1,
                     seed: Optional[int] = None) -> List[dict]:
    """
    Simulate `num_battles` random pairwise battles.

    For each battle two distinct models are drawn uniformly at random. With
    probability `tie_prob` the outcome is a tie; otherwise the winner is sampled
    according to the Bradley-Terry win probability implied by the latent skills
    (so upsets happen, but stronger models win more often).

    Args:
        true_skills: Mapping of model name -> latent skill (Elo points).
        num_battles: Number of battles to generate.
        tie_prob: Probability that a battle ends in a tie.
        seed: Optional RNG seed for reproducibility.

    Returns:
        List of dicts with keys 'model_a', 'model_b', 'winner'
        (winner in {'model_a', 'model_b', 'tie'}), matching the Chatbot Arena
        schema consumed by the Elo / Bradley-Terry code.
    """
    if len(true_skills) < 2:
        raise ValueError("Need at least 2 models to simulate battles")

    rng = random.Random(seed)
    models = list(true_skills.keys())
    battles: List[dict] = []

    for _ in range(num_battles):
        model_a, model_b = rng.sample(models, 2)
        if rng.random() < tie_prob:
            winner = "tie"
        elif rng.random() < expected_score(true_skills[model_a], true_skills[model_b]):
            winner = "model_a"
        else:
            winner = "model_b"
        battles.append({"model_a": model_a, "model_b": model_b, "winner": winner})

    return battles
