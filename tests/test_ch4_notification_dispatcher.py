"""Unit tests for chapter4/collaboration-tools/src/notification_dispatcher.py."""

import asyncio
import logging
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
    dispatcher = NotificationDispatcher(use_mock_channels=True)
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
    dispatcher = NotificationDispatcher(use_mock_channels=True)
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
    dispatcher = NotificationDispatcher(use_mock_channels=True)
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
    dispatcher = NotificationDispatcher(fallback_action="auto-approve", use_mock_channels=True)

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
    dispatcher = NotificationDispatcher(fallback_action="auto-reject", use_mock_channels=True)

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
    dispatcher = NotificationDispatcher(use_mock_channels=True)

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
    dispatcher = NotificationDispatcher(use_mock_channels=True)

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
    dispatcher = NotificationDispatcher(fallback_action="auto-approve", use_mock_channels=True)

    trace = dispatcher.dispatch_and_wait_sync("Ping test", timeout=0.05)

    assert isinstance(trace, DecisionTrace)
    assert trace.approved is True
    assert trace.status == "auto-approved"
    assert trace.fallback_triggered is True


@pytest.mark.asyncio
async def test_dispatcher_default_channels_honored():
    """Test that configured default_channels on dispatcher are honored when request has no channels."""
    dispatcher = NotificationDispatcher(default_channels=["slack"], use_mock_channels=True)
    trace = await dispatcher.dispatch_and_wait("Test msg", timeout=0.05)
    assert len(trace.channels_dispatched) == 1
    assert trace.channels_dispatched[0]["channel"] == "slack"


@pytest.mark.asyncio
async def test_custom_decision_string_accepted():
    """Test that custom decision string submitted by operator is preserved without fallback trigger."""
    dispatcher = NotificationDispatcher(use_mock_channels=True)
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
    dispatcher = NotificationDispatcher(use_mock_channels=True)
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
    dispatcher = NotificationDispatcher(fallback_action="escalate", use_mock_channels=True)

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
    dispatcher = NotificationDispatcher(use_mock_channels=True)

    def failing_handler(msg, ctx):
        return {"success": False, "error": "Gateway unavailable"}

    dispatcher.register_channel_handler("sms", failing_handler)
    res = asyncio.run(dispatcher.dispatch_notification("sms", "Test sms"))

    assert res["success"] is False
    assert res["channel"] == "sms"
    assert res["result"]["error"] == "Gateway unavailable"


@pytest.mark.asyncio
async def test_decision_request_default_channels_none():
    """Test DecisionRequest has channels default to None."""
    req = DecisionRequest(message="Test message")
    assert req.channels is None


@pytest.mark.asyncio
async def test_non_pending_record_with_custom_decision_string_without_approved():
    """Test that a non-pending record with a custom decision string and approved=None is accepted."""
    dispatcher = NotificationDispatcher(use_mock_channels=True)
    req_id = "req_custom_no_approved"
    request = {"request_id": req_id, "message": "Manual override test"}

    task = asyncio.create_task(dispatcher.dispatch_and_wait(request, timeout=2.0))
    await asyncio.sleep(0.05)

    # Manually set non-pending status with custom decision and no approved boolean
    dispatcher._pending_requests[req_id]["status"] = "deferred"
    dispatcher._pending_requests[req_id]["decision"] = "deferred"
    dispatcher._pending_requests[req_id]["approved"] = None
    dispatcher._decision_events[req_id].set()

    trace = await task
    assert trace.fallback_triggered is False
    assert trace.status == "deferred"
    assert trace.decision == "deferred"
    assert trace.approved is False


@pytest.mark.asyncio
async def test_try_finally_cleanup_on_dispatch_exception():
    """Test that pending requests and decision events are cleaned up even if dispatch raises an exception."""
    dispatcher = NotificationDispatcher(use_mock_channels=True)

    async def mock_raise(*args, **kwargs):
        raise RuntimeError("Internal dispatch pipeline failure")

    dispatcher.dispatch_all = mock_raise
    req_id = "req_exception_cleanup"
    request = DecisionRequest(request_id=req_id, message="Fail test")

    with pytest.raises(RuntimeError, match="Internal dispatch pipeline failure"):
        await dispatcher.dispatch_and_wait(request, timeout=1.0)

    assert req_id not in dispatcher._pending_requests
    assert req_id not in dispatcher._decision_events


@pytest.mark.asyncio
async def test_enum_fallback_action_normalization():
    """Test that passing FallbackAction Enum instances normalizes correctly."""
    dispatcher = NotificationDispatcher(fallback_action=FallbackAction.AUTO_APPROVE, use_mock_channels=True)
    assert dispatcher.fallback_action == "auto-approve"

    request = DecisionRequest(message="Enum test", fallback_action=FallbackAction.ESCALATE)
    trace = await dispatcher.dispatch_and_wait(request, timeout=0.05)
    assert trace.fallback_action == "escalate"
    assert trace.status == "escalated"

def test_custom_channel_handler_returns_false():
    """Test that a custom channel returning boolean False is marked as success=False."""
    dispatcher = NotificationDispatcher(use_mock_channels=True)

    def false_handler(msg, ctx):
        return False

    dispatcher.register_channel_handler("webhook_custom", false_handler)
    res = asyncio.run(dispatcher.dispatch_notification("webhook_custom", "Test message"))

    assert res["success"] is False
    assert res["channel"] == "webhook_custom"
    assert res["result"] is False


@pytest.mark.asyncio
async def test_submit_decision_non_boolean_approved():
    """Test submit_decision with non-boolean approved argument preserves custom decision string."""
    dispatcher = NotificationDispatcher(use_mock_channels=True)
    req_id = "req_non_bool"
    request = DecisionRequest(request_id=req_id, message="Non-bool test")

    task = asyncio.create_task(dispatcher.dispatch_and_wait(request, timeout=2.0))
    await asyncio.sleep(0.05)

    submitted = dispatcher.submit_decision(req_id, approved="custom_approved_status")
    assert submitted is True

    trace = await task
    assert trace.fallback_triggered is False
    assert trace.status == "custom_approved_status"
    assert trace.decision == "custom_approved_status"
    assert trace.approved is True


@pytest.mark.asyncio
async def test_enum_string_fallback_action_normalization():
    """Test that string representation of Enum like 'FallbackAction.AUTO_APPROVE' normalizes correctly."""
    dispatcher = NotificationDispatcher(fallback_action="FallbackAction.AUTO_APPROVE", use_mock_channels=True)
    assert dispatcher.fallback_action == "auto-approve"

    request = DecisionRequest(message="Enum string test", fallback_action="FallbackAction.ESCALATE")
    trace = await dispatcher.dispatch_and_wait(request, timeout=0.05)
    assert trace.fallback_action == "escalate"
    assert trace.status == "escalated"


@pytest.mark.asyncio
async def test_late_decision_rejection_is_logged(caplog):
    """Regression: late human decision after timeout fallback must be explicitly rejected with a log warning, not silently dropped."""
    dispatcher = NotificationDispatcher(fallback_action="auto-reject", use_mock_channels=True)
    req_id = "req_late_logged"

    # Simulate a request already resolved by timeout fallback
    dispatcher._pending_requests[req_id] = {
        "request_id": req_id,
        "message": "Late decision log test",
        "channels": ["telegram"],
        "fallback_action": "auto-reject",
        "status": "auto-rejected",
        "approved": False,
        "decision": "auto-rejected",
        "notes": "Timeout reached",
        "dispatched_at": "2025-01-01T00:00:00+00:00",
        "resolved_at": "2025-01-01T00:00:01+00:00",
    }

    with caplog.at_level(logging.WARNING):
        submitted = dispatcher.submit_decision(req_id, approved=True)

    assert submitted is False
    assert any(
        "late decision" in record.message.lower() for record in caplog.records
    ), "Expected a warning log when late decision is rejected"


@pytest.mark.asyncio
async def test_text_reject_decision_recorded_as_rejected():
    """Regression: human-submitted text 'reject' must be recorded as rejected (approved=False), not approved."""
    dispatcher = NotificationDispatcher(use_mock_channels=True)
    req_id = "req_text_reject"
    request = DecisionRequest(request_id=req_id, message="Reject text test")

    task = asyncio.create_task(dispatcher.dispatch_and_wait(request, timeout=2.0))
    await asyncio.sleep(0.05)

    submitted = dispatcher.submit_decision(req_id, approved="reject")
    assert submitted is True

    trace = await task
    assert trace.approved is False
    assert trace.fallback_triggered is False
    assert trace.decision == "reject"
    assert trace.status == "reject"


@pytest.mark.asyncio
async def test_text_deny_decision_recorded_as_rejected():
    """Regression: human-submitted text 'deny' must be recorded as rejected (approved=False), not approved."""
    dispatcher = NotificationDispatcher(use_mock_channels=True)
    req_id = "req_text_deny"
    request = DecisionRequest(request_id=req_id, message="Deny text test")

    task = asyncio.create_task(dispatcher.dispatch_and_wait(request, timeout=2.0))
    await asyncio.sleep(0.05)

    submitted = dispatcher.submit_decision(req_id, approved="deny")
    assert submitted is True

    trace = await task
    assert trace.approved is False
    assert trace.fallback_triggered is False
    assert trace.decision == "deny"


@pytest.mark.asyncio
async def test_duplicate_request_id_preserves_existing_decision():
    """Regression: re-submitting same request ID must not discard an existing human decision by overwriting with a fresh pending record."""
    dispatcher = NotificationDispatcher(use_mock_channels=True)
    req_id = "req_dup_preserve"

    # Pre-populate a pending request that already has a human decision submitted
    dispatcher._pending_requests[req_id] = {
        "request_id": req_id,
        "message": "Original request",
        "channels": ["telegram"],
        "fallback_action": "auto-reject",
        "status": "approved",
        "approved": True,
        "decision": "approved",
        "notes": "Approved by lead",
        "dispatched_at": "2025-01-01T00:00:00+00:00",
        "resolved_at": "2025-01-01T00:00:01+00:00",
    }

    request = DecisionRequest(request_id=req_id, message="Duplicate request")
    trace = await dispatcher.dispatch_and_wait(request, timeout=0.1)

    # The existing decision must be preserved, not overwritten to pending + fallback
    assert trace.approved is True
    assert trace.status == "approved"
    assert trace.fallback_triggered is False
    assert trace.decision == "approved"


@pytest.mark.asyncio
async def test_pending_as_decision_string_rejected():
    """Regression: 'pending' is reserved; submitting it as a decision must be rejected, not silently treated as timeout."""
    dispatcher = NotificationDispatcher(use_mock_channels=True)
    req_id = "req_pending_str"
    request = DecisionRequest(request_id=req_id, message="Pending string test")

    task = asyncio.create_task(dispatcher.dispatch_and_wait(request, timeout=0.1))
    await asyncio.sleep(0.05)

    submitted = dispatcher.submit_decision(req_id, approved=True, decision="pending")
    assert submitted is False

    trace = await task
    # No human decision was accepted, so fallback must fire
    assert trace.fallback_triggered is True


@pytest.mark.asyncio
async def test_channel_exception_does_not_kill_dispatch_all():
    """Regression: a single channel raising must not abort the entire dispatch_all batch."""
    dispatcher = NotificationDispatcher(use_mock_channels=True)

    def boom_handler(msg, ctx):
        raise RuntimeError("channel exploded")

    dispatcher.register_channel_handler("boom", boom_handler)
    results = await dispatcher.dispatch_all(["boom", "telegram"], "msg", {})

    # The healthy channel must still produce a result
    assert len(results) == 2
    telegram_result = [r for r in results if isinstance(r, dict) and r.get("channel") == "telegram"]
    assert len(telegram_result) == 1
    assert telegram_result[0]["success"] is True


@pytest.mark.asyncio
async def test_custom_and_unsupported_channels_include_timestamp():
    """Regression: all dispatch branches must return a 'timestamp' key for downstream consumers."""
    dispatcher = NotificationDispatcher(use_mock_channels=True)

    def sync_handler(msg, ctx):
        return {"info": "ok"}

    dispatcher.register_channel_handler("custom_ts", sync_handler)
    custom_res = await dispatcher.dispatch_notification("custom_ts", "msg", {})
    assert "timestamp" in custom_res

    unsupported_res = await dispatcher.dispatch_notification("nonexistent_channel", "msg", {})
    assert "timestamp" in unsupported_res


@pytest.mark.asyncio
async def test_escalation_dispatch_timeout_does_not_hang():
    """Regression: escalation dispatch must have a timeout so a slow channel cannot block dispatch_and_wait indefinitely."""
    dispatcher = NotificationDispatcher(fallback_action="escalate", use_mock_channels=True)

    call_count = 0
    async def fast_then_slow(msg, ctx):
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            await asyncio.sleep(10)
        return {"sent": True}

    dispatcher.register_channel_handler("slow_esc", fast_then_slow)
    request = DecisionRequest(
        message="Escalation timeout test",
        channels=["slow_esc"],
        fallback_action="escalate",
    )

    # timeout=0.05 means the decision wait times out quickly, then escalation
    # dispatch gets the same 0.05s budget. Total should be well under 5s.
    trace = await asyncio.wait_for(
        dispatcher.dispatch_and_wait(request, timeout=0.05),
        timeout=5.0,
    )
    assert trace.fallback_triggered is True
    assert trace.status == "escalated"


@pytest.mark.asyncio
async def test_unconfigured_production_channel_fails_explicitly():
    """Regression: an unconfigured production channel must fail explicitly, not silently succeed.

    Closes the class where mock channels reported success by default, causing
    dispatch_and_wait to mark a HITL request as dispatched when nothing left
    the process. With use_mock_channels=False (the default), a built-in
    channel with no configured adapter must return success=False with an error.
    """
    dispatcher = NotificationDispatcher(use_mock_channels=False)
    res = await dispatcher.dispatch_notification("telegram", "test message", {})
    assert res["success"] is False
    assert "error" in res
    assert "timestamp" in res


@pytest.mark.asyncio
async def test_unconfigured_webhook_fails_explicitly():
    """Regression: webhook channel without webhook_url in channel_config must fail explicitly."""
    dispatcher = NotificationDispatcher(use_mock_channels=False)
    res = await dispatcher.dispatch_notification("webhook", "test message", {})
    assert res["success"] is False
    assert "webhook_url" in res["error"].lower()


@pytest.mark.asyncio
async def test_real_adapter_routes_to_notification_tools(monkeypatch):
    """Regression: built-in channels route to real notification_tools adapters, not mocks.

    Verifies the adapter boundary: when use_mock_channels=False and a real
    adapter is loaded, dispatch delegates to it. The adapter's own
    not-configured error propagates as success=False.
    """
    dispatcher = NotificationDispatcher(use_mock_channels=False)

    # If notification_tools is importable, the adapter should be loaded
    if "telegram" not in dispatcher._real_adapters:
        pytest.skip("notification_tools not importable in this environment")

    res = await dispatcher.dispatch_notification("telegram", "test", {})
    # The real adapter returns success=False when no token is configured
    assert res["success"] is False
    assert "error" in res


@pytest.mark.asyncio
async def test_mock_channels_opt_in_still_succeeds():
    """Regression: use_mock_channels=True preserves the original mock success behavior.

    Ensures the opt-in mock path still returns success=True for built-in
    channels, so existing test suites that rely on mock delivery continue
    to work.
    """
    dispatcher = NotificationDispatcher(use_mock_channels=True)
    res = await dispatcher.dispatch_notification("telegram", "test", {})
    assert res["success"] is True
    assert res["channel"] == "telegram"


@pytest.mark.asyncio
async def test_channel_config_passed_to_real_adapter(monkeypatch):
    """Regression: channel_config values are forwarded to the real adapter.

    Verifies that config like chat_id, webhook_url, and to_email are passed
    through to the adapter callable, not ignored.
    """
    dispatcher = NotificationDispatcher(
        use_mock_channels=False,
        channel_config={"slack": {"webhook_url": "https://hooks.example.com/test"}},
    )

    # Monkeypatch the real adapter to capture args
    captured = {}

    async def fake_slack(message, webhook_url=None, channel=None, username="Collaboration Agent"):
        captured["message"] = message
        captured["webhook_url"] = webhook_url
        captured["channel"] = channel
        return {"success": True, "channel": channel or "default"}

    dispatcher._real_adapters["slack"] = fake_slack
    res = await dispatcher.dispatch_notification("slack", "hello", {})

    assert res["success"] is True
    assert captured["message"] == "hello"
    assert captured["webhook_url"] == "https://hooks.example.com/test"


@pytest.mark.asyncio
async def test_dispatch_and_wait_does_not_silently_succeed_unconfigured():
    """Regression: dispatch_and_wait with unconfigured channels must not mark dispatched as successful.

    The channels_dispatched results must show success=False for unconfigured
    production channels, so downstream consumers know nothing was delivered.
    """
    dispatcher = NotificationDispatcher(
        use_mock_channels=False,
        fallback_action="auto-reject",
    )
    trace = await dispatcher.dispatch_and_wait(
        {"message": "test", "channels": ["telegram"]}, timeout=0.05
    )
    # Fallback fires on timeout, but channel dispatch must show failure
    assert trace.fallback_triggered is True
    channel_result = trace.channels_dispatched[0]
    assert channel_result["success"] is False
    assert "error" in channel_result


@pytest.mark.asyncio
async def test_concurrent_duplicate_request_id_same_decision():
    """Regression: two simultaneous dispatches sharing a request_id get the
    same decision when one approval is submitted.

    Closes the class where dispatch_and_wait assigned a new asyncio.Event to
    _decision_events[request_id] before checking for an existing pending
    request. The duplicate branch then retrieved the newly assigned event
    rather than the first waiter's event, so a single approval submission
    woke only the second waiter while the first timed out to auto-rejected,
    producing contradictory HITL decisions for one request.
    """
    dispatcher = NotificationDispatcher(
        use_mock_channels=True,
        fallback_action="auto-reject",
    )
    request_id = "dup-req-001"
    req = DecisionRequest(
        message="Concurrent duplicate test",
        channels=["slack"],
        request_id=request_id,
    )

    # Launch both dispatches concurrently so they overlap while pending.
    task_a = asyncio.create_task(dispatcher.dispatch_and_wait(req, timeout=2.0))
    task_b = asyncio.create_task(dispatcher.dispatch_and_wait(req, timeout=2.0))

    # Give both tasks time to register as waiters on the same request_id.
    await asyncio.sleep(0.1)
    assert dispatcher._waiter_counts.get(request_id) == 2

    # Submit a single approval — both waiters must see the same decision.
    dispatcher.submit_decision(request_id, approved=True, decision="approved")

    trace_a = await task_a
    trace_b = await task_b

    assert trace_a.request_id == request_id
    assert trace_b.request_id == request_id
    assert trace_a.approved is True
    assert trace_b.approved is True
    assert trace_a.status == "approved"
    assert trace_b.status == "approved"
    assert trace_a.fallback_triggered is False
    assert trace_b.fallback_triggered is False

    # Cleanup must have removed all tracking for this request_id.
    assert request_id not in dispatcher._pending_requests
    assert request_id not in dispatcher._decision_events
    assert request_id not in dispatcher._waiter_counts
@pytest.mark.asyncio
async def test_initial_dispatch_timeout_does_not_block_hitl_timeout():
    """Regression: a slow initial dispatch must not prevent the HITL timeout.

    The initial dispatch_all() is bounded by the same deadline as the
    HITL wait.  A slow or hung channel that exceeds the timeout must
    trigger the fallback, not block indefinitely.  This is analogous to
    the escalation-dispatch timeout test but for the initial
    notification path.
    """
    dispatcher = NotificationDispatcher(
        fallback_action="auto-reject", use_mock_channels=True
    )

    async def slow_handler(msg, ctx):
        await asyncio.sleep(10)
        return {"sent": True}

    dispatcher.register_channel_handler("slow_init", slow_handler)
    request = DecisionRequest(
        message="Initial dispatch timeout test",
        channels=["slow_init"],
        fallback_action="auto-reject",
    )

    # timeout=0.05 means the initial dispatch must be bounded to 0.05s.
    # Without the fix, the slow handler blocks for 10s and the fallback
    # never runs.  Total must be well under 5s.
    trace = await asyncio.wait_for(
        dispatcher.dispatch_and_wait(request, timeout=0.05),
        timeout=5.0,
    )
    assert trace.fallback_triggered is True
    assert trace.status == "auto-rejected"
    assert trace.approved is False
