"""Notification Dispatcher module for multi-channel notifications and Human-in-the-Loop decision timeout policy management."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union
import uuid

logger = logging.getLogger(__name__)


class FallbackAction(str, Enum):
    """Fallback action policies for HITL decision timeout."""

    AUTO_APPROVE = "auto-approve"
    AUTO_REJECT = "auto-reject"
    ESCALATE = "escalate"


@dataclass
class DecisionRequest:
    """Request object for Human-in-the-Loop approval/decision."""

    message: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    channels: Optional[List[str]] = None
    fallback_action: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    urgent: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionRequest":
        return cls(
            request_id=data.get("request_id") or str(uuid.uuid4()),
            message=data.get("message", data.get("title", "")),
            channels=data.get("channels"),
            fallback_action=data.get("fallback_action"),
            context=data.get("context", {}),
            urgent=data.get("urgent", False),
        )


class DecisionTrace(dict):
    """Structured decision trace object with dict and attribute access."""

    def __init__(
        self,
        request_id: str,
        message: str,
        status: str,
        approved: bool,
        decision: str,
        fallback_action: str,
        fallback_triggered: bool,
        channels_dispatched: List[Dict[str, Any]],
        dispatched_at: str,
        resolved_at: str,
        duration_seconds: float,
        notes: Optional[str] = None,
        trace: Optional[List[Dict[str, Any]]] = None,
    ):
        trace_list = trace or []
        super().__init__(
            request_id=request_id,
            message=message,
            status=status,
            approved=approved,
            decision=decision,
            fallback_action=fallback_action,
            fallback_triggered=fallback_triggered,
            channels_dispatched=channels_dispatched,
            dispatched_at=dispatched_at,
            resolved_at=resolved_at,
            duration_seconds=duration_seconds,
            notes=notes,
            trace=trace_list,
        )
        self.request_id = request_id
        self.message = message
        self.status = status
        self.approved = approved
        self.decision = decision
        self.fallback_action = fallback_action
        self.fallback_triggered = fallback_triggered
        self.channels_dispatched = channels_dispatched
        self.dispatched_at = dispatched_at
        self.resolved_at = resolved_at
        self.duration_seconds = duration_seconds
        self.notes = notes
        self.trace = trace_list

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'DecisionTrace' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class NotificationDispatcher:
    """Unified multi-channel dispatcher and HITL timeout policy engine."""

    def __init__(
        self,
        fallback_action: str = "auto-reject",
        default_channels: Optional[List[str]] = None,
    ):
        self.fallback_action = self._normalize_fallback(fallback_action)
        self.default_channels = default_channels or ["telegram", "slack", "webhook", "email"]
        self._custom_handlers: Dict[str, Callable] = {}
        self._pending_requests: Dict[str, Dict[str, Any]] = {}
        self._decision_events: Dict[str, asyncio.Event] = {}

    def register_channel_handler(self, channel_name: str, handler: Callable) -> None:
        """Register a custom handler function for a specific channel."""
        self._custom_handlers[channel_name.lower()] = handler

    def _normalize_fallback(self, action: str) -> str:
        act = str(action).lower().replace("_", "-")
        if act in ("auto-approve", "approve"):
            return FallbackAction.AUTO_APPROVE.value
        elif act in ("auto-reject", "reject"):
            return FallbackAction.AUTO_REJECT.value
        elif act in ("escalate", "escalation"):
            return FallbackAction.ESCALATE.value
        return FallbackAction.AUTO_REJECT.value

    async def mock_telegram_send(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Telegram channel dispatcher."""
        return {
            "channel": "telegram",
            "success": True,
            "message_id": f"tg_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def mock_slack_send(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Slack channel dispatcher."""
        return {
            "channel": "slack",
            "success": True,
            "ts": f"{datetime.now().timestamp():.6f}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def mock_webhook_send(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Webhook channel dispatcher."""
        return {
            "channel": "webhook",
            "success": True,
            "status_code": 200,
            "response": {"received": True},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def mock_email_send(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Email channel dispatcher."""
        return {
            "channel": "email",
            "success": True,
            "delivery_id": f"email_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def dispatch_notification(
        self, channel: str, message: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Dispatch notification to a single channel."""
        ch = channel.lower().strip()
        ctx = context or {}

        if ch in self._custom_handlers:
            try:
                res = self._custom_handlers[ch](message, ctx)
                if asyncio.iscoroutine(res):
                    res = await res
                success = res.get("success", True) if isinstance(res, dict) else True
                return {"channel": ch, "success": success, "result": res}
            except Exception as e:
                logger.error(f"Error in custom channel handler '{ch}': {e}")
                return {"channel": ch, "success": False, "error": str(e)}

        if ch == "telegram":
            return await self.mock_telegram_send(message, ctx)
        elif ch == "slack":
            return await self.mock_slack_send(message, ctx)
        elif ch == "webhook":
            return await self.mock_webhook_send(message, ctx)
        elif ch == "email":
            return await self.mock_email_send(message, ctx)
        else:
            return {
                "channel": ch,
                "success": False,
                "error": f"Unsupported notification channel '{channel}'",
            }

    async def dispatch_all(
        self, channels: List[str], message: str, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Dispatch notification across multiple channels."""
        tasks = [
            self.dispatch_notification(channel, message, context)
            for channel in channels
        ]
        return await asyncio.gather(*tasks)

    def submit_decision(
        self,
        request_id: str,
        approved: bool,
        notes: Optional[str] = None,
        decision: Optional[str] = None,
    ) -> bool:
        """Submit human decision for a pending request."""
        if request_id not in self._pending_requests:
            return False

        req = self._pending_requests[request_id]
        if req["status"] != "pending":
            return False

        dec_str = decision or ("approved" if approved else "rejected")
        req["status"] = dec_str
        req["approved"] = approved
        req["decision"] = dec_str
        req["notes"] = notes
        req["resolved_at"] = datetime.now(timezone.utc).isoformat()

        if request_id in self._decision_events:
            self._decision_events[request_id].set()

        return True

    def get_pending_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve details of a pending request."""
        return self._pending_requests.get(request_id)

    async def dispatch_and_wait(
        self,
        request: Union[Dict[str, Any], DecisionRequest, str],
        timeout: Optional[float] = None,
    ) -> DecisionTrace:
        """Dispatch notification and wait for HITL decision or timeout fallback execution."""
        start_time = datetime.now(timezone.utc)
        dispatched_at = start_time.isoformat()

        if isinstance(request, DecisionRequest):
            req_obj = request
        elif isinstance(request, dict):
            req_obj = DecisionRequest.from_dict(request)
        else:
            req_obj = DecisionRequest(message=str(request))

        request_id = req_obj.request_id
        channels = req_obj.channels or self.default_channels
        fallback = self._normalize_fallback(
            req_obj.fallback_action or self.fallback_action
        )
        wait_timeout = timeout if timeout is not None else 10.0

        trace_events: List[Dict[str, Any]] = []

        # Store pending state before dispatching to handle instant decisions cleanly
        event = asyncio.Event()
        self._decision_events[request_id] = event
        self._pending_requests[request_id] = {
            "request_id": request_id,
            "message": req_obj.message,
            "channels": channels,
            "fallback_action": fallback,
            "status": "pending",
            "approved": None,
            "decision": None,
            "notes": None,
            "dispatched_at": dispatched_at,
        }

        try:
            # Dispatch across multi-channels
            channel_results = await self.dispatch_all(channels, req_obj.message, req_obj.context)
            trace_events.append(
                {
                    "event": "dispatched",
                    "channels": channels,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            trace_events.append(
                {
                    "event": "waiting_decision",
                    "timeout": wait_timeout,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            try:
                if wait_timeout > 0:
                    await asyncio.wait_for(event.wait(), timeout=wait_timeout)
            except asyncio.TimeoutError:
                pass

            req_record = self._pending_requests.get(request_id, {})
            end_time = datetime.now(timezone.utc)
            resolved_at = end_time.isoformat()
            duration = round((end_time - start_time).total_seconds(), 4)

            if req_record.get("status") not in (None, "pending") and req_record.get("approved") is not None:
                # Decision submitted before timeout
                approved = req_record["approved"]
                decision = req_record["decision"]
                status = decision
                notes = req_record.get("notes")
                fallback_triggered = False
                trace_events.append(
                    {
                        "event": "human_decision_received",
                        "decision": decision,
                        "approved": approved,
                        "timestamp": resolved_at,
                    }
                )
            else:
                # Timeout elapses - apply fallback action policy engine
                fallback_triggered = True
                if fallback == FallbackAction.AUTO_APPROVE.value:
                    approved = True
                    decision = "auto-approved"
                    status = "auto-approved"
                    notes = f"Timeout reached ({wait_timeout}s): policy engine auto-approved request."
                elif fallback == FallbackAction.AUTO_REJECT.value:
                    approved = False
                    decision = "auto-rejected"
                    status = "auto-rejected"
                    notes = f"Timeout reached ({wait_timeout}s): policy engine auto-rejected request."
                else:  # ESCALATE
                    approved = False
                    decision = "escalated"
                    status = "escalated"
                    notes = f"Timeout reached ({wait_timeout}s): policy engine escalated request."

                # Update pending record immediately to prevent decision race conditions during escalation
                if req_record:
                    req_record["status"] = status
                    req_record["approved"] = approved
                    req_record["decision"] = decision
                    req_record["notes"] = notes
                    req_record["resolved_at"] = resolved_at

                if fallback == FallbackAction.ESCALATE.value:
                    # Trigger escalation notification
                    escalation_msg = (
                        f"🚨 ESCALATION ALERT: HITL decision request {request_id} "
                        f"timed out after {wait_timeout}s without operator input."
                    )
                    await self.dispatch_all(channels, escalation_msg, req_obj.context)

                trace_events.append(
                    {
                        "event": "fallback_policy_triggered",
                        "fallback_action": fallback,
                        "decision": decision,
                        "timestamp": resolved_at,
                    }
                )

            return DecisionTrace(
                request_id=request_id,
                message=req_obj.message,
                status=status,
                approved=approved,
                decision=decision,
                fallback_action=fallback,
                fallback_triggered=fallback_triggered,
                channels_dispatched=channel_results,
                dispatched_at=dispatched_at,
                resolved_at=resolved_at,
                duration_seconds=duration,
                notes=notes,
                trace=trace_events,
            )
        finally:
            # Cleanup internal tracking
            self._pending_requests.pop(request_id, None)
            self._decision_events.pop(request_id, None)

    def dispatch_and_wait_sync(
        self,
        request: Union[Dict[str, Any], DecisionRequest, str],
        timeout: Optional[float] = None,
    ) -> DecisionTrace:
        """Synchronous wrapper for dispatch_and_wait."""
        return asyncio.run(self.dispatch_and_wait(request, timeout))


async def dispatch_and_wait(
    request: Union[Dict[str, Any], DecisionRequest, str],
    timeout: Optional[float] = None,
) -> DecisionTrace:
    """Standalone module-level function for dispatching and waiting."""
    dispatcher = NotificationDispatcher()
    return await dispatcher.dispatch_and_wait(request, timeout)
