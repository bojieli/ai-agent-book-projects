"""
Chess game tools for game management and analysis.
Based on AWorld MCP server implementation.
"""
import logging
import traceback
from typing import Dict, Any

import chess
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class ChessBoardState(BaseModel):
    """Structured representation of the chess board state."""
    
    fen: str
    turn: str  # 'white' or 'black'
    castling_rights: str
    ep_square: str | None = None
    halfmove_clock: int
    fullmove_number: int
    is_check: bool
    is_checkmate: bool
    is_stalemate: bool
    is_insufficient_material: bool
    is_game_over: bool
    ascii_board: str
    legal_moves_uci: list[str]
    legal_moves_san: list[str]


class ChessMoveResult(BaseModel):
    """Result of making a chess move."""
    
    move_uci: str
    move_san: str
    is_capture: bool
    is_check: bool
    is_kingside_castling: bool
    is_queenside_castling: bool
    board_after_move: ChessBoardState


# Global board instance for the session
_game_board = chess.Board()


def _get_current_board_state() -> ChessBoardState:
    """Get the current board state in a structured format."""
    legal_moves_uci = [move.uci() for move in _game_board.legal_moves]
    legal_moves_san = []
    
    # Generate SAN for legal moves
    for move in _game_board.legal_moves:
        try:
            legal_moves_san.append(_game_board.san(move))
        except Exception:
            legal_moves_san.append(move.uci())
    
    ep_sq_name = chess.square_name(_game_board.ep_square) if _game_board.ep_square else None
    
    return ChessBoardState(
        fen=_game_board.fen(),
        turn="white" if _game_board.turn == chess.WHITE else "black",
        castling_rights=_game_board.castling_xfen(),
        ep_square=ep_sq_name,
        halfmove_clock=_game_board.halfmove_clock,
        fullmove_number=_game_board.fullmove_number,
        is_check=_game_board.is_check(),
        is_checkmate=_game_board.is_checkmate(),
        is_stalemate=_game_board.is_stalemate(),
        is_insufficient_material=_game_board.is_insufficient_material(),
        is_game_over=_game_board.is_game_over(),
        ascii_board=str(_game_board),
        legal_moves_uci=legal_moves_uci,
        legal_moves_san=legal_moves_san
    )


async def new_game() -> Dict[str, Any]:
    """
    Start a new chess game.
    
    Returns:
        Dictionary with initial board state
    """
    try:
        global _game_board
        _game_board.reset()
        
        logger.info("🎮 New chess game started")
        
        state = _get_current_board_state()
        
        return {
            "success": True,
            "message": "New game started",
            "board_state": state.model_dump()
        }
        
    except Exception as e:
        error_msg = f"Failed to start new game: {str(e)}"
        logger.error(f"New game error: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": error_msg
        }


async def load_fen(fen_string: str) -> Dict[str, Any]:
    """
    Load a chess position from FEN notation.
    
    Args:
        fen_string: FEN string representing the board state
        
    Returns:
        Dictionary with loaded board state
    """
    try:
        global _game_board
        _game_board.set_fen(fen_string)
        
        logger.info(f"♟️ Loaded FEN: {fen_string}")
        
        state = _get_current_board_state()
        
        return {
            "success": True,
            "message": "Loaded position from FEN",
            "board_state": state.model_dump()
        }
        
    except ValueError as e:
        error_msg = f"Invalid FEN string: {str(e)}"
        logger.error(f"FEN loading error: {error_msg}")
        
        return {
            "success": False,
            "error": error_msg
        }


async def make_move(move_str: str) -> Dict[str, Any]:
    """
    Make a move on the chess board.
    
    Args:
        move_str: Move in UCI (e.g., 'e2e4') or SAN (e.g., 'Nf3') format
        
    Returns:
        Dictionary with move result and new board state
    """
    try:
        global _game_board
        
        move = None
        
        # Try parsing as UCI first, then SAN
        try:
            move = _game_board.parse_uci(move_str)
        except ValueError:
            try:
                move = _game_board.parse_san(move_str)
            except ValueError:
                raise ValueError(f"Invalid move format: {move_str}")
        
        if move not in _game_board.legal_moves:
            raise ValueError(f"Illegal move: {move_str}")
        
        move_san = _game_board.san(move)
        is_capture = _game_board.is_capture(move)
        is_kingside_castling = _game_board.is_kingside_castling(move)
        is_queenside_castling = _game_board.is_queenside_castling(move)
        
        _game_board.push(move)
        is_check_after_move = _game_board.is_check()
        
        logger.info(f"♟️ Move made: {move_str} (UCI: {move.uci()}, SAN: {move_san})")
        
        current_state = _get_current_board_state()
        
        move_result = ChessMoveResult(
            move_uci=move.uci(),
            move_san=move_san,
            is_capture=is_capture,
            is_check=is_check_after_move,
            is_kingside_castling=is_kingside_castling,
            is_queenside_castling=is_queenside_castling,
            board_after_move=current_state
        )
        
        return {
            "success": True,
            "message": f"Move {move_san} played",
            "move_result": move_result.model_dump()
        }
        
    except ValueError as e:
        error_msg = f"Failed to make move: {str(e)}"
        logger.error(f"Move error: {error_msg}")
        
        return {
            "success": False,
            "error": error_msg
        }


async def get_legal_moves() -> Dict[str, Any]:
    """
    Get all legal moves in the current position.
    
    Returns:
        Dictionary with legal moves in UCI and SAN formats
    """
    try:
        legal_moves_uci = [move.uci() for move in _game_board.legal_moves]
        legal_moves_san = []
        
        for move in _game_board.legal_moves:
            try:
                legal_moves_san.append(_game_board.san(move))
            except Exception:
                legal_moves_san.append(move.uci())
        
        logger.info(f"📋 Retrieved {len(legal_moves_uci)} legal moves")
        
        return {
            "success": True,
            "legal_moves": {
                "uci": legal_moves_uci,
                "san": legal_moves_san,
                "count": len(legal_moves_uci)
            }
        }
        
    except Exception as e:
        error_msg = f"Failed to get legal moves: {str(e)}"
        logger.error(f"Legal moves error: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": error_msg
        }


async def get_board_state() -> Dict[str, Any]:
    """
    Get the current board state.
    
    Returns:
        Dictionary with complete board state
    """
    try:
        state = _get_current_board_state()
        
        return {
            "success": True,
            "board_state": state.model_dump()
        }
        
    except Exception as e:
        error_msg = f"Failed to get board state: {str(e)}"
        logger.error(f"Board state error: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": error_msg
        }


async def get_game_status() -> Dict[str, Any]:
    """
    Get the current game status.
    
    Returns:
        Dictionary with game status information
    """
    try:
        state = _get_current_board_state()
        
        is_draw = state.is_stalemate or state.is_insufficient_material or (state.is_game_over and not state.is_checkmate)
        status_message = "Game in progress"
        winner = None
        
        if state.is_checkmate:
            status_message = f"Checkmate! {state.turn.capitalize()} is mated"
            winner = "black" if _game_board.turn == chess.WHITE else "white"
        elif state.is_stalemate:
            status_message = "Stalemate! The game is a draw"
        elif state.is_insufficient_material:
            status_message = "Draw by insufficient material"
        elif state.is_game_over:
            status_message = "Game over! The game is a draw"
        elif state.is_check:
            status_message = f"{state.turn.capitalize()} is in check"
        
        status_data = {
            "status_message": status_message,
            "is_game_over": state.is_game_over,
            "is_check": state.is_check,
            "is_checkmate": state.is_checkmate,
            "is_stalemate": state.is_stalemate,
            "is_draw": is_draw,
            "winner": winner,
            "current_turn": state.turn
        }
        
        logger.info(f"📊 Game status: {status_message}")
        
        return {
            "success": True,
            "game_status": status_data
        }
        
    except Exception as e:
        error_msg = f"Failed to get game status: {str(e)}"
        logger.error(f"Game status error: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": error_msg
        }


async def undo_move() -> Dict[str, Any]:
    """
    Undo the last move.
    
    Returns:
        Dictionary with board state after undo
    """
    try:
        global _game_board
        
        if len(_game_board.move_stack) == 0:
            return {
                "success": False,
                "error": "No moves to undo"
            }
        
        last_move = _game_board.pop()
        
        logger.info(f"↩️ Undid move: {last_move.uci()}")
        
        state = _get_current_board_state()
        
        return {
            "success": True,
            "message": f"Undid move {last_move.uci()}",
            "board_state": state.model_dump()
        }
        
    except Exception as e:
        error_msg = f"Failed to undo move: {str(e)}"
        logger.error(f"Undo error: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": error_msg
        }


async def get_move_history() -> Dict[str, Any]:
    """
    Get the history of moves played in the current game.
    
    Returns:
        Dictionary with move history
    """
    try:
        moves_uci = [move.uci() for move in _game_board.move_stack]
        
        # Generate SAN notation for moves
        board_copy = chess.Board()
        moves_san = []
        
        for move in _game_board.move_stack:
            try:
                san = board_copy.san(move)
                moves_san.append(san)
                board_copy.push(move)
            except Exception:
                moves_san.append(move.uci())
        
        logger.info(f"📜 Retrieved move history: {len(moves_uci)} moves")
        
        return {
            "success": True,
            "move_history": {
                "moves_uci": moves_uci,
                "moves_san": moves_san,
                "move_count": len(moves_uci)
            }
        }
        
    except Exception as e:
        error_msg = f"Failed to get move history: {str(e)}"
        logger.error(f"Move history error: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": error_msg
        }


async def reset_board() -> Dict[str, Any]:
    """
    Reset the board to the starting position.
    
    Returns:
        Dictionary with reset board state
    """
    return await new_game()
