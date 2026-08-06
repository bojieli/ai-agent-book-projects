"""Bounded agent loop tests."""

from __future__ import annotations

from app.agents.bounded_loop import BoundedAgentLoop, MockPlanner, PlannerAction, PlannerDecision, deny_first_pre_tool_hook
from app.connectors.discovery import ConnectorCatalog, DiscoveryGrant, ToolDiscoveryService
from app.connectors.mock import MockDefectConnector, MockTaskConnector
from app.harness import ToolRuntime
from app.memory.repository import InMemoryJournalRepository
from app.memory.session_journal import SessionJournal


def _loop(max_steps: int = 5) -> BoundedAgentLoop:
    rt = ToolRuntime()
    rt.register(MockDefectConnector())
    rt.register(MockTaskConnector())
    cat = ConnectorCatalog()
    cat.register_from_connector(MockDefectConnector(), org_domains=["eng"], scenarios=["*"])
    cat.register_from_connector(MockTaskConnector(), org_domains=["eng"], scenarios=["*"])
    return BoundedAgentLoop(
        runtime=rt,
        discovery=ToolDiscoveryService(catalog=cat, min_score=1.0),
        planner=MockPlanner(),
        max_steps=max_steps,
    )


def test_agent_loop_tool_call_two_rounds():
    """工具执行后 append observation，planner 第二轮 answer。"""
    repo = InMemoryJournalRepository()
    j = SessionJournal.resume("agent1", repo)
    j.append("message", {"role": "user", "content": "请建缺陷：网关超时"})
    result = _loop().run(
        journal=j,
        need="建缺陷 网关",
        org_domains=["eng"],
        scenario="dialog",
        tool_allowlist=["connector.defect.create"],
    )
    assert result.terminal == "succeeded"
    assert result.tool_calls == 1
    assert result.steps == 2
    types = [e.entry_type for e in j.entries]
    assert "tool_result" in types
    assert "observation" in types
    assert "external_id" in result.answer


def test_agent_loop_suspend_and_resume():
    repo = InMemoryJournalRepository()
    j = SessionJournal.resume("agent2", repo)
    j.append("message", {"role": "user", "content": "需要人工 HITL 确认"})
    loop = _loop()
    r1 = loop.run(journal=j, need="人工", org_domains=["eng"], scenario="dialog")
    assert r1.terminal == "suspended"
    assert j.pending_suspend() is not None
    r2 = loop.resume(
        journal=j,
        need="建任务 follow-up",
        org_domains=["eng"],
        scenario="dialog",
        tool_allowlist=["connector.task.create"],
        hitl_approved=True,
        user_id="u1",
    )
    assert r2.terminal == "succeeded"
    assert j.pending_suspend() is None


def test_agent_loop_reject_terminal():
    repo = InMemoryJournalRepository()
    j = SessionJournal.resume("agent2b", repo)
    j.append("message", {"role": "user", "content": "需要人工 HITL"})
    loop = _loop()
    loop.run(journal=j, need="人工", org_domains=["eng"], scenario="dialog")
    r = loop.resume(
        journal=j,
        need="",
        org_domains=["eng"],
        scenario="dialog",
        hitl_approved=False,
        user_id="u1",
    )
    assert r.terminal == "rejected"
    assert "hitl.rejected" in r.events


def test_agent_loop_deny_tool_not_in_grant():
    repo = InMemoryJournalRepository()
    j = SessionJournal.resume("agent3", repo)
    j.append("message", {"role": "user", "content": "建缺陷 x"})

    class ForceDefectPlanner:
        def decide(self, *, context, grant, step, tools_called, pending_hitl=False):
            return PlannerDecision(
                PlannerAction.TOOL_CALL,
                tool_id="connector.defect.create",
                tool_args={"title": "x"},
            )

    loop = _loop()
    loop.planner = ForceDefectPlanner()
    result = loop.run(
        journal=j,
        need="建缺陷",
        org_domains=["eng"],
        scenario="dialog",
        tool_allowlist=["connector.task.create"],
    )
    assert result.terminal == "failed"
    assert any("pretool.denied" in e for e in result.events)


def test_agent_loop_max_steps_exceeded():
    repo = InMemoryJournalRepository()
    j = SessionJournal.resume("agent4", repo)
    j.append("message", {"role": "user", "content": "x"})

    class AlwaysToolPlanner:
        def decide(self, *, context, grant, step, tools_called, pending_hitl=False):
            tid = grant.granted_ids[0] if grant.granted_ids else "connector.defect.create"
            return PlannerDecision(
                PlannerAction.TOOL_CALL,
                tool_id=tid,
                tool_args={"title": "loop"},
            )

    loop = _loop(max_steps=2)
    loop.planner = AlwaysToolPlanner()
    j.append("message", {"role": "user", "content": "建缺陷 loop"})
    result = loop.run(
        journal=j,
        need="建缺陷",
        org_domains=["eng"],
        scenario="dialog",
        tool_allowlist=["connector.defect.create"],
    )
    assert result.terminal == "failed"
    assert "max_steps.exceeded" in result.events
    assert result.tool_calls == 2


def test_pretool_deny_not_in_grant():
    ok, reason = deny_first_pre_tool_hook(
        "connector.evil",
        {},
        DiscoveryGrant(granted_ids=["connector.task.create"], ranked_summaries=[]),
    )
    assert not ok
    assert "grant" in reason


def test_resume_allowlist_cannot_expand_beyond_suspend_grant():
    """resume = 当前 allowlist ∩ suspend 时 discovery grant；不得扩大。"""
    repo = InMemoryJournalRepository()
    j = SessionJournal.resume("agent5", repo)
    j.append("message", {"role": "user", "content": "建任务需要人工确认"})
    loop = _loop()
    loop.run(
        journal=j,
        need="建任务人工确认",
        org_domains=["eng"],
        scenario="dialog",
        tool_allowlist=["connector.task.create"],
    )
    suspend = j.pending_suspend()
    assert suspend is not None
    assert "connector.task.create" in suspend.get("discovery_grant_ids", [])

    from app.agents.bounded_loop import resolve_resume_allowlist

    narrowed = resolve_resume_allowlist(
        suspend_payload=suspend,
        policy_allowlist=["connector.defect.create", "connector.task.create"],
        default_policy=loop.default_policy_allowlist,
    )
    assert narrowed == ["connector.task.create"]
    assert "connector.defect.create" not in narrowed
