"""Real-browser workers and central coordinator for Experiment 10-6."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from llm import extract_profile
from message_bus import BROADCAST, MessageBus
from sources import Website


class TaskState(str, Enum):
    SUBMITTED = "已提交"
    RUNNING = "执行中"
    SUCCEEDED = "已完成"
    FAILED = "失败"
    TERMINATED = "已终止"


@dataclass
class TaskRecord:
    worker_id: str
    source_name: str
    state: TaskState = TaskState.SUBMITTED
    note: str = ""
    updated: float = field(default_factory=time.monotonic)


class BrowserPool:
    """One Chromium process, one fully isolated browser context per worker."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._pw = None
        self.browser = None
        self.contexts_created = 0
        self.contexts_closed = 0

    async def start(self):
        from playwright.async_api import async_playwright
        self._pw = await async_playwright().start()
        self.browser = await self._pw.chromium.launch(headless=self.headless)

    async def new_context(self):
        if not self.browser:
            raise RuntimeError("BrowserPool not started")
        context = await self.browser.new_context()
        self.contexts_created += 1
        return context

    async def mark_closed(self):
        self.contexts_closed += 1

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self._pw:
            await self._pw.stop()


class WorkerAgent:
    def __init__(self, worker_id: str, site: Website, bus: MessageBus, target: str,
                 browsers: BrowserPool, timeout: float = 120,
                 browser_receipt_sink: Optional[Callable[[dict], None]] = None,
                 llm_receipt_sink: Optional[Callable[[dict], None]] = None,
                 run_phase: str = "parallel"):
        self.id, self.site, self.bus, self.target = worker_id, site, bus, target
        self.browsers, self.timeout = browsers, timeout
        self.sub = bus.subscribe(worker_id, types=["task_assigned", "terminate"])
        self.terminate = asyncio.Event()
        self._termination_reason = ""
        self.context = None
        self.browser_receipt_sink = browser_receipt_sink
        self.llm_receipt_sink = llm_receipt_sink
        self.run_phase = run_phase

    async def report(self, state: TaskState, note: str):
        await self.bus.send(self.id, "coordinator", "status_update", {
            "state": state.value, "note": note, "source": self.site.name,
        })

    async def _signals(self):
        while True:
            message = await self.sub.get()
            if message.type == "terminate":
                self._termination_reason = message.payload.get("reason", "cascade")
                self.terminate.set()
                return

    async def _await_interruptibly(self, awaitable):
        operation = asyncio.create_task(awaitable)
        stopping = asyncio.create_task(self.terminate.wait())
        try:
            done, _ = await asyncio.wait(
                {operation, stopping}, return_when=asyncio.FIRST_COMPLETED
            )
        except BaseException:
            operation.cancel()
            stopping.cancel()
            await asyncio.gather(operation, stopping, return_exceptions=True)
            raise
        if stopping in done and self.terminate.is_set():
            operation.cancel()
            await asyncio.gather(operation, return_exceptions=True)
            raise asyncio.CancelledError
        stopping.cancel()
        await asyncio.gather(stopping, return_exceptions=True)
        return await operation

    async def _navigate_interruptibly(self, page):
        return await self._await_interruptibly(page.goto(
            self.site.url, wait_until="domcontentloaded", timeout=int(self.timeout * 1000)
        ))

    async def run(self):
        assigned = await self.sub.get()
        while assigned.type != "task_assigned":
            if assigned.type == "terminate":
                self._termination_reason = assigned.payload.get("reason", "cascade")
                self.terminate.set()
                await self.report(TaskState.TERMINATED, f"安全点响应终止：{self._termination_reason}")
                await self.bus.send(self.id, "coordinator", "ack", {
                    "acked": "terminate", "source": self.site.name,
                })
                return
            assigned = await self.sub.get()
        signal_task = asyncio.create_task(self._signals())
        try:
            await self.report(TaskState.RUNNING, "创建独立 Chromium context")
            self.context = await self.browsers.new_context()
            page = await self.context.new_page()
            await self.report(TaskState.RUNNING, f"正在加载 {self.site.url}")
            navigation = await self._navigate_interruptibly(page)
            if self.terminate.is_set():
                raise asyncio.CancelledError
            await self.report(TaskState.RUNNING, "正在读取渲染后的教师页面")
            text = await self._await_interruptibly(
                page.locator("body").inner_text(timeout=20_000)
            )
            if self.browser_receipt_sink:
                self.browser_receipt_sink({
                    "kind": "rendered_browser_observation",
                    "phase": self.run_phase,
                    "worker_id": self.id,
                    "site": self.site.name,
                    "college": self.site.college,
                    "requested_url": self.site.url,
                    "final_url": page.url,
                    "http_status": navigation.status if navigation else None,
                    "rendered_body_text": text,
                })
            if self.terminate.is_set():
                raise asyncio.CancelledError
            await self.report(TaskState.RUNNING, "正在做证据约束的教师信息抽取")
            profile = await self._await_interruptibly(
                extract_profile(
                    self.target,
                    self.site.college,
                    self.site.url,
                    text,
                    receipt_sink=self.llm_receipt_sink,
                    call_context={
                        "phase": self.run_phase,
                        "worker_id": self.id,
                        "site": self.site.name,
                    },
                )
            )
            if profile.get("found"):
                await self.bus.send(self.id, "coordinator", "target_found", {
                    "data": profile, "source": self.site.name,
                })
                await self.report(TaskState.SUCCEEDED, "找到目标教师")
            else:
                await self.bus.send(self.id, "coordinator", "not_found", {
                    "reason": profile.get("reason", "not found"), "source": self.site.name,
                })
                await self.report(TaskState.SUCCEEDED, "页面中未找到目标")
        except asyncio.CancelledError:
            if self.terminate.is_set():
                await self.report(TaskState.TERMINATED, f"安全点响应终止：{self._termination_reason}")
                await self.bus.send(self.id, "coordinator", "ack", {
                    "acked": "terminate", "source": self.site.name,
                })
            else:
                await self.bus.send(self.id, "coordinator", "worker_error", {
                    "error": f"TimeoutError: exceeded {self.timeout + 15:.0f}s worker deadline",
                    "source": self.site.name,
                })
                await self.report(TaskState.FAILED, "任务超时，已关闭独立浏览器会话")
        except Exception as exc:
            await self.bus.send(self.id, "coordinator", "worker_error", {
                "error": f"{type(exc).__name__}: {exc}", "source": self.site.name,
            })
            await self.report(TaskState.FAILED, f"{type(exc).__name__}: {exc}")
        finally:
            signal_task.cancel()
            await asyncio.gather(signal_task, return_exceptions=True)
            context_closed = self.context is None
            if self.context:
                try:
                    await self.context.close()
                    await self.browsers.mark_closed()
                    context_closed = True
                except Exception as exc:
                    await self.bus.send(self.id, "coordinator", "worker_error", {
                        "error": f"ContextCloseError: {exc}", "source": self.site.name,
                    })
            await self.bus.send(self.id, "coordinator", "resource_closed", {
                "browser_context_closed": context_closed, "source": self.site.name,
            })


class Coordinator:
    def __init__(self, bus: MessageBus, target: str):
        self.bus, self.target = bus, target
        self.sub = bus.subscribe("coordinator", types=None)
        self.workers: List[WorkerAgent] = []
        self.table: Dict[str, TaskRecord] = {}
        self._lock = asyncio.Lock()
        self._settled = False
        self.winner: Optional[str] = None
        self.profile: Optional[dict] = None
        self.expected_loser_acks: Optional[set[str]] = None
        self.duplicate_hits: List[str] = []
        self.acks: set[str] = set()
        self.errors: Dict[str, str] = {}
        self.not_found: Dict[str, str] = {}
        self.closed: set[str] = set()
        self.resource_failures: Dict[str, str] = {}

    def add_worker(self, worker: WorkerAgent):
        self.workers.append(worker)
        self.table[worker.id] = TaskRecord(worker.id, worker.site.name)

    async def _settle(self, worker_id: str, profile: dict):
        async with self._lock:
            if self._settled:
                self.duplicate_hits.append(worker_id)
                return
            self._settled, self.winner, self.profile = True, worker_id, profile
            # Only workers still running when the winner settles receive the
            # terminate broadcast and therefore owe an acknowledgement.
            self.expected_loser_acks = {
                worker.id
                for worker in self.workers
                if worker.id != worker_id
                and worker.id not in self.not_found
                and worker.id not in self.errors
            }
            await self.bus.send("coordinator", BROADCAST, "terminate", {
                "reason": f"target_found_by_{worker_id}", "winner": worker_id,
            })

    async def run(self) -> dict:
        started = time.monotonic()
        for w in self.workers:
            await self.bus.send("coordinator", w.id, "task_assigned", {
                "target": self.target, "url": w.site.url, "task_id": w.id,
            })
        tasks = [asyncio.create_task(asyncio.wait_for(w.run(), timeout=w.timeout + 15)) for w in self.workers]
        while len(self.closed) < len(self.workers):
            try:
                env = await asyncio.wait_for(self.sub.get(), timeout=0.5)
            except asyncio.TimeoutError:
                if all(t.done() for t in tasks):
                    break
                continue
            rec = self.table.get(env.sender_id)
            if env.type == "status_update" and rec:
                rec.state = TaskState(env.payload["state"])
                rec.note = env.payload.get("note", "")
                rec.updated = time.monotonic()
            elif env.type == "target_found":
                await self._settle(env.sender_id, env.payload["data"])
            elif env.type == "ack":
                self.acks.add(env.sender_id)
            elif env.type == "worker_error":
                self.errors[env.sender_id] = env.payload["error"]
            elif env.type == "not_found":
                self.not_found[env.sender_id] = env.payload.get("reason", "not found")
            elif env.type == "resource_closed":
                self.closed.add(env.sender_id)
                if not env.payload.get("browser_context_closed", False):
                    self.resource_failures[env.sender_id] = "browser context did not close"
        await asyncio.gather(*tasks, return_exceptions=True)
        failure_types: Dict[str, int] = {}
        for error in self.errors.values():
            kind = error.split(":", 1)[0]
            failure_types[kind] = failure_types.get(kind, 0) + 1
        expected_acks = self.expected_loser_acks or set()
        missing_acks = expected_acks - self.acks
        return {
            "outcome": "found" if self.winner else "not_found",
            "winner": self.winner,
            "profile": self.profile,
            "duplicate_hits": self.duplicate_hits,
            "acks": sorted(self.acks),
            "expected_loser_acks": sorted(expected_acks),
            "missing_loser_acks": sorted(missing_acks),
            "errors": self.errors,
            "failure_summary": {
                "count": len(self.errors),
                "by_type": failure_types,
            },
            "not_found_reasons": self.not_found,
            "status_table": {
                worker_id: {
                    "source": record.source_name,
                    "state": record.state.value,
                    "note": record.note,
                }
                for worker_id, record in self.table.items()
            },
            "terminate_broadcasts": sum(1 for e in self.bus.history if e.type == "terminate"),
            "parallel_seconds": round(time.monotonic() - started, 3),
            "contexts_closed": len(self.closed),
            "resource_failures": self.resource_failures,
        }


async def search_one(
    site: Website,
    target: str,
    browsers: BrowserPool,
    timeout: float,
    browser_receipt_sink: Optional[Callable[[dict], None]] = None,
    llm_receipt_sink: Optional[Callable[[dict], None]] = None,
    worker_id: str = "serial",
    run_phase: str = "serial",
) -> dict:
    context = await browsers.new_context()
    started = time.monotonic()
    try:
        page = await context.new_page()
        navigation = await page.goto(site.url, wait_until="domcontentloaded", timeout=int(timeout * 1000))
        text = await page.locator("body").inner_text(timeout=20_000)
        if browser_receipt_sink:
            browser_receipt_sink({
                "kind": "rendered_browser_observation",
                "phase": run_phase,
                "worker_id": worker_id,
                "site": site.name,
                "college": site.college,
                "requested_url": site.url,
                "final_url": page.url,
                "http_status": navigation.status if navigation else None,
                "rendered_body_text": text,
            })
        profile = await extract_profile(
            target,
            site.college,
            site.url,
            text,
            receipt_sink=llm_receipt_sink,
            call_context={"phase": run_phase, "worker_id": worker_id, "site": site.name},
        )
        return {"site": site.name, "profile": profile, "seconds": time.monotonic() - started}
    finally:
        await context.close()
        await browsers.mark_closed()


async def run_sequential(
    sites: List[Website],
    target: str,
    browsers: BrowserPool,
    timeout: float,
    browser_receipt_sink: Optional[Callable[[dict], None]] = None,
    llm_receipt_sink: Optional[Callable[[dict], None]] = None,
    run_phase: str = "serial",
) -> dict:
    started = time.monotonic()
    results = []
    for site in sites:
        try:
            item = await search_one(
                site,
                target,
                browsers,
                timeout,
                browser_receipt_sink=browser_receipt_sink,
                llm_receipt_sink=llm_receipt_sink,
                worker_id=f"serial-{len(results):02d}",
                run_phase=run_phase,
            )
            results.append(item)
            if item["profile"].get("found"):
                break
        except Exception as exc:
            results.append({"site": site.name, "error": f"{type(exc).__name__}: {exc}"})
    return {"seconds": round(time.monotonic() - started, 3), "visited": len(results), "results": results}
