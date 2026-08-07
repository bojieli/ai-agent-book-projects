import asyncio
import pytest
import sys
from pathlib import Path

# Ensure chapter10/parallel-web-research is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

from agents import WorkerAgent
from message_bus import MessageBus, BROADCAST
from sources import Website


@pytest.mark.asyncio
async def test_worker_exits_early_when_terminate_arrives_before_task_assigned():
    """Contract proved: WorkerAgent handles terminate broadcast received before task_assigned without hanging or ignoring the signal.
    Bug locked out: infinite loop awaiting task_assigned while ignoring terminate signal."""
    bus = MessageBus(verbose=False)
    site = Website("s1", "http://site1.edu", "College 1")
    w = WorkerAgent("worker-1", site, bus, "target", None)

    # Broadcast terminate to bus BEFORE worker-1 gets task_assigned
    await bus.send("coordinator", BROADCAST, "terminate", {"reason": "target_found_by_other"})

    # w.run() must exit promptly (not hang awaiting task_assigned), set terminate event, and send ACK
    await asyncio.wait_for(w.run(), timeout=2.0)

    assert w.terminate.is_set()
    assert w._termination_reason == "target_found_by_other"
    acks = [m for m in bus.history if m.type == "ack" and m.sender_id == "worker-1"]
    assert len(acks) == 1
    assert acks[0].payload.get("acked") == "terminate"
