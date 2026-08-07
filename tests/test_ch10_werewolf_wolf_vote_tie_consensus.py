import sys
from pathlib import Path
import pytest

ch10_werewolf = Path(__file__).resolve().parent.parent / "chapter10" / "voice-werewolf"
if str(ch10_werewolf) not in sys.path:
    sys.path.insert(0, str(ch10_werewolf))

from werewolf.game import Judge
from werewolf.agent import PlayerAgent
from werewolf.roles import Role


def test_wolf_vote_tie_consensus_selects_from_top_vote_getters():
    """Regression test: Werewolf night vote tie-breaking must select from top vote-getters.
    When W1 votes for a 1-vote minority candidate (P1) while W2/W3 vote for P2 (2 votes)
    and W4/W5 vote for P3 (2 votes), the killed player must be among the tied top-vote getters
    ({'P2', 'P3'}), NOT the 1-vote minority candidate P1."""
    w1 = PlayerAgent("W1", Role.WEREWOLF, offline=True)
    w2 = PlayerAgent("W2", Role.WEREWOLF, offline=True)
    w3 = PlayerAgent("W3", Role.WEREWOLF, offline=True)
    w4 = PlayerAgent("W4", Role.WEREWOLF, offline=True)
    w5 = PlayerAgent("W5", Role.WEREWOLF, offline=True)

    p1 = PlayerAgent("P1", Role.VILLAGER, offline=True)
    p2 = PlayerAgent("P2", Role.VILLAGER, offline=True)
    p3 = PlayerAgent("P3", Role.VILLAGER, offline=True)

    judge = Judge([w1, w2, w3, w4, w5, p1, p2, p3])

    w1.choose_target = lambda prompt, candidates, players, allow_none=False: "P1"
    w2.choose_target = lambda prompt, candidates, players, allow_none=False: "P2"
    w3.choose_target = lambda prompt, candidates, players, allow_none=False: "P2"
    w4.choose_target = lambda prompt, candidates, players, allow_none=False: "P3"
    w5.choose_target = lambda prompt, candidates, players, allow_none=False: "P3"

    killed = judge._wolves_act()

    assert killed in {"P2", "P3"}, (
        f"Expected consensus kill from top vote getters {{'P2', 'P3'}}, but got {killed!r}"
    )
