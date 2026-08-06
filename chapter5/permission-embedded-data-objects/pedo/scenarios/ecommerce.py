"""Case study: E-commerce orders.

Architectural pattern demonstrated: **compound state machine + reactions**.
An order moves through cart -> placed -> paid -> shipped -> delivered, with
refund inverting the state from delivered back to refunded. Each transition
has invariants (placed orders cannot be modified; only paid orders can ship).
The state-machine validator + reactions handle the bookkeeping; the handler
just describes the user intent (place / pay / ship / refund).

Object types: customer, product, order, order_item, audit_log
Key invariants:
  - order status follows: cart -> placed -> paid -> shipped -> delivered, or any -> cancelled, delivered -> refunded
  - only the order owner can place / cancel; only admin can ship; only paid orders can ship
  - inventory decremented on payment (via reaction)
  - refund inverts inventory (via reaction)
"""
from __future__ import annotations

from pedo.core.models import (
    AccessContext, DataObject, ObjectType, Operation,
    PermissionRule, PrivilegeType, ReactionDeclaration,
    Relationship, RelationshipAction,
)
from pedo.core.store import ObjectStore


ORDER_TRANSITIONS = {
    None: ["cart"],
    "cart": ["placed", "cancelled"],
    "placed": ["paid", "cancelled"],
    "paid": ["shipped", "refunded"],     # paid can be refunded
    "shipped": ["delivered"],
    "delivered": ["refunded"],            # delivered can be refunded
    "cancelled": [],
    "refunded": [],
}


def validate_order_status(proposed, existing, accessor, store):
    new_status = proposed.content.get("status")
    if existing is None:
        if new_status not in ("cart", None):
            return f"New orders must start as 'cart', got {new_status!r}"
        return True
    old_status = existing.content.get("status")
    if new_status and new_status != old_status:
        valid = ORDER_TRANSITIONS.get(old_status, [])
        if new_status not in valid:
            return f"Invalid order transition {old_status} -> {new_status}; valid: {valid}"
    return True


def validate_only_paid_can_ship(proposed, existing, accessor, store):
    if existing is None:
        return True
    if proposed.content.get("status") == "shipped":
        if existing.content.get("status") != "paid":
            return f"Only paid orders can ship; current status is {existing.content.get('status')}"
    return True


def adjust_inventory_on_state_change(event, store):
    """Reaction: decrement inventory on 'paid', increment on 'refunded'."""
    sys_ctx = AccessContext(user_id="system", role="system", org_id=event["object_org"])
    new_status = event["object_content"].get("status")
    if new_status not in ("paid", "refunded"):
        return
    direction = -1 if new_status == "paid" else +1
    # Find order_items for this order, adjust each product's stock
    order_id = event["object_id"]
    items = store.raw_query("order_item")
    for item in items:
        if item.content.get("order_id") != order_id:
            continue
        product_id = item.content.get("product_id")
        qty = item.content.get("quantity", 0)
        product = store.raw_read(product_id)
        if product is None:
            continue
        current = product.content.get("stock", 0)
        store.update(product_id, {"stock": current + direction * qty},
                     sys_ctx, _reaction_depth=event["depth"])


def register_ecommerce_types(store: ObjectStore) -> None:
    store.register_reaction_handler("adjust_inventory_on_state_change",
                                    adjust_inventory_on_state_change)

    store.register_type(ObjectType(
        name="customer",
        fields={"name": "str", "email": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"is_owner": True}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
        ],
        default_policy=Operation.DENY,
    ))

    store.register_type(ObjectType(
        name="product",
        fields={"name": "str", "price": "int", "stock": "int"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {}),  # public catalog
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "admin"}),
            # Stock writes only via reactions (system role)
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "system"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "admin"}),
        ],
        default_policy=Operation.DENY,
    ))

    store.register_type(ObjectType(
        name="order",
        fields={"status": "str", "total": "int"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"is_owner": True}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
            # Owner can update during cart/place/cancel; admin can ship; system runs reactions.
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"is_owner": True}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "system"}),
        ],
        validators=[validate_order_status, validate_only_paid_can_ship],
        reactions=[
            ReactionDeclaration(event="after_update:status",
                                 handler="adjust_inventory_on_state_change"),
        ],
        default_policy=Operation.DENY,
    ))

    store.register_type(ObjectType(
        name="order_item",
        fields={"order_id": "str", "product_id": "str", "quantity": "int", "unit_price": "int"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"is_owner": True}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
        ],
        relationships=[
            Relationship(name="order", target_type="order",
                         on_delete=RelationshipAction.CASCADE),
            Relationship(name="product", target_type="product",
                         on_delete=RelationshipAction.RESTRICT),
        ],
        default_policy=Operation.DENY,
    ))
