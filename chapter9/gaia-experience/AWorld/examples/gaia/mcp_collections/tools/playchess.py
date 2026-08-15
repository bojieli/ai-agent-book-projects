"""
Chess MCP Server

This module provides MCP server functionality for chess game operations and analysis.
It utilizes the 'python-chess' library to support various chess-related tasks.

Key features:
- Manage chess game states (new game, load FEN, make moves)
- Validate and execute moves in UCI or SAN format
- Get legal moves for the current position
- Check game status (checkmate, stalemate, draw, etc.)
- Basic board visualization (ASCII)
- LLM-optimized output formatting for game states and analysis

Main functions:
- mcp_new_game: Start a new chess game
- mcp_load_fen: Load a game state from FEN notation
- mcp_make_move: Make a move on the current board
- mcp_get_legal_moves: List all legal moves in the current position
- mcp_get_board_state: Get the current board state (FEN, ASCII, status)
- mcp_get_game_status: Check the current game status (e.g., checkmate)
- mcp_get_chess_capabilities: Get service capabilities
"""

import json
import traceback
from datetime import datetime
from typing import Any

import chess
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from aworld.logs.util import Color
from examples.gaia.mcp_collections.base import ActionArguments, ActionCollection, ActionResponse


class ChessBoardState(BaseModel):
    """Structured representation of the chess board state."""

    fen: str
    turn: str  # 'white' or 'black'
    castling_rights: str
    ep_square: str | None = None  # The target square if an en passant capture is possible *right now*
    halfmove_clock: int
    fullmove_number: int
    is_check: bool
    is_checkmate: bool
    is_stalemate: bool
    is_insufficient_material: bool
    is_seventyfive_moves: bool
    is_fivefold_repetition: bool
    is_game_over: bool
    ascii_board: str
    legal_moves_uci: list[str]
    legal_moves_san: list[str]
    is_en_passant_possible: bool  # True if there is a legal en passant capture
    en_passant_capture_square: str | None = None  # The square a pawn would move TO for en passant


class ChessMoveResult(BaseModel):
    """Result of making a chess move."""

    move_uci: str
    move_san: str
    is_capture: bool
    is_check: bool
    is_kingside_castling: bool
    is_queenside_castling: bool
    board_after_move: ChessBoardState


class ChessMetadata(BaseModel):
    """Metadata for Chess operation results."""

    operation: str
    fen_before: str | None = None
    fen_after: str | None = None
    move_played: str | None = None
    execution_time: float | None = None
    error_type: str | None = None
    engine_analysis_depth: int | None = None


class ChessCollection(ActionCollection):
    """MCP service for chess game operations and analysis.

    Provides capabilities to manage chess games, make moves, analyze positions,
    and get game status, all formatted for LLM interaction.
    """

    def __init__(self, arguments: ActionArguments) -> None:
        super().__init__(arguments)
        self.board = chess.Board()
        # For more advanced analysis, you might initialize a chess engine here
        # Example: self.engine = chess.engine.SimpleEngine.popen_uci("/path/to/stockfish")
        # Ensure Stockfish or another UCI engine is installed and path is correct.
        self._color_log("Chess service initialized", Color.green, "debug")
        self._color_log(f"Initial board FEN: {self.board.fen()}", Color.blue, "debug")

    def _get_current_board_state(self) -> ChessBoardState:
        """Helper to get the current board state in a structured format."""
        legal_moves_uci = [move.uci() for move in self.board.legal_moves]
        legal_moves_san = []
        # Generating SAN for all moves can be slow, do it carefully or on demand
        # for move in self.board.legal_moves:
        #     try:
        #         legal_moves_san.append(self.board.san(move))
        #     except Exception:
        #         legal_moves_san.append(move.uci()) # Fallback to UCI if SAN fails

        has_legal_ep = self.board.has_legal_en_passant()
        ep_sq_name = chess.square_name(self.board.ep_square) if self.board.ep_square else None

        return ChessBoardState(
            fen=self.board.fen(),
            turn="white" if self.board.turn == chess.WHITE else "black",
            castling_rights=self.board.castling_xfen(),
            ep_square=ep_sq_name,  # This is the target square from FEN, might not be a legal capture
            halfmove_clock=self.board.halfmove_clock,
            fullmove_number=self.board.fullmove_number,
            is_check=self.board.is_check(),
            is_checkmate=self.board.is_checkmate(),
            is_stalemate=self.board.is_stalemate(),
            is_insufficient_material=self.board.is_insufficient_material(),
            is_seventyfive_moves=self.board.is_seventyfive_moves(),
            is_fivefold_repetition=self.board.is_fivefold_repetition(),
            is_game_over=self.board.is_game_over(),
            ascii_board=str(self.board),
            legal_moves_uci=legal_moves_uci,
            legal_moves_san=legal_moves_san,  # Populate if SAN generation is enabled
            is_en_passant_possible=has_legal_ep,
            en_passant_capture_square=ep_sq_name if has_legal_ep else None,
        )

    def _format_board_state_output(self, state: ChessBoardState, output_format: str = "markdown") -> str:
        """Format board state for LLM consumption."""
        if output_format == "json":
            return json.dumps(state.model_dump(), indent=2)

        status_parts = []
        if state.is_checkmate:
            status_parts.append("Checkmate!")
        elif state.is_stalemate:
            status_parts.append("Stalemate!")
        elif state.is_insufficient_material:
            status_parts.append("Draw by insufficient material.")
        elif state.is_seventyfive_moves:
            status_parts.append("Draw by 75-move rule.")
        elif state.is_fivefold_repetition:
            status_parts.append("Draw by fivefold repetition.")
        elif state.is_check:
            status_parts.append("Check!")
        game_status = " ".join(status_parts) if status_parts else "Game in progress."

        en_passant_info = "N/A"
        if state.is_en_passant_possible and state.en_passant_capture_square:
            en_passant_info = f"Yes, capture on {state.en_passant_capture_square}"
        elif state.ep_square:  # FEN might list an ep_square even if no legal ep move
            en_passant_info = f"Target square {state.ep_square} (no legal en passant capture)"

        if output_format == "text":
            return (
                f"Board FEN: {state.fen}\n"
                f"Turn: {state.turn.capitalize()}\n"
                f"Status: {game_status}\n"
                f"Castling: {state.castling_rights}\n"
                f"En Passant Possible: {en_passant_info}\n"  # Updated line
                f"Halfmove Clock: {state.halfmove_clock}\n"
                f"Fullmove Number: {state.fullmove_number}\n"
                f"Game Over: {'Yes' if state.is_game_over else 'No'}\n"
                f"Legal Moves (UCI): {', '.join(state.legal_moves_uci[:10])}... ({len(state.legal_moves_uci)} total)\n"
                f"Board:\n{state.ascii_board}"
            )
        else:  # markdown (default)
            return (
                f"### Chess Board State\n"
                f"**FEN:** `{state.fen}`\n"
                f"**Turn:** {state.turn.capitalize()}\n"
                f"**Status:** {game_status}\n"
                f"**Castling Rights:** {state.castling_rights}\n"
                f"**En Passant Possible:** {en_passant_info}\n"  # Updated line
                f"**Game Over:** {'Yes' if state.is_game_over else 'No'}\n"
                f"**Legal Moves (UCI, sample):** `{', '.join(state.legal_moves_uci[:5])}`... ({len(state.legal_moves_uci)} total)\n"
                f"```\n{state.ascii_board}\n```"
            )

    async def mcp_new_game(self) -> ActionResponse:
        """Starts a new standard chess game, resetting the board.

        Returns:
            ActionResponse with the initial board state.
        """
        start_time = datetime.now()
        self.board.reset()
        self._color_log("🚀 New chess game started", Color.green)

        current_state = self._get_current_board_state()
        formatted_output = self._format_board_state_output(current_state)
        execution_time = (datetime.now() - start_time).total_seconds()

        metadata = ChessMetadata(
            operation="new_game", fen_after=self.board.fen(), execution_time=execution_time
        ).model_dump()

        return ActionResponse(success=True, message=formatted_output, metadata=metadata)

    async def mcp_load_fen(
        self, fen_string: str = Field(description="FEN string representing the board state.")
    ) -> ActionResponse:
        """Loads a chess game from a FEN (Forsyth-Edwards Notation) string.

        Args:
            fen_string: The FEN string to load.

        Returns:
            ActionResponse with the board state after loading the FEN.
        """
        # Handle FieldInfo
        if isinstance(fen_string, FieldInfo):
            fen_string = fen_string.default

        start_time = datetime.now()
        try:
            self.board.set_fen(fen_string)
            self._color_log(f"🔄 Board loaded from FEN: {fen_string}", Color.blue)
            current_state = self._get_current_board_state()
            formatted_output = self._format_board_state_output(current_state)
            execution_time = (datetime.now() - start_time).total_seconds()
            metadata = ChessMetadata(
                operation="load_fen", fen_after=self.board.fen(), execution_time=execution_time
            ).model_dump()
            return ActionResponse(success=True, message=formatted_output, metadata=metadata)
        except ValueError as e:
            error_msg = f"Invalid FEN string: {str(e)}"
            self.logger.error(f"FEN loading error: {traceback.format_exc()}")
            execution_time = (datetime.now() - start_time).total_seconds()
            metadata = ChessMetadata(
                operation="load_fen", error_type="invalid_fen", execution_time=execution_time
            ).model_dump()
            return ActionResponse(success=False, message=error_msg, metadata=metadata)

    async def mcp_make_move(
        self, move_str: str = Field(description="Move in UCI (e.g., 'e2e4') or SAN (e.g., 'Nf3') format.")
    ) -> ActionResponse:
        """Makes a move on the current chess board.

        The move can be in UCI (Universal Chess Interface) format (e.g., 'g1f3')
        or SAN (Standard Algebraic Notation) format (e.g., 'Nf3').

        Args:
            move_str: The move to make.

        Returns:
            ActionResponse with the result of the move and new board state.
        """
        # Handle FieldInfo
        if isinstance(move_str, FieldInfo):
            move_str = move_str.default

        start_time = datetime.now()
        fen_before = self.board.fen()
        try:
            move = None
            # Try parsing as UCI first, then SAN
            try:
                move = self.board.parse_uci(move_str)
            except ValueError:
                try:
                    move = self.board.parse_san(move_str)
                except ValueError as e_san:
                    raise ValueError(f"Invalid move format. UCI error: N/A, SAN error: {e_san}") from e_san

            if move not in self.board.legal_moves:
                raise ValueError(f"Illegal move: {move_str}")

            move_san = self.board.san(move)
            is_capture = self.board.is_capture(move)
            is_kingside_castling = self.board.is_kingside_castling(move)
            is_queenside_castling = self.board.is_queenside_castling(move)

            self.board.push(move)
            is_check_after_move = self.board.is_check()

            self._color_log(f"♟️ Move made: {move_str} (UCI: {move.uci()}, SAN: {move_san})", Color.cyan)

            current_state = self._get_current_board_state()
            move_result = ChessMoveResult(
                move_uci=move.uci(),
                move_san=move_san,
                is_capture=is_capture,
                is_check=is_check_after_move,  # Check status *after* the move
                is_kingside_castling=is_kingside_castling,
                is_queenside_castling=is_queenside_castling,
                board_after_move=current_state,
            )

            # Format output (can be customized)
            formatted_output = f"Move {move_result.move_san} (UCI: {move_result.move_uci}) played.\n"
            formatted_output += self._format_board_state_output(current_state)

            execution_time = (datetime.now() - start_time).total_seconds()
            metadata = ChessMetadata(
                operation="make_move",
                fen_before=fen_before,
                fen_after=self.board.fen(),
                move_played=move.uci(),
                execution_time=execution_time,
            ).model_dump()

            return ActionResponse(success=True, message=formatted_output, metadata=metadata)

        except ValueError as e:
            error_msg = f"Failed to make move '{move_str}': {str(e)}"
            self.logger.error(f"Move error: {traceback.format_exc()}")
            execution_time = (datetime.now() - start_time).total_seconds()
            metadata = ChessMetadata(
                operation="make_move",
                fen_before=fen_before,
                move_played=move_str,
                error_type="invalid_or_illegal_move",
                execution_time=execution_time,
            ).model_dump()
            return ActionResponse(success=False, message=error_msg, metadata=metadata)

    async def mcp_get_legal_moves(
        self,
        output_format: str = Field(
            default="markdown", description="Output format: 'uci_list', 'san_list', 'markdown', 'json'"
        ),
    ) -> ActionResponse:
        """Gets all legal moves for the current board position.

        Args:
            output_format: 'uci_list' (simple list of UCI moves),
                           'san_list' (simple list of SAN moves),
                           'markdown' (formatted list),
                           'json' (structured list).

        Returns:
            ActionResponse with the list of legal moves.
        """
        # Handle FieldInfo
        if isinstance(output_format, FieldInfo):
            output_format = output_format.default

        start_time = datetime.now()
        legal_moves_uci = [move.uci() for move in self.board.legal_moves]

        message_content: Any
        if output_format == "uci_list":
            message_content = legal_moves_uci
        elif output_format == "san_list":
            try:
                message_content = [self.board.san(move) for move in self.board.legal_moves]
            except Exception as e:
                self.logger.warning(
                    f"Could not generate all SAN moves: {e}. Falling back to UCI for problematic moves."
                )
                san_moves = []
                for move in self.board.legal_moves:
                    try:
                        san_moves.append(self.board.san(move))
                    except Exception:
                        san_moves.append(move.uci() + " (SAN failed)")
                message_content = san_moves
        elif output_format == "json":
            moves_data = []
            for move in self.board.legal_moves:
                try:
                    san = self.board.san(move)
                except Exception:
                    san = move.uci() + " (SAN failed)"
                moves_data.append({"uci": move.uci(), "san": san})
            message_content = json.dumps(moves_data, indent=2)
        else:  # markdown
            if not legal_moves_uci:
                message_content = "No legal moves available (game might be over)."
            else:
                san_formatted_moves = []
                for move_uci in legal_moves_uci[:20]:  # Display sample for markdown
                    try:
                        move_obj = self.board.parse_uci(move_uci)
                        san_formatted_moves.append(f"`{self.board.san(move_obj)}` ({move_uci})")
                    except Exception:
                        san_formatted_moves.append(f"`{move_uci}` (SAN failed)")

                header = f"### Legal Moves ({len(legal_moves_uci)} total)\n"
                moves_list_md = "\n".join([f"- {m}" for m in san_formatted_moves])
                if len(legal_moves_uci) > 20:
                    moves_list_md += "\n- ... (and more)"
                message_content = header + moves_list_md

        execution_time = (datetime.now() - start_time).total_seconds()
        metadata = ChessMetadata(
            operation="get_legal_moves", fen_before=self.board.fen(), execution_time=execution_time
        ).model_dump()

        return ActionResponse(success=True, message=message_content, metadata=metadata)

    async def mcp_get_board_state(
        self, output_format: str = Field(default="markdown", description="Output format: 'markdown', 'json', or 'text'")
    ) -> ActionResponse:
        """Gets the current state of the chess board.

        Includes FEN, turn, game status, ASCII board, and legal moves.

        Args:
            output_format: Desired format for the board state.

        Returns:
            ActionResponse with the current board state.
        """
        # Handle FieldInfo
        if isinstance(output_format, FieldInfo):
            output_format = output_format.default

        start_time = datetime.now()
        current_state = self._get_current_board_state()
        formatted_output = self._format_board_state_output(current_state, output_format)
        execution_time = (datetime.now() - start_time).total_seconds()

        metadata = ChessMetadata(
            operation="get_board_state",
            fen_before=self.board.fen(),  # FEN is part of the state, so 'before' and 'after' are same here
            execution_time=execution_time,
        ).model_dump()

        return ActionResponse(success=True, message=formatted_output, metadata=metadata)

    async def mcp_get_game_status(self) -> ActionResponse:
        """Checks and returns the current game status (e.g., checkmate, stalemate).

        Returns:
            ActionResponse with a human-readable game status and structured data.
        """
        start_time = datetime.now()
        state = self._get_current_board_state()

        status_message = "Game in progress."
        if state.is_checkmate:
            status_message = f"Checkmate! {state.turn.capitalize()} is mated."
        elif state.is_stalemate:
            status_message = "Stalemate! The game is a draw."
        elif state.is_insufficient_material:
            status_message = "Draw by insufficient material."
        elif state.is_seventyfive_moves:
            status_message = "Draw by 75-move rule."
        elif state.is_fivefold_repetition:
            status_message = "Draw by fivefold repetition."
        elif state.is_check:
            status_message = f"{state.turn.capitalize()} is in check."

        status_data = {
            "status_message": status_message,
            "is_game_over": state.is_game_over,
            "is_check": state.is_check,
            "is_checkmate": state.is_checkmate,
            "is_stalemate": state.is_stalemate,
            "is_draw": state.is_stalemate
            or state.is_insufficient_material
            or state.is_seventyfive_moves
            or state.is_fivefold_repetition,
            "winner": None,  # Could be determined if checkmate
        }
        if state.is_checkmate:
            status_data["winner"] = "black" if self.board.turn == chess.WHITE else "white"

        execution_time = (datetime.now() - start_time).total_seconds()
        metadata = ChessMetadata(
            operation="get_game_status", fen_before=self.board.fen(), execution_time=execution_time
        ).model_dump()
        metadata.update(status_data)  # Add specific status flags to metadata

        return ActionResponse(success=True, message=status_message, metadata=metadata)

    def mcp_get_chess_capabilities(self) -> ActionResponse:
        """Get information about the Chess service capabilities.

        Returns:
            ActionResponse with service capabilities.
        """
        capabilities_info = {
            "service_name": "Chess MCP Service",
            "library_used": "python-chess",
            "supported_operations": [
                "new_game: Start a new chess game.",
                "load_fen: Load game state from FEN string.",
                "make_move: Make a move (UCI or SAN).",
                "get_legal_moves: List legal moves.",
                "get_board_state: Get current board FEN, ASCII, status, etc.",
                "get_game_status: Check for checkmate, stalemate, draw conditions.",
            ],
            "output_formats": ["markdown", "json", "text"],
            "move_input_formats": ["UCI (e.g., e2e4)", "SAN (e.g., Nf3)"],
            "fen_support": "Full FEN loading and generation.",
            "engine_integration": "Basic structure for UCI engine integration (not fully implemented by default).",
        }

        formatted_message = "# Chess Service Capabilities\n\n"
        formatted_message += f"**Service Name:** {capabilities_info['service_name']}\n"
        formatted_message += f"**Core Library:** {capabilities_info['library_used']}\n\n"
        formatted_message += "**Supported Operations:**\n"
        for op in capabilities_info["supported_operations"]:
            formatted_message += f"- {op}\n"
        formatted_message += "\n**Supported Output Formats:** " + ", ".join(capabilities_info["output_formats"]) + "\n"
        formatted_message += "**Move Input Formats:** " + ", ".join(capabilities_info["move_input_formats"]) + "\n"

        return ActionResponse(success=True, message=formatted_message, metadata=capabilities_info)

    # Optional: Method to close engine if it was initialized
    # def __del__(self):
    #     if hasattr(self, 'engine') and self.engine:
    #         self.engine.quit()
    #         self._color_log("Chess engine quit.", Color.yellow)


# Default arguments for testing
if __name__ == "__main__":
    import os

    load_dotenv()

    arguments = ActionArguments(
        name="chess_service",
        transport="stdio",
        workspace=os.getenv("AWORLD_WORKSPACE", "~"),
    )

    try:
        service = ChessCollection(arguments)
        service.run()
    except Exception as e:
        print(f"An error occurred: {e}: {traceback.format_exc()}")
