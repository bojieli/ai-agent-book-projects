"""Unit tests for chapter4/collaboration-tools/src/notification_dispatcher.py."""

import asyncio
from pathlib import Path
import sys
import pytest

# Ensure chapter4/collaboration-tools/src is in sys.path
ch4_src = (Path(__file__).resolve().parent.parent / "chapter4" / "collaboration-tools" / "src").resolve()
if str(ch4_src) not in sys.path:
    sys.path.insert(0, str(ch4_src))

from notification_dispatcher import (
    DecisionRequest,
    DecisionTrace,
    FallbackAction,
    NotificationDispatcher,
    dispatch_and_wait,
)


@pytest.mark.asyncio
async def test_multi_channel_dispatch_all():
    """Test unified multi-channel notification dispatching across mock channels."""
    dispatcher = NotificationDispatcher()
    channels = ["telegram", "slack", "webhook", "email"]
    message = "Deployment preflight check completed."

    results = await dispatcher.dispatch_all(channels, message, context={"env": "prod"})

    assert len(results) == 4
    for res in results:
        assert res["success"] is True
        assert res["channel"] in channels
        assert "timestamp" in res


@pytest.mark.asyncio
async def test_hitl_human_approval_before_timeout():
    """Test Human-in-the-Loop decision approval submitted before timeout."""
    dispatcher = NotificationDispatcher()
    request_id = "req_test_approve_123"

    request = {
        "request_id": request_id,
        "message": "Approve production schema migration",
        "channels": ["telegram", "slack"],
        "fallback_action": "auto-reject",
    }

    # Start dispatch and wait in background task
    task = asyncio.create_task(dispatcher.dispatch_and_wait(request, timeout=2.0))

    # Wait briefly for task to enter waiting state
    await asyncio.sleep(0.1)

    # Submit human approval decision
    submitted = dispatcher.submit_decision(
        request_id=request_id, approved=True, notes="Approved by Lead DB Architect"
    )
    assert submitted is True

    trace = await task

    assert isinstance(trace, DecisionTrace)
    assert trace.request_id == request_id
    assert trace.approved is True
    assert trace.status == "approved"
    assert trace.decision == "approved"
    assert trace.fallback_triggered is False
    assert trace.notes == "Approved by Lead DB Architect"
    assert len(trace.channels_dispatched) == 2


@pytest.mark.asyncio
async def test_hitl_human_rejection_before_timeout():
    """Test Human-in-the-Loop decision rejection submitted before timeout."""
    dispatcher = NotificationDispatcher()
    request_id = "req_test_reject_456"

    request = DecisionRequest(
        request_id=request_id,
        message="Request permission for data wipe",
        channels=["email"],
        fallback_action="auto-approve",
    )

    task = asyncio.create_task(dispatcher.dispatch_and_wait(request, timeout=2.0))
    await asyncio.sleep(0.1)

    submitted = dispatcher.submit_decision(
        request_id=request_id, approved=False, notes="Denied due to compliance"
    )
    assert submitted is True

    trace = await task

    assert trace.approved is False
    assert trace.status == "rejected"
    assert trace.decision == "rejected"
    assert trace.fallback_triggered is False
    assert trace.notes == "Denied due to compliance"


@pytest.mark.asyncio
async def test_hitl_timeout_fallback_auto_approve():
    """Test HITL timeout triggering auto-approve fallback policy."""
    dispatcher = NotificationDispatcher(fallback_action="auto-approve")

    request = {
        "message": "Routine server restart",
        "fallback_action": "auto-approve",
    }

    trace = await dispatcher.dispatch_and_wait(request, timeout=0.1)

    assert trace.fallback_triggered is True
    assert trace.approved is True
    assert trace.status == "auto-approved"
    assert trace.decision == "auto-approved"
    assert "auto-approved request" in trace.notes


@pytest.mark.asyncio
async def test_hitl_timeout_fallback_auto_reject():
    """Test HITL timeout triggering auto-reject fallback policy."""
    dispatcher = NotificationDispatcher(fallback_action="auto-reject")

    request = {
        "message": "High-risk administrative action",
        "fallback_action": "auto-reject",
    }

    trace = await dispatcher.dispatch_and_wait(request, timeout=0.1)

    assert trace.fallback_triggered is True
    assert trace.approved is False
    assert trace.status == "auto-rejected"
    assert trace.decision == "auto-rejected"
    assert "auto-rejected request" in trace.notes


@pytest.mark.asyncio
async def test_hitl_timeout_fallback_escalate():
    """Test HITL timeout triggering escalation fallback policy and escalation notification."""
    dispatcher = NotificationDispatcher()

    request = {
        "message": "Critical security policy exception",
        "channels": ["slack", "email"],
        "fallback_action": "escalate",
    }

    trace = await dispatcher.dispatch_and_wait(request, timeout=0.1)

    assert trace.fallback_triggered is True
    assert trace.approved is False
    assert trace.status == "escalated"
    assert trace.decision == "escalated"
    assert "escalated request" in trace.notes


def test_custom_channel_handler():
    """Test registering a custom channel handler."""
    dispatcher = NotificationDispatcher()

    invoked = []

    def custom_pager(msg, ctx):
        invoked.append((msg, ctx))
        return {"pager_id": "pager_999"}

    dispatcher.register_channel_handler("pager", custom_pager)

    res = asyncio.run(dispatcher.dispatch_notification("pager", "Alert!", {"severity": 1}))

    assert res["success"] is True
    assert res["channel"] == "pager"
    assert res["result"] == {"pager_id": "pager_999"}
    assert len(invoked) == 1


def test_sync_wrapper():
    """Test synchronous dispatch_and_wait_sync wrapper."""
    dispatcher = NotificationDispatcher(fallback_action="auto-approve")

    trace = dispatcher.dispatch_and_wait_sync("Ping test", timeout=0.05)

    assert isinstance(trace, DecisionTrace)
    assert trace.approved is True
    assert trace.status == "auto-approved"
    assert trace.fallback_triggered is True


@pytest.mark.asyncio
async def test_dispatcher_default_channels_honored():
    """Test that configured default_channels on dispatcher are honored when request has no channels."""
    dispatcher = NotificationDispatcher(default_channels=["slack"])
    trace = await dispatcher.dispatch_and_wait("Test msg", timeout=0.05)
    assert len(trace.channels_dispatched) == 1
    assert trace.channels_dispatched[0]["channel"] == "slack"


@pytest.mark.asyncio
async def test_custom_decision_string_accepted():
    """Test that custom decision string submitted by operator is preserved without fallback trigger."""
    dispatcher = NotificationDispatcher()
    req_id = "req_custom_dec_1"
    request = {"request_id": req_id, "message": "Deploy code"}

    task = asyncio.create_task(dispatcher.dispatch_and_wait(request, timeout=2.0))
    await asyncio.sleep(0.05)

    dispatcher.submit_decision(req_id, approved=True, decision="approved_by_lead")
    trace = await task

    assert trace.fallback_triggered is False
    assert trace.approved is True
    assert trace.decision == "approved_by_lead"
    assert trace.status == "approved_by_lead"


@pytest.mark.asyncio
async def test_cleanup_on_cancellation():
    """Test that pending requests and decision events are cleaned up if task is cancelled."""
    dispatcher = NotificationDispatcher()
    req_id = "req_cancel_test"
    task = asyncio.create_task(
        dispatcher.dispatch_and_wait({"request_id": req_id, "message": "Long wait"}, timeout=10.0)
    )
    await asyncio.sleep(0.05)
    assert req_id in dispatcher._pending_requests
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert req_id not in dispatcher._pending_requests
    assert req_id not in dispatcher._decision_events


@pytest.mark.asyncio
async def test_late_decision_submission_rejected_after_fallback():
    """Test that submitting a decision after fallback policy has triggered returns False."""
    dispatcher = NotificationDispatcher(fallback_action="escalate")

    # Slow custom channel to simulate delay during escalation dispatch
    async def slow_channel(msg, ctx):
        await asyncio.sleep(0.3)
        return {"sent": True}

    dispatcher.register_channel_handler("slow", slow_channel)
    req_id = "req_late_sub"
    request = {
        "request_id": req_id,
        "message": "Escalated task",
        "channels": ["slow"],
        "fallback_action": "escalate",
    }

    task = asyncio.create_task(dispatcher.dispatch_and_wait(request, timeout=0.05))
    await asyncio.sleep(0.4)

    # Attempt decision submission after timeout
    submitted = dispatcher.submit_decision(req_id, approved=True)
    assert submitted is False

    trace = await task
    assert trace.status == "escalated"
    assert trace.fallback_triggered is True


def test_custom_channel_handler_failure_dict():
    """Test that a custom channel returning success=False in dict result is marked as success=False."""
    dispatcher = NotificationDispatcher()

    def failing_handler(msg, ctx):
        return {"success": False, "error": "Gateway unavailable"}

    dispatcher.register_channel_handler("sms", failing_handler)
    res = asyncio.run(dispatcher.dispatch_notification("sms", "Test sms"))

    assert res["success"] is False
    assert res["channel"] == "sms"
    assert res["result"]["error"] == "Gateway unavailable"
