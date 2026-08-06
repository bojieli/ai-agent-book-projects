import pytest
pytest.importorskip("chess")
"""
Regression test suite for chess get_game_status covering rule-based draws,
stalemate, insufficient material, checkmate, and game in progress.
"""

import asyncio
import sys
from pathlib import Path
import chess

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        / "chapter4"
        / "collaboration-tools"
        / "src"
    ),
)

import chess_tools


def test_chess_game_over_75_move_rule_draw():
    # 75-move rule / 150 halfmoves automatic draw
    board = chess.Board("8/8/8/8/8/8/R7/r6k w - - 150 1")
    assert board.is_game_over() is True
    assert board.is_checkmate() is False

    chess_tools._game_board = board
    res = asyncio.run(chess_tools.get_game_status())
    assert res["success"] is True

    status = res["game_status"]
    assert status["is_game_over"] is True
    assert status["is_draw"] is True
    assert status["winner"] is None
    assert status["status_message"] == "Game over! The game is a draw"


def test_chess_stalemate_draw():
    # Black king stalemated
    board = chess.Board("k7/8/1Q6/8/8/8/8/K7 b - - 0 1")
    assert board.is_stalemate() is True

    chess_tools._game_board = board
    res = asyncio.run(chess_tools.get_game_status())
    assert res["success"] is True

    status = res["game_status"]
    assert status["is_game_over"] is True
    assert status["is_stalemate"] is True
    assert status["is_draw"] is True
    assert status["winner"] is None
    assert status["status_message"] == "Stalemate! The game is a draw"


def test_chess_insufficient_material_draw():
    # Bare kings
    board = chess.Board("k7/8/8/8/8/8/8/K7 w - - 0 1")
    assert board.is_insufficient_material() is True

    chess_tools._game_board = board
    res = asyncio.run(chess_tools.get_game_status())
    assert res["success"] is True

    status = res["game_status"]
    assert status["is_game_over"] is True
    assert status["is_draw"] is True
    assert status["status_message"] == "Draw by insufficient material"


def test_chess_checkmate_not_draw():
    # Scholar's mate
    board = chess.Board(
        "r1bqkb1r/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 0 4"
    )
    board.push_san("Qxf7#")
    assert board.is_checkmate() is True

    chess_tools._game_board = board
    res = asyncio.run(chess_tools.get_game_status())
    assert res["success"] is True

    status = res["game_status"]
    assert status["is_game_over"] is True
    assert status["is_checkmate"] is True
    assert status["is_draw"] is False
    assert status["winner"] == "white"
    assert "Checkmate!" in status["status_message"]


def test_chess_game_in_progress():
    board = chess.Board()
    chess_tools._game_board = board
    res = asyncio.run(chess_tools.get_game_status())
    assert res["success"] is True

    status = res["game_status"]
    assert status["is_game_over"] is False
    assert status["is_draw"] is False
    assert status["winner"] is None
    assert status["status_message"] == "Game in progress"
