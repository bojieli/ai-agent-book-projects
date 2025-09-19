# Copyright Sierra

import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool


class ListAllProductTypes(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any]) -> str:
        products = data["products"]
        product_dict = {
            product["name"]: product["product_id"] for product in products.values()
        }
        product_dict = dict(sorted(product_dict.items()))
        return json.dumps(product_dict)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_all_product_types",
                "description": "List the name and product id of all product types. Each product type has a variety of different items with unique item ids and options. There are only 50 product types in the store.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }
