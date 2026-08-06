"""M4 R1 旗舰闭环演示：技术评审 → HITL → 缺陷 → 企微 → webhook 关闭 → 下一场 briefing。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.bff import BffApp
from app.connectors.jira_simulator import JiraSimulator
from app.connectors.mock_saas import MockJiraConnector, MockWeComClient
from app.connectors.persistent_defect import PersistentDefectConnector
from app.orchestrator import Orchestrator
from app.store.meetings import MeetingDraft


def main() -> int:
    series_id = "series_r1_flagship"
    meeting_a = "mtg_r1_flagship_a"
    meeting_b = "mtg_r1_flagship_b"

    orch = Orchestrator(ROOT, allow_draft_skills=True)
    # 使用独立 series，避免 seed_demo 的 series_pay 干扰
    out_a = orch.bind_and_run(
        scenario_code="tech_review",
        meeting_id=meeting_a,
        series_id=series_id,
        hitl_passed=True,
    )
    pipe_a = out_a["pipeline"]
    work_objects = pipe_a.get("work_objects") or []
    if pipe_a.get("terminal") != "succeeded" or not work_objects:
        print(json.dumps({"ok": False, "stage": "meeting_a", "out": out_a}, ensure_ascii=False))
        return 1

    wo = work_objects[0]
    idem_key = wo.get("idempotency_key", "")
    item_id = f"{meeting_a}_open"

    # 企微可追踪通知（msgid）
    wecom = MockWeComClient()
    wx = wecom.send_markdown(
        touser=["u_pm"],
        content=f"**技术评审** 已创建缺陷 `{wo.get('external_id')}`",
        meeting_id=meeting_a,
    )

    # Jira 幂等：同 idempotency_key 不重复建单
    defect_store = PersistentDefectConnector(ROOT / "data" / "r1_flagship_defects.json")
    jira = MockJiraConnector(backend=defect_store, simulator=JiraSimulator(backend=defect_store))
    j1 = jira.execute({"title": "接口超时缺陷", "idempotency_key": idem_key, "project": "ENG"})
    j2 = jira.execute({"title": "接口超时缺陷", "idempotency_key": idem_key, "project": "ENG"})
    idempotent_ok = j1.get("external_id") == j2.get("external_id")

    # webhook 关闭 Work Object Link + Continuum
    bff = BffApp(ROOT)
    bff.knowledge = orch.knowledge
    draft = MeetingDraft(
        meeting_id=meeting_a,
        org_domains=["eng"],
        scenario_code="tech_review",
        purpose="R1 旗舰闭环 A",
        success_criteria="",
        created_by="u_pm",
        idempotency_key=f"idem_{meeting_a}",
        series_id=series_id,
        participants=["u_dev_a", "u_pm"],
        work_objects=[dict(wo)],
    )
    bff.store.create(draft)
    wh = bff.internal_connector_webhook(
        "svc_connector",
        {
            "meeting_id": meeting_a,
            "work_object_id": wo.get("work_object_id"),
            "status": "closed",
            "external_id": wo.get("external_id"),
            "series_id": series_id,
            "item_id": item_id,
        },
    )

    # 下一场会议：briefing 不再召回已关闭事项
    brief_before_b = orch.dialog.briefing(
        user_id="u_pm",
        org_domains=["eng"],
        query="超时 阻塞",
        series_id=series_id,
    )
    closed_item_absent = all(i.get("item_id") != item_id for i in (brief_before_b.series_open_items or []))

    out_b = orch.bind_and_run(
        scenario_code="tech_review",
        meeting_id=meeting_b,
        series_id=series_id,
        hitl_passed=True,
    )
    brief_after_b = orch.dialog.briefing(
        user_id="u_pm",
        org_domains=["eng"],
        query="超时 阻塞",
        series_id=series_id,
    )
    # 已关闭的 A 会事项不应再出现
    closed_still_absent = all(
        i.get("item_id") != item_id for i in (brief_after_b.series_open_items or [])
    )

    result = {
        "ok": True,
        "series_id": series_id,
        "meeting_a": {
            "meeting_id": meeting_a,
            "terminal": pipe_a.get("terminal"),
            "work_object_id": wo.get("work_object_id"),
            "idempotency_key": idem_key,
            "events": pipe_a.get("events"),
        },
        "wecom": {"msgid": wx.get("msgid"), "ok": wx.get("ok")},
        "jira_idempotent": idempotent_ok,
        "jira_external_id": j1.get("external_id"),
        "webhook": wh,
        "briefing_before_b": {
            "open_count": brief_before_b.series_open_count,
            "closed_item_absent": closed_item_absent,
        },
        "meeting_b": {
            "meeting_id": meeting_b,
            "terminal": out_b["pipeline"].get("terminal"),
            "briefing_open_count": brief_after_b.series_open_count,
            "closed_still_absent": closed_still_absent,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    ok = (
        pipe_a.get("terminal") == "succeeded"
        and wx.get("ok")
        and wx.get("msgid")
        and idempotent_ok
        and wh.get("continuum_closed") is True
        and closed_item_absent
        and closed_still_absent
        and out_b["pipeline"].get("terminal") == "succeeded"
        and "hitl.resolved" in (pipe_a.get("events") or [])
    )
    if not ok:
        print("R1_FLAGSHIP_LOOP FAILED", file=sys.stderr)
        return 1
    print("R1_FLAGSHIP_LOOP PASSED", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
