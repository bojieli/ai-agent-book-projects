# Copyright Sierra

import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool


class ModifyUserAddress(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        user_id: str,
        address1: str,
        address2: str,
        city: str,
        state: str,
        country: str,
        zip: str,
    ) -> str:
        users = data["users"]
        if user_id not in users:
            return "Error: user not found"
        user = users[user_id]
        user["address"] = {
            "address1": address1,
            "address2": address2,
            "city": city,
            "state": state,
            "country": country,
            "zip": zip,
        }
        return json.dumps(user)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "modify_user_address",
                "description": "Modify the default address of a user. The agent needs to explain the modification detail and ask for explicit user confirmation (yes/no) to proceed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "The user id, such as 'sara_doe_496'.",
                        },
                        "address1": {
                            "type": "string",
                            "description": "The first line of the address, such as '123 Main St'.",
                        },
                        "address2": {
                            "type": "string",
                            "description": "The second line of the address, such as 'Apt 1' or ''.",
                        },
                        "city": {
                            "type": "string",
                            "description": "The city, such as 'San Francisco'.",
                        },
                        "state": {
                            "type": "string",
                            "description": "The state, such as 'CA'.",
                        },
                        "country": {
                            "type": "string",
                            "description": "The country, such as 'USA'.",
                        },
                        "zip": {
                            "type": "string",
                            "description": "The zip code, such as '12345'.",
                        },
                    },
                    "required": [
                        "user_id",
                        "address1",
                        "address2",
                        "city",
                        "state",
                        "country",
                        "zip",
                    ],
                },
            },
        }
