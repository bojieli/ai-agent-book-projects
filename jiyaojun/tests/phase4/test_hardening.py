"""Phase 4: multi-connector register, glossary admin, rate limit, chaos."""

from __future__ import annotations

from pathlib import Path

from app.connectors.departments import department_connectors
from app.connectors.persistent_defect import PersistentDefectConnector
from app.events.enums import PRODUCTION_EFFECT_RANK
from app.governance.glossary_admin import GlossaryAdmin
from app.harness import ToolRuntime
from app.knowledge.glossary import GlossaryEntry
from app.ops.chaos import ChaosProxy
from app.runtime.full import FullRuntime
from app.security.hardening import RateLimiter, redact_text

ROOT = Path(__file__).resolve().parents[2]


def test_register_department_connectors_without_orchestrator_change():
    rt = ToolRuntime()
    before = set(rt._tools)
    for c in department_connectors():
        rt.register(c)
    after = set(rt._tools)
    assert after - before >= {
        "connector.limit_draft.create",
        "connector.policy_draft.create",
        "connector.remediation_ledger.upsert",
    }
    # discover under draft_only excludes production
    discovered = rt.discover(None, "draft_only", PRODUCTION_EFFECT_RANK)
    assert "connector.limit_draft.create" in discovered


def test_glossary_admin_approve():
    admin = GlossaryAdmin()
    admin.submit(GlossaryEntry("eng", "半成功", "部分写回成功需补偿", "draft"))
    approved = admin.approve("eng", "半成功", "approver")
    assert approved.governance_status == "approved"
    hits = admin.store.lookup("半成功", ["eng"])
    assert hits and hits[0].governance_status == "approved"


def test_rate_limiter_blocks():
    rl = RateLimiter(max_per_window=3, window_sec=60)
    assert rl.allow("u1")
    assert rl.allow("u1")
    assert rl.allow("u1")
    assert rl.allow("u1") is False


def test_redact_sensitive():
    s = redact_text("联系 13812345678 或 a@b.com")
    assert "[PHONE]" in s and "[EMAIL]" in s


def test_chaos_timeout_then_success(tmp_path: Path):
    inner = PersistentDefectConnector(tmp_path / "c.json")
    proxy = ChaosProxy(inner, timeout_next=1)
    rt = ToolRuntime()
    rt._tools[proxy.id] = proxy
    try:
        rt.call(
            proxy.id,
            "m",
            {"title": "x", "idempotency_key": "c1"},
            allowlist=[proxy.id],
            max_effect="draft_only",
            effect_rank=PRODUCTION_EFFECT_RANK,
        )
        assert False, "expected timeout"
    except TimeoutError:
        pass
    # retry succeeds
    out = rt.call(
        proxy.id,
        "m",
        {"title": "x", "idempotency_key": "c1"},
        allowlist=[proxy.id],
        max_effect="draft_only",
        effect_rank=PRODUCTION_EFFECT_RANK,
    )
    assert out["external_id"]


def test_phase4_hr_critical_no_embed(tmp_path: Path):
    rt = FullRuntime(ROOT)
    rt.store = __import__("app.store.meetings", fromlist=["MeetingStore"]).MeetingStore(
        tmp_path / "m.json"
    )
    from app.schedule.service import ScheduleService

    rt.schedule = ScheduleService(rt.store, rt.calendar, rt.events)
    out = rt.run_meeting_lifecycle(
        event_id="cal_hr_001",
        purpose="绩效校准",
        idempotency_key=f"hr-{tmp_path.name}",
        user_id="u_hrbp",
        segments=["这个先放到 M 档", "不要外传"],
        hitl_approve=True,
        allowlist=None,
    )
    assert out["stage"] == "critical_no_embed"
    assert all(d.get("suppressed") for d in out["deliveries"])


def test_phase4_x1_ambiguity_resolve(tmp_path: Path):
    rt = FullRuntime(ROOT)
    rt.store = __import__("app.store.meetings", fromlist=["MeetingStore"]).MeetingStore(
        tmp_path / "m.json"
    )
    from app.schedule.service import ScheduleService

    rt.schedule = ScheduleService(rt.store, rt.calendar, rt.events)
    rt.defect = PersistentDefectConnector(tmp_path / "defects.json")
    rt.runtime.register(rt.defect)
    from app.connectors.work_embed import WorkEmbedService

    rt.work_embed = WorkEmbedService(rt.runtime, rt.events)
    out = rt.run_meeting_lifecycle(
        event_id="cal_x1_001",
        purpose="业务科技灰度对齐",
        idempotency_key=f"x1-{tmp_path.name}",
        user_id="u_pm",
        segments=["我说的灰度是发布灰度，你补齐 canary 文档"],
        hitl_approve=True,
    )
    assert "ambiguity.opened" in out["events"]
    assert "ambiguity.resolved" in out["events"]
    assert out["stage"] == "succeeded"
