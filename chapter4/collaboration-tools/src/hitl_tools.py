"""Human-in-the-loop (HITL) tools for requesting admin assistance."""

import asyncio
import json
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Store pending requests
_pending_requests: Dict[str, Dict[str, Any]] = {}


async def request_admin_approval(
    request_message: str,
    context: Optional[Dict[str, Any]] = None,
    timeout_seconds: Optional[int] = None,
    urgent: bool = False
) -> Dict[str, Any]:
    """Request approval from a human administrator.
    
    Args:
        request_message: Message describing what needs approval
        context: Optional context information about the request
        timeout_seconds: How long to wait for response (None = wait indefinitely)
        urgent: Whether this is an urgent request
        
    Returns:
        Dictionary with approval status and admin response
    """
    try:
        from config import config
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Create request record
        request_data = {
            "request_id": request_id,
            "message": request_message,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "urgent": urgent,
            "status": "pending",
            "response": None,
            "admin_notes": None
        }
        
        _pending_requests[request_id] = request_data
        
        # Notify admin via configured channels
        notification_sent = await _notify_admin_of_request(request_data)
        
        if not notification_sent:
            logger.warning("Failed to send admin notification")
        
        # Wait for response
        timeout = timeout_seconds or config.hitl.timeout_seconds
        response = await _wait_for_admin_response(request_id, timeout)
        
        return response
        
    except Exception as e:
        logger.error(f"Admin approval request failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "approved": False,
            "message": "Failed to request admin approval"
        }


async def _notify_admin_of_request(request_data: Dict[str, Any]) -> bool:
    """Notify admin about pending approval request."""
    try:
        from config import config
        from notification_tools import send_email, send_telegram_message, send_slack_message
        
        request_id = request_data["request_id"]
        message = request_data["message"]
        urgent_flag = "🚨 URGENT" if request_data["urgent"] else "ℹ️"
        
        # Construct notification message
        notification = f"""
{urgent_flag} Admin Approval Required

Request ID: {request_id}
Message: {message}
Time: {request_data["timestamp"]}

Context:
{json.dumps(request_data["context"], indent=2)}

To respond, call the approval endpoint or use the admin interface:
- Approve: /approve/{request_id}
- Reject: /reject/{request_id}
"""
        
        notifications_sent = False
        
        # Send email notification
        if config.hitl.admin_email:
            result = await send_email(
                to_email=config.hitl.admin_email,
                subject=f"{urgent_flag} Admin Approval Required - {request_id[:8]}",
                body=notification
            )
            if result["success"]:
                notifications_sent = True
        
        # Send Telegram notification
        if config.im.telegram_bot_token:
            result = await send_telegram_message(
                message=notification,
                parse_mode=None
            )
            if result["success"]:
                notifications_sent = True
        
        # Send Slack notification
        if config.im.slack_webhook_url:
            result = await send_slack_message(message=notification)
            if result["success"]:
                notifications_sent = True
        
        # Call webhook if configured
        if config.hitl.webhook_url:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        config.hitl.webhook_url,
                        json=request_data,
                        timeout=10.0
                    )
                    if response.status_code < 400:
                        notifications_sent = True
            except Exception as e:
                logger.error(f"Failed to call HITL webhook: {e}")
        
        return notifications_sent
        
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")
        return False


async def _wait_for_admin_response(request_id: str, timeout_seconds: int) -> Dict[str, Any]:
    """Wait for admin to respond to approval request."""
    try:
        start_time = datetime.now()
        timeout = timedelta(seconds=timeout_seconds)
        
        while datetime.now() - start_time < timeout:
            request = _pending_requests.get(request_id)
            
            if not request:
                return {
                    "success": False,
                    "approved": False,
                    "error": "Request not found",
                    "message": "Request was cancelled or not found"
                }
            
            if request["status"] == "approved":
                return {
                    "success": True,
                    "approved": True,
                    "request_id": request_id,
                    "admin_notes": request.get("admin_notes"),
                    "message": "Request approved by administrator"
                }
            
            elif request["status"] == "rejected":
                return {
                    "success": True,
                    "approved": False,
                    "request_id": request_id,
                    "admin_notes": request.get("admin_notes"),
                    "reason": request.get("rejection_reason", "No reason provided"),
                    "message": "Request rejected by administrator"
                }
            
            # Wait a bit before checking again
            await asyncio.sleep(2)
        
        # Timeout reached
        _pending_requests[request_id]["status"] = "timeout"
        
        return {
            "success": True,
            "approved": False,
            "request_id": request_id,
            "timeout": True,
            "message": f"Admin response timeout after {timeout_seconds} seconds"
        }
        
    except Exception as e:
        logger.error(f"Error waiting for admin response: {e}")
        return {
            "success": False,
            "approved": False,
            "error": str(e),
            "message": "Error while waiting for admin response"
        }


async def respond_to_request(
    request_id: str,
    approved: bool,
    admin_notes: Optional[str] = None
) -> Dict[str, Any]:
    """Admin response to an approval request.
    
    Args:
        request_id: ID of the request to respond to
        approved: Whether the request is approved
        admin_notes: Optional notes from the admin
        
    Returns:
        Dictionary with response status
    """
    try:
        if request_id not in _pending_requests:
            return {
                "success": False,
                "error": "Request not found",
                "message": f"No pending request found with ID {request_id}"
            }
        
        request = _pending_requests[request_id]
        if request.get("status") != "pending":
            current_status = request.get("status", "unknown")
            return {
                "success": False,
                "approved": False,
                "request_id": request_id,
                "current_status": current_status,
                "error": "Request is no longer pending",
                "message": (
                    f"Request {request_id} is already {current_status}; "
                    "late or duplicate responses cannot change a terminal decision"
                ),
            }
        request["status"] = "approved" if approved else "rejected"
        request["admin_notes"] = admin_notes
        request["response_time"] = datetime.now().isoformat()
        
        if not approved:
            request["rejection_reason"] = admin_notes or "No reason provided"
        
        logger.info(f"Request {request_id} {'approved' if approved else 'rejected'} by admin")
        
        return {
            "success": True,
            "request_id": request_id,
            "approved": approved,
            "message": f"Request {'approved' if approved else 'rejected'} successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to respond to request: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to process admin response"
        }


async def list_pending_requests() -> Dict[str, Any]:
    """List all pending approval requests.
    
    Returns:
        Dictionary with list of pending requests
    """
    try:
        pending = [
            req for req in _pending_requests.values()
            if req["status"] == "pending"
        ]
        
        return {
            "success": True,
            "count": len(pending),
            "requests": pending,
            "message": f"Found {len(pending)} pending requests"
        }
        
    except Exception as e:
        logger.error(f"Failed to list pending requests: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list pending requests"
        }


async def request_admin_input(
    prompt: str,
    input_type: str = "text",
    options: Optional[List[str]] = None,
    timeout_seconds: Optional[int] = None
) -> Dict[str, Any]:
    """Request input from a human administrator.
    
    Args:
        prompt: Question or prompt for the admin
        input_type: Type of input expected (text, choice, number)
        options: For choice type, list of available options
        timeout_seconds: How long to wait for response
        
    Returns:
        Dictionary with admin's input
    """
    context = {
        "type": "input_request",
        "input_type": input_type,
        "options": options
    }
    
    result = await request_admin_approval(
        request_message=prompt,
        context=context,
        timeout_seconds=timeout_seconds,
        urgent=False
    )
    
    # Transform approval result to input result
    if result.get("approved"):
        return {
            "success": True,
            "input": result.get("admin_notes", ""),
            "message": "Admin input received"
        }
    else:
        return {
            "success": False,
            "error": result.get("message", "No input received"),
            "message": "Admin did not provide input"
        }
