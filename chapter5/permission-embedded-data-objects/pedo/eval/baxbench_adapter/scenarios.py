"""PEDO scenarios that mirror BaxBench scenarios.

These are translations of BaxBench scenario API specs into PEDO object
schemas. Each scenario keeps the same endpoint surface (handler signatures)
so a single security oracle can run against either RAW or PEDO conditions.

Scenarios covered:
  - SecretStorage   (BaxBench id "SecretStorage")
  - UserCreation    (BaxBench id "UserCreation") — invite-only signup
  - ShoppingCart    (BaxBench id "ShoppingCart") — anonymous bearer carts
  - ImageTransfer   (BaxBench id "ImageTransfer") — anonymous bearer images
"""
from __future__ import annotations

from pedo.core.models import (
    AccessContext, ObjectType, Operation,
    PermissionRule, PrivilegeType,
)
from pedo.core.store import ObjectStore


# ── BaxBench: SecretStorage ───────────────────────────────────────────
#
# Endpoints: /register, /login, /set_secret, /get_secret
# CWEs covered:    CWE-284 IMPROPER_ACCESS_CONTROL (cross-user)
# CWEs orthogonal: CWE-89 SQL_INJECTION (parsing layer),
#                  CWE-522 INSUFFICIENTLY_PROTECTED_CREDENTIALS,
#                  CWE-863 INCORRECT_AUTHORIZATION (token collision)

def register_secret_storage_types(store: ObjectStore) -> None:
    """user (self-owner) and secret (owner-only access)."""
    user_type = ObjectType(
        name="user",
        fields={"email": "str", "username": "str", "password_hash": "str"},
        permission_rules=[
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.INSERT, condition={}),
            # Auth subsystem (system role) needs to look up users for login.
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.READ,
                           condition={"role": "system"}),
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.READ,
                           condition={"is_owner": True}),
        ],
        default_policy=Operation.DENY,
    )
    secret_type = ObjectType(
        name="secret",
        fields={"secret_text": "str"},
        permission_rules=[
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.INSERT, condition={}),
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.READ,
                           condition={"is_owner": True}),
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.WRITE,
                           condition={"is_owner": True}),
        ],
        default_policy=Operation.DENY,
    )
    store.register_type(user_type)
    store.register_type(secret_type)


# ── BaxBench: UserCreation ────────────────────────────────────────────
#
# Endpoints: /invite_user, /create_user
# CWEs covered:
#   CWE-284 IMPROPER_ACCESS_CONTROL — sec_test_create_user_without_invite
#       (LLM accepts any string as invite_id; PEDO rejects because invite is a
#       PEDO object that must exist and be in 'issued' state)
#   CWE-284 IMPROPER_ACCESS_CONTROL — sec_test_guessable_invite_id
#       (LLM uses sequential/empty IDs; DataObject defaults to uuid4())
# CWEs orthogonal: CWE-522, CWE-89

def _validate_invite_unconsumed(proposed, existing, accessor, store):
    """Validator on user creation: invite must exist, match email, be unconsumed."""
    invite_id = proposed.content.get("invite_id")
    if not invite_id:
        return "invite_id is required"
    invite = store.raw_read(invite_id)
    if invite is None or invite.type_name != "invite":
        return f"invite_id {invite_id!r} does not refer to a valid invite"
    if invite.content.get("status") != "issued":
        return f"invite is in status {invite.content.get('status')!r}, not 'issued'"
    return True


def register_user_creation_types(store: ObjectStore) -> None:
    invite_type = ObjectType(
        name="invite",
        fields={"email": "str", "status": "str"},  # status: issued | consumed
        permission_rules=[
            # Anyone can create an invite (BaxBench spec: /invite_user is open).
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.INSERT, condition={}),
            # The signup flow needs to inspect the invite to mark it consumed.
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.READ,
                           condition={"role": "system"}),
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.WRITE,
                           condition={"role": "system"}),
        ],
        default_policy=Operation.DENY,
    )
    user_type = ObjectType(
        name="user",
        fields={"username": "str", "password_hash": "str", "invite_id": "str"},
        permission_rules=[
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.INSERT, condition={}),
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.READ,
                           condition={"role": "system"}),
        ],
        validators=[_validate_invite_unconsumed],
        default_policy=Operation.DENY,
    )
    store.register_type(invite_type)
    store.register_type(user_type)


# ── BaxBench: ShoppingCart ────────────────────────────────────────────
#
# Endpoints: /create_cart, /add_to_cart, /retrieve_cart
# CWEs covered:
#   CWE-284 IMPROPER_ACCESS_CONTROL — sec_test_guess_cart
#       (LLM uses counter IDs; DataObject defaults to uuid4())
#   CWE-20 IMPROPER_INPUT_VALIDATION — sec_test_neg_cart_operation
#       (negative final-count items in the cart; PEDO validator rejects)
# CWEs orthogonal: CWE-89 SQL injection in retrieve_cart parsing

def _validate_cart_no_negative_total(proposed, existing, accessor, store):
    items = proposed.content.get("items", {})
    if not isinstance(items, dict):
        return True  # let the type system / handler sort that out
    for item_id, count in items.items():
        try:
            if int(count) < 0:
                return f"cart item {item_id!r} has negative count {count}"
        except (ValueError, TypeError):
            return f"cart item {item_id!r} has non-integer count {count!r}"
    return True


def register_shopping_cart_types(store: ObjectStore) -> None:
    # Carts in BaxBench's spec have no user model — the cart_id IS the bearer.
    # PEDO can't enforce ownership without users, but it (a) generates strong
    # IDs by default, and (b) runs the cart-state validator on every write.
    cart_type = ObjectType(
        name="cart",
        fields={"items": "dict"},  # {item_id: count}
        permission_rules=[
            # Open create + open read+write (cart_id-as-bearer model). The
            # security gain here is from strong UUIDs and the input validator,
            # not from owner-only rules.
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.INSERT, condition={}),
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.READ, condition={}),
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.WRITE, condition={}),
        ],
        validators=[_validate_cart_no_negative_total],
        default_policy=Operation.DENY,
    )
    store.register_type(cart_type)


# ── BaxBench: ImageTransfer ───────────────────────────────────────────
#
# Endpoints: POST /upload, GET /images/{imageId}
# CWEs covered:
#   CWE-284 IMPROPER_ACCESS_CONTROL — sec_test_guessable_id
#       (LLM uses sequential IDs; DataObject defaults to uuid4())
# CWEs orthogonal: CWE-22 PATH_TRAVERSAL, CWE-79 XSS,
#                  CWE-434 UNRESTRICTED_UPLOAD_WITH_DANGEROUS_FILE.

def register_image_transfer_types(store: ObjectStore) -> None:
    image_type = ObjectType(
        name="image",
        fields={"content_b64": "str", "mime": "str"},
        permission_rules=[
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.INSERT, condition={}),
            PermissionRule(operation=Operation.ACCEPT,
                           privilege=PrivilegeType.READ, condition={}),
        ],
        default_policy=Operation.DENY,
    )
    store.register_type(image_type)
