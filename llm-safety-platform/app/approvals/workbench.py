"""HITL Approval workbench."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import ApprovalRow


class ApprovalWorkbench:
    def enqueue(
        self,
        db: Session,
        *,
        tenant_id: str,
        app_id: str,
        request_id: str,
        action: dict[str, Any],
    ) -> ApprovalRow:
        row = ApprovalRow(
            approval_id="apr_" + uuid.uuid4().hex[:12],
            tenant_id=tenant_id,
            app_id=app_id,
            request_id=request_id,
            action_json=json.dumps(action, ensure_ascii=False),
            status="pending",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def decide(
        self, db: Session, approval_id: str, *, approve: bool, actor: str
    ) -> ApprovalRow:
        row = db.query(ApprovalRow).filter(ApprovalRow.approval_id == approval_id).one_or_none()
        if row is None:
            raise KeyError(approval_id)
        if row.status != "pending":
            raise ValueError("already decided")
        row.status = "approved" if approve else "rejected"
        row.decided_by = actor
        db.commit()
        db.refresh(row)
        return row

    def list_pending(self, db: Session, tenant_id: str | None = None) -> list[ApprovalRow]:
        q = db.query(ApprovalRow).filter(ApprovalRow.status == "pending")
        if tenant_id:
            q = q.filter(ApprovalRow.tenant_id == tenant_id)
        return list(q.order_by(ApprovalRow.id.desc()).all())
