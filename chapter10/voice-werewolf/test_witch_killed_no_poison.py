import pytest
from werewolf.game import Judge
from werewolf.agent import PlayerAgent
from werewolf.roles import Role, Faction


def test_witch_killed_by_wolves_cannot_use_poison_in_same_night():
    """Contract proved: Judge._witch_act prevents a Witch who was killed by wolves at night and not saved from using poison in the same night.
    Bug locked out: allowing a dead witch killed by wolves to poison another player on the night she dies."""
    players = [
        PlayerAgent("P1", Role.WEREWOLF, offline=True),
        PlayerAgent("P2", Role.WEREWOLF, offline=True),
        PlayerAgent("P3", Role.SEER, offline=True),
        PlayerAgent("P4", Role.WITCH, offline=True),
        PlayerAgent("P5", Role.VILLAGER, offline=True),
    ]

    judge = Judge(players, seed=42)
    witch = judge.by_name("P4")

    # Override witch target selection to attempt poisoning P3 if asked
    witch._offline_choose_target = lambda candidates, allow_none: "P3"

    # Wolves killed P4 (the witch)
    killed = "P4"
    poisoned, saved = judge._witch_act(killed)

    assert saved is False
    assert poisoned is None, "A witch killed by wolves at night cannot use poison in the same night"
