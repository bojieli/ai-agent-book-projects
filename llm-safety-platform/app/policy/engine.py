"""PolicyEngine — load YAML fixtures and resolve current binding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.policy.binding import PolicyBinding, PolicyStore, ScannerSpec
from app.tool_runtime.risk_classifier import ToolRiskRule

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_DIR = ROOT / "configs" / "policies"


def _specs(raw: list[dict[str, Any]] | None) -> tuple[ScannerSpec, ...]:
    out: list[ScannerSpec] = []
    for item in raw or []:
        topics = item.get("topics") or []
        categories = item.get("categories") or []
        out.append(
            ScannerSpec(
                id=item["id"],
                threshold=float(item.get("threshold", 0.5)),
                max_tokens=item.get("max_tokens"),
                topics=tuple(topics),
                categories=tuple(categories),
            )
        )
    return tuple(out)


def _risk_rules(raw: list[dict[str, Any]] | None) -> tuple[ToolRiskRule, ...]:
    out: list[ToolRiskRule] = []
    for item in raw or []:
        out.append(
            ToolRiskRule(
                id=item["id"],
                tool_id=item["tool_id"],
                field=item.get("field", ""),
                type=item["type"],
                op_risk_tier=item.get("op_risk_tier", "medium"),
                decision=item.get("decision", "confirm_only"),
                pattern=item.get("pattern", ""),
            )
        )
    return tuple(out)


def binding_from_dict(data: dict[str, Any]) -> PolicyBinding:
    return PolicyBinding(
        policy_binding_id=data["policy_binding_id"],
        tenant_id=data["tenant_id"],
        app_id=data["app_id"],
        version=int(data["version"]),
        reason=data["reason"],
        risk_tier=data["risk_tier"],
        fail_mode=data["fail_mode"],
        effect_cap=data["effect_cap"],
        tool_allowlist=tuple(data.get("tool_allowlist") or []),
        tool_denylist=tuple(data.get("tool_denylist") or []),
        model_allowlist=tuple(data.get("model_allowlist") or []),
        email_domain_allowlist=tuple(data.get("email_domain_allowlist") or []),
        tool_risk_rules=_risk_rules(data.get("tool_risk_rules")),
        input_scanners=_specs(data.get("input_scanners")),
        output_scanners=_specs(data.get("output_scanners")),
        retention=data.get("retention", "hash_only"),
        require_dual_publish=bool(
            data.get("require_dual_publish", data.get("risk_tier") == "critical")
        ),
        scanner_bundle_id=str(data.get("scanner_bundle_id") or "bundle_shim_v1"),
        model_digests=tuple(data.get("model_digests") or []),
        system_prompt_hash=str(data.get("system_prompt_hash") or ""),
        grounding_required=bool(data.get("grounding_required", False)),
        daily_token_budget=int(data.get("daily_token_budget") or 0),
        max_concurrency=int(data.get("max_concurrency") or 0),
    )


class PolicyEngine:
    def __init__(self, store: PolicyStore | None = None) -> None:
        self.store = store or PolicyStore()

    def load_yaml_dir(self, directory: Path | None = None) -> int:
        d = directory or DEFAULT_POLICY_DIR
        n = 0
        for path in sorted(d.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            binding = binding_from_dict(data)
            existing = self.store.current(binding.tenant_id, binding.app_id)
            if existing is None:
                self.store.create_initial(binding)
            else:
                if existing.version >= binding.version:
                    continue
                self.store.append_version(binding)
            n += 1
        return n

    def resolve(self, tenant_id: str, app_id: str) -> PolicyBinding:
        cur = self.store.current(tenant_id, app_id)
        if cur is None:
            raise KeyError(f"no policy for {tenant_id}/{app_id}")
        return cur

    def publish(
        self,
        *,
        tenant_id: str,
        app_id: str,
        reason: str,
        risk_tier: str | None = None,
        effect_cap: str | None = None,
        tool_allowlist: list[str] | None = None,
        tool_denylist: list[str] | None = None,
        input_scanners: list[ScannerSpec] | None = None,
        output_scanners: list[ScannerSpec] | None = None,
    ) -> PolicyBinding:
        cur = self.resolve(tenant_id, app_id)
        nxt = PolicyBinding(
            policy_binding_id=cur.policy_binding_id,
            tenant_id=cur.tenant_id,
            app_id=cur.app_id,
            version=cur.version + 1,
            reason=reason,
            risk_tier=risk_tier or cur.risk_tier,
            fail_mode="fail_closed"
            if (risk_tier or cur.risk_tier) in ("high", "critical")
            else cur.fail_mode,
            effect_cap=effect_cap or cur.effect_cap,
            tool_allowlist=tuple(tool_allowlist)
            if tool_allowlist is not None
            else cur.tool_allowlist,
            tool_denylist=tuple(tool_denylist)
            if tool_denylist is not None
            else cur.tool_denylist,
            model_allowlist=cur.model_allowlist,
            email_domain_allowlist=cur.email_domain_allowlist,
            tool_risk_rules=cur.tool_risk_rules,
            input_scanners=tuple(input_scanners)
            if input_scanners is not None
            else cur.input_scanners,
            output_scanners=tuple(output_scanners)
            if output_scanners is not None
            else cur.output_scanners,
            retention=cur.retention,
            require_dual_publish=(risk_tier or cur.risk_tier) == "critical",
            scanner_bundle_id=cur.scanner_bundle_id,
            model_digests=cur.model_digests,
            system_prompt_hash=cur.system_prompt_hash,
            grounding_required=cur.grounding_required,
            daily_token_budget=cur.daily_token_budget,
            max_concurrency=cur.max_concurrency,
        )
        return self.store.append_version(nxt)
