"""SQLAlchemy models + engine (Postgres in prod, SQLite for local/CI)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PolicyBindingRow(Base):
    __tablename__ = "policy_bindings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    policy_binding_id: Mapped[str] = mapped_column(String(128), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    app_id: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(64))
    risk_tier: Mapped[str] = mapped_column(String(16))
    fail_mode: Mapped[str] = mapped_column(String(16))
    effect_cap: Mapped[str] = mapped_column(String(16))
    body_json: Mapped[str] = mapped_column(Text)
    require_dual_publish: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class VirtualKeyRow(Base):
    __tablename__ = "virtual_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    key_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    app_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128), default="")
    model_allowlist_json: Mapped[str] = mapped_column(Text, default="[]")
    rpm_limit: Mapped[int] = mapped_column(Integer, default=120)
    budget_tokens: Mapped[int] = mapped_column(Integer, default=1_000_000)
    spent_tokens: Mapped[int] = mapped_column(Integer, default=0)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AuditDecisionRow(Base):
    __tablename__ = "audit_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    app_id: Mapped[str] = mapped_column(String(64), index=True)
    decision: Mapped[str] = mapped_column(String(32))
    body_json: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(128))
    chain_hash: Mapped[str] = mapped_column(String(128), default="")
    prev_chain_hash: Mapped[str] = mapped_column(String(128), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EventRow(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    app_id: Mapped[str] = mapped_column(String(64), index=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    body_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ApprovalRow(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    approval_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    app_id: Mapped[str] = mapped_column(String(64), index=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    action_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|approved|rejected|expired
    decided_by: Mapped[str] = mapped_column(String(128), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RedTeamRunRow(Base):
    __tablename__ = "redteam_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    suite: Mapped[str] = mapped_column(String(64))  # promptfoo|garak|pyrit|shim
    status: Mapped[str] = mapped_column(String(32), default="completed")
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    report_json: Mapped[str] = mapped_column(Text, default="{}")
    leak_rate: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class VaultEntryRow(Base):
    __tablename__ = "vault_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    pii_type: Mapped[str] = mapped_column(String(32))
    ciphertext: Mapped[str] = mapped_column(Text)
    nonce: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PublishGateRow(Base):
    __tablename__ = "publish_gates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gate_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64))
    app_id: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    security_approved_by: Mapped[str] = mapped_column(String(128), default="")
    owner_approved_by: Mapped[str] = mapped_column(String(128), default="")
    eval_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    body_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


_engine = None
SessionLocal = None


def get_engine():
    global _engine, SessionLocal
    if _engine is None:
        url = settings.database_url
        if url.startswith("sqlite"):
            Path("data").mkdir(parents=True, exist_ok=True)
            _engine = create_engine(url, connect_args={"check_same_thread": False})

            @event.listens_for(_engine, "connect")
            def _fk(dbapi_conn, _):  # noqa: ANN001
                dbapi_conn.execute("PRAGMA foreign_keys=ON")
        else:
            _engine = create_engine(url, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def init_db() -> None:
    eng = get_engine()
    Base.metadata.create_all(bind=eng)
    from app.db.migrate import upgrade_audit_chain

    upgrade_audit_chain(eng)


def get_session():
    get_engine()
    assert SessionLocal is not None
    return SessionLocal()
