#!/usr/bin/env bash
# Start moderation + gateway using LLM creds from stock_analysis/.env
# (GLOBAL_EVENT_LLM_*), falling back to deploy/.env.moderation.
# Never prints the API key.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STOCK_ENV="${STOCK_ENV:-/Users/liaolu/Projects/stock_analysis/.env}"
LOCAL_ENV="$ROOT/deploy/.env.moderation"

.venv/bin/python - <<'PY'
"""Sync stock_analysis LLM vars → deploy/.env.moderation (safe parse)."""
from __future__ import annotations

import os
import re
from pathlib import Path

root = Path.cwd()
stock = Path(os.environ.get("STOCK_ENV", "/Users/liaolu/Projects/stock_analysis/.env"))
local = root / "deploy" / ".env.moderation"


def parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        out[k] = v
    return out


stock_vars = parse_env(stock)
local_vars = parse_env(local)

url = (
    stock_vars.get("GLOBAL_EVENT_LLM_BASE_URL")
    or local_vars.get("MODERATION_UPSTREAM_URL")
    or ""
)
model = (
    stock_vars.get("GLOBAL_EVENT_LLM_MODEL")
    or local_vars.get("MODERATION_MODEL")
    or ""
)
key = (
    stock_vars.get("GLOBAL_EVENT_LLM_API_KEY")
    or local_vars.get("MODERATION_UPSTREAM_KEY")
    or ""
)

if not url or not model or not key:
    raise SystemExit(
        f"missing LLM config: url={bool(url)} model={bool(model)} key={bool(key)} "
        f"(checked {stock} and {local})"
    )

text = "\n".join(
    [
        "MODERATION_MOCK=0",
        "MODERATION_FUSE_RULES=1",
        f"MODERATION_UPSTREAM_URL={url}",
        f"MODERATION_MODEL={model}",
        f"MODERATION_UPSTREAM_KEY={key}",
        "MODERATION_TIMEOUT_SEC=45",
        "MODERATION_PORT=8091",
        "SAFETY_SCANNER_MODE=remote",
        "SAFETY_CLASSIFIER_URL=http://127.0.0.1:8091/v1/classify",
        "SAFETY_OIDC_DISABLED=1",
        "SAFETY_ADMIN_TOKEN=admin-dev-token",
        "",
    ]
)
local.parent.mkdir(parents=True, exist_ok=True)
local.write_text(text, encoding="utf-8")
os.chmod(local, 0o600)
print(f"synced {stock.name if stock.is_file() else 'n/a'} → {local}")
print(f"upstream={url} model={model} key_len={len(key)}")
PY

set -a
# shellcheck disable=SC1090
source "$LOCAL_ENV"
set +a

export SAFETY_SCANNER_MODE=remote
export SAFETY_CLASSIFIER_URL="${SAFETY_CLASSIFIER_URL:-http://127.0.0.1:8091/v1/classify}"
export SAFETY_OIDC_DISABLED=1
export SAFETY_ADMIN_TOKEN="${SAFETY_ADMIN_TOKEN:-admin-dev-token}"

echo "starting moderation on :${MODERATION_PORT:-8091}"
.venv/bin/uvicorn workers.moderation.app:app --host 127.0.0.1 --port "${MODERATION_PORT:-8091}" &
MOD_PID=$!
cleanup() { kill "$MOD_PID" 2>/dev/null || true; }
trap cleanup EXIT

for i in $(seq 1 20); do
  if curl -sf "http://127.0.0.1:${MODERATION_PORT:-8091}/healthz" >/dev/null; then
    echo "moderation healthz ok (pid=$MOD_PID)"
    break
  fi
  sleep 0.3
  if [[ "$i" -eq 20 ]]; then
    echo "moderation failed to start" >&2
    exit 1
  fi
done

echo "starting gateway on :8080"
.venv/bin/uvicorn app.api.main:app --host 127.0.0.1 --port 8080
