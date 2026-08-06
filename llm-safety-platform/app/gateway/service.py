"""Safety Gateway — Online plane orchestration (L1–L4) + OWASP control hooks."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.config import settings
from app.decisions import max_strict
from app.events import DomainEvent, EventBus
from app.events import enums as E
from app.gateway.envelope import build_decision
from app.gateway.refusal import refusal_for_reasons
from app.observability import AuditLedger
from app.policy import PolicyEngine
from app.providers import MockModelProvider
from app.scanners import ScannerOrchestrator
from app.scanners.owasp_controls import system_prompt_hash
from app.tool_runtime import ToolRuntime
from app.vault import Vault


@dataclass
class GatewayResponse:
    request_id: str
    decision: str
    policy_binding_id: str
    policy_version: int
    messages: list[dict[str, str]]
    model_output: str | None
    tool_results: list[dict[str, Any]]
    safety_decision: dict[str, Any]
    blocked_reason: str | None = None
    events: list[str] = field(default_factory=list)
    refusal_message: str | None = None


class SafetyGateway:
    def __init__(
        self,
        policy: PolicyEngine | None = None,
        vault: Vault | None = None,
        tools: ToolRuntime | None = None,
        events: EventBus | None = None,
        ledger: AuditLedger | None = None,
        scanners: ScannerOrchestrator | None = None,
        provider: MockModelProvider | None = None,
    ) -> None:
        self.policy = policy or PolicyEngine()
        self.vault = vault or Vault()
        self.tools = tools or ToolRuntime()
        self.tools.register_defaults()
        self.events = events or EventBus()
        self.ledger = ledger or AuditLedger()
        self.scanners = scanners or ScannerOrchestrator()
        self.provider = provider or MockModelProvider()
        if self.policy.store.current("t_demo", "customer_bot") is None:
            self.policy.load_yaml_dir()

    def chat(
        self,
        *,
        tenant_id: str,
        app_id: str,
        user_content: str,
        invoke_model: bool = True,
        tool_calls: list[dict[str, Any]] | None = None,
        deanonymize_output: bool = True,
        system_prompt: str = "",
        rag_chunks: list[dict[str, Any]] | None = None,
        model_id: str | None = None,
        model_digest: str = "",
        session_id: str = "",
    ) -> GatewayResponse:
        t0 = time.perf_counter()
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        binding = self.policy.resolve(tenant_id, app_id)
        emitted: list[str] = []
        mid = model_id or getattr(self.provider, "id", "mock-llm")

        scan_extra: dict[str, Any] = {
            "system_prompt": system_prompt,
            "rag_chunks": list(rag_chunks or []),
            "grounding_required": binding.grounding_required,
            "model_id": mid,
            "model_allowlist": list(binding.model_allowlist),
            "model_digest": model_digest,
            "model_digests": list(binding.model_digests),
            "scanner_bundle_id": settings.scanner_mode + ":" + binding.scanner_bundle_id,
            "expected_scanner_bundle_id": settings.scanner_mode
            + ":"
            + binding.scanner_bundle_id,
            "session_id": session_id or "",
        }

        # L2a — system prompt integrity (LLM07)
        if binding.system_prompt_hash and system_prompt:
            if system_prompt_hash(system_prompt) != binding.system_prompt_hash:
                return self._finalize_block(
                    request_id,
                    tenant_id,
                    app_id,
                    binding,
                    user_content,
                    [],
                    t0,
                    emitted,
                    layer="L2",
                    extra_reasons=["system_prompt_hash_mismatch"],
                )

        # L1 (+ rag_gate / system_leak via policy scanners)
        d1, text1, r1 = self.scanners.run_input(
            user_content, binding, tenant_id, request_id, self.vault, extra=scan_extra
        )
        if d1 == "redact":
            self._emit(
                E.SAFETY_REDACTED,
                tenant_id,
                app_id,
                request_id,
                binding,
                {"tokens": self.vault.tokens_for_request(request_id)},
            )
            emitted.append(E.SAFETY_REDACTED)
        if d1 == "block":
            return self._finalize_block(
                request_id,
                tenant_id,
                app_id,
                binding,
                user_content,
                r1,
                t0,
                emitted,
                layer="L1",
            )

        # L2 — model allowlist / context budget / supply chain
        if mid not in binding.model_allowlist:
            return self._finalize_block(
                request_id,
                tenant_id,
                app_id,
                binding,
                user_content,
                r1,
                t0,
                emitted,
                layer="L2",
                extra_reasons=["model_not_allowlisted"],
            )
        if binding.model_digests and model_digest and model_digest not in binding.model_digests:
            return self._finalize_block(
                request_id,
                tenant_id,
                app_id,
                binding,
                user_content,
                r1,
                t0,
                emitted,
                layer="L2",
                extra_reasons=["model_digest_mismatch"],
            )
        if len(text1) // 4 > 100_000:
            return self._finalize_block(
                request_id,
                tenant_id,
                app_id,
                binding,
                user_content,
                r1,
                t0,
                emitted,
                layer="L2",
                extra_reasons=["context_budget"],
            )

        # Merge cleaned RAG into model context (LLM08)
        clean_chunks = list(scan_extra.get("rag_clean_texts") or [])
        if not clean_chunks and rag_chunks:
            # rag_gate may have been absent from policy — still filter inline
            from app.scanners.owasp_controls import RagGateScanner
            from app.policy.binding import ScannerSpec
            from app.scanners.base import ScanContext

            rg = RagGateScanner()
            ctx = ScanContext(
                tenant_id, request_id, self.vault, ScannerSpec("rag_gate", 0.5), scan_extra
            )
            rg.scan(text1, ctx)
            clean_chunks = list(scan_extra.get("rag_clean_texts") or [])
        context_prefix = ""
        if clean_chunks:
            # Spotlight / datamark untrusted RAG (ADR-021) — still scanned by rag_gate
            from app.gateway.spotlight import spotlight_rag_chunks

            context_prefix = spotlight_rag_chunks(clean_chunks, max_chunks=8)

        model_output: str | None = None
        r3: list = []
        d3 = "allow"
        out_text = ""
        if invoke_model:
            from app.gateway.dual_llm import dual_llm_enabled, run_dual_llm_path
            from app.gateway.spotlight import SPOTLIGHT_SYSTEM_HINT

            if dual_llm_enabled() or settings.dual_llm:
                dual = run_dual_llm_path(
                    text1,
                    spotlight_data=context_prefix,
                    provider_callable=lambda msgs: self.provider.chat(msgs),
                )
                if not dual.get("ok"):
                    return self._finalize_block(
                        request_id,
                        tenant_id,
                        app_id,
                        binding,
                        user_content,
                        list(r1),
                        t0,
                        emitted,
                        layer="L2",
                        extra_reasons=list(dual.get("reasons") or ["dual_llm_block"]),
                    )
                model_output = str(dual.get("output") or "")
                scan_extra["dual_llm"] = {
                    "intent": (dual.get("analyzer_intent") or {}).get("intent"),
                    "risk_flags": (dual.get("analyzer_intent") or {}).get("risk_flags"),
                }
            else:
                messages = []
                sys_content = system_prompt or ""
                if context_prefix:
                    sys_content = (
                        f"{sys_content}\n\n{SPOTLIGHT_SYSTEM_HINT}".strip()
                        if sys_content
                        else SPOTLIGHT_SYSTEM_HINT
                    )
                if sys_content:
                    messages.append({"role": "system", "content": sys_content})
                user_msg = text1 if not context_prefix else f"{context_prefix}\n\n用户问题：{text1}"
                messages.append({"role": "user", "content": user_msg})
                model_output = self.provider.chat(messages)
            d3, out_text, r3 = self.scanners.run_output(
                model_output,
                binding,
                tenant_id,
                request_id,
                self.vault,
                extra=scan_extra,
            )
            if d3 == "block":
                return self._finalize_block(
                    request_id,
                    tenant_id,
                    app_id,
                    binding,
                    user_content,
                    list(r1) + list(r3),
                    t0,
                    emitted,
                    layer="L3",
                    model_output=None,
                )
            if deanonymize_output:
                out_text = self.vault.deanonymize(out_text, tenant_id=tenant_id)
                model_output = out_text

        # L4 tools — denylist / allowlist / effect_cap / ToolRiskClassifier (ADR-019)
        tool_results: list[dict[str, Any]] = []
        from app.tool_runtime import ConfirmRequiredError

        for tc in tool_calls or []:
            tid = tc["name"]
            try:
                result = self.tools.call(
                    tid,
                    request_id,
                    tc.get("arguments") or {},
                    allowlist=binding.tool_allowlist,
                    effect_cap=binding.effect_cap,
                    denylist=binding.tool_denylist,
                    risk_rules=binding.tool_risk_rules,
                    email_domain_allowlist=binding.email_domain_allowlist,
                    idempotency_key=tc.get("idempotency_key"),
                )
                risk = result.pop("_risk", {}) if isinstance(result, dict) else {}
                # LLM06 — re-scan tool observation (narrow scanners only)
                obs = json.dumps(result, ensure_ascii=False) if isinstance(result, dict) else str(result)
                from app.policy.binding import ScannerSpec

                tool_specs = (
                    ScannerSpec("secrets", 0.5),
                    ScannerSpec("prompt_injection", 0.7),
                    ScannerSpec("indirect_injection", 0.7),
                    ScannerSpec("system_leak", 0.7),
                )
                d_tool, _, r_tool = self.scanners.run_layer(
                    layer="L4",
                    text=obs,
                    specs=tool_specs,
                    tenant_id=tenant_id,
                    request_id=request_id,
                    vault=self.vault,
                    extra={**scan_extra, "tool_observation": True},
                )
                if d_tool == "block":
                    self._emit(
                        E.TOOL_DENIED,
                        tenant_id,
                        app_id,
                        request_id,
                        binding,
                        {"tool_id": tid, "reason": "tool_result_unsafe"},
                    )
                    emitted.append(E.TOOL_DENIED)
                    return self._finalize_block(
                        request_id,
                        tenant_id,
                        app_id,
                        binding,
                        user_content,
                        list(r1) + list(r3) + list(r_tool),
                        t0,
                        emitted,
                        layer="L4",
                        extra_reasons=["tool_result_unsafe"],
                        model_output=model_output,
                    )
                tool_results.append({"tool_id": tid, "result": result, "risk": risk})
                if risk.get("decision") == "alert_only" or (
                    risk.get("op_risk_tier") in ("medium", "high", "critical")
                ):
                    self._emit(
                        E.TOOL_RISK_FLAGGED,
                        tenant_id,
                        app_id,
                        request_id,
                        binding,
                        {"tool_id": tid, "risk": risk},
                    )
                    emitted.append(E.TOOL_RISK_FLAGGED)
                self._emit(
                    E.TOOL_EXECUTED,
                    tenant_id,
                    app_id,
                    request_id,
                    binding,
                    {"tool_id": tid, "risk": risk},
                )
                emitted.append(E.TOOL_EXECUTED)
            except ConfirmRequiredError as e:
                self._emit(
                    E.SAFETY_CONFIRM,
                    tenant_id,
                    app_id,
                    request_id,
                    binding,
                    {"tool_id": tid, "risk": e.risk.as_dict()},
                )
                emitted.append(E.SAFETY_CONFIRM)
                sd = self._decision(
                    request_id,
                    tenant_id,
                    app_id,
                    binding,
                    user_content,
                    list(r1) + list(r3),
                    "confirm_only",
                    t0,
                    layer="L4",
                    reasons=[str(e)] + e.risk.reason_codes,
                )
                return GatewayResponse(
                    request_id=request_id,
                    decision="confirm_only",
                    policy_binding_id=binding.policy_binding_id,
                    policy_version=binding.version,
                    messages=[{"role": "user", "content": text1}],
                    model_output=model_output,
                    tool_results=tool_results,
                    safety_decision=sd,
                    blocked_reason=str(e),
                    events=emitted,
                )
            except PermissionError as e:
                self._emit(
                    E.TOOL_DENIED,
                    tenant_id,
                    app_id,
                    request_id,
                    binding,
                    {"tool_id": tid, "reason": str(e)},
                )
                emitted.append(E.TOOL_DENIED)
                final = "block" if "denylist" in str(e) or "dangerous" in str(e) else (
                    "confirm_only" if binding.risk_tier == "critical" else "alert_only"
                )
                decision = max_strict([d1, d3, final])
                sd = self._decision(
                    request_id,
                    tenant_id,
                    app_id,
                    binding,
                    user_content,
                    list(r1) + list(r3),
                    decision,
                    t0,
                    layer="L4",
                    reasons=[str(e)],
                )
                return GatewayResponse(
                    request_id=request_id,
                    decision=decision,
                    policy_binding_id=binding.policy_binding_id,
                    policy_version=binding.version,
                    messages=[{"role": "user", "content": text1}],
                    model_output=model_output,
                    tool_results=tool_results,
                    safety_decision=sd,
                    blocked_reason=str(e),
                    events=emitted,
                )

        decision = max_strict([d1, d3])
        sd = self._decision(
            request_id,
            tenant_id,
            app_id,
            binding,
            user_content,
            list(r1) + list(r3),
            decision,
            t0,
            layer="gateway",
        )
        return GatewayResponse(
            request_id=request_id,
            decision=decision,
            policy_binding_id=binding.policy_binding_id,
            policy_version=binding.version,
            messages=[{"role": "user", "content": text1}],
            model_output=model_output,
            tool_results=tool_results,
            safety_decision=sd,
            events=emitted,
        )

    def _finalize_block(
        self,
        request_id: str,
        tenant_id: str,
        app_id: str,
        binding,
        source: str,
        results,
        t0: float,
        emitted: list[str],
        *,
        layer: str,
        extra_reasons: list[str] | None = None,
        model_output: str | None = None,
    ) -> GatewayResponse:
        reasons = []
        for r in results:
            reasons.extend(r.reasons)
        if extra_reasons:
            reasons.extend(extra_reasons)
        self._emit(
            E.SAFETY_BLOCKED,
            tenant_id,
            app_id,
            request_id,
            binding,
            {"layer": layer, "reason_codes": reasons},
        )
        emitted.append(E.SAFETY_BLOCKED)
        refusal = refusal_for_reasons(reasons)
        sd = self._decision(
            request_id,
            tenant_id,
            app_id,
            binding,
            source,
            results,
            "block",
            t0,
            layer=layer,
            reasons=reasons,
        )
        return GatewayResponse(
            request_id=request_id,
            decision="block",
            policy_binding_id=binding.policy_binding_id,
            policy_version=binding.version,
            messages=[],
            model_output=model_output if model_output is not None else refusal,
            tool_results=[],
            safety_decision=sd,
            blocked_reason=";".join(reasons) or "blocked",
            events=emitted,
            refusal_message=refusal,
        )

    def _decision(
        self,
        request_id,
        tenant_id,
        app_id,
        binding,
        source,
        results,
        decision,
        t0,
        *,
        layer,
        reasons: list[str] | None = None,
    ):
        scanner_results = [r.as_dict() for r in results]
        reason_codes = reasons or []
        for r in results:
            reason_codes.extend(r.reasons)
        seen: set[str] = set()
        uniq = []
        for x in reason_codes:
            if x not in seen:
                seen.add(x)
                uniq.append(x)
        env = build_decision(
            request_id=request_id,
            tenant_id=tenant_id,
            app_id=app_id,
            policy_binding_id=binding.policy_binding_id,
            policy_version=binding.version,
            risk_tier=binding.risk_tier,
            layer=layer,
            decision=decision,
            reason_codes=uniq,
            scanner_results=scanner_results,
            source_text=source,
            retention=binding.retention,
            latency_ms=(time.perf_counter() - t0) * 1000,
        )
        self.ledger.write(env)
        return env

    def _emit(self, etype, tenant_id, app_id, request_id, binding, payload):
        self.events.emit(
            DomainEvent(
                event_type=etype,
                tenant_id=tenant_id,
                app_id=app_id,
                request_id=request_id,
                payload=payload,
                policy_binding_id=binding.policy_binding_id,
                policy_version=binding.version,
            )
        )
