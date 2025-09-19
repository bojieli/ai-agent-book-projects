# Copyright Sierra

import json
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool


class ExchangeDeliveredOrderItems(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        order_id: str,
        item_ids: List[str],
        new_item_ids: List[str],
        payment_method_id: str,
    ) -> str:
        products, orders, users = data["products"], data["orders"], data["users"]

        # check order exists and is delivered
        if order_id not in orders:
            return "Error: order not found"
        order = orders[order_id]
        if order["status"] != "delivered":
            return "Error: non-delivered order cannot be exchanged"

        # check the items to be exchanged exist
        all_item_ids = [item["item_id"] for item in order["items"]]
        for item_id in item_ids:
            if item_ids.count(item_id) > all_item_ids.count(item_id):
                return f"Error: {item_id} not found"

        # check new items exist and match old items and are available
        if len(item_ids) != len(new_item_ids):
            return "Error: the number of items to be exchanged should match"

        diff_price = 0
        for item_id, new_item_id in zip(item_ids, new_item_ids):
            item = [item for item in order["items"] if item["item_id"] == item_id][0]
            product_id = item["product_id"]
            if not (
                new_item_id in products[product_id]["variants"]
                and products[product_id]["variants"][new_item_id]["available"]
            ):
                return f"Error: new item {new_item_id} not found or available"

            old_price = item["price"]
            new_price = products[product_id]["variants"][new_item_id]["price"]
            diff_price += new_price - old_price

        diff_price = round(diff_price, 2)

        # check payment method exists and can cover the price difference if gift card
        if payment_method_id not in users[order["user_id"]]["payment_methods"]:
            return "Error: payment method not found"

        payment_method = users[order["user_id"]]["payment_methods"][payment_method_id]
        if (
            payment_method["source"] == "gift_card"
            and payment_method["balance"] < diff_price
        ):
            return (
                "Error: insufficient gift card balance to pay for the price difference"
            )

        # modify the order
        order["status"] = "exchange requested"
        order["exchange_items"] = sorted(item_ids)
        order["exchange_new_items"] = sorted(new_item_ids)
        order["exchange_payment_method_id"] = payment_method_id
        order["exchange_price_difference"] = diff_price

        return json.dumps(order)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "exchange_delivered_order_items",
                "description": (
                    "Exchange items in a delivered order to new items of the same product type. "
                    "For a delivered order, return or exchange can be only done once by the agent. "
                    "The agent needs to explain the exchange detail and ask for explicit user confirmation (yes/no) to proceed."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.",
                        },
                        "item_ids": {
                            "type": "array",
                            "items": {
                                "type": "string",
                            },
                            "description": "The item ids to be exchanged, each such as '1008292230'. There could be duplicate items in the list.",
                        },
                        "new_item_ids": {
                            "type": "array",
                            "items": {
                                "type": "string",
                            },
                            "description": (
                                "The item ids to be exchanged for, each such as '1008292230'. "
                                "There could be duplicate items in the list. Each new item id should match the item id in the same position and be of the same product."
                            ),
                        },
                        "payment_method_id": {
                            "type": "string",
                            "description": (
                                "The payment method id to pay or receive refund for the item price difference, "
                                "such as 'gift_card_0000000' or 'credit_card_0000000'. These can be looked up from the user or order details."
                            ),
                        },
                    },
                    "required": [
                        "order_id",
                        "item_ids",
                        "new_item_ids",
                        "payment_method_id",
                    ],
                },
            },
        }
