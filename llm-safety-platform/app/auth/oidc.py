"""OIDC JWT validation via configurable JWKS (ADR-015 / ADR-025).

Env:
  SAFETY_OIDC_DISABLED=0     enable JWT path (default 1 = admin token)
  OIDC_REQUIRED=1            fail-closed when JWT invalid / JWKS unreachable
  SAFETY_OIDC_JWKS_URL       JWKS endpoint (or derived from issuer)
  SAFETY_OIDC_ISSUER         expected iss
  SAFETY_OIDC_AUDIENCE       expected aud (default llm-safety)
  SAFETY_OIDC_ROLE_CLAIM     claim name for roles (default roles)
"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWKClient
from fastapi import HTTPException

from app.config import settings

_JWKS_CLIENT: PyJWKClient | None = None
_JWKS_URL_CACHED: str = ""


def _b(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).lower() in ("1", "true", "yes", "on")


def oidc_required() -> bool:
    return _b("OIDC_REQUIRED", "0") or _b("SAFETY_OIDC_REQUIRED", "0")


def jwks_url() -> str:
    explicit = os.getenv("SAFETY_OIDC_JWKS_URL", "").strip()
    if explicit:
        return explicit
    issuer = (settings.oidc_issuer or "").rstrip("/")
    if issuer:
        return f"{issuer}/.well-known/jwks.json"
    return ""


def _client(url: str) -> PyJWKClient:
    global _JWKS_CLIENT, _JWKS_URL_CACHED
    if _JWKS_CLIENT is None or _JWKS_URL_CACHED != url:
        _JWKS_CLIENT = PyJWKClient(url, cache_keys=True, lifespan=300)
        _JWKS_URL_CACHED = url
    return _JWKS_CLIENT


@dataclass
class OIDCClaims:
    subject: str
    roles: list[str]
    raw: dict[str, Any]


def validate_jwt(token: str) -> OIDCClaims:
    """Validate bearer JWT against JWKS. Fail-closed when OIDC_REQUIRED=1."""
    url = jwks_url()
    if not url:
        if oidc_required() or not settings.oidc_disabled:
            raise HTTPException(status_code=401, detail="oidc_jwks_url_missing")
        raise HTTPException(status_code=401, detail="oidc_not_configured")

    try:
        client = _client(url)
        signing_key = client.get_signing_key_from_jwt(token)
        options = {
            "require": ["exp", "iat", "sub"],
            "verify_aud": bool(settings.oidc_audience),
        }
        decode_kwargs: dict[str, Any] = {
            "algorithms": ["RS256", "ES256"],
            "options": options,
        }
        if settings.oidc_audience:
            decode_kwargs["audience"] = settings.oidc_audience
        if settings.oidc_issuer:
            decode_kwargs["issuer"] = settings.oidc_issuer
        claims = jwt.decode(token, signing_key.key, **decode_kwargs)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        if oidc_required() or not settings.oidc_disabled:
            raise HTTPException(
                status_code=401, detail=f"oidc_jwt_invalid:{type(exc).__name__}"
            ) from exc
        raise HTTPException(status_code=401, detail="oidc_jwt_invalid") from exc

    role_claim = os.getenv("SAFETY_OIDC_ROLE_CLAIM", "roles")
    roles_raw = claims.get(role_claim) or claims.get("realm_access", {}).get("roles") or []
    if isinstance(roles_raw, str):
        roles = [r.strip() for r in roles_raw.split(",") if r.strip()]
    else:
        roles = [str(r) for r in roles_raw]
    return OIDCClaims(subject=str(claims.get("sub", "")), roles=roles, raw=claims)


def fetch_jwks(url: str, timeout: float = 5.0) -> dict[str, Any]:
    """Test helper / health probe — fetch JWKS document."""
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def reset_jwks_cache() -> None:
    global _JWKS_CLIENT, _JWKS_URL_CACHED
    _JWKS_CLIENT = None
    _JWKS_URL_CACHED = ""
