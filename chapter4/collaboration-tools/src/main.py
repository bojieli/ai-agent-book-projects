"""Collaboration Tools MCP Server

This MCP server provides tools for:
- Browser automation (using browser-use)
- Human-in-the-loop assistance requests
- IM and email notifications
- Timer/scheduling capabilities
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import tool modules
from browser_tools import (
    browser_navigate,
    browser_get_content,
    browser_execute_task,
    browser_screenshot,
    browser_list_tabs,
    close_browser,
    init_browser
)
from notification_tools import (
    send_email,
    send_telegram_message,
    send_slack_message,
    send_discord_message
)
from hitl_tools import (
    request_admin_approval,
    request_admin_input,
    respond_to_request,
    list_pending_requests
)
from timer_tools import (
    set_timer,
    set_recurring_timer,
    cancel_timer,
    list_timers,
    get_timer_status,
    _load_timers
)
from chess_tools import (
    new_game,
    load_fen,
    make_move,
    get_legal_moves,
    get_board_state,
    get_game_status,
    undo_move,
    get_move_history,
    reset_board
)
from excel_tools import (
    read_excel_data,
    write_excel_data,
    create_excel_workbook,
    create_excel_worksheet,
    apply_excel_formula,
    get_excel_metadata,
    create_excel_screenshot
)
from intelligence_tools import (
    generate_python_code,
    complex_problem_reasoning,
    guard_reasoning_process
)
from subagent_tools import (
    spawn_subagent,
    send_message_to_subagent,
    cancel_subagent,
    get_subagent_status
)
from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("collaboration-tools")


# ============================================================================
# BROWSER AUTOMATION TOOLS
# ============================================================================

@mcp.tool(description="Navigate to a URL in the virtual browser")
async def mcp_browser_navigate(
    url: str = Field(description="The URL to navigate to"),
    new_tab: bool = Field(default=False, description="Whether to open in a new tab")
) -> str:
    """Navigate to a URL in the browser."""
    result = await browser_navigate(url, new_tab)
    return str(result)


@mcp.tool(description="Get content from the current browser page")
async def mcp_browser_get_content(
    selector: Optional[str] = Field(default=None, description="Optional CSS selector to extract specific content")
) -> str:
    """Get content from the current page."""
    result = await browser_get_content(selector)
    return str(result)


@mcp.tool(description="Execute a high-level browser task using AI agent")
async def mcp_browser_execute_task(
    task: str = Field(description="Natural language description of the task to perform"),
    max_steps: int = Field(default=20, description="Maximum number of steps the agent can take")
) -> str:
    """Execute a browser task using autonomous AI agent."""
    result = await browser_execute_task(task, max_steps)
    return str(result)


@mcp.tool(description="Take a screenshot of the current browser page")
async def mcp_browser_screenshot(
    full_page: bool = Field(default=False, description="Whether to capture the full page or just viewport")
) -> str:
    """Take a screenshot of the current page."""
    result = await browser_screenshot(full_page)
    return str(result)


@mcp.tool(description="List all open browser tabs")
async def mcp_browser_list_tabs() -> str:
    """List all open browser tabs."""
    result = await browser_list_tabs()
    return str(result)


# ============================================================================
# EMAIL NOTIFICATION TOOLS
# ============================================================================

@mcp.tool(description="Send an email notification")
async def mcp_send_email(
    to_email: str = Field(description="Recipient email address"),
    subject: str = Field(description="Email subject"),
    body: str = Field(description="Email body content"),
    html: bool = Field(default=False, description="Whether body is HTML formatted"),
    cc: Optional[List[str]] = Field(default=None, description="Optional list of CC recipients")
) -> str:
    """Send an email notification."""
    result = await send_email(to_email, subject, body, html, cc)
    return str(result)


# ============================================================================
# INSTANT MESSAGING TOOLS
# ============================================================================

@mcp.tool(description="Send a Telegram message")
async def mcp_send_telegram_message(
    message: str = Field(description="Message text to send"),
    chat_id: Optional[str] = Field(default=None, description="Optional Telegram chat ID"),
    parse_mode: str = Field(default="HTML", description="Message parse mode (HTML, Markdown, or None)")
) -> str:
    """Send a Telegram message."""
    result = await send_telegram_message(message, chat_id, parse_mode)
    return str(result)


@mcp.tool(description="Send a Slack message via webhook")
async def mcp_send_slack_message(
    message: str = Field(description="Message text to send"),
    webhook_url: Optional[str] = Field(default=None, description="Optional Slack webhook URL"),
    channel: Optional[str] = Field(default=None, description="Optional channel to post to"),
    username: str = Field(default="Collaboration Agent", description="Bot username to display")
) -> str:
    """Send a Slack message."""
    result = await send_slack_message(message, webhook_url, channel, username)
    return str(result)


@mcp.tool(description="Send a Discord message via webhook")
async def mcp_send_discord_message(
    message: str = Field(description="Message text to send"),
    webhook_url: Optional[str] = Field(default=None, description="Optional Discord webhook URL"),
    username: str = Field(default="Collaboration Agent", description="Bot username to display")
) -> str:
    """Send a Discord message."""
    result = await send_discord_message(message, webhook_url, username)
    return str(result)


# ============================================================================
# HUMAN-IN-THE-LOOP TOOLS
# ============================================================================

@mcp.tool(description="Request approval from a human administrator")
async def mcp_request_admin_approval(
    request_message: str = Field(description="Message describing what needs approval"),
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context information"),
    timeout_seconds: Optional[int] = Field(default=None, description="How long to wait for response"),
    urgent: bool = Field(default=False, description="Whether this is an urgent request")
) -> str:
    """Request approval from human administrator."""
    result = await request_admin_approval(request_message, context, timeout_seconds, urgent)
    return str(result)


@mcp.tool(description="Request input from a human administrator")
async def mcp_request_admin_input(
    prompt: str = Field(description="Question or prompt for the admin"),
    input_type: str = Field(default="text", description="Type of input expected (text, choice, number)"),
    options: Optional[List[str]] = Field(default=None, description="For choice type, list of available options"),
    timeout_seconds: Optional[int] = Field(default=None, description="How long to wait for response")
) -> str:
    """Request input from human administrator."""
    result = await request_admin_input(prompt, input_type, options, timeout_seconds)
    return str(result)


@mcp.tool(description="Respond to an admin approval request (admin use)")
async def mcp_respond_to_request(
    request_id: str = Field(description="ID of the request to respond to"),
    approved: bool = Field(description="Whether the request is approved"),
    admin_notes: Optional[str] = Field(default=None, description="Optional notes from the admin")
) -> str:
    """Admin response to an approval request."""
    result = await respond_to_request(request_id, approved, admin_notes)
    return str(result)


@mcp.tool(description="List all pending admin approval requests")
async def mcp_list_pending_requests() -> str:
    """List all pending approval requests."""
    result = await list_pending_requests()
    return str(result)


# ============================================================================
# TIMER TOOLS
# ============================================================================

@mcp.tool(description="Set a timer that will notify when completed")
async def mcp_set_timer(
    duration_seconds: int = Field(description="How long to wait before timer expires"),
    timer_name: Optional[str] = Field(default=None, description="Optional name for the timer"),
    callback_message: Optional[str] = Field(default=None, description="Message to return when timer expires"),
    callback_data: Optional[Dict[str, Any]] = Field(default=None, description="Optional data to include")
) -> str:
    """Set a timer that will notify when completed."""
    result = await set_timer(duration_seconds, timer_name, callback_message, callback_data)
    return str(result)


@mcp.tool(description="Set a recurring timer that repeats at intervals")
async def mcp_set_recurring_timer(
    interval_seconds: int = Field(description="Time between occurrences"),
    max_occurrences: Optional[int] = Field(default=None, description="Maximum number of times to repeat"),
    timer_name: Optional[str] = Field(default=None, description="Optional name for the timer"),
    callback_message: Optional[str] = Field(default=None, description="Message for each occurrence")
) -> str:
    """Set a recurring timer."""
    result = await set_recurring_timer(interval_seconds, max_occurrences, timer_name, callback_message)
    return str(result)


@mcp.tool(description="Cancel an active timer")
async def mcp_cancel_timer(
    timer_id: str = Field(description="ID of the timer to cancel")
) -> str:
    """Cancel an active timer."""
    result = await cancel_timer(timer_id)
    return str(result)


@mcp.tool(description="List all timers, optionally filtered by status")
async def mcp_list_timers(
    status: Optional[str] = Field(default=None, description="Optional status filter (active, expired, cancelled)")
) -> str:
    """List all timers."""
    result = await list_timers(status)
    return str(result)


@mcp.tool(description="Get status of a specific timer")
async def mcp_get_timer_status(
    timer_id: str = Field(description="ID of the timer to check")
) -> str:
    """Get timer status."""
    result = await get_timer_status(timer_id)
    return str(result)


# ============================================================================
# CHESS GAME TOOLS
# ============================================================================

@mcp.tool(description="Start a new chess game")
async def mcp_chess_new_game() -> str:
    """Start a new chess game with the standard starting position."""
    result = await new_game()
    return str(result)


@mcp.tool(description="Load a chess position from FEN notation")
async def mcp_chess_load_fen(
    fen_string: str = Field(description="FEN string representing the board state")
) -> str:
    """Load a chess position from FEN."""
    result = await load_fen(fen_string)
    return str(result)


@mcp.tool(description="Make a move on the chess board")
async def mcp_chess_make_move(
    move_str: str = Field(description="Move in UCI (e.g., 'e2e4') or SAN (e.g., 'e4') format")
) -> str:
    """Make a chess move."""
    result = await make_move(move_str)
    return str(result)


@mcp.tool(description="Get all legal moves in the current position")
async def mcp_chess_get_legal_moves() -> str:
    """Get all legal moves."""
    result = await get_legal_moves()
    return str(result)


@mcp.tool(description="Get the current chess board state")
async def mcp_chess_get_board_state() -> str:
    """Get current board state."""
    result = await get_board_state()
    return str(result)


@mcp.tool(description="Get the current game status (checkmate, stalemate, etc.)")
async def mcp_chess_get_game_status() -> str:
    """Get game status."""
    result = await get_game_status()
    return str(result)


@mcp.tool(description="Undo the last move")
async def mcp_chess_undo_move() -> str:
    """Undo the last move."""
    result = await undo_move()
    return str(result)


@mcp.tool(description="Get the history of moves played")
async def mcp_chess_get_move_history() -> str:
    """Get move history."""
    result = await get_move_history()
    return str(result)


@mcp.tool(description="Reset the chess board to starting position")
async def mcp_chess_reset_board() -> str:
    """Reset the board."""
    result = await reset_board()
    return str(result)


# ============================================================================
# EXCEL OPERATION TOOLS
# ============================================================================

@mcp.tool(description="Read data from Excel file")
async def mcp_excel_read(
    file_path: str = Field(description="Path to Excel file"),
    sheet_name: str | None = Field(default=None, description="Sheet name (None for all sheets)"),
    max_rows: int = Field(default=1000, description="Maximum rows to read")
) -> str:
    """Read Excel data."""
    result = await read_excel_data(file_path, sheet_name, max_rows)
    return str(result)


@mcp.tool(description="Write data to Excel file")
async def mcp_excel_write(
    file_path: str = Field(description="Path to Excel file"),
    data: Dict[str, List[Dict]] = Field(description="Data to write {sheet_name: [rows]}"),
    overwrite: bool = Field(default=False, description="Overwrite existing file")
) -> str:
    """Write Excel data."""
    result = await write_excel_data(file_path, data, overwrite)
    return str(result)


@mcp.tool(description="Create a new Excel workbook")
async def mcp_excel_create_workbook(
    file_path: str = Field(description="Path for new workbook")
) -> str:
    """Create Excel workbook."""
    result = await create_excel_workbook(file_path)
    return str(result)


@mcp.tool(description="Create a new worksheet in Excel")
async def mcp_excel_create_worksheet(
    file_path: str = Field(description="Path to Excel file"),
    sheet_name: str = Field(description="Name for new worksheet")
) -> str:
    """Create Excel worksheet."""
    result = await create_excel_worksheet(file_path, sheet_name)
    return str(result)


@mcp.tool(description="Apply formula to Excel cell")
async def mcp_excel_apply_formula(
    file_path: str = Field(description="Path to Excel file"),
    sheet_name: str = Field(description="Worksheet name"),
    cell: str = Field(description="Cell reference (e.g., 'A1')"),
    formula: str = Field(description="Excel formula (e.g., '=SUM(A1:A10)')")
) -> str:
    """Apply Excel formula."""
    result = await apply_excel_formula(file_path, sheet_name, cell, formula)
    return str(result)


@mcp.tool(description="Get Excel file metadata")
async def mcp_excel_get_metadata(
    file_path: str = Field(description="Path to Excel file")
) -> str:
    """Get Excel metadata."""
    result = await get_excel_metadata(file_path)
    return str(result)


@mcp.tool(description="Create screenshot of Excel file")
async def mcp_excel_screenshot(
    file_path: str = Field(description="Path to Excel file"),
    sheet_name: str | None = Field(default=None, description="Sheet name"),
    output_dir: str = Field(default=".", description="Output directory")
) -> str:
    """Create Excel screenshot."""
    result = await create_excel_screenshot(file_path, sheet_name, output_dir)
    return str(result)


# ============================================================================
# INTELLIGENCE PROCESSING TOOLS
# ============================================================================

@mcp.tool(description="Generate Python code based on task description")
async def mcp_intelligence_generate_code(
    task_description: str = Field(description="Description of coding task"),
    requirements: str | None = Field(default=None, description="Additional requirements"),
    temperature: float = Field(default=0.7, description="LLM temperature")
) -> str:
    """Generate Python code."""
    result = await generate_python_code(task_description, requirements, temperature)
    return str(result)


@mcp.tool(description="Perform complex problem reasoning with step-by-step thinking")
async def mcp_intelligence_think(
    problem: str = Field(description="Problem statement"),
    context: str | None = Field(default=None, description="Optional context"),
    reasoning_steps: int = Field(default=3, description="Number of reasoning steps")
) -> str:
    """Complex problem reasoning."""
    result = await complex_problem_reasoning(problem, context, reasoning_steps)
    return str(result)


@mcp.tool(description="Guard and validate a proposed action for safety")
async def mcp_intelligence_guard(
    proposed_action: str = Field(description="Proposed action to validate"),
    context: Dict[str, Any] = Field(description="Context for evaluation"),
    safety_rules: List[str] | None = Field(default=None, description="Safety rules to check")
) -> str:
    """Guard reasoning process."""
    result = await guard_reasoning_process(proposed_action, context, safety_rules)
    return str(result)


# ============================================================================
# SUB-AGENT MANAGEMENT TOOLS
# ============================================================================

@mcp.tool(description="Spawn a sub-agent to handle a delegated task. Supports sync (waits and returns result) and async (returns a task_id immediately) modes, and two context-passing strategies: 'minimal' or 'llm_generated'.")
async def mcp_spawn_subagent(
    task: str = Field(description="The sub-task to delegate to the sub-agent"),
    context_strategy: str = Field(default="minimal", description="Context-passing strategy: 'minimal' (task + hand-picked slice only) or 'llm_generated' (extra LLM call synthesizes privacy-filtered context)"),
    mode: str = Field(default="sync", description="'sync' waits and returns the result; 'async' starts in background and returns a task_id"),
    parent_context: Optional[Dict[str, Any]] = Field(default=None, description="Parent agent trajectory/state to prepare per the chosen strategy"),
    role: Optional[str] = Field(default=None, description="Optional explicit role for the sub-agent's system prompt"),
    minimal_slice: Optional[Any] = Field(default=None, description="For 'minimal' strategy: hand-picked slice (string, dict, or list of keys into parent_context)"),
    business_rules: Optional[str] = Field(default=None, description="For 'llm_generated' strategy: privacy/compression rules")
) -> str:
    """Spawn a sub-agent (sync or async) with a chosen context-passing strategy."""
    result = await spawn_subagent(
        task, context_strategy, mode, parent_context, role, minimal_slice, business_rules
    )
    return str(result)


@mcp.tool(description="Send a follow-up message to an existing sub-agent and get its reply")
async def mcp_send_message_to_subagent(
    subagent_id: str = Field(description="ID of the sub-agent to message"),
    message: str = Field(description="Message to send (labeled [FROM_MAIN_AGENT] to the sub-agent)")
) -> str:
    """Send a message to a sub-agent."""
    result = await send_message_to_subagent(subagent_id, message)
    return str(result)


@mcp.tool(description="Cancel a sub-agent (cancels the background task for async sub-agents)")
async def mcp_cancel_subagent(
    subagent_id: str = Field(description="ID of the sub-agent to cancel")
) -> str:
    """Cancel a sub-agent."""
    result = await cancel_subagent(subagent_id)
    return str(result)


@mcp.tool(description="Get the status and result of a sub-agent (useful for async sub-agents)")
async def mcp_get_subagent_status(
    subagent_id: str = Field(description="ID of the sub-agent to inspect")
) -> str:
    """Get sub-agent status."""
    result = await get_subagent_status(subagent_id)
    return str(result)


# ============================================================================
# SERVER LIFECYCLE
# ============================================================================

async def _serve() -> None:
    """Restore saved timers and serve requests on the SAME event loop.

    `asyncio.run(_load_timers())` used to run in a throwaway loop: closing it
    cancelled every `_run_timer` task that had just been restored, and the
    CancelledError handler then marked those timers "cancelled" and re-saved,
    which drops them from storage. Restored timers therefore never fired and
    were lost from memory *and* disk.

    `FastMCP.run(transport="stdio")` is itself just `anyio.run(run_stdio_async)`,
    so awaiting `run_stdio_async()` here is the same server entry point.
    """
    await _load_timers()
    await mcp.run_stdio_async()


# Run the server
if __name__ == "__main__":
    logger.info("Starting Collaboration Tools MCP Server...")
    
    # Load configuration
    config = load_config()
    logger.info(f"Configuration loaded: log_level={config.log_level}")
    
    try:
        # Restore saved timers, then run the MCP server (one shared loop)
        asyncio.run(_serve())
    finally:
        # Cleanup on exit
        logger.info("Shutting down Collaboration Tools MCP Server...")
        asyncio.run(close_browser())
        logger.info("Server shutdown complete")
