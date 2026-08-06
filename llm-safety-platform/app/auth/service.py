"""Virtual keys, RBAC roles, OIDC/dev admin auth."""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import VirtualKeyRow, get_session

ROLES = ("Admin", "Security", "AppOwner", "Auditor")


def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class Principal:
    subject: str
    roles: list[str]
    tenant_id: str | None = None
    app_id: str | None = None
    vk: VirtualKeyRow | None = None
    kind: str = "admin"  # admin|vk


class VirtualKeyService:
    def create(
        self,
        db: Session,
        *,
        tenant_id: str,
        app_id: str,
        name: str = "",
        model_allowlist: list[str] | None = None,
        rpm_limit: int | None = None,
        budget_tokens: int = 1_000_000,
    ) -> tuple[str, VirtualKeyRow]:
        raw = "vk_" + secrets.token_urlsafe(24)
        row = VirtualKeyRow(
            key_id="kid_" + uuid.uuid4().hex[:12],
            key_hash=hash_key(raw),
            tenant_id=tenant_id,
            app_id=app_id,
            name=name or f"{app_id}-key",
            model_allowlist_json=json.dumps(model_allowlist or ["mock-llm"]),
            rpm_limit=rpm_limit or settings.default_rpm,
            budget_tokens=budget_tokens,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return raw, row

    def resolve(self, db: Session, raw: str) -> VirtualKeyRow:
        row = (
            db.query(VirtualKeyRow)
            .filter(VirtualKeyRow.key_hash == hash_key(raw), VirtualKeyRow.revoked.is_(False))
            .one_or_none()
        )
        if row is None:
            raise HTTPException(status_code=401, detail="invalid virtual key")
        return row

    def revoke(self, db: Session, key_id: str) -> None:
        row = db.query(VirtualKeyRow).filter(VirtualKeyRow.key_id == key_id).one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="key not found")
        row.revoked = True
        db.commit()

    def list_keys(self, db: Session, tenant_id: str | None = None) -> list[VirtualKeyRow]:
        q = db.query(VirtualKeyRow)
        if tenant_id:
            q = q.filter(VirtualKeyRow.tenant_id == tenant_id)
        return list(q.order_by(VirtualKeyRow.id.desc()).all())


vk_service = VirtualKeyService()


def _parse_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    return authorization.split(" ", 1)[1].strip()


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def require_vk(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Principal:
    token = _parse_bearer(authorization)
    if not token.startswith("vk_"):
        raise HTTPException(status_code=401, detail="virtual key required")
    row = vk_service.resolve(db, token)
    return Principal(
        subject=row.key_id,
        roles=["AppCaller"],
        tenant_id=row.tenant_id,
        app_id=row.app_id,
        vk=row,
        kind="vk",
    )


def require_admin(
    authorization: str | None = Header(default=None),
    x_roles: str | None = Header(default=None, alias="X-Roles"),
) -> Principal:
    """OIDC disabled → admin_token; enabled → JWKS-validated JWT (fail-closed when OIDC_REQUIRED=1)."""
    token = _parse_bearer(authorization)
    if settings.oidc_disabled and not settings.oidc_required:
        if token != settings.admin_token:
            raise HTTPException(status_code=401, detail="invalid admin token")
        roles = [r.strip() for r in (x_roles or "Admin,Security,AppOwner,Auditor").split(",") if r.strip()]
        return Principal(subject="admin-dev", roles=roles, kind="admin")

    # JWT / JWKS path (ADR-015 / ADR-025)
    from app.auth.oidc import validate_jwt

    claims = validate_jwt(token)
    roles = [r for r in claims.roles if r in ROLES]
    # Optional header merge only when claim roles empty (legacy proxy adapter)
    if not roles and x_roles:
        roles = [r.strip() for r in x_roles.split(",") if r.strip() in ROLES]
    if not roles:
        raise HTTPException(status_code=403, detail="no rbac role")
    return Principal(subject=claims.subject or "oidc-user", roles=roles, kind="admin")


def require_roles(*needed: str):
    def _dep(principal: Principal = Depends(require_admin)) -> Principal:
        if not set(needed) & set(principal.roles) and "Admin" not in principal.roles:
            raise HTTPException(status_code=403, detail=f"requires roles {needed}")
        return principal

    return _dep
