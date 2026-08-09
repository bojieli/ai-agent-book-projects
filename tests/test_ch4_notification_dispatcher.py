"""Unit tests for chapter4/collaboration-tools/src/notification_dispatcher.py."""

import asyncio
from pathlib import Path
import sys
import pytest

# Ensure chapter4/collaboration-tools/src is in sys.path
ch4_src = Path(__file__).resolve().parent.parent / "chapter4" / "collaboration-tools" / "src"
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
