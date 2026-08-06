"""Case study: Banking / transactions.

Architectural pattern demonstrated: **cross-object balance invariant**.
A transaction's validity depends on the sender account's current balance --
the validator must read related state (the sender account) and compare to the
proposed change. This pattern doesn't fit single-table CHECK constraints; it
requires a runtime validator that reads cross-object state at write time.

Object types: account, transaction, audit_log
Key invariants:
  - sender_account.balance >= amount before transaction commits
  - account ownership: only the account's owner can initiate transfers
  - transactions are immutable after creation (no UPDATE)
  - balance updates are reactions, not direct writes (single source of truth)
"""
from __future__ import annotations

from pedo.core.models import (
    AccessContext, DataObject, ObjectType, Operation,
    PermissionRule, PrivilegeType, ReactionDeclaration,
    Relationship, RelationshipAction,
)
from pedo.core.store import ObjectStore


def validate_transaction_balance(proposed, existing, accessor, store):
    """Sender account must have sufficient balance for the transfer."""
    if existing is not None:
        return "Transactions are immutable; cannot UPDATE"
    sender_id = proposed.content.get("sender_account_id")
    amount = proposed.content.get("amount", 0)
    if sender_id is None or amount is None:
        return "sender_account_id and amount are required"
    if amount <= 0:
        return f"Transfer amount must be positive, got {amount}"
    sender = store.raw_read(sender_id)
    if sender is None:
        return f"Sender account {sender_id} not found"
    if sender.type_name != "account":
        return f"sender_account_id must reference an account, not {sender.type_name}"
    if sender.content.get("balance", 0) < amount:
        return (f"Insufficient balance: account has "
                f"{sender.content.get('balance', 0)}, transfer requires {amount}")
    return True


def validate_transaction_recipient_exists(proposed, existing, accessor, store):
    """Recipient account must exist and accept transfers."""
    if existing is not None:
        return True
    recipient_id = proposed.content.get("recipient_account_id")
    if not recipient_id:
        return "recipient_account_id is required"
    recipient = store.raw_read(recipient_id)
    if recipient is None or recipient.type_name != "account":
        return f"Recipient account {recipient_id} not found"
    if recipient.content.get("status") == "frozen":
        return "Recipient account is frozen"
    return True


def apply_transaction(event, store):
    """Reaction: when a transaction commits, debit sender and credit recipient.
    The handler did not have to encode this -- the schema declares it."""
    sys_ctx = AccessContext(user_id="system", role="system", org_id=event["object_org"])
    sender_id = event["object_content"]["sender_account_id"]
    recipient_id = event["object_content"]["recipient_account_id"]
    amount = event["object_content"]["amount"]

    sender = store.raw_read(sender_id)
    if sender is not None:
        store.update(sender_id,
                     {"balance": sender.content.get("balance", 0) - amount},
                     sys_ctx, _reaction_depth=event["depth"])
    recipient = store.raw_read(recipient_id)
    if recipient is not None:
        store.update(recipient_id,
                     {"balance": recipient.content.get("balance", 0) + amount},
                     sys_ctx, _reaction_depth=event["depth"])


def register_banking_types(store: ObjectStore) -> None:
    store.register_reaction_handler("apply_transaction", apply_transaction)

    # Account: owner-only management; balance is updated only by reactions.
    store.register_type(ObjectType(
        name="account",
        fields={"holder_name": "str", "balance": "int", "status": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"is_owner": True}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "auditor"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "admin"}),
            # Balance writes happen via the apply_transaction reaction (system role)
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "system"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "admin"}),
        ],
        default_policy=Operation.DENY,
    ))

    # Transaction: immutable after create; validators run cross-object checks.
    store.register_type(ObjectType(
        name="transaction",
        fields={"sender_account_id": "str", "recipient_account_id": "str",
                "amount": "int", "subject": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"is_owner": True}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "auditor"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {}),  # any authenticated user
            # No WRITE / UPDATE / DELETE rules: transactions are immutable.
        ],
        validators=[validate_transaction_balance,
                    validate_transaction_recipient_exists],
        reactions=[
            ReactionDeclaration(event="after_create", handler="apply_transaction"),
        ],
        default_policy=Operation.DENY,
    ))
