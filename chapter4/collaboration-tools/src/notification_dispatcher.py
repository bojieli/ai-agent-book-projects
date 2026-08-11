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
    """Unified multi-channel dispatcher and HITL timeout policy engine.

    By default, built-in channels (telegram, slack, email, webhook) are wired
    to the real adapters in ``notification_tools``. An unconfigured production
    channel fails explicitly — the adapter returns ``success: False`` with an
    error message — so a HITL request is never marked dispatched when nothing
    left the process. Set ``use_mock_channels=True`` to route built-in channels
    through the in-process mock senders instead; this is intended for tests.
    """

    def __init__(
        self,
        fallback_action: str = "auto-reject",
        default_channels: Optional[List[str]] = None,
        use_mock_channels: bool = False,
        channel_config: Optional[Dict[str, Any]] = None,
    ):
        self.fallback_action = self._normalize_fallback(fallback_action)
        self.default_channels = default_channels or ["telegram", "slack", "webhook", "email"]
        self.use_mock_channels = use_mock_channels
        self.channel_config: Dict[str, Any] = channel_config or {}
        self._custom_handlers: Dict[str, Callable] = {}
        self._pending_requests: Dict[str, Dict[str, Any]] = {}
        self._decision_events: Dict[str, asyncio.Event] = {}
        self._waiter_counts: Dict[str, int] = {}
        self._real_adapters = self._load_real_adapters()

    def _load_real_adapters(self) -> Dict[str, Callable]:
        """Loads real channel adapter functions from notification_tools.

        Returns a dict mapping channel name to the async send callable. If
        notification_tools cannot be imported (e.g. missing dependencies), an
        empty dict is returned and built-in channels will fail explicitly.
        """
        adapters: Dict[str, Callable] = {}
        try:
            from notification_tools import (
                send_telegram_message,
                send_slack_message,
                send_email,
            )
            adapters["telegram"] = send_telegram_message
            adapters["slack"] = send_slack_message
            adapters["email"] = send_email
        except ImportError:
            logger.debug(
                "notification_tools not available; built-in channels will fail "
                "explicitly unless mock channels are enabled"
            )
        return adapters

    def register_channel_handler(self, channel_name: str, handler: Callable) -> None:
        """Register a custom handler function for a specific channel."""
        self._custom_handlers[channel_name.lower()] = handler

    def _normalize_fallback(self, action: Union[str, Enum]) -> str:
        raw = action.value if isinstance(action, Enum) else str(action)
        if "." in raw:
            raw = raw.split(".")[-1]
        act = raw.lower().replace("_", "-")
        if act in ("auto-approve", "approve", "autoapprove"):
            return FallbackAction.AUTO_APPROVE.value
        elif act in ("auto-reject", "reject", "autoreject"):
            return FallbackAction.AUTO_REJECT.value
        elif act in ("escalate", "escalation"):
            return FallbackAction.ESCALATE.value
        return FallbackAction.AUTO_REJECT.value

    async def mock_telegram_send(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Telegram channel dispatcher (opt-in via use_mock_channels)."""
        return {
            "channel": "telegram",
            "success": True,
            "message_id": f"tg_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def mock_slack_send(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Slack channel dispatcher (opt-in via use_mock_channels)."""
        return {
            "channel": "slack",
            "success": True,
            "ts": f"{datetime.now().timestamp():.6f}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def mock_webhook_send(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Webhook channel dispatcher (opt-in via use_mock_channels)."""
        return {
            "channel": "webhook",
            "success": True,
            "status_code": 200,
            "response": {"received": True},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def mock_email_send(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Email channel dispatcher (opt-in via use_mock_channels)."""
        return {
            "channel": "email",
            "success": True,
            "delivery_id": f"email_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _send_via_real_adapter(
        self, channel: str, message: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatches through a real adapter from notification_tools.

        Adapters that are not configured return ``success: False`` with an
        explicit error, so the dispatcher never silently claims delivery.
        """
        adapter = self._real_adapters.get(channel)
        cfg = self.channel_config.get(channel, {})
        ts = datetime.now(timezone.utc).isoformat()

        if adapter is None:
            return {
                "channel": channel,
                "success": False,
                "error": f"No real adapter available for channel '{channel}'; "
                         f"configure the adapter or enable mock channels",
                "timestamp": ts,
            }

        try:
            if channel == "telegram":
                result = await adapter(
                    message,
                    chat_id=cfg.get("chat_id"),
                    parse_mode=cfg.get("parse_mode", "HTML"),
                )
            elif channel == "slack":
                result = await adapter(
                    message,
                    webhook_url=cfg.get("webhook_url"),
                    channel=cfg.get("channel"),
                    username=cfg.get("username", "Collaboration Agent"),
                )
            elif channel == "email":
                result = await adapter(
                    cfg.get("to_email", ""),
                    cfg.get("subject", "HITL Decision Request"),
                    message,
                    html=cfg.get("html", False),
                )
            else:
                result = await adapter(message, **cfg)
        except Exception as e:
            logger.error(f"Real adapter for channel '{channel}' raised: {e}")
            return {
                "channel": channel,
                "success": False,
                "error": str(e),
                "timestamp": ts,
            }

        success = bool(result.get("success", False)) if isinstance(result, dict) else False
        return {
            "channel": channel,
            "success": success,
            "result": result,
            "error": result.get("error") if isinstance(result, dict) and not success else None,
            "timestamp": ts,
        }

    async def _send_webhook(
        self, message: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatches a webhook notification via HTTP POST.

        Requires a ``webhook_url`` in channel_config; fails explicitly if not
        configured.
        """
        cfg = self.channel_config.get("webhook", {})
        url = cfg.get("webhook_url")
        ts = datetime.now(timezone.utc).isoformat()
        if not url:
            return {
                "channel": "webhook",
                "success": False,
                "error": "Webhook URL not configured; set channel_config['webhook']['webhook_url']",
                "timestamp": ts,
            }
        try:
            import httpx
            template = cfg.get("payload_template")
            if isinstance(template, dict):
                payload = {**template, "text": message}
            else:
                payload = {"text": message}
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, json=payload, headers=cfg.get("headers", {})
                )
                response.raise_for_status()
            return {
                "channel": "webhook",
                "success": True,
                "status_code": response.status_code,
                "timestamp": ts,
            }
        except Exception as e:
            logger.error(f"Webhook dispatch failed: {e}")
            return {
                "channel": "webhook",
                "success": False,
                "error": str(e),
                "timestamp": ts,
            }

    async def dispatch_notification(
        self, channel: str, message: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Dispatch notification to a single channel."""
        ch = str(channel).lower().strip()
        ctx = context or {}

        if ch in self._custom_handlers:
            try:
                res = self._custom_handlers[ch](message, ctx)
                if asyncio.iscoroutine(res):
                    res = await res
                if isinstance(res, bool):
                    success = res
                elif isinstance(res, dict):
                    success = bool(res.get("success", True))
                else:
                    success = True
                return {"channel": ch, "success": success, "result": res, "timestamp": datetime.now(timezone.utc).isoformat()}
            except Exception as e:
                logger.error(f"Error in custom channel handler '{ch}': {e}")
                return {"channel": ch, "success": False, "error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}

        if self.use_mock_channels:
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
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        # Production path: route built-in channels to real adapters
        if ch == "webhook":
            return await self._send_webhook(message, ctx)
        elif ch in ("telegram", "slack", "email"):
            return await self._send_via_real_adapter(ch, message, ctx)
        else:
            return {
                "channel": ch,
                "success": False,
                "error": f"Unsupported notification channel '{channel}'",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def dispatch_all(
        self, channels: List[str], message: str, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Dispatch notification across multiple channels."""
        tasks = [
            self.dispatch_notification(channel, message, context)
            for channel in channels
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def submit_decision(
        self,
        request_id: str,
        approved: Any,
        notes: Optional[str] = None,
        decision: Optional[str] = None,
    ) -> bool:
        """Submit human decision for a pending request."""
        if request_id not in self._pending_requests:
            return False

        req = self._pending_requests[request_id]
        if req["status"] != "pending":
            logger.warning(
                f"Decision for request '{request_id}' submitted after status "
                f"changed to '{req['status']}'; late decision rejected."
            )
            return False

        if not isinstance(approved, bool):
            if decision is None:
                decision = str(approved)
            approved_str = str(approved).lower().strip()
            rejection_words = {
                "reject", "rejected", "deny", "denied",
                "no", "false", "decline", "declined",
            }
            if approved_str in rejection_words:
                approved_bool = False
            else:
                approved_bool = bool(approved)
        else:
            approved_bool = approved

        dec_str = decision or ("approved" if approved_bool else "rejected")
        if dec_str == "pending":
            logger.warning(
                f"Decision string 'pending' is reserved for in-flight requests; "
                f"rejecting decision for request '{request_id}'."
            )
            return False
        req["status"] = dec_str
        req["approved"] = approved_bool
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
        try:
            existing = self._pending_requests.get(request_id)
            if existing and existing.get("status") not in (None, "pending"):
                # A human decision already exists for this request_id; preserve it
                # instead of discarding it by overwriting with a fresh pending record.
                logger.warning(
                    f"Duplicate request_id '{request_id}' submitted while decision "
                    f"'{existing.get('status')}' exists; preserving existing decision."
                )
                existing["message"] = req_obj.message
                existing["channels"] = channels
                existing["fallback_action"] = fallback
                existing["dispatched_at"] = dispatched_at
                event = self._decision_events.get(request_id)
                if event is None:
                    event = asyncio.Event()
                    self._decision_events[request_id] = event
                event.set()
            elif existing and existing.get("status") == "pending":
                # Another dispatch is already waiting on this request_id; reuse
                # its event instead of creating a new one that orphans the first
                # waiter. The original event in _decision_events is the one the
                # first waiter is blocked on; we must wait on that same event.
                logger.warning(
                    f"Duplicate request_id '{request_id}' submitted while pending; "
                    f"reusing existing pending request record and event."
                )
                event = self._decision_events.get(request_id)
                if event is None:
                    event = asyncio.Event()
                    self._decision_events[request_id] = event
            else:
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
            # Track this waiter so cleanup does not remove the event while
            # other waiters on the same request_id are still blocked.
            self._waiter_counts[request_id] = self._waiter_counts.get(request_id, 0) + 1
            # Dispatch across multi-channels.  The initial dispatch is
            # bounded by the same deadline as the HITL wait so a slow or
            # hung channel cannot prevent the timeout fallback from
            # running.  The remaining time after dispatch is used for the
            # decision wait, making the timeout end-to-end from start.
            dispatch_deadline = wait_timeout
            try:
                if dispatch_deadline > 0:
                    channel_results = await asyncio.wait_for(
                        self.dispatch_all(channels, req_obj.message, req_obj.context),
                        timeout=dispatch_deadline,
                    )
                else:
                    channel_results = await self.dispatch_all(channels, req_obj.message, req_obj.context)
            except asyncio.TimeoutError:
                logger.warning(
                    f"Initial dispatch for request '{request_id}' "
                    f"timed out after {dispatch_deadline}s; applying fallback."
                )
                channel_results = []
            trace_events.append(
                {
                    "event": "dispatched",
                    "channels": channels,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            # Remaining time for the decision wait after dispatch.
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            remaining_timeout = max(0.0, wait_timeout - elapsed)

            trace_events.append(
                {
                    "event": "waiting_decision",
                    "timeout": remaining_timeout,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            try:
                if remaining_timeout > 0:
                    await asyncio.wait_for(event.wait(), timeout=remaining_timeout)
            except asyncio.TimeoutError:
                pass

            req_record = self._pending_requests.get(request_id, {})
            end_time = datetime.now(timezone.utc)
            resolved_at = end_time.isoformat()
            duration = round((end_time - start_time).total_seconds(), 4)

            if req_record.get("status") not in (None, "pending"):
                # Decision submitted before timeout
                approved = req_record.get("approved")
                if approved is None:
                    approved = False
                decision = req_record.get("decision") or req_record.get("status")
                status = req_record.get("status") or decision
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
                    try:
                        await asyncio.wait_for(
                            self.dispatch_all(channels, escalation_msg, req_obj.context),
                            timeout=wait_timeout,
                        )
                    except asyncio.TimeoutError:
                        logger.warning(
                            f"Escalation dispatch for request '{request_id}' "
                            f"timed out after {wait_timeout}s; continuing with fallback decision."
                        )

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
            # Decrement waiter count; only the last waiter cleans up the
            # event and pending request so concurrent duplicate dispatches
            # sharing a request_id do not orphan each other's wait.
            count = self._waiter_counts.get(request_id, 0) - 1
            if count <= 0:
                self._waiter_counts.pop(request_id, None)
                self._pending_requests.pop(request_id, None)
                self._decision_events.pop(request_id, None)
            else:
                self._waiter_counts[request_id] = count

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
    use_mock_channels: bool = False,
) -> DecisionTrace:
    """Standalone module-level function for dispatching and waiting.

    By default uses real channel adapters (which fail explicitly when
    unconfigured). Pass ``use_mock_channels=True`` for in-process testing.
    """
    dispatcher = NotificationDispatcher(use_mock_channels=use_mock_channels)
    return await dispatcher.dispatch_and_wait(request, timeout)
