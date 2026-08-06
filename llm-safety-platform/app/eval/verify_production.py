"""Production Cut L3 capability verification (filesystem + module contracts)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        PASS.append(name)
        print(f"  OK  {name}")
    else:
        FAIL.append(f"{name}: {detail}")
        print(f" FAIL {name}: {detail}")


def main() -> int:
    print("=== verify_production ===")
    docs = ROOT.parent / "docs" / "llm-safety-platform"
    check("docs.completion", (docs / "COMPLETION.md").exists())
    check("docs.v2_03", "v2.0" in (docs / "03_架构基线.md").read_text(encoding="utf-8"))
    check("deploy.compose", (ROOT / "deploy" / "docker-compose.yml").exists())
    check("deploy.dockerfile", (ROOT / "Dockerfile").exists())
    check("deploy.helm_chart", (ROOT / "deploy/helm/llm-safety-platform/Chart.yaml").exists())
    check("deploy.helm_deploy", (ROOT / "deploy/helm/llm-safety-platform/templates/deployment.yaml").exists())
    check("migrations.sql", (ROOT / "migrations/001_init.sql").exists())
    check("console.public", (ROOT / "console/public/index.html").exists())
    check("console.vite", (ROOT / "console/package.json").exists())
    check("evals.promptfoo", (ROOT / "configs/evals/promptfoo.yaml").exists())

    from app.auth import ROLES, vk_service
    from app.config import settings
    from app.observability import HashChainLedger, SIEMSink
    from app.providers import ModelProxy
    from app.quota import QuotaService
    from app.redteam import RedTeamRunner, ReleaseEvaluator
    from app.tool_runtime import ToolRuntime
    from app.vault import Vault

    check("roles.four", set(ROLES) == {"Admin", "Security", "AppOwner", "Auditor"})
    check("scanner.shim_default", settings.scanner_mode in ("shim", "onnx", "remote"))
    v = Vault()
    tok = v.put(tenant_id="t", request_id="r", pii_type="PHONE", value="13800138000")
    check("vault.encrypt_fields", bool(v._entries[tok].ciphertext and v._entries[tok].nonce))  # noqa: SLF001
    check("vault.roundtrip", v.get(tok, tenant_id="t") == "13800138000")

    rt = ToolRuntime()
    rt.register_defaults()
    filtered = rt.filter_mcp_tools([{"name": "search_kb"}, {"name": "evil_tool"}])
    check("mcp.filter", [t["name"] for t in filtered] == ["search_kb"])

    from app.tool_runtime import PLATFORM_TOOL_DENYLIST, ToolRiskClassifier, ToolRiskRule

    check("denylist.platform", "shell_exec" in PLATFORM_TOOL_DENYLIST)
    ra = ToolRiskClassifier().assess(
        "send_email",
        {"to": "x@evil.com"},
        rules=[
            ToolRiskRule(
                "e", "send_email", "to", "regex", "critical", "block", r"@evil\.com$"
            )
        ],
    )
    check("risk.classifier_block", ra.decision == "block")

    proxy = ModelProxy()
    text, meta = proxy.chat([{"role": "user", "content": "hi"}])
    check("modelproxy.mock", text.startswith("MOCK_REPLY") and meta["upstream"] == "mock")

    q = QuotaService()
    check("quota.rpm", q.check_rpm("k1", 100) is True)

    report = RedTeamRunner().run_shim_suite()
    ev = ReleaseEvaluator().evaluate(redteam=report, risk_tier="medium")
    check("redteam.shim_pass", report["passed"] and ev.passed)

    led = HashChainLedger()
    led.write(
        {
            "request_id": "a",
            "decision": "allow",
            "content_hash": "x",
        }
    )
    check("hashchain.append", bool(led.chain and led.chain[0].get("chain_hash")))
    check("siem.buffer", isinstance(SIEMSink().buffer, list))
    check("vk.service", hasattr(vk_service, "create"))

    # API module importable
    from app.api.main import app as fastapi_app

    routes = {getattr(r, "path", "") for r in fastapi_app.routes}
    for path in (
        "/healthz",
        "/v1/safety/chat",
        "/v1/safety/scan",
        "/v1/chat/completions",
        "/v1/tools/execute",
        "/v1/admin/virtual-keys",
        "/v1/admin/audit/chain/verify",
        "/v1/approvals",
        "/v1/redteam/run",
    ):
        check(f"route.{path}", path in routes)

    print(f"\nPASS={len(PASS)} FAIL={len(FAIL)}")
    if FAIL:
        for f in FAIL:
            print(" ", f)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
