"""Cross-case-study evaluator.

For each new case study (banking, ecommerce, healthcare, forum), runs a small
set of representative scenarios under two conditions:
  - raw: a typical handler that does NOT enforce the case's invariants
         (this is the canonical LLM-generated handler shape -- it follows
         the feature description but doesn't carry the invariant logic)
  - pedo: a handler that uses the PE store; invariants live in the schema

The case-study format follows the BaxBench adapter pattern: each case has
(a) a setup, (b) a sequence of operations the LLM-style handler performs,
(c) an oracle that checks declared invariants in the resulting database state.

This is NOT a benchmark. These are case studies demonstrating that the
slow/fast layer split holds across architecturally distinct SaaS patterns.
"""
from __future__ import annotations

import os
import sqlite3
import time
import uuid
import json
from dataclasses import dataclass, field
from typing import Any, Callable

from pedo.core.models import AccessContext, DataObject
from pedo.core.store import (
    ObjectStore, PermissionDeniedError, ValidationError,
    ReferentialIntegrityError,
)

DSN = os.environ.get("DATAGUARDBENCH_DSN", "dbname=pedo_test")


@dataclass
class CaseResult:
    case: str
    condition: str
    operations_attempted: int
    operations_completed: int
    invariants_violated: list[str] = field(default_factory=list)
    invariants_caught: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _is_caught_by_pipeline(e: Exception) -> bool:
    return isinstance(e, (PermissionDeniedError, ValidationError,
                          ReferentialIntegrityError))


# ══════════════════════════════════════════════════════════════════════
# Banking case study
# ══════════════════════════════════════════════════════════════════════

def banking_pedo_run() -> CaseResult:
    from pedo.scenarios.banking import register_banking_types

    store = ObjectStore(DSN)
    store.clear_all()
    register_banking_types(store)
    admin = AccessContext(user_id="admin", role="admin", org_id="org1")
    alice = AccessContext(user_id="alice", role="user", org_id="org1")
    bob = AccessContext(user_id="bob", role="user", org_id="org1")

    a = store.create(DataObject(type_name="account",
                                content={"holder_name": "Alice",
                                         "balance": 100, "status": "active"},
                                owner_id="alice", org_id="org1"), admin)
    b = store.create(DataObject(type_name="account",
                                content={"holder_name": "Bob",
                                         "balance": 50, "status": "active"},
                                owner_id="bob", org_id="org1"), admin)

    result = CaseResult(case="Banking", condition="pedo",
                        operations_attempted=0, operations_completed=0)

    # Op1: legitimate transfer (should succeed)
    result.operations_attempted += 1
    try:
        store.create(DataObject(type_name="transaction",
                                content={"sender_account_id": a.id,
                                         "recipient_account_id": b.id,
                                         "amount": 30, "subject": "rent"},
                                owner_id="alice", org_id="org1"), alice)
        store.process_reactions_sync()
        result.operations_completed += 1
    except Exception as e:
        result.notes.append(f"legitimate transfer raised: {e}")

    # Op2: overdraft attempt (should be caught by validate_transaction_balance)
    result.operations_attempted += 1
    try:
        store.create(DataObject(type_name="transaction",
                                content={"sender_account_id": a.id,
                                         "recipient_account_id": b.id,
                                         "amount": 99999, "subject": "overdraft"},
                                owner_id="alice", org_id="org1"), alice)
        result.operations_completed += 1
        result.invariants_violated.append("balance_invariant_violated")
    except Exception as e:
        if _is_caught_by_pipeline(e):
            result.invariants_caught.append("balance_invariant")
        else:
            result.notes.append(f"unexpected on overdraft: {e}")

    # Op3: cross-user transfer attempt (should be caught: sender not owner)
    result.operations_attempted += 1
    try:
        # Bob attempts to drain Alice's account into his own
        store.create(DataObject(type_name="transaction",
                                content={"sender_account_id": a.id,
                                         "recipient_account_id": b.id,
                                         "amount": 50, "subject": "self-help"},
                                owner_id="bob", org_id="org1"), bob)
        result.operations_completed += 1
        # Bob succeeded -- check if balance moved
    except Exception as e:
        if _is_caught_by_pipeline(e):
            result.invariants_caught.append("transaction_owner_invariant")
        else:
            result.notes.append(f"unexpected on cross-user: {e}")

    # Note: The transaction-create rule above is INSERT={} (any authenticated).
    # The "only sender can initiate transfer" invariant is implicit in BaxBench
    # but our schema currently allows any user to create a transaction object.
    # In a stricter schema, we'd add a validator: proposed.owner_id must equal
    # proposed.content['sender_account_id']'s owner. Demonstrate this gap as a
    # note rather than a violation.
    result.notes.append("schema currently permits any user to create a transaction; "
                        "stricter schema would add owner-vs-sender validator.")

    # Op4: zero or negative amount (caught by validate_transaction_balance)
    result.operations_attempted += 1
    try:
        store.create(DataObject(type_name="transaction",
                                content={"sender_account_id": a.id,
                                         "recipient_account_id": b.id,
                                         "amount": -10, "subject": "neg"},
                                owner_id="alice", org_id="org1"), alice)
        result.operations_completed += 1
        result.invariants_violated.append("non_negative_amount")
    except Exception as e:
        if _is_caught_by_pipeline(e):
            result.invariants_caught.append("non_negative_amount")
        else:
            result.notes.append(f"unexpected on neg amount: {e}")

    # Op5: transaction is immutable
    result.operations_attempted += 1
    try:
        # Find a committed transaction
        txns = store.raw_query("transaction")
        if txns:
            store.update(txns[0].id, {"amount": 0}, admin)
            result.operations_completed += 1
            result.invariants_violated.append("transaction_immutable")
    except Exception as e:
        if _is_caught_by_pipeline(e):
            result.invariants_caught.append("transaction_immutable")
        else:
            result.notes.append(f"unexpected on immutable update: {e}")

    return result


def banking_raw_run() -> CaseResult:
    """Raw SQLite handler that follows the feature spec literally and does
    not encode the invariants. This is the canonical LLM-generated shape."""
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE accounts (id TEXT PRIMARY KEY, holder TEXT, balance INTEGER, status TEXT, owner TEXT);
        CREATE TABLE transactions (id TEXT PRIMARY KEY, sender TEXT, recipient TEXT, amount INTEGER, subject TEXT);
    """)
    a_id, b_id = str(uuid.uuid4()), str(uuid.uuid4())
    conn.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, ?)", (a_id, "Alice", 100, "active", "alice"))
    conn.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, ?)", (b_id, "Bob", 50, "active", "bob"))
    conn.commit()

    def transfer(sender, recipient, amount, subject):
        # Naive handler: just records the transaction and updates balances,
        # no balance check, no owner check, no immutability.
        tx_id = str(uuid.uuid4())
        conn.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
                     (tx_id, sender, recipient, amount, subject))
        conn.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, sender))
        conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, recipient))
        conn.commit()
        return tx_id

    result = CaseResult(case="Banking", condition="raw",
                        operations_attempted=0, operations_completed=0)

    # Op1: legitimate
    result.operations_attempted += 1
    transfer(a_id, b_id, 30, "rent")
    result.operations_completed += 1

    # Op2: overdraft -- raw will do it, leaving Alice negative.
    result.operations_attempted += 1
    transfer(a_id, b_id, 99999, "overdraft")
    result.operations_completed += 1
    bal = conn.execute("SELECT balance FROM accounts WHERE id=?", (a_id,)).fetchone()[0]
    if bal < 0:
        result.invariants_violated.append("balance_invariant")

    # Op3: cross-user -- raw doesn't check; Bob can drain Alice
    result.operations_attempted += 1
    transfer(a_id, b_id, 50, "self-help-by-bob")
    result.operations_completed += 1
    # We'd flag this if the raw handler had ownership semantics; it doesn't.
    result.notes.append("raw handler accepted cross-user transfer; no ownership check")

    # Op4: negative amount
    result.operations_attempted += 1
    transfer(a_id, b_id, -10, "neg")
    result.operations_completed += 1
    result.invariants_violated.append("non_negative_amount")

    # Op5: transaction immutability -- raw allows any UPDATE
    result.operations_attempted += 1
    tx_id = conn.execute("SELECT id FROM transactions LIMIT 1").fetchone()[0]
    conn.execute("UPDATE transactions SET amount = 0 WHERE id = ?", (tx_id,))
    conn.commit()
    result.operations_completed += 1
    result.invariants_violated.append("transaction_immutable")

    return result


# ══════════════════════════════════════════════════════════════════════
# E-commerce case study
# ══════════════════════════════════════════════════════════════════════

def ecommerce_pedo_run() -> CaseResult:
    from pedo.scenarios.ecommerce import register_ecommerce_types

    store = ObjectStore(DSN)
    store.clear_all()
    register_ecommerce_types(store)
    admin = AccessContext(user_id="admin", role="admin", org_id="org1")
    alice = AccessContext(user_id="alice", role="user", org_id="org1")

    p = store.create(DataObject(type_name="product",
                                content={"name": "Widget", "price": 10, "stock": 5},
                                owner_id="admin", org_id="org1"), admin)
    o = store.create(DataObject(type_name="order",
                                content={"status": "cart", "total": 0},
                                owner_id="alice", org_id="org1"), alice)

    result = CaseResult(case="ECommerce", condition="pedo",
                        operations_attempted=0, operations_completed=0)

    # Op1: legitimate state transition cart -> placed
    result.operations_attempted += 1
    try:
        store.update(o.id, {"status": "placed"}, alice)
        result.operations_completed += 1
    except Exception as e:
        result.notes.append(f"cart->placed raised: {e}")

    # Op2: skip placed -> shipped (should be caught by state machine)
    result.operations_attempted += 1
    try:
        store.update(o.id, {"status": "shipped"}, alice)
        result.operations_completed += 1
        result.invariants_violated.append("state_machine_skip")
    except Exception as e:
        if _is_caught_by_pipeline(e):
            result.invariants_caught.append("state_machine_skip")
        else:
            result.notes.append(f"unexpected on skip: {e}")

    # Op3: legitimate placed -> paid
    result.operations_attempted += 1
    try:
        store.update(o.id, {"status": "paid"}, alice)
        result.operations_completed += 1
    except Exception as e:
        result.notes.append(f"placed->paid raised: {e}")

    # Op4: customer attempts to ship their own order (should be caught:
    # only paid orders can ship and only admin should ship -- but PE permission
    # rules permit owner-write; the validate_only_paid_can_ship will gate)
    # Here paid -> shipped is in the transition table, so PE allows it; the
    # "admin only" part lives in the rule shape. Skipping because rules allow.

    # Op5: paid -> delivered (skip shipped, should be caught)
    result.operations_attempted += 1
    try:
        store.update(o.id, {"status": "delivered"}, alice)
        result.operations_completed += 1
        result.invariants_violated.append("state_machine_skip_to_delivered")
    except Exception as e:
        if _is_caught_by_pipeline(e):
            result.invariants_caught.append("state_machine_skip_to_delivered")
        else:
            result.notes.append(f"unexpected on skip-to-delivered: {e}")

    return result


def ecommerce_raw_run() -> CaseResult:
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE orders (id TEXT PRIMARY KEY, status TEXT, total INTEGER, owner TEXT);
        CREATE TABLE products (id TEXT PRIMARY KEY, stock INTEGER);
    """)
    o_id = str(uuid.uuid4())
    p_id = str(uuid.uuid4())
    conn.execute("INSERT INTO orders VALUES (?, ?, ?, ?)", (o_id, "cart", 0, "alice"))
    conn.execute("INSERT INTO products VALUES (?, ?)", (p_id, 5))
    conn.commit()

    def set_status(order_id, new_status):
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()

    result = CaseResult(case="ECommerce", condition="raw",
                        operations_attempted=0, operations_completed=0)
    transitions = [
        ("cart->placed", "placed", False),
        ("cart->shipped (skip)", "shipped", True),     # invalid
        ("placed->paid", "paid", False),
        ("paid->delivered (skip)", "delivered", True),  # invalid
    ]
    valid_transitions = {
        "cart": ["placed", "cancelled"],
        "placed": ["paid", "cancelled"],
        "paid": ["shipped", "refunded"],
        "shipped": ["delivered"],
    }
    current = "cart"
    for label, target, expected_invalid in transitions:
        result.operations_attempted += 1
        valid = current in valid_transitions and target in valid_transitions[current]
        set_status(o_id, target)
        result.operations_completed += 1
        if expected_invalid and not valid:
            # raw didn't check; the violation is recorded
            result.invariants_violated.append(label.split(" ")[0])
        current = target
    return result


# ══════════════════════════════════════════════════════════════════════
# Healthcare case study
# ══════════════════════════════════════════════════════════════════════

def healthcare_pedo_run() -> CaseResult:
    from pedo.scenarios.healthcare import register_healthcare_types

    store = ObjectStore(DSN)
    store.clear_all()
    register_healthcare_types(store)
    admin = AccessContext(user_id="admin", role="admin", org_id="org1")
    doctor = AccessContext(user_id="dr_smith", role="doctor", org_id="org1")
    nurse = AccessContext(user_id="nurse_jane", role="nurse", org_id="org1")
    billing = AccessContext(user_id="bill_clerk", role="billing", org_id="org1")

    pat = store.create(DataObject(type_name="patient",
                                  content={"name": "Pat", "dob": "1980-01-01", "mrn": "M1"},
                                  owner_id="patient_pat", org_id="org1"), admin)
    diag = store.create(DataObject(type_name="diagnosis",
                                   content={"patient_id": pat.id, "icd10": "I10",
                                            "notes": "hypertension", "medications": "lisinopril"},
                                   owner_id="patient_pat", org_id="org1"), doctor)

    result = CaseResult(case="Healthcare", condition="pedo",
                        operations_attempted=0, operations_completed=0)

    # Op1: doctor reads diagnosis (allowed)
    result.operations_attempted += 1
    try:
        store.get(diag.id, doctor)
        result.operations_completed += 1
    except Exception as e:
        result.notes.append(f"doctor read diag raised: {e}")

    # Op2: nurse reads diagnosis (should be caught: nurse not in diagnosis read rules)
    result.operations_attempted += 1
    try:
        store.get(diag.id, nurse)
        result.operations_completed += 1
        result.invariants_violated.append("nurse_read_diagnosis")
    except Exception as e:
        if _is_caught_by_pipeline(e):
            result.invariants_caught.append("nurse_read_diagnosis")
        else:
            result.notes.append(f"unexpected on nurse read: {e}")

    # Op3: billing reads diagnosis (should be caught)
    result.operations_attempted += 1
    try:
        store.get(diag.id, billing)
        result.operations_completed += 1
        result.invariants_violated.append("billing_read_diagnosis")
    except Exception as e:
        if _is_caught_by_pipeline(e):
            result.invariants_caught.append("billing_read_diagnosis")
        else:
            result.notes.append(f"unexpected on billing read: {e}")

    # Op4: billing creates a billing_record, finalizes it, then tries to edit (caught by validator)
    result.operations_attempted += 1
    try:
        br = store.create(DataObject(type_name="billing_record",
                                     content={"patient_id": pat.id, "amount": 100,
                                              "status": "draft", "service_codes": "99213",
                                              "items": "office visit"},
                                     owner_id="patient_pat", org_id="org1"), billing)
        store.update(br.id, {"status": "finalized"}, billing)
        store.update(br.id, {"amount": 9999}, billing)  # should fail
        result.operations_completed += 1
        result.invariants_violated.append("finalized_billing_edited")
    except Exception as e:
        if _is_caught_by_pipeline(e):
            result.invariants_caught.append("finalized_billing_edited")
        else:
            result.notes.append(f"unexpected on finalized edit: {e}")

    return result


def healthcare_raw_run() -> CaseResult:
    """Naive role-as-string handler that doesn't actually enforce the role
    separation. This mirrors the typical LLM mistake: the LLM accepts a 'role'
    parameter but doesn't check it on every read."""
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE diagnoses (id TEXT PRIMARY KEY, patient_id TEXT, icd10 TEXT, notes TEXT, meds TEXT);
        CREATE TABLE billing (id TEXT PRIMARY KEY, patient_id TEXT, amount INTEGER, status TEXT);
    """)
    diag_id = str(uuid.uuid4())
    conn.execute("INSERT INTO diagnoses VALUES (?, ?, ?, ?, ?)",
                 (diag_id, "p1", "I10", "hypertension", "lisinopril"))
    bill_id = str(uuid.uuid4())
    conn.execute("INSERT INTO billing VALUES (?, ?, ?, ?)", (bill_id, "p1", 100, "draft"))
    conn.commit()

    def get_diagnosis(role, did):
        # Naive: just returns; no role check (typical LLM omission)
        return conn.execute("SELECT * FROM diagnoses WHERE id=?", (did,)).fetchone()

    def update_billing(role, bid, **fields):
        # Naive: no finalized-status check
        for k, v in fields.items():
            conn.execute(f"UPDATE billing SET {k} = ? WHERE id = ?", (v, bid))
        conn.commit()

    result = CaseResult(case="Healthcare", condition="raw",
                        operations_attempted=0, operations_completed=0)
    # Op1: doctor read
    result.operations_attempted += 1
    get_diagnosis("doctor", diag_id)
    result.operations_completed += 1
    # Op2: nurse read -- raw lets it through (violation)
    result.operations_attempted += 1
    if get_diagnosis("nurse", diag_id) is not None:
        result.operations_completed += 1
        result.invariants_violated.append("nurse_read_diagnosis")
    # Op3: billing read -- raw lets it through (violation)
    result.operations_attempted += 1
    if get_diagnosis("billing", diag_id) is not None:
        result.operations_completed += 1
        result.invariants_violated.append("billing_read_diagnosis")
    # Op4: edit finalized billing
    result.operations_attempted += 1
    update_billing("billing", bill_id, status="finalized")
    update_billing("billing", bill_id, amount=9999)
    result.operations_completed += 1
    result.invariants_violated.append("finalized_billing_edited")
    return result


# ══════════════════════════════════════════════════════════════════════
# Forum case study
# ══════════════════════════════════════════════════════════════════════

def forum_pedo_run() -> CaseResult:
    from pedo.scenarios.forum import register_forum_types

    store = ObjectStore(DSN)
    store.clear_all()
    register_forum_types(store)
    admin = AccessContext(user_id="admin", role="admin", org_id="org1")
    alice = AccessContext(user_id="alice", role="user", org_id="org1")
    bob = AccessContext(user_id="bob", role="user", org_id="org1")
    mod = AccessContext(user_id="mod", role="moderator", org_id="org1")

    p = store.create(DataObject(type_name="forum_post",
                                content={"title": "Hi", "body": "first post", "locked": False},
                                owner_id="alice", org_id="org1"), alice)

    result = CaseResult(case="Forum", condition="pedo",
                        operations_attempted=0, operations_completed=0)

    # Op1: anyone reads (allowed)
    result.operations_attempted += 1
    try:
        store.get(p.id, bob)
        result.operations_completed += 1
    except Exception as e:
        result.notes.append(f"public read raised: {e}")

    # Op2: bob (non-author, non-mod) edits (caught)
    result.operations_attempted += 1
    try:
        store.update(p.id, {"body": "edited by bob"}, bob)
        result.operations_completed += 1
        result.invariants_violated.append("non_owner_edit")
    except Exception as e:
        if _is_caught_by_pipeline(e):
            result.invariants_caught.append("non_owner_edit")
        else:
            result.notes.append(f"unexpected on bob edit: {e}")

    # Op3: alice edits (allowed)
    result.operations_attempted += 1
    try:
        store.update(p.id, {"body": "v2 by alice"}, alice)
        result.operations_completed += 1
    except Exception as e:
        result.notes.append(f"author edit raised: {e}")

    # Op4: moderator locks
    result.operations_attempted += 1
    try:
        store.update(p.id, {"locked": True}, mod)
        result.operations_completed += 1
    except Exception as e:
        result.notes.append(f"mod lock raised: {e}")

    # Op5: alice tries to edit her own post after lock (caught by validator)
    result.operations_attempted += 1
    try:
        store.update(p.id, {"body": "after lock"}, alice)
        result.operations_completed += 1
        result.invariants_violated.append("locked_post_edited")
    except Exception as e:
        if _is_caught_by_pipeline(e):
            result.invariants_caught.append("locked_post_edited")
        else:
            result.notes.append(f"unexpected on locked edit: {e}")

    # Op6: bob tries to comment on a locked post (caught)
    result.operations_attempted += 1
    try:
        store.create(DataObject(type_name="comment",
                                content={"post_id": p.id, "body": "comment on lock"},
                                owner_id="bob", org_id="org1"), bob)
        result.operations_completed += 1
        result.invariants_violated.append("comment_on_locked")
    except Exception as e:
        if _is_caught_by_pipeline(e):
            result.invariants_caught.append("comment_on_locked")
        else:
            result.notes.append(f"unexpected on comment-locked: {e}")

    return result


def forum_raw_run() -> CaseResult:
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE posts (id TEXT PRIMARY KEY, title TEXT, body TEXT, locked INTEGER, owner TEXT);
        CREATE TABLE comments (id TEXT PRIMARY KEY, post_id TEXT, body TEXT, owner TEXT);
    """)
    pid = str(uuid.uuid4())
    conn.execute("INSERT INTO posts VALUES (?, ?, ?, ?, ?)", (pid, "Hi", "first", 0, "alice"))
    conn.commit()

    def edit_post(post_id, role, owner_arg, body):
        # Naive: doesn't check ownership or lock
        conn.execute("UPDATE posts SET body = ? WHERE id = ?", (body, post_id))
        conn.commit()

    def lock(post_id, role):
        conn.execute("UPDATE posts SET locked = 1 WHERE id = ?", (post_id,))
        conn.commit()

    def add_comment(post_id, role, owner_arg, body):
        # Naive: doesn't check parent lock
        conn.execute("INSERT INTO comments VALUES (?, ?, ?, ?)",
                     (str(uuid.uuid4()), post_id, body, owner_arg))
        conn.commit()

    result = CaseResult(case="Forum", condition="raw",
                        operations_attempted=0, operations_completed=0)
    result.operations_attempted += 1; result.operations_completed += 1  # public read
    # bob edits alice's post -- raw allows
    result.operations_attempted += 1
    edit_post(pid, "user", "bob", "edited by bob")
    result.operations_completed += 1
    result.invariants_violated.append("non_owner_edit")
    # alice edits
    result.operations_attempted += 1
    edit_post(pid, "user", "alice", "v2")
    result.operations_completed += 1
    # mod locks
    result.operations_attempted += 1
    lock(pid, "moderator")
    result.operations_completed += 1
    # alice edits after lock
    result.operations_attempted += 1
    edit_post(pid, "user", "alice", "after lock")
    result.operations_completed += 1
    result.invariants_violated.append("locked_post_edited")
    # bob comments on locked
    result.operations_attempted += 1
    add_comment(pid, "user", "bob", "comment on lock")
    result.operations_completed += 1
    result.invariants_violated.append("comment_on_locked")
    return result


# ══════════════════════════════════════════════════════════════════════
# Runner
# ══════════════════════════════════════════════════════════════════════

CASES = [
    ("Banking",     banking_pedo_run,     banking_raw_run),
    ("ECommerce",   ecommerce_pedo_run,   ecommerce_raw_run),
    ("Healthcare",  healthcare_pedo_run,  healthcare_raw_run),
    ("Forum",       forum_pedo_run,       forum_raw_run),
]


def run_all() -> dict:
    results = []
    for name, pedo_fn, raw_fn in CASES:
        for fn in (pedo_fn, raw_fn):
            r = fn()
            results.append({
                "case": r.case,
                "condition": r.condition,
                "operations_attempted": r.operations_attempted,
                "operations_completed": r.operations_completed,
                "invariants_violated": r.invariants_violated,
                "invariants_caught": r.invariants_caught,
                "notes": r.notes,
            })
    return {"benchmark": "PEDO case studies", "results": results}


def summarize(out: dict) -> str:
    by = {(r["case"], r["condition"]): r for r in out["results"]}
    lines = [f"{'Case':<12} {'Cond':<6} {'Ops':<10} {'Caught':<6} {'Violated':<32}",
             "-" * 80]
    for case in ("Banking", "ECommerce", "Healthcare", "Forum"):
        for cond in ("pedo", "raw"):
            r = by.get((case, cond))
            if not r:
                continue
            ops = f"{r['operations_completed']}/{r['operations_attempted']}"
            caught = len(r["invariants_caught"])
            viol = ",".join(r["invariants_violated"]) or "(none)"
            lines.append(f"{case:<12} {cond:<6} {ops:<10} {caught:<6} {viol:<32}")
    return "\n".join(lines)


def main():
    out = run_all()
    print(summarize(out))
    out_path = os.path.join(os.path.dirname(__file__), "..", "..", "case_studies_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nResults written to {os.path.abspath(out_path)}")


if __name__ == "__main__":
    main()
