import pytest
from werewolf.game import Judge
from werewolf.agent import PlayerAgent
from werewolf.roles import Role, Faction

def test_simultaneous_deaths_returns_undecided_faction():
    """Contract proved: Judge._check_winner returns Faction.UNDECIDED when all wolves and good players die simultaneously.
    Bug locked out: returning Faction.GOOD when zero good players survive alongside zero wolves."""
    # Setup players: 1 Werewolf and 1 Witch (Good)
    p_wolf = PlayerAgent("P1", Role.WEREWOLF, offline=True)
    p_witch = PlayerAgent("P2", Role.WITCH, offline=True)
    judge = Judge([p_wolf, p_witch])
    
    # Both players die in night phase
    p_wolf.alive = False
    p_witch.alive = False
    
    # Check winner must report UNDECIDED, not GOOD when zero good players survive
    winner = judge._check_winner()
    assert winner == Faction.UNDECIDED
