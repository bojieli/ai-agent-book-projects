"""Render plane: acl_view FIRST, then template. Critical without allowlist → skip."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


@dataclass
class AclView:
    view_id: str
    meeting_id: str
    recipient_ids: list[str]
    artifacts: list[dict[str, Any]]
    empty: bool = False


@dataclass
class RenderResult:
    status: str  # completed | skipped
    render_job_id: str
    acl_view_id: str
    skip_reason: str | None = None
    html: str | None = None
    format: str = "email_html"


class RenderService:
    def __init__(self, template_dir: Path) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml", "j2"]),
        )

    def materialize_acl_view(
        self,
        *,
        view_id: str,
        meeting_id: str,
        artifacts: list[dict[str, Any]],
        viewer_ids: list[str],
        classification: str,
        allowlist: list[str] | None,
    ) -> AclView:
        if classification == "critical":
            if not allowlist:
                return AclView(
                    view_id=view_id,
                    meeting_id=meeting_id,
                    recipient_ids=[],
                    artifacts=[],
                    empty=True,
                )
            recipients = [u for u in viewer_ids if u in allowlist]
            if not recipients:
                return AclView(
                    view_id=view_id,
                    meeting_id=meeting_id,
                    recipient_ids=[],
                    artifacts=[],
                    empty=True,
                )
            return AclView(
                view_id=view_id,
                meeting_id=meeting_id,
                recipient_ids=recipients,
                artifacts=artifacts,
            )
        return AclView(
            view_id=view_id,
            meeting_id=meeting_id,
            recipient_ids=viewer_ids,
            artifacts=artifacts,
        )

    def render_email(
        self,
        *,
        job_id: str,
        acl_view: AclView,
        classification: str,
        allowlist: list[str] | None,
        template_name: str = "email_html.j2",
        context: dict[str, Any] | None = None,
    ) -> RenderResult:
        if classification == "critical" and not allowlist:
            return RenderResult(
                status="skipped",
                render_job_id=job_id,
                acl_view_id=acl_view.view_id,
                skip_reason="critical_no_allowlist",
            )
        if acl_view.empty:
            return RenderResult(
                status="skipped",
                render_job_id=job_id,
                acl_view_id=acl_view.view_id,
                skip_reason="empty_view",
            )
        tpl = self.env.get_template(template_name)
        html = tpl.render(**(context or {"artifacts": acl_view.artifacts}))
        return RenderResult(
            status="completed",
            render_job_id=job_id,
            acl_view_id=acl_view.view_id,
            html=html,
        )
