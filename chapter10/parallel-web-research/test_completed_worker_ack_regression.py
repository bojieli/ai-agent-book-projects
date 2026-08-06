import asyncio
import pytest
from agents import Coordinator, TaskRecord
from message_bus import MessageBus
from sources import Website

@pytest.mark.asyncio
async def test_worker_completing_before_winner_is_not_reported_as_missing_ack():
    """Contract proved: Coordinator.run excludes workers that completed with not_found or errors prior to target settlement from expected_loser_acks.
    Bug locked out: falsely reporting self-completed workers as missing loser ACKs when a winner settles."""
    bus = MessageBus(verbose=False)
    coordinator = Coordinator(bus, "target")
    
    site1 = Website("Site 1", "https://site1.edu", "College 1")
    site2 = Website("Site 2", "https://site2.edu", "College 2")
    site3 = Website("Site 3", "https://site3.edu", "College 3")
    
    # Create fake worker objects for coordinator.workers
    class FakeWorker:
        def __init__(self, wid, site):
            self.id = wid
            self.site = site
            self.timeout = 10
        async def run(self):
            pass

    workers = [
        FakeWorker("worker-1", site1),
        FakeWorker("worker-2", site2),
        FakeWorker("worker-3", site3),
    ]

    for w in workers:
        coordinator.add_worker(w)

    # Worker 1 completed with not_found BEFORE settlement
    await bus.send("worker-1", "coordinator", "not_found", {"reason": "not found", "source": "Site 1"})
    await bus.send("worker-1", "coordinator", "resource_closed", {"browser_context_closed": True, "source": "Site 1"})
    
    # Worker 2 found target (winner)
    await bus.send("worker-2", "coordinator", "target_found", {"data": {"found": True}, "source": "Site 2"})
    await bus.send("worker-2", "coordinator", "resource_closed", {"browser_context_closed": True, "source": "Site 2"})

    # Worker 3 received terminate and acknowledged it
    await bus.send("worker-3", "coordinator", "ack", {"acked": "terminate", "source": "Site 3"})
    await bus.send("worker-3", "coordinator", "resource_closed", {"browser_context_closed": True, "source": "Site 3"})

    result = await coordinator.run()
    
    assert result["winner"] == "worker-2"
    assert result["expected_loser_acks"] == ["worker-3"]
    assert result["missing_loser_acks"] == []


@pytest.mark.asyncio
async def test_worker_completing_after_winner_still_owes_ack():
    """The expected ACK set is a snapshot taken when the winner settles."""
    bus = MessageBus(verbose=False)
    coordinator = Coordinator(bus, "target")

    class FakeWorker:
        timeout = 10

        def __init__(self, wid):
            self.id = wid
            self.site = Website(wid, f"https://{wid}.edu", wid)

        async def run(self):
            pass

    for worker_id in ("worker-1", "worker-2"):
        coordinator.add_worker(FakeWorker(worker_id))

    await bus.send("worker-2", "coordinator", "target_found", {"data": {"found": True}})
    await bus.send("worker-1", "coordinator", "not_found", {"reason": "finished after settlement"})
    for worker_id in ("worker-1", "worker-2"):
        await bus.send(worker_id, "coordinator", "resource_closed", {"browser_context_closed": True})

    result = await coordinator.run()

    assert result["expected_loser_acks"] == ["worker-1"]
    assert result["missing_loser_acks"] == ["worker-1"]
