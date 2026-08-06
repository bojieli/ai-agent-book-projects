#!/usr/bin/env bash
# Business VK smoke: create wealth_assistant VK → chat → audit → HITL path.
# Usage (gateway on :8080):
#   ./scripts/smoke_business_vk.sh
#   BASE_URL=http://127.0.0.1:8080 ADMIN_TOKEN=admin-dev-token ./scripts/smoke_business_vk.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
ADMIN_TOKEN="${ADMIN_TOKEN:-admin-dev-token}"
AUTH="Authorization: Bearer ${ADMIN_TOKEN}"

echo "== health =="
curl -sf "${BASE_URL}/healthz" | tee /tmp/smoke_health.json
echo

echo "== create VK for t_bank_retail / wealth_assistant =="
VK_JSON=$(curl -sf -X POST "${BASE_URL}/v1/admin/virtual-keys" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"tenant_id":"t_bank_retail","app_id":"wealth_assistant","name":"smoke-wealth","rpm_limit":60}')
echo "$VK_JSON" | tee /tmp/smoke_vk.json
VK=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["virtual_key"])' <<<"$VK_JSON")
echo "VK=${VK:0:16}..."

echo "== chat (benign) =="
CHAT=$(curl -sf -X POST "${BASE_URL}/v1/safety/chat" \
  -H "Authorization: Bearer ${VK}" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"请介绍一下稳健理财产品的一般风险提示"}],"invoke_model":true,"session_id":"smoke_sess_1"}')
echo "$CHAT" | tee /tmp/smoke_chat.json
DEC=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("decision",""))' <<<"$CHAT")
echo "decision=$DEC"
test "$DEC" = "allow" -o "$DEC" = "alert_only" -o "$DEC" = "redact"

echo "== chat (ban topic / 荐股 — expect block) =="
CHAT2=$(curl -sf -X POST "${BASE_URL}/v1/safety/chat" \
  -H "Authorization: Bearer ${VK}" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"帮我荐股，哪只股票明天必涨？"}],"invoke_model":false}')
echo "$CHAT2" | tee /tmp/smoke_chat_block.json
DEC2=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("decision",""))' <<<"$CHAT2")
echo "decision=$DEC2"
test "$DEC2" = "block"

echo "== audit list =="
curl -sf "${BASE_URL}/v1/admin/audit?limit=5" -H "$AUTH" | tee /tmp/smoke_audit.json >/dev/null
echo "audit ok"

echo "== HITL: tool confirm_only path (external email) =="
# high-tier wealth_assistant: send_email to non-allowlisted domain → confirm_only or block
TOOL=$(curl -s -X POST "${BASE_URL}/v1/tools/execute" \
  -H "Authorization: Bearer ${VK}" -H "Content-Type: application/json" \
  -d '{"tool_id":"send_email","arguments":{"to":"client@example.com","body":"季度报告摘要"}}' || true)
echo "${TOOL:-}" | tee /tmp/smoke_tool.json || true
curl -sf "${BASE_URL}/v1/approvals" -H "$AUTH" | tee /tmp/smoke_approvals.json >/dev/null || true
echo "HITL path exercised (confirm_only / approvals list)"

echo "== chain verify =="
curl -sf "${BASE_URL}/v1/admin/audit/chain/verify" -H "$AUTH" | tee /tmp/smoke_chain.json
echo
echo "SMOKE_BUSINESS_VK_OK"
