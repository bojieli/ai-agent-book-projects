"""Timer and scheduling tools for delayed task execution."""

import asyncio
import json
import uuid
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Active timers storage
_active_timers: Dict[str, Dict[str, Any]] = {}
_timer_tasks: Dict[str, asyncio.Task] = {}


async def set_timer(
    duration_seconds: int,
    timer_name: Optional[str] = None,
    callback_message: Optional[str] = None,
    callback_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Set a timer that will notify when completed.
    
    Args:
        duration_seconds: How long to wait before timer expires
        timer_name: Optional name for the timer
        callback_message: Message to return when timer expires
        callback_data: Optional data to include in callback
        
    Returns:
        Dictionary with timer ID and metadata
    """
    try:
        # Generate timer ID
        timer_id = str(uuid.uuid4())
        
        # Calculate expiry time
        start_time = datetime.now()
        expiry_time = start_time + timedelta(seconds=duration_seconds)
        
        # Create timer record
        timer_data = {
            "timer_id": timer_id,
            "name": timer_name or f"Timer-{timer_id[:8]}",
            "duration_seconds": duration_seconds,
            "start_time": start_time.isoformat(),
            "expiry_time": expiry_time.isoformat(),
            "callback_message": callback_message,
            "callback_data": callback_data or {},
            "status": "active",
            "created_at": start_time.isoformat()
        }
        
        _active_timers[timer_id] = timer_data
        
        # Start the timer task
        task = asyncio.create_task(_run_timer(timer_id, duration_seconds))
        _timer_tasks[timer_id] = task
        
        # Save timers to storage
        await _save_timers()
        
        logger.info(f"Timer {timer_id} set for {duration_seconds} seconds")
        
        return {
            "success": True,
            "timer_id": timer_id,
            "name": timer_data["name"],
            "duration_seconds": duration_seconds,
            "expiry_time": expiry_time.isoformat(),
            "message": f"Timer set for {duration_seconds} seconds"
        }
        
    except Exception as e:
        logger.error(f"Failed to set timer: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to set timer"
        }


async def _run_timer(timer_id: str, duration_seconds: int):
    """Internal function to run a timer."""
    try:
        await asyncio.sleep(duration_seconds)
        
        # Timer expired
        if timer_id in _active_timers:
            timer_data = _active_timers[timer_id]
            timer_data["status"] = "expired"
            timer_data["completed_at"] = datetime.now().isoformat()
            
            logger.info(f"Timer {timer_id} expired: {timer_data.get('name')}")
            
            # Trigger callback notification if configured
            await _trigger_timer_callback(timer_data)
            
            await _save_timers()
            
    except asyncio.CancelledError:
        # Timer was cancelled
        if timer_id in _active_timers:
            _active_timers[timer_id]["status"] = "cancelled"
            await _save_timers()
        logger.info(f"Timer {timer_id} was cancelled")
    except Exception as e:
        logger.error(f"Error in timer {timer_id}: {e}")
        if timer_id in _active_timers:
            _active_timers[timer_id]["status"] = "error"
            _active_timers[timer_id]["error"] = str(e)
            await _save_timers()


async def _trigger_timer_callback(timer_data: Dict[str, Any]):
    """Trigger callback actions when timer expires."""
    try:
        # You could integrate with notification systems here
        callback_message = timer_data.get("callback_message")
        
        if callback_message:
            # Log the callback (in a real system, you might want to
            # send notifications or trigger other actions)
            logger.info(f"Timer callback: {callback_message}")
            
            # Optionally send notification
            try:
                from notification_tools import send_slack_message, send_telegram_message
                
                message = f"⏰ Timer Expired: {timer_data['name']}\n\n{callback_message}"
                
                # Try Slack first
                result = await send_slack_message(message)
                if not result["success"]:
                    # Try Telegram
                    await send_telegram_message(message)
                    
            except Exception as e:
                logger.error(f"Failed to send timer notification: {e}")
                
    except Exception as e:
        logger.error(f"Error in timer callback: {e}")


async def cancel_timer(timer_id: str) -> Dict[str, Any]:
    """Cancel an active timer.
    
    Args:
        timer_id: ID of the timer to cancel
        
    Returns:
        Dictionary with cancellation status
    """
    try:
        if timer_id not in _active_timers:
            return {
                "success": False,
                "error": "Timer not found",
                "message": f"No timer found with ID {timer_id}"
            }
        
        timer = _active_timers[timer_id]
        
        if timer["status"] != "active":
            return {
                "success": False,
                "error": "Timer not active",
                "status": timer["status"],
                "message": f"Timer is already {timer['status']}"
            }
        
        # Cancel the task
        if timer_id in _timer_tasks:
            _timer_tasks[timer_id].cancel()
            del _timer_tasks[timer_id]
        
        timer["status"] = "cancelled"
        timer["cancelled_at"] = datetime.now().isoformat()
        
        await _save_timers()
        
        logger.info(f"Timer {timer_id} cancelled")
        
        return {
            "success": True,
            "timer_id": timer_id,
            "name": timer["name"],
            "message": "Timer cancelled successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel timer: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to cancel timer"
        }


async def list_timers(status: Optional[str] = None) -> Dict[str, Any]:
    """List all timers, optionally filtered by status.
    
    Args:
        status: Optional status filter (active, expired, cancelled)
        
    Returns:
        Dictionary with list of timers
    """
    try:
        timers = list(_active_timers.values())
        
        if status:
            timers = [t for t in timers if t["status"] == status]
        
        # Sort by creation time
        timers.sort(key=lambda t: t["created_at"], reverse=True)
        
        return {
            "success": True,
            "count": len(timers),
            "timers": timers,
            "message": f"Found {len(timers)} timers"
        }
        
    except Exception as e:
        logger.error(f"Failed to list timers: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list timers"
        }


async def get_timer_status(timer_id: str) -> Dict[str, Any]:
    """Get status of a specific timer.
    
    Args:
        timer_id: ID of the timer to check
        
    Returns:
        Dictionary with timer status
    """
    try:
        if timer_id not in _active_timers:
            return {
                "success": False,
                "error": "Timer not found",
                "message": f"No timer found with ID {timer_id}"
            }
        
        timer = _active_timers[timer_id]
        
        # Recurring timers have an interval rather than a fixed expiry time.
        if timer["status"] == "active" and timer.get("type") != "recurring":
            expiry = datetime.fromisoformat(timer["expiry_time"])
            remaining = (expiry - datetime.now()).total_seconds()
            timer["remaining_seconds"] = max(0, int(remaining))
        
        return {
            "success": True,
            "timer": timer,
            "message": "Timer found"
        }
        
    except Exception as e:
        logger.error(f"Failed to get timer status: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get timer status"
        }


async def set_recurring_timer(
    interval_seconds: int,
    max_occurrences: Optional[int] = None,
    timer_name: Optional[str] = None,
    callback_message: Optional[str] = None
) -> Dict[str, Any]:
    """Set a recurring timer that repeats at intervals.
    
    Args:
        interval_seconds: Time between occurrences
        max_occurrences: Maximum number of times to repeat (None = infinite)
        timer_name: Optional name for the timer
        callback_message: Message for each occurrence
        
    Returns:
        Dictionary with recurring timer ID
    """
    try:
        if interval_seconds is None or interval_seconds <= 0:
            return {
                "success": False,
                "error": "interval_seconds must be positive",
                "message": "Failed to set recurring timer"
            }

        timer_id = str(uuid.uuid4())
        
        timer_data = {
            "timer_id": timer_id,
            "name": timer_name or f"Recurring-{timer_id[:8]}",
            "type": "recurring",
            "interval_seconds": interval_seconds,
            "max_occurrences": max_occurrences,
            "occurrences": 0,
            "callback_message": callback_message,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        _active_timers[timer_id] = timer_data
        
        # Start recurring task
        task = asyncio.create_task(
            _run_recurring_timer(timer_id, interval_seconds, max_occurrences)
        )
        _timer_tasks[timer_id] = task
        
        await _save_timers()
        
        return {
            "success": True,
            "timer_id": timer_id,
            "name": timer_data["name"],
            "interval_seconds": interval_seconds,
            "max_occurrences": max_occurrences,
            "message": f"Recurring timer set with {interval_seconds}s interval"
        }
        
    except Exception as e:
        logger.error(f"Failed to set recurring timer: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to set recurring timer"
        }


async def _run_recurring_timer(
    timer_id: str,
    interval_seconds: int,
    max_occurrences: Optional[int]
):
    """Internal function to run a recurring timer."""
    try:
        timer_data = _active_timers.get(timer_id)
        if timer_data is None:
            return

        occurrence = timer_data.get("occurrences", 0)

        # max_occurrences=0 means "never fire" (None means infinite).
        if max_occurrences is not None and occurrence >= max_occurrences:
            timer_data["status"] = "completed"
            await _save_timers()
            return
        
        while True:
            await asyncio.sleep(interval_seconds)

            timer_data = _active_timers.get(timer_id)
            if timer_data is None:
                return

            occurrence += 1
            timer_data["occurrences"] = occurrence
            timer_data["last_occurrence"] = datetime.now().isoformat()

            logger.info(f"Recurring timer {timer_id} occurrence {occurrence}")

            await _trigger_timer_callback(timer_data)

            # Persist the terminal state, not an active record at the limit.
            # Use `is not None`: max_occurrences=0 means "never fire", not infinite.
            if max_occurrences is not None and occurrence >= max_occurrences:
                timer_data["status"] = "completed"
                logger.info(f"Recurring timer {timer_id} completed after {occurrence} occurrences")

            await _save_timers()

            if timer_data["status"] == "completed":
                break
                    
    except asyncio.CancelledError:
        if timer_id in _active_timers:
            _active_timers[timer_id]["status"] = "cancelled"
            await _save_timers()
        logger.info(f"Recurring timer {timer_id} was cancelled")
    except Exception as e:
        logger.error(f"Error in recurring timer {timer_id}: {e}")


async def _save_timers():
    """Save timer state to storage."""
    try:
        from config import config
        storage_path = Path(config.timer.storage_path).expanduser()
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Only save timers with relevant status
        timers_to_save = {
            tid: timer for tid, timer in _active_timers.items()
            if timer["status"] in ["active", "expired", "completed"]
        }
        
        with open(storage_path, 'w') as f:
            json.dump(timers_to_save, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to save timers: {e}")


async def _load_timers():
    """Load timer state from storage."""
    try:
        from config import config
        storage_path = Path(config.timer.storage_path).expanduser()
        
        if not storage_path.exists():
            return
        
        with open(storage_path, 'r') as f:
            saved_timers = json.load(f)
        
        # Restore active timers
        state_changed = False
        for timer_id, timer_data in saved_timers.items():
            if timer_data["status"] == "active":
                if timer_data.get("type") == "recurring":
                    _active_timers[timer_id] = timer_data

                    max_occurrences = timer_data.get("max_occurrences")
                    occurrences = timer_data.get("occurrences", 0)
                    if max_occurrences is not None and occurrences >= max_occurrences:
                        # Older versions persisted the final occurrence before
                        # changing the in-memory status to completed.
                        timer_data["status"] = "completed"
                        state_changed = True
                        continue

                    task = asyncio.create_task(
                        _run_recurring_timer(
                            timer_id,
                            timer_data["interval_seconds"],
                            max_occurrences
                        )
                    )
                    _timer_tasks[timer_id] = task
                    logger.info(
                        f"Restored recurring timer {timer_id} after "
                        f"{occurrences} occurrences"
                    )
                    continue

                # Calculate remaining time
                expiry = datetime.fromisoformat(timer_data["expiry_time"])
                remaining = (expiry - datetime.now()).total_seconds()
                
                if remaining > 0:
                    # Timer still active, restart it
                    _active_timers[timer_id] = timer_data
                    task = asyncio.create_task(_run_timer(timer_id, int(remaining)))
                    _timer_tasks[timer_id] = task
                    logger.info(f"Restored timer {timer_id} with {remaining}s remaining")
                else:
                    # Timer already expired
                    timer_data["status"] = "expired"
                    _active_timers[timer_id] = timer_data
            else:
                _active_timers[timer_id] = timer_data

        if state_changed:
            await _save_timers()

    except Exception as e:
        logger.error(f"Failed to load timers: {e}")
