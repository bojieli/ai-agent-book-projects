"""Application bootstrap — DB seed + shared gateway services."""

from __future__ import annotations

import json
from pathlib import Path

from app.approvals import ApprovalWorkbench
from app.auth import vk_service
from app.db import get_session, init_db
from app.db.models import AuditDecisionRow, PolicyBindingRow
from app.observability.chain_verify import ChainIntegrityError, hydrate_ledger_from_rows, verify_audit_rows
from app.gateway import SafetyGateway
from app.observability import HashChainLedger, metrics, siem
from app.policy import PolicyEngine
from app.providers import ModelProxy
from app.quota import QuotaService
from app.redteam import RedTeamRunner, ReleaseEvaluator
from app.scanners import ScannerOrchestrator
from app.tool_runtime import ToolRuntime
from app.vault import Vault

ROOT = Path(__file__).resolve().parents[1]


class AppState:
    def __init__(self) -> None:
        init_db()
        self.chain_ok = True
        self.chain_error: dict | None = None
        self.policy = PolicyEngine()
        self.policy.load_yaml_dir()
        self._persist_policies()
        self.vault = Vault()
        self.tools = ToolRuntime()
        self.tools.register_defaults()
        self.ledger = HashChainLedger()
        self._hydrate_ledger_from_db()
        provider = _ProviderAdapter(ModelProxy())
        self.gateway = SafetyGateway(
            policy=self.policy,
            vault=self.vault,
            tools=self.tools,
            ledger=self.ledger,
            scanners=ScannerOrchestrator(),
            provider=provider,  # type: ignore[arg-type]
        )
        self.quota = QuotaService()
        self.approvals = ApprovalWorkbench()
        self.redteam = RedTeamRunner()
        self.evaluator = ReleaseEvaluator()
        self.metrics = metrics
        self.siem = siem
        from app.governance import CorpusAdmissionService

        self.corpus = CorpusAdmissionService()
        self._ensure_demo_vk()

    def _hydrate_ledger_from_db(self) -> None:
        """跨重启：验证 DB 链拓扑后 hydrate；损坏则 fail-closed（readyz 503，禁止续链）。"""
        db = get_session()
        try:
            rows = db.query(AuditDecisionRow).all()
            chained = [r for r in rows if (r.chain_hash or "").strip()]
            if not chained:
                return
            result = verify_audit_rows(rows)
            if not result.get("ok"):
                self.chain_ok = False
                self.chain_error = result
                return
            hydrate_ledger_from_rows(self.ledger, rows)
        except ChainIntegrityError as exc:
            self.chain_ok = False
            self.chain_error = exc.result
        finally:
            db.close()

    def _persist_policies(self) -> None:
        db = get_session()
        try:
            for (tenant, app), hist in self.policy.store._by_app.items():  # noqa: SLF001
                for b in hist:
                    exists = (
                        db.query(PolicyBindingRow)
                        .filter_by(
                            tenant_id=tenant,
                            app_id=app,
                            version=b.version,
                        )
                        .one_or_none()
                    )
                    if exists:
                        continue
                    db.add(
                        PolicyBindingRow(
                            policy_binding_id=b.policy_binding_id,
                            tenant_id=b.tenant_id,
                            app_id=b.app_id,
                            version=b.version,
                            reason=b.reason,
                            risk_tier=b.risk_tier,
                            fail_mode=b.fail_mode,
                            effect_cap=b.effect_cap,
                            body_json=json.dumps(b.to_dict(), ensure_ascii=False),
                            require_dual_publish=b.risk_tier == "critical",
                        )
                    )
            db.commit()
        finally:
            db.close()

    def _ensure_demo_vk(self) -> None:
        db = get_session()
        try:
            from app.db.models import VirtualKeyRow

            if db.query(VirtualKeyRow).count() == 0:
                raw, _ = vk_service.create(
                    db,
                    tenant_id="t_demo",
                    app_id="customer_bot",
                    name="demo-customer-bot",
                    model_allowlist=["mock-llm"],
                )
                (ROOT / "data").mkdir(exist_ok=True)
                (ROOT / "data" / "demo_vk.txt").write_text(raw, encoding="utf-8")
        finally:
            db.close()


class _ProviderAdapter:
    """Adapt ModelProxy.chat(tuple) to gateway's str-returning provider."""

    def __init__(self, proxy: ModelProxy) -> None:
        self.id = "mock-llm"
        self.proxy = proxy
        self.last_meta: dict = {}

    def chat(self, messages: list[dict[str, str]], **kwargs):  # noqa: ANN003
        text, meta = self.proxy.chat(messages, model=kwargs.get("model", "mock-llm"))
        self.last_meta = meta
        return text


_STATE: AppState | None = None


def get_state() -> AppState:
    global _STATE
    if _STATE is None:
        _STATE = AppState()
    return _STATE
