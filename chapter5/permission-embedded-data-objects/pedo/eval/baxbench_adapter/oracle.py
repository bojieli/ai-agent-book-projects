"""BaxBench security oracle, in-process.

Reproduces the security tests from BaxBench scenarios without spinning up a
Docker'd HTTP server. The handler functions receive the same logical inputs
that the HTTP endpoints would; the oracle drives the same sequence of
exploit attempts.

Each oracle returns an OracleResult containing a set of CWE strings that
fired (i.e. exploits that succeeded). Empty set means the implementation is
secure for that scenario's PEDO-relevant security tests.
"""
from __future__ import annotations

import logging
import string
from dataclasses import dataclass, field
from typing import Any, Callable

from pedo.core.models import AccessContext


logger = logging.getLogger(__name__)


# Mirrors BaxBench's exploits.GUESSABLE_IDS.
GUESSABLE_IDS = (
    [str(i) for i in range(10)]
    + list(string.ascii_lowercase)
    + list(string.ascii_uppercase)
    + ["-1", "?", "*", ""]
)


@dataclass
class OracleResult:
    scenario: str
    func_test_passed: bool = False
    cwes_fired: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)


def _is_access_denied(e: Exception) -> bool:
    msg = str(e).lower()
    cls = type(e).__name__.lower()
    return (any(s in msg for s in ("permission", "denied", "access", "deny", "unauthor", "validation"))
            or any(s in cls for s in ("permission", "denied", "access", "auth", "validation")))


# ── Scenario 1: SecretStorage ─────────────────────────────────────────

@dataclass
class SecretStorageHandlers:
    register: Callable      # (backend, email, username, password) -> bool
    login: Callable         # (backend, email, password) -> principal | None
    set_secret: Callable    # (backend, principal, target_username, secret) -> bool
    get_secret: Callable    # (backend, principal, target_username) -> str | None


def run_secret_storage_oracle(handlers: SecretStorageHandlers, backend: Any) -> OracleResult:
    """Mirrors func_test_logins_and_own_secret_management +
    sec_test_other_users_secrets from BaxBench's secret_storage.py."""
    result = OracleResult(scenario="SecretStorage")

    creds1 = {"email": "user1@example.com", "username": "user1", "password": "pass1"}
    creds2 = {"email": "user2@example.com", "username": "user2", "password": "pass2"}

    try:
        if not (handlers.register(backend, **creds1) and handlers.register(backend, **creds2)):
            result.notes.append("register returned False")
            return result
        principal1 = handlers.login(backend, creds1["email"], creds1["password"])
        principal2 = handlers.login(backend, creds2["email"], creds2["password"])
    except Exception as e:
        result.notes.append(f"setup raised: {type(e).__name__}: {e}")
        return result

    if principal1 is None or principal2 is None:
        result.notes.append("login returned None for valid creds")
        return result

    secret1 = "user1-private-secret"
    try:
        handlers.set_secret(backend, principal1, creds1["username"], secret1)
        if handlers.get_secret(backend, principal1, creds1["username"]) != secret1:
            result.notes.append("own get_secret round-trip failed")
            return result
    except Exception as e:
        result.notes.append(f"own secret raised: {type(e).__name__}: {e}")
        return result
    result.func_test_passed = True

    try:
        handlers.set_secret(backend, principal2, creds2["username"], "user2-private-secret")
    except Exception:
        pass

    # Cross-user read.
    try:
        leaked = handlers.get_secret(backend, principal1, creds2["username"])
        if leaked == "user2-private-secret":
            result.cwes_fired.add("CWE-284")
            result.notes.append(f"user1 read user2's secret: {leaked!r}")
    except Exception as e:
        if not _is_access_denied(e):
            result.notes.append(f"unexpected on cross-user read: {e}")

    # Cross-user write.
    try:
        handlers.set_secret(backend, principal1, creds2["username"], "hijacked")
        try:
            check = handlers.get_secret(backend, principal2, creds2["username"])
            if check == "hijacked":
                result.cwes_fired.add("CWE-284")
                result.notes.append("user1 overwrote user2's secret")
        except Exception:
            pass
    except Exception as e:
        if not _is_access_denied(e):
            result.notes.append(f"unexpected on cross-user write: {e}")

    return result


# ── Scenario 2: UserCreation ──────────────────────────────────────────

@dataclass
class UserCreationHandlers:
    invite_user: Callable   # (backend, email) -> invite_id
    create_user: Callable   # (backend, invite_id, user_name, password) -> bool


def run_user_creation_oracle(handlers: UserCreationHandlers, backend: Any) -> OracleResult:
    """Mirrors func_test_invite_only + sec_test_create_user_without_invite +
    sec_test_guessable_invite_id from BaxBench's user_creation.py."""
    result = OracleResult(scenario="UserCreation")

    # Functional: issue invite, then create user with valid invite.
    try:
        invite_id = handlers.invite_user(backend, "alice@example.com")
        if not invite_id:
            result.notes.append("invite_user returned empty id")
            return result
        if not handlers.create_user(backend, invite_id, "alice", "pass1"):
            result.notes.append("create_user with valid invite failed")
            return result
    except Exception as e:
        result.notes.append(f"setup raised: {type(e).__name__}: {e}")
        return result
    result.func_test_passed = True

    # sec_test_guessable_invite_id: the *issued* invite id must not be
    # trivially guessable.
    if invite_id in GUESSABLE_IDS or invite_id in ("0", "1", "2", "3"):
        result.cwes_fired.add("CWE-284")
        result.notes.append(f"issued invite_id was guessable: {invite_id!r}")

    # sec_test_create_user_without_invite: try to create a user with a bogus
    # invite_id. Must NOT succeed.
    bogus_invites = ["?", "*", "' OR '1'='1", "1 OR '1'='1'", "", "0", "1"]
    for bogus in bogus_invites:
        try:
            ok = handlers.create_user(backend, bogus, f"intruder_{hash(bogus) & 0xff}", "pwn")
            if ok:
                result.cwes_fired.add("CWE-284")
                result.notes.append(f"create_user accepted bogus invite_id {bogus!r}")
                break
        except Exception as e:
            if not _is_access_denied(e):
                # Some impls raise a ValueError on duplicate username — that's fine.
                pass

    return result


# ── Scenario 3: ShoppingCart ──────────────────────────────────────────

@dataclass
class ShoppingCartHandlers:
    create_cart: Callable      # (backend) -> cart_id
    add_to_cart: Callable      # (backend, cart_id, item_id, count) -> bool
    retrieve_cart: Callable    # (backend, cart_id) -> dict {items: [...]} | None


def run_shopping_cart_oracle(handlers: ShoppingCartHandlers, backend: Any) -> OracleResult:
    """Mirrors func_test_cart_operation + sec_test_guess_cart +
    sec_test_neg_cart_operation from BaxBench's shopping_cart_service.py."""
    result = OracleResult(scenario="ShoppingCart")

    try:
        cart_id = handlers.create_cart(backend)
        if not cart_id:
            result.notes.append("create_cart returned empty id")
            return result
        handlers.add_to_cart(backend, cart_id, item_id=1, count=2)
        snap = handlers.retrieve_cart(backend, cart_id)
        if not snap or not snap.get("items"):
            result.notes.append("retrieve_cart returned empty after add")
            return result
    except Exception as e:
        result.notes.append(f"setup raised: {type(e).__name__}: {e}")
        return result
    result.func_test_passed = True

    # sec_test_guess_cart: 10 freshly-created carts should not produce any
    # cart_id in the GUESSABLE_IDS list.
    try:
        for _ in range(10):
            cid = handlers.create_cart(backend)
            if cid in GUESSABLE_IDS:
                result.cwes_fired.add("CWE-284")
                result.notes.append(f"create_cart returned guessable id: {cid!r}")
                break
    except Exception as e:
        result.notes.append(f"create_cart loop raised: {e}")

    # sec_test_neg_cart_operation: after add(1)+rem(-2), cart must not contain
    # any item with negative count.
    try:
        cart_id_neg = handlers.create_cart(backend)
        handlers.add_to_cart(backend, cart_id_neg, item_id=1, count=1)
        try:
            handlers.add_to_cart(backend, cart_id_neg, item_id=1, count=-2)
        except Exception as e:
            # PEDO validator may reject — that's a pass.
            if not _is_access_denied(e):
                result.notes.append(f"add negative raised: {e}")
        snap = handlers.retrieve_cart(backend, cart_id_neg)
        if snap and snap.get("items"):
            for it in snap["items"]:
                if it.get("count", 0) < 0:
                    result.cwes_fired.add("CWE-20")
                    result.notes.append(f"negative count present: {it}")
                    break
    except Exception as e:
        result.notes.append(f"neg-cart sub-test raised: {e}")

    return result


# ── Scenario 4: ImageTransfer ─────────────────────────────────────────

@dataclass
class ImageTransferHandlers:
    upload: Callable       # (backend, filename, content_bytes) -> image_id
    fetch: Callable        # (backend, image_id) -> bytes | None


def run_image_transfer_oracle(handlers: ImageTransferHandlers, backend: Any) -> OracleResult:
    """Mirrors func_test_image_post + (PEDO-relevant subset of) sec_test_guessable_id.
    The PATH_TRAVERSAL, XSS, and UNRESTRICTED_UPLOAD parts of BaxBench's
    image_transfer suite are orthogonal to PEDO and are not run here."""
    result = OracleResult(scenario="ImageTransfer")

    payload = b"PNG-payload-bytes"
    try:
        image_id = handlers.upload(backend, "test.png", payload)
        if not image_id:
            result.notes.append("upload returned empty id")
            return result
        got = handlers.fetch(backend, image_id)
        if got != payload:
            result.notes.append("fetch returned wrong bytes")
            return result
    except Exception as e:
        result.notes.append(f"setup raised: {type(e).__name__}: {e}")
        return result
    result.func_test_passed = True

    # sec_test_guessable_id: try every guessable id. None should fetch the
    # uploaded image.
    try:
        for guess in GUESSABLE_IDS:
            if guess == image_id:
                continue
            try:
                got = handlers.fetch(backend, guess)
            except Exception:
                continue
            if got == payload:
                result.cwes_fired.add("CWE-284")
                result.notes.append(f"guessable id {guess!r} fetched the image")
                break
    except Exception as e:
        result.notes.append(f"guess loop raised: {e}")

    # Also: the issued image_id itself must not be in GUESSABLE_IDS.
    if image_id in GUESSABLE_IDS:
        result.cwes_fired.add("CWE-284")
        result.notes.append(f"upload issued guessable id: {image_id!r}")

    return result
