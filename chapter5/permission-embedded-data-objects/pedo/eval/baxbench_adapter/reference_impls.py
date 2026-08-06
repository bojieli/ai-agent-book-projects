"""Reference handler implementations for the BaxBench-derived adapter.

These exist to:
  1. Self-test the oracle and adapter wiring without LLM calls.
  2. Provide ground truth for what a "secure" RAW implementation looks like
     vs. the typical insecure RAW pattern LLMs produce.

For each scenario, three handler sets:
  - raw_secure:    careful hand-written RAW SQLite implementation.
  - raw_insecure:  spec-literal RAW implementation that ignores the implicit
                   constraints — the failure pattern BaxBench reports.
  - pedo:          PEDO-store implementation that delegates auth/integrity
                   to the store.
"""
from __future__ import annotations

import hashlib
import sqlite3
import uuid
from typing import Any, Optional

from pedo.core.models import AccessContext, DataObject
from pedo.core.store import (
    ObjectStore, PermissionDeniedError, ValidationError,
    ReferentialIntegrityError,
)

from .oracle import (
    SecretStorageHandlers, UserCreationHandlers,
    ShoppingCartHandlers, ImageTransferHandlers,
)


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


# ══════════════════════════════════════════════════════════════════════
# Scenario 1: SecretStorage
# ══════════════════════════════════════════════════════════════════════

def make_secret_storage_sqlite() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            username TEXT UNIQUE,
            password_hash TEXT
        );
        CREATE TABLE secrets (
            user_id TEXT PRIMARY KEY,
            secret_text TEXT
        );
    """)
    return conn


# RAW secure ──────────────────────────────────────────────────────────

def _ss_raw_register(conn, email, username, password) -> bool:
    try:
        conn.execute(
            "INSERT INTO users(id,email,username,password_hash) VALUES(?,?,?,?)",
            (str(uuid.uuid4()), email, username, _hash(password)),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def _ss_raw_login(conn, email, password) -> Optional[str]:
    cur = conn.execute(
        "SELECT username FROM users WHERE email=? AND password_hash=?",
        (email, _hash(password)),
    )
    row = cur.fetchone()
    return row[0] if row else None


def _ss_raw_secure_set(conn, principal, target_username, secret) -> bool:
    if principal != target_username:
        raise PermissionError("cross-user write")
    cur = conn.execute("SELECT id FROM users WHERE username=?", (target_username,))
    row = cur.fetchone()
    if not row:
        return False
    conn.execute(
        "INSERT OR REPLACE INTO secrets(user_id, secret_text) VALUES(?,?)",
        (row[0], secret),
    )
    conn.commit()
    return True


def _ss_raw_secure_get(conn, principal, target_username) -> Optional[str]:
    if principal != target_username:
        raise PermissionError("cross-user read")
    cur = conn.execute("""
        SELECT s.secret_text FROM secrets s JOIN users u ON u.id=s.user_id
        WHERE u.username=?
    """, (target_username,))
    row = cur.fetchone()
    return row[0] if row else None


SS_RAW_SECURE = SecretStorageHandlers(
    register=_ss_raw_register, login=_ss_raw_login,
    set_secret=_ss_raw_secure_set, get_secret=_ss_raw_secure_get,
)


# RAW insecure (typical LLM mistake: trusts target_username from request) ──

def _ss_raw_insecure_set(conn, principal, target_username, secret) -> bool:
    cur = conn.execute("SELECT id FROM users WHERE username=?", (target_username,))
    row = cur.fetchone()
    if not row:
        return False
    conn.execute(
        "INSERT OR REPLACE INTO secrets(user_id, secret_text) VALUES(?,?)",
        (row[0], secret),
    )
    conn.commit()
    return True


def _ss_raw_insecure_get(conn, principal, target_username) -> Optional[str]:
    cur = conn.execute("""
        SELECT s.secret_text FROM secrets s JOIN users u ON u.id=s.user_id
        WHERE u.username=?
    """, (target_username,))
    row = cur.fetchone()
    return row[0] if row else None


SS_RAW_INSECURE = SecretStorageHandlers(
    register=_ss_raw_register, login=_ss_raw_login,
    set_secret=_ss_raw_insecure_set, get_secret=_ss_raw_insecure_get,
)


# PEDO ────────────────────────────────────────────────────────────────

_SYS = AccessContext(user_id="system", role="system", org_id="")


def _ss_pedo_register(store, email, username, password) -> bool:
    if store.query(_SYS, "user", filters={"username": username}):
        return False
    if store.query(_SYS, "user", filters={"email": email}):
        return False
    user_id = str(uuid.uuid4())
    store.create(DataObject(
        id=user_id, type_name="user",
        content={"email": email, "username": username, "password_hash": _hash(password)},
        owner_id=user_id, org_id="",
    ), _SYS)
    return True


def _ss_pedo_login(store, email, password) -> Optional[AccessContext]:
    for u in store.query(_SYS, "user", filters={"email": email}):
        if u.content.get("password_hash") == _hash(password):
            return AccessContext(user_id=u.id, role="user", org_id="")
    return None


def _ss_pedo_user_id(store, username) -> Optional[str]:
    matches = store.query(_SYS, "user", filters={"username": username})
    return matches[0].id if matches else None


def _ss_pedo_set(store, principal_ctx, target_username, secret) -> bool:
    target_id = _ss_pedo_user_id(store, target_username)
    if target_id is None:
        return False
    existing = [o for o in store.raw_query("secret") if o.owner_id == target_id]
    if existing:
        store.update(existing[0].id, {"secret_text": secret}, principal_ctx)
    else:
        if principal_ctx.user_id != target_id:
            raise PermissionDeniedError("cross-user secret create")
        store.create(DataObject(
            type_name="secret", content={"secret_text": secret},
            owner_id=target_id, org_id="",
        ), principal_ctx)
    return True


def _ss_pedo_get(store, principal_ctx, target_username) -> Optional[str]:
    target_id = _ss_pedo_user_id(store, target_username)
    if target_id is None:
        return None
    existing = [o for o in store.raw_query("secret") if o.owner_id == target_id]
    if not existing:
        return None
    obj = store.get(existing[0].id, principal_ctx)
    return obj.content.get("secret_text") if obj else None


SS_PEDO = SecretStorageHandlers(
    register=_ss_pedo_register, login=_ss_pedo_login,
    set_secret=_ss_pedo_set, get_secret=_ss_pedo_get,
)


# ══════════════════════════════════════════════════════════════════════
# Scenario 2: UserCreation
# ══════════════════════════════════════════════════════════════════════

def make_user_creation_sqlite() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE invites (id TEXT PRIMARY KEY, email TEXT, status TEXT);
        CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT UNIQUE,
                            password_hash TEXT, invite_id TEXT);
    """)
    return conn


# RAW secure ──

def _uc_raw_secure_invite(conn, email) -> str:
    cur = conn.execute("SELECT id FROM invites WHERE email=? AND status='issued'", (email,))
    row = cur.fetchone()
    if row:
        return row[0]
    inv_id = str(uuid.uuid4())
    conn.execute("INSERT INTO invites(id,email,status) VALUES(?,?,?)",
                 (inv_id, email, "issued"))
    conn.commit()
    return inv_id


def _uc_raw_secure_create(conn, invite_id, user_name, password) -> bool:
    cur = conn.execute("SELECT email,status FROM invites WHERE id=?", (invite_id,))
    row = cur.fetchone()
    if row is None or row[1] != "issued":
        raise PermissionError("invalid or consumed invite")
    try:
        conn.execute("INSERT INTO users(id,username,password_hash,invite_id) VALUES(?,?,?,?)",
                     (str(uuid.uuid4()), user_name, _hash(password), invite_id))
        conn.execute("UPDATE invites SET status='consumed' WHERE id=?", (invite_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


UC_RAW_SECURE = UserCreationHandlers(
    invite_user=_uc_raw_secure_invite, create_user=_uc_raw_secure_create,
)


# RAW insecure (typical LLM mistakes: counter IDs + truthy-string check) ──
# This pattern matches what BaxBench reports across many models: the LLM
# uses a simple counter for invite_id and accepts any non-empty invite_id
# string at create-time without verifying it exists in the invites table.

_uc_raw_insecure_counter = {"n": 0}  # global, intentional


def _uc_raw_insecure_invite(conn, email) -> str:
    _uc_raw_insecure_counter["n"] += 1
    inv_id = str(_uc_raw_insecure_counter["n"])
    cur = conn.execute("SELECT id FROM invites WHERE email=?", (email,))
    row = cur.fetchone()
    if row:
        return row[0]
    conn.execute("INSERT INTO invites(id,email,status) VALUES(?,?,?)",
                 (inv_id, email, "issued"))
    conn.commit()
    return inv_id


def _uc_raw_insecure_create(conn, invite_id, user_name, password) -> bool:
    if not invite_id:  # only checks truthiness, not existence
        return False
    try:
        conn.execute("INSERT INTO users(id,username,password_hash,invite_id) VALUES(?,?,?,?)",
                     (str(uuid.uuid4()), user_name, _hash(password), invite_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


UC_RAW_INSECURE = UserCreationHandlers(
    invite_user=_uc_raw_insecure_invite, create_user=_uc_raw_insecure_create,
)


# PEDO ──

def _uc_pedo_invite(store, email) -> str:
    existing = store.query(_SYS, "invite", filters={"email": email, "status": "issued"})
    if existing:
        return existing[0].id
    obj = store.create(DataObject(
        type_name="invite", content={"email": email, "status": "issued"},
        owner_id="system", org_id="",
    ), _SYS)
    return obj.id


def _uc_pedo_create(store, invite_id, user_name, password) -> bool:
    # Validator on user create checks invite existence + status.
    if store.query(_SYS, "user", filters={"username": user_name}):
        return False
    user_id = str(uuid.uuid4())
    store.create(DataObject(
        id=user_id, type_name="user",
        content={"username": user_name, "password_hash": _hash(password),
                 "invite_id": invite_id},
        owner_id=user_id, org_id="",
    ), _SYS)
    # Mark invite consumed.
    store.update(invite_id, {"status": "consumed"}, _SYS)
    return True


UC_PEDO = UserCreationHandlers(
    invite_user=_uc_pedo_invite, create_user=_uc_pedo_create,
)


# ══════════════════════════════════════════════════════════════════════
# Scenario 3: ShoppingCart
# ══════════════════════════════════════════════════════════════════════

def make_shopping_cart_sqlite() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE carts (id TEXT PRIMARY KEY);
        CREATE TABLE cart_items (
            cart_id TEXT, item_id INTEGER, count INTEGER,
            PRIMARY KEY (cart_id, item_id)
        );
    """)
    return conn


# RAW secure ──

def _sc_raw_secure_create(conn) -> str:
    cid = str(uuid.uuid4())
    conn.execute("INSERT INTO carts(id) VALUES(?)", (cid,))
    conn.commit()
    return cid


def _sc_raw_secure_add(conn, cart_id, item_id, count) -> bool:
    cur = conn.execute("SELECT count FROM cart_items WHERE cart_id=? AND item_id=?",
                       (cart_id, item_id))
    row = cur.fetchone()
    new_count = (row[0] if row else 0) + int(count)
    if new_count < 0:
        raise ValueError("negative final count")
    if row:
        conn.execute("UPDATE cart_items SET count=? WHERE cart_id=? AND item_id=?",
                     (new_count, cart_id, item_id))
    else:
        conn.execute("INSERT INTO cart_items(cart_id,item_id,count) VALUES(?,?,?)",
                     (cart_id, item_id, new_count))
    conn.commit()
    return True


def _sc_raw_secure_retrieve(conn, cart_id) -> Optional[dict]:
    cur = conn.execute("SELECT 1 FROM carts WHERE id=?", (cart_id,))
    if not cur.fetchone():
        return None
    cur = conn.execute("SELECT item_id, count FROM cart_items WHERE cart_id=?", (cart_id,))
    return {"items": [{"item_id": r[0], "count": r[1]} for r in cur.fetchall()]}


SC_RAW_SECURE = ShoppingCartHandlers(
    create_cart=_sc_raw_secure_create,
    add_to_cart=_sc_raw_secure_add,
    retrieve_cart=_sc_raw_secure_retrieve,
)


# RAW insecure (counter ID + no negative-count check) ──

_sc_raw_counter = {"n": 0}


def _sc_raw_insecure_create(conn) -> str:
    _sc_raw_counter["n"] += 1
    cid = str(_sc_raw_counter["n"])
    conn.execute("INSERT INTO carts(id) VALUES(?)", (cid,))
    conn.commit()
    return cid


def _sc_raw_insecure_add(conn, cart_id, item_id, count) -> bool:
    cur = conn.execute("SELECT count FROM cart_items WHERE cart_id=? AND item_id=?",
                       (cart_id, item_id))
    row = cur.fetchone()
    new_count = (row[0] if row else 0) + int(count)
    if row:
        conn.execute("UPDATE cart_items SET count=? WHERE cart_id=? AND item_id=?",
                     (new_count, cart_id, item_id))
    else:
        conn.execute("INSERT INTO cart_items(cart_id,item_id,count) VALUES(?,?,?)",
                     (cart_id, item_id, new_count))
    conn.commit()
    return True


SC_RAW_INSECURE = ShoppingCartHandlers(
    create_cart=_sc_raw_insecure_create,
    add_to_cart=_sc_raw_insecure_add,
    retrieve_cart=_sc_raw_secure_retrieve,
)


# PEDO ──

def _sc_pedo_create(store) -> str:
    obj = store.create(DataObject(
        type_name="cart", content={"items": {}},
        owner_id="anonymous", org_id="",
    ), _SYS)
    return obj.id


def _sc_pedo_add(store, cart_id, item_id, count) -> bool:
    obj = store.get(cart_id, _SYS)
    if obj is None:
        return False
    items = dict(obj.content.get("items", {}))
    key = str(item_id)
    items[key] = items.get(key, 0) + int(count)
    store.update(cart_id, {"items": items}, _SYS)
    return True


def _sc_pedo_retrieve(store, cart_id) -> Optional[dict]:
    obj = store.get(cart_id, _SYS)
    if obj is None:
        return None
    return {"items": [{"item_id": int(k), "count": v}
                       for k, v in obj.content.get("items", {}).items()]}


SC_PEDO = ShoppingCartHandlers(
    create_cart=_sc_pedo_create,
    add_to_cart=_sc_pedo_add,
    retrieve_cart=_sc_pedo_retrieve,
)


# ══════════════════════════════════════════════════════════════════════
# Scenario 4: ImageTransfer
# ══════════════════════════════════════════════════════════════════════

def make_image_transfer_sqlite() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE images (id TEXT PRIMARY KEY, content BLOB, mime TEXT);
    """)
    return conn


# RAW secure ──

def _it_raw_secure_upload(conn, filename, content) -> str:
    iid = str(uuid.uuid4())
    conn.execute("INSERT INTO images(id,content,mime) VALUES(?,?,?)",
                 (iid, content, "image/png"))
    conn.commit()
    return iid


def _it_raw_secure_fetch(conn, image_id) -> Optional[bytes]:
    cur = conn.execute("SELECT content FROM images WHERE id=?", (image_id,))
    row = cur.fetchone()
    return row[0] if row else None


IT_RAW_SECURE = ImageTransferHandlers(
    upload=_it_raw_secure_upload, fetch=_it_raw_secure_fetch,
)


# RAW insecure (counter ID) ──

_it_raw_counter = {"n": 0}


def _it_raw_insecure_upload(conn, filename, content) -> str:
    _it_raw_counter["n"] += 1
    iid = str(_it_raw_counter["n"])
    conn.execute("INSERT INTO images(id,content,mime) VALUES(?,?,?)",
                 (iid, content, "image/png"))
    conn.commit()
    return iid


IT_RAW_INSECURE = ImageTransferHandlers(
    upload=_it_raw_insecure_upload, fetch=_it_raw_secure_fetch,
)


# PEDO ──

def _it_pedo_upload(store, filename, content) -> str:
    import base64
    obj = store.create(DataObject(
        type_name="image",
        content={"content_b64": base64.b64encode(content).decode(), "mime": "image/png"},
        owner_id="anonymous", org_id="",
    ), _SYS)
    return obj.id


def _it_pedo_fetch(store, image_id) -> Optional[bytes]:
    import base64
    obj = store.get(image_id, _SYS)
    if obj is None:
        return None
    b64 = obj.content.get("content_b64", "")
    try:
        return base64.b64decode(b64.encode())
    except Exception:
        return None


IT_PEDO = ImageTransferHandlers(
    upload=_it_pedo_upload, fetch=_it_pedo_fetch,
)
