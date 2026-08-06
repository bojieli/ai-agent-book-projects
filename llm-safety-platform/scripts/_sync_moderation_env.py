"""Sync stock_analysis GLOBAL_EVENT_LLM_* → deploy/.env.moderation."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STOCK = Path(os.environ.get("STOCK_ENV", "/Users/liaolu/Projects/stock_analysis/.env"))
LOCAL = ROOT / "deploy" / ".env.moderation"


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
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        out[k] = v
    return out


def main() -> None:
    stock = parse_env(STOCK)
    local = parse_env(LOCAL)
    url = stock.get("GLOBAL_EVENT_LLM_BASE_URL") or local.get("MODERATION_UPSTREAM_URL") or ""
    model = stock.get("GLOBAL_EVENT_LLM_MODEL") or local.get("MODERATION_MODEL") or ""
    key = stock.get("GLOBAL_EVENT_LLM_API_KEY") or local.get("MODERATION_UPSTREAM_KEY") or ""
    if not (url and model and key):
        raise SystemExit(
            f"missing LLM config url={bool(url)} model={bool(model)} key={bool(key)}"
        )
    LOCAL.parent.mkdir(parents=True, exist_ok=True)
    LOCAL.write_text(
        "\n".join(
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
        ),
        encoding="utf-8",
    )
    os.chmod(LOCAL, 0o600)
    print(f"synced → {LOCAL} upstream={url} model={model} key_len={len(key)}")


if __name__ == "__main__":
    main()
