"""Meeting series ↔ KnowledgePlane Continuum 桥接（写入前校验，briefing ACL 过滤）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.knowledge.series import MeetingSeriesStore, SeriesOpenItem

if TYPE_CHECKING:
    from app.knowledge.plane import KnowledgePlane


class SeriesContinuumBridge:
    """统一跨会 open items：仅 accepted 项进入 SeriesStore；Continuum 与 briefing 同源 ACL。"""

    def __init__(
        self,
        knowledge: KnowledgePlane,
        series_store: MeetingSeriesStore | None = None,
    ) -> None:
        self.knowledge = knowledge
        self.series = series_store or MeetingSeriesStore()

    def sync_open_items_to_continuum(
        self,
        series_id: str,
        *,
        org_domain: str | None = None,
        classification: str | None = None,
        write_class: str | None = None,
        acl_principals: list[str] | None = None,
    ) -> int:
        """将 SeriesStore 中 open 项索引到 Continuum；`none` 项跳过；使用项自带元数据。"""
        from app.knowledge.plane import ContinuumItem

        existing = {c.id for c in self.knowledge.continuum}
        indexed = 0
        for item in self.series.list_open(series_id):
            wc = item.write_class if write_class is None else write_class
            if wc == "none" or item.write_class == "none":
                continue
            org = item.org_domain if org_domain is None else org_domain
            cls = item.classification if classification is None else classification
            principals = item.acl_principals if acl_principals is None else acl_principals
            dec = self.knowledge.decide_continuum_write(
                classification=cls,
                requested_write_class=wc,
            )
            if not dec.accepted:
                continue
            cid = f"series_{series_id}_{item.item_id}"
            if cid in existing:
                continue
            cont = ContinuumItem(
                id=cid,
                org_domain=org,
                classification=cls,
                write_class=dec.write_class,
                acl_principals=principals,
                summary=item.title,
                open=True,
                meeting_id=item.source_meeting_id or cid,
                series_id=series_id,
            )
            wdec = self.knowledge.write_continuum_and_index(cont, classification=cls)
            if wdec.accepted:
                indexed += 1
                existing.add(cid)
        return indexed

    def write_open_item(
        self,
        *,
        series_id: str,
        item_id: str,
        title: str,
        source_meeting_id: str,
        org_domain: str,
        classification: str,
        write_class: str,
        acl_principals: list[str],
    ) -> bool:
        """先校验 Continuum 写入策略；拒绝则**不**进入 SeriesStore（防 briefing 泄露）。"""
        from app.knowledge.plane import ContinuumItem

        if write_class == "none":
            return False

        dec = self.knowledge.decide_continuum_write(
            classification=classification,
            requested_write_class=write_class,
        )
        if not dec.accepted:
            return False

        cid = f"series_{series_id}_{item_id}"
        wdec = self.knowledge.write_continuum_and_index(
            ContinuumItem(
                id=cid,
                org_domain=org_domain,
                classification=classification,
                write_class=dec.write_class,
                acl_principals=acl_principals,
                summary=title,
                open=True,
                meeting_id=source_meeting_id,
                series_id=series_id,
            ),
            classification=classification,
        )
        if not wdec.accepted:
            return False

        self.series.add_open(
            series_id,
            SeriesOpenItem(
                item_id=item_id,
                title=title,
                source_meeting_id=source_meeting_id,
                org_domain=org_domain,
                classification=classification,
                write_class=dec.write_class,
                acl_principals=list(acl_principals),
            ),
        )
        return True

    def briefing_open_items(
        self,
        series_id: str,
        *,
        user_id: str,
        org_domains: list[str],
    ) -> list[dict]:
        """按 user / org / ACL / write_class 过滤；`none` 与未授权项不返回。"""
        items = self.series.list_open_for_user(
            series_id, user_id=user_id, org_domains=org_domains
        )
        return [i.to_briefing_dict() for i in items]

    def close_open_item(self, series_id: str, item_id: str) -> bool:
        """关闭跨会 open item：SeriesStore 移除 open 状态，Continuum 标记 closed。"""
        if not self.series.close_open_item(series_id, item_id):
            return False
        continuum_id = f"series_{series_id}_{item_id}"
        self.knowledge.close_continuum_item(continuum_id)
        return True
