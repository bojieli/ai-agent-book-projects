"""Scanner orchestration + max_strict reduction."""

from __future__ import annotations

from typing import Any

from app.decisions import max_strict
from app.policy.binding import PolicyBinding, ScannerSpec
from app.scanners.base import ScanContext, ScanResult
from app.scanners.mocks import default_registry


class ScannerOrchestrator:
    def __init__(self, registry: dict[str, object] | None = None) -> None:
        self.registry = registry or default_registry()

    def run_layer(
        self,
        *,
        layer: str,
        text: str,
        specs: tuple[ScannerSpec, ...],
        tenant_id: str,
        request_id: str,
        vault,
        extra: dict[str, Any] | None = None,
    ) -> tuple[str, str, list[ScanResult]]:
        """Returns (decision, possibly_redacted_text, results)."""
        results: list[ScanResult] = []
        current = text
        shared_extra = dict(extra or {})
        for spec in specs:
            scanner = self.registry.get(spec.id)
            if scanner is None:
                results.append(
                    ScanResult(spec.id, "block", 1.0, [f"unknown_scanner:{spec.id}"])
                )
                continue
            ctx = ScanContext(
                tenant_id=tenant_id,
                request_id=request_id,
                vault=vault,
                spec=spec,
                extra=shared_extra,
            )
            res = scanner.scan(current, ctx)  # type: ignore[attr-defined]
            results.append(res)
            if res.redacted_text is not None:
                current = res.redacted_text
        decision = max_strict(r.decision for r in results) if results else "allow"
        return decision, current, results

    def run_input(
        self,
        text: str,
        binding: PolicyBinding,
        tenant_id: str,
        request_id: str,
        vault,
        extra: dict[str, Any] | None = None,
    ):
        return self.run_layer(
            layer="L1",
            text=text,
            specs=binding.input_scanners,
            tenant_id=tenant_id,
            request_id=request_id,
            vault=vault,
            extra=extra,
        )

    def run_output(
        self,
        text: str,
        binding: PolicyBinding,
        tenant_id: str,
        request_id: str,
        vault,
        extra: dict[str, Any] | None = None,
    ):
        return self.run_layer(
            layer="L3",
            text=text,
            specs=binding.output_scanners,
            tenant_id=tenant_id,
            request_id=request_id,
            vault=vault,
            extra=extra,
        )
