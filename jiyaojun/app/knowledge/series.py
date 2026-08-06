"""Meeting series continuum — open items carry across meetings (ACL-aware)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SeriesOpenItem:
    item_id: str
    title: str
    status: str = "open"
    source_meeting_id: str = ""
    org_domain: str = "eng"
    classification: str = "internal"
    write_class: str = "wide"
    acl_principals: list[str] = field(default_factory=lambda: ["u_pm"])

    def visible_to(self, *, user_id: str, org_domains: list[str]) -> bool:
        """briefing 可见性：none 永不返回；须 ACL + org 域匹配。"""
        if self.write_class == "none" or self.status != "open":
            return False
        if user_id not in self.acl_principals:
            return False
        if self.org_domain not in org_domains:
            return False
        if self.classification == "critical" and self.write_class not in {"sealed", "none"}:
            return False
        return True

    def to_briefing_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "title": self.title,
            "status": self.status,
            "source_meeting_id": self.source_meeting_id,
            "org_domain": self.org_domain,
            "classification": self.classification,
            "write_class": self.write_class,
        }


@dataclass
class MeetingSeriesStore:
    series: dict[str, list[SeriesOpenItem]] = field(default_factory=dict)

    def add_open(self, series_id: str, item: SeriesOpenItem) -> None:
        self.series.setdefault(series_id, []).append(item)

    def list_open(self, series_id: str) -> list[SeriesOpenItem]:
        return [i for i in self.series.get(series_id, []) if i.status == "open"]

    def list_open_for_user(
        self,
        series_id: str,
        *,
        user_id: str,
        org_domains: list[str],
    ) -> list[SeriesOpenItem]:
        return [i for i in self.list_open(series_id) if i.visible_to(user_id=user_id, org_domains=org_domains)]

    def close(self, series_id: str, item_id: str) -> None:
        """兼容旧 API：将 open item 标为 done。"""
        self.close_open_item(series_id, item_id)

    def close_open_item(self, series_id: str, item_id: str) -> bool:
        """从 open 列表关闭：status 置为 closed，briefing 不再召回。"""
        for i in self.series.get(series_id, []):
            if i.item_id == item_id and i.status == "open":
                i.status = "closed"
                return True
        return False

    def briefing_payload(
        self,
        series_id: str,
        *,
        user_id: str,
        org_domains: list[str],
    ) -> dict[str, Any]:
        opens = self.list_open_for_user(series_id, user_id=user_id, org_domains=org_domains)
        return {
            "series_id": series_id,
            "open_count": len(opens),
            "open_items": [i.to_briefing_dict() for i in opens],
        }
