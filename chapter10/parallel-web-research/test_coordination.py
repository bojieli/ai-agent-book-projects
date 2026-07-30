import asyncio
from types import SimpleNamespace

import pytest

from agents import Coordinator
from agents import WorkerAgent
from message_bus import MessageBus
from sources import DEFAULT_SITES, load_sites


@pytest.mark.asyncio
async def test_near_simultaneous_hits_settle_and_broadcast_once():
    bus = MessageBus(verbose=False)
    coordinator = Coordinator(bus, "target")
    await asyncio.gather(
        coordinator._settle("agent-a", {"name": "target"}),
        coordinator._settle("agent-b", {"name": "target"}),
    )
    assert coordinator.winner in {"agent-a", "agent-b"}
    assert len(coordinator.duplicate_hits) == 1
    assert sum(m.type == "terminate" for m in bus.history) == 1


def test_default_dataset_is_ten_real_http_university_pages():
    sites = load_sites(None)
    assert len(sites) == 10
    assert all(s.url.startswith("https://") for s in sites)
    assert all(not hasattr(s, "content") and not hasattr(s, "latency") for s in sites)


class StubWorker:
    def __init__(self, worker_id, bus, events):
        self.id = worker_id
        self.site = SimpleNamespace(
            name=f"source-{worker_id}", url=f"https://example.test/{worker_id}"
        )
        self.bus = bus
        self.events = events
        self.timeout = 0.1
        self.sub = bus.subscribe(worker_id, types=["task_assigned", "terminate"])

    async def run(self):
        assigned = await self.sub.get()
        assert assigned.type == "task_assigned"
        for event_type, payload in self.events:
            if event_type == "status_update":
                payload = {"source": self.site.name, **payload}
            else:
                payload = {**payload, "source": self.site.name}
            await self.bus.send(self.id, "coordinator", event_type, payload)


@pytest.mark.asyncio
async def test_all_not_found_has_no_cascade_and_returns_reason_and_status_aggregation():
    bus = MessageBus(verbose=False)
    coordinator = Coordinator(bus, "missing")
    for worker_id in ("agent-a", "agent-b"):
        coordinator.add_worker(StubWorker(worker_id, bus, [
            ("status_update", {"state": "执行中", "note": "reading"}),
            ("not_found", {"reason": "target absent"}),
            ("status_update", {"state": "已完成", "note": "未找到目标"}),
            ("resource_closed", {"browser_context_closed": True}),
        ]))

    result = await coordinator.run()

    assert result["outcome"] == "not_found"
    assert result["winner"] is None
    assert result["terminate_broadcasts"] == 0
    assert result["not_found_reasons"] == {
        "agent-a": "target absent", "agent-b": "target absent",
    }
    assert all(row["state"] == "已完成" for row in result["status_table"].values())
    assert result["failure_summary"] == {"count": 0, "by_type": {}}


@pytest.mark.asyncio
async def test_worker_failure_is_isolated_and_summarized_while_peer_completes():
    bus = MessageBus(verbose=False)
    coordinator = Coordinator(bus, "missing")
    coordinator.add_worker(StubWorker("bad", bus, [
        ("worker_error", {"error": "TimeoutError: deadline"}),
        ("status_update", {"state": "失败", "note": "timeout"}),
        ("resource_closed", {"browser_context_closed": True}),
    ]))
    coordinator.add_worker(StubWorker("good", bus, [
        ("not_found", {"reason": "target absent"}),
        ("status_update", {"state": "已完成", "note": "peer completed"}),
        ("resource_closed", {"browser_context_closed": True}),
    ]))

    result = await coordinator.run()

    assert result["outcome"] == "not_found"
    assert result["errors"] == {"bad": "TimeoutError: deadline"}
    assert result["not_found_reasons"] == {"good": "target absent"}
    assert result["failure_summary"] == {"count": 1, "by_type": {"TimeoutError": 1}}
    assert result["status_table"]["good"]["state"] == "已完成"


@pytest.mark.asyncio
async def test_timeout_cancellation_closes_real_worker_context():
    class BlockingPage:
        async def goto(self, *args, **kwargs):
            return None

        def locator(self, _selector):
            return self

        async def inner_text(self, **kwargs):
            await asyncio.Future()

    class Context:
        def __init__(self):
            self.closed = False

        async def new_page(self):
            return BlockingPage()

        async def close(self):
            self.closed = True

    class Pool:
        def __init__(self):
            self.context = Context()
            self.closed = 0

        async def new_context(self):
            return self.context

        async def mark_closed(self):
            self.closed += 1

    bus = MessageBus(verbose=False)
    pool = Pool()
    site = SimpleNamespace(name="blocking", url="https://example.test")
    worker = WorkerAgent("agent-timeout", site, bus, "target", pool, timeout=0.01)
    coordinator_sub = bus.subscribe("coordinator", types=None)
    await bus.send("coordinator", worker.id, "task_assigned", {})

    # The outer Manager deadline cancels the worker while body text is pending.
    await asyncio.wait_for(worker.run(), timeout=0.05)

    assert pool.context.closed is True
    assert pool.closed == 1
    messages = []
    while not coordinator_sub.inbox.empty():
        messages.append(coordinator_sub.inbox.get_nowait())
    assert any(m.type == "worker_error" and "TimeoutError" in m.payload["error"] for m in messages)
    assert any(m.type == "resource_closed" and m.payload["browser_context_closed"] for m in messages)
