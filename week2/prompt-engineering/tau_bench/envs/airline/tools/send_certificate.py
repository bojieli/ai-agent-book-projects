# Copyright Sierra

from typing import Any, Dict
from tau_bench.envs.tool import Tool


class SendCertificate(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        user_id: str,
        amount: int,
    ) -> str:
        users = data["users"]
        if user_id not in users:
            return "Error: user not found"
        user = users[user_id]

        # add a certificate, assume at most 3 cases per task
        for id in [3221322, 3221323, 3221324]:
            payment_id = f"certificate_{id}"
            if payment_id not in user["payment_methods"]:
                user["payment_methods"][payment_id] = {
                    "source": "certificate",
                    "amount": amount,
                    "id": payment_id,
                }
                return f"Certificate {payment_id} added to user {user_id} with amount {amount}."

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "send_certificate",
                "description": "Send a certificate to a user. Be careful!",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "The ID of the user to book the reservation, such as 'sara_doe_496'.",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Certificate amount to send.",
                        },
                    },
                    "required": ["user_id", "amount"],
                },
            },
        }
