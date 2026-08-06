"""Mock SSO / AuthZ — every write audited."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class Principal:
    user_id: str
    roles: list[str]
    org_domains: list[str]


@dataclass
class AuditEntry:
    actor: str
    action: str
    resource: str
    ok: bool
    detail: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)


class MockAuthZ:
    def __init__(self) -> None:
        self.audit: list[AuditEntry] = []
        self.principals: dict[str, Principal] = {
            "u_pm": Principal("u_pm", ["user"], ["eng"]),
            "u_hrbp": Principal("u_hrbp", ["user", "hr"], ["hr"]),
            "u_admin": Principal("u_admin", ["admin"], ["eng", "business", "hr", "risk", "compliance"]),
            "svc_transcript": Principal("svc_transcript", ["service"], ["*"]),
            "svc_connector": Principal("svc_connector", ["service"], ["*"]),
        }

    def authenticate(self, token: str) -> Principal:
        # mock: token == user_id
        if token not in self.principals:
            self.audit.append(AuditEntry(token, "auth", "token", False))
            raise PermissionError("invalid token")
        p = self.principals[token]
        self.audit.append(AuditEntry(p.user_id, "auth", "token", True))
        return p

    def authorize(self, principal: Principal, action: str, resource: str, *, org_domain: str | None = None) -> bool:
        ok = True
        if action.startswith("admin.") and "admin" not in principal.roles:
            ok = False
        if org_domain and org_domain != "*" and "*" not in principal.org_domains:
            if org_domain not in principal.org_domains and "admin" not in principal.roles:
                ok = False
        if resource.startswith("artifact:critical") and "hr" not in principal.roles and "admin" not in principal.roles:
            ok = False
        self.audit.append(AuditEntry(principal.user_id, action, resource, ok, {"org_domain": org_domain}))
        if not ok:
            raise PermissionError(f"denied {action} on {resource}")
        return True
