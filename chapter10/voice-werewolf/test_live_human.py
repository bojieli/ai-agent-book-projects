import json
import sys
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

import demo
from werewolf.agent import PlayerAgent
from werewolf.game import Judge, create_players
from werewolf.human import HumanPlayerAgent, LiveVoiceSession
from werewolf.roles import Faction, Role
from werewolf.strategy_audit import evaluate_strategy, strategy_acceptance_passes, validate_strategy_result


class NoAudio:
    def __init__(self):
        self.private_prompts = []

    def say(self, speaker, text, round_no, allow_barge_in=False):
        self.private_prompts.append(text)


def test_exact_acceptance_roster_has_one_human_and_required_roles():
    players = create_players(seed=42, players=7, wolves=2, human_seat=1, voice=NoAudio())
    assert sum(isinstance(p, HumanPlayerAgent) for p in players) == 1
    roles = [p.role for p in players]
    assert roles.count(Role.WEREWOLF) == 2
    assert roles.count(Role.SEER) == 1
    assert roles.count(Role.WITCH) == 1
    assert players[0].role in set(Role)


@pytest.mark.parametrize("seat_count", [6, 7, 8])
def test_every_allowed_live_roster_has_one_human_and_five_to_seven_ai(seat_count):
    players = create_players(
        seed=seat_count,
        players=seat_count,
        wolves=2,
        human_seat=1,
        voice=NoAudio(),
    )
    roles = [player.role for player in players]
    assert sum(isinstance(player, HumanPlayerAgent) for player in players) == 1
    assert sum(not isinstance(player, HumanPlayerAgent) for player in players) == seat_count - 1
    assert 5 <= seat_count - 1 <= 7
    assert roles.count(Role.WEREWOLF) == 2
    assert roles.count(Role.SEER) == 1
    assert roles.count(Role.WITCH) == 1
    assert roles.count(Role.VILLAGER) == seat_count - 4


def test_spoken_player_number_parser():
    candidates = ["P2", "P3", "P4"]
    assert HumanPlayerAgent._spoken_target("我投三号玩家", candidates, True) == "P3"
    assert HumanPlayerAgent._spoken_target("player 4", candidates, True) == "P4"
    assert HumanPlayerAgent._spoken_target("I choose player three", candidates, True) == "P3"
    assert HumanPlayerAgent._spoken_target("我弃票", candidates, True) is None
    assert HumanPlayerAgent._spoken_target("I choose to abstain", candidates, True) is None
    assert not HumanPlayerAgent._explicit_none("P1 is not")


def test_live_human_terminal_never_prints_god_view(capsys):
    voice = NoAudio()
    players = create_players(seed=42, players=7, wolves=2, human_seat=1, voice=voice)
    judge = Judge(players, seed=42)
    judge.assign_identities()
    output = capsys.readouterr().out
    assert "上帝视角身份表已隐藏" in output
    assert "P2:" not in output
    assert any("您的身份" in prompt for prompt in voice.private_prompts)
    judge._print_private(["P2"], "SECRET_WOLF_ACTION")
    assert "SECRET_WOLF_ACTION" not in capsys.readouterr().out
    judge._print_private(["P1"], "MY_PRIVATE_ACTION")
    assert "MY_PRIVATE_ACTION" in capsys.readouterr().out


def test_live_default_without_consent_stops_before_game_or_voice_construction(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["demo.py"])
    with patch("demo.run_game") as run_game, patch(
        "werewolf.human.LiveVoiceSession"
    ) as live_session:
        with pytest.raises(SystemExit) as exc:
            demo.main()
    assert exc.value.code == 2
    run_game.assert_not_called()
    live_session.assert_not_called()


def test_human_role_is_actually_randomized_by_the_shared_shuffle():
    observed = {
        create_players(seed=seed, players=7, wolves=2, human_seat=1, voice=NoAudio())[0].role
        for seed in range(40)
    }
    assert observed == set(Role)


class PassivePlayer(PlayerAgent):
    def choose_target(self, prompt, candidates, players, allow_none=False):
        if self.role == Role.SEER and candidates:
            return candidates[0]
        return None

    def speak(self, players):
        return "我暂时没有可验证的判断。"

    def vote(self, candidates, players):
        return None


def test_three_cycles_count_only_after_night_day_vote_and_round_cap_is_not_fake_win(capsys):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.SEER, Role.WITCH,
             Role.VILLAGER, Role.VILLAGER, Role.VILLAGER]
    players = [PassivePlayer(f"P{i + 1}", role, offline=True) for i, role in enumerate(roles)]
    judge = Judge(players, seed=7, max_rounds=3)

    winner = judge.run()

    assert judge.completed_rounds == 3
    assert len([r for r in judge.audit.records if r.category == "公开-死讯"]) == 3
    assert len([r for r in judge.audit.records if r.category == "公开-放逐"]) == 3
    assert winner == Faction.UNDECIDED
    output = capsys.readouterr().out
    assert "本局未决" in output
    assert "获胜阵营：未决" not in output


def test_deterministic_winner_conditions():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.SEER, Role.WITCH,
             Role.VILLAGER, Role.VILLAGER]
    players = [PlayerAgent(f"P{i + 1}", role, offline=True) for i, role in enumerate(roles)]
    judge = Judge(players)
    players[0].alive = players[1].alive = False
    assert judge._check_winner() == Faction.GOOD
    players[0].alive = players[1].alive = True
    players[4].alive = players[5].alive = False
    assert judge._check_winner() == Faction.WEREWOLF
    players[5].alive = True
    assert judge._check_winner() is None


def test_strategy_acceptance_requires_all_named_criteria_and_evidence():
    valid = {
        "criteria": {
            name: {"status": "pass", "evidence": f"quoted evidence for {name}"}
            for name in (
                "werewolf_concealment", "seer_timing_and_evidence",
                "villager_logical_reasoning", "role_consistency",
            )
        },
        "overall_pass": True,
    }
    assert strategy_acceptance_passes(validate_strategy_result(valid))
    valid_fail = {
        "criteria": {
            name: {"status": "fail", "evidence": f"counterevidence for {name}"}
            for name in (
                "werewolf_concealment", "seer_timing_and_evidence",
                "villager_logical_reasoning", "role_consistency",
            )
        },
        "overall_pass": False,
    }
    checked_fail = validate_strategy_result(valid_fail)
    assert checked_fail["schema_valid"] is True
    assert checked_fail["overall_pass"] is False
    assert not strategy_acceptance_passes(checked_fail)
    malformed = {"criteria": {"role_consistency": {"status": "pass"}}, "overall_pass": True}
    checked = validate_strategy_result(malformed)
    assert checked["schema_valid"] is False
    assert checked["overall_pass"] is False
    assert not strategy_acceptance_passes(checked)


def test_strategy_audit_retains_invalid_schema_and_tries_next_backend(monkeypatch):
    from werewolf import strategy_audit as audit_module

    criteria = {
        name: {"status": "pass", "evidence": f"quoted evidence for {name}"}
        for name in (
            "werewolf_concealment", "seer_timing_and_evidence",
            "villager_logical_reasoning", "role_consistency",
        )
    }
    malformed = {
        "criteria": dict(list(criteria.items())[:3]),
        "role_consistency": criteria["role_consistency"],
    }
    valid = {"criteria": criteria, "overall_pass": True}

    class Completion:
        def __init__(self, payload, response_id):
            self.payload = payload
            self.response_id = response_id

        def create(self, **kwargs):
            return SimpleNamespace(
                id=self.response_id,
                model="reported-model",
                usage=SimpleNamespace(model_dump=lambda: {"prompt_tokens": 10, "completion_tokens": 5}),
                choices=[SimpleNamespace(message=SimpleNamespace(content=__import__("json").dumps(self.payload)))],
            )

    def client(payload, response_id):
        return SimpleNamespace(chat=SimpleNamespace(completions=Completion(payload, response_id)))

    monkeypatch.setattr(audit_module, "_backends", lambda: [
        (client(malformed, "bad-schema"), "judge-a", "provider-a"),
        (client(valid, "valid-schema"), "judge-b", "provider-b"),
    ])
    judge = SimpleNamespace(
        players=[SimpleNamespace(name="P1", role=Role.VILLAGER)],
        action_history=[{"actor": "P1", "role": "村民", "action": "vote", "target": "P2"}],
    )
    result = evaluate_strategy(judge)
    assert result["schema_valid"] is True
    assert result["overall_pass"] is True
    assert result["provider"] == "provider-b"
    assert [attempt["response_id"] for attempt in result["judge_attempts"]] == [
        "bad-schema", "valid-schema"
    ]
    assert result["judge_attempts"][0]["schema_valid"] is False
    # Invalid-attempt provenance must remain acyclic when attached to the
    # accepted result so the retained acceptance report can be serialized.
    json.dumps(result)


def test_barge_in_cancels_playback_and_transcribes_without_real_audio(monkeypatch, tmp_path):
    class FakeProcess:
        def __init__(self):
            self.terminated = False

        def poll(self):
            return 0 if self.terminated else None

        def terminate(self):
            self.terminated = True

    class FakeInputStream:
        def __init__(self, **kwargs):
            self.frames = iter([
                np.full((1024, 1), 0.2, dtype="float32"),
                np.full((1024, 1), 0.2, dtype="float32"),
                np.zeros((1024, 1), dtype="float32"),
            ])

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, _block):
            return next(self.frames), False

    session = LiveVoiceSession.__new__(LiveVoiceSession)
    session.allow_interruptions = True
    session.sample_rate = 1024
    session.threshold = 0.05
    session.silence_seconds = 1.0
    session.max_utterance = 1.0
    session.player = "fake-player"
    events = []
    session._tts = lambda *args: tmp_path / "synthetic.mp3"
    session._event = lambda kind, **data: events.append((kind, data))
    session._write_wav = lambda frames, path: None
    session._transcribe = lambda path, kind: "我来打断"
    proc = FakeProcess()
    monkeypatch.setitem(
        sys.modules, "sounddevice", SimpleNamespace(InputStream=FakeInputStream)
    )
    monkeypatch.setattr("werewolf.human.subprocess.Popen", lambda *args, **kwargs: proc)

    result = session.say("P2", "一段 AI 发言", 1, allow_barge_in=True)

    assert result == "我来打断"
    assert proc.terminated is True
    assert events == [("barge_in", {"interrupted_speaker": "P2"})]
