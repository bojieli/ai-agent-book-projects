# Copyright Sierra

import json
from copy import deepcopy
from typing import Any, Dict, List
from tau_bench.envs.tool import Tool


class BookReservation(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        user_id: str,
        origin: str,
        destination: str,
        flight_type: str,
        cabin: str,
        flights: List[Dict[str, Any]],
        passengers: List[Dict[str, Any]],
        payment_methods: List[Dict[str, Any]],
        total_baggages: int,
        nonfree_baggages: int,
        insurance: str,
    ) -> str:
        reservations, users = data["reservations"], data["users"]
        if user_id not in users:
            return "Error: user not found"
        user = users[user_id]

        # assume each task makes at most 3 reservations
        reservation_id = "HATHAT"
        if reservation_id in reservations:
            reservation_id = "HATHAU"
            if reservation_id in reservations:
                reservation_id = "HATHAV"

        reservation = {
            "reservation_id": reservation_id,
            "user_id": user_id,
            "origin": origin,
            "destination": destination,
            "flight_type": flight_type,
            "cabin": cabin,
            "flights": deepcopy(flights),
            "passengers": passengers,
            "payment_history": payment_methods,
            "created_at": "2024-05-15T15:00:00",
            "total_baggages": total_baggages,
            "nonfree_baggages": nonfree_baggages,
            "insurance": insurance,
        }

        # update flights and calculate price
        total_price = 0
        for flight in reservation["flights"]:
            flight_number = flight["flight_number"]
            if flight_number not in data["flights"]:
                return f"Error: flight {flight_number} not found"
            flight_data = data["flights"][flight_number]
            if flight["date"] not in flight_data["dates"]:
                return (
                    f"Error: flight {flight_number} not found on date {flight['date']}"
                )
            flight_date_data = flight_data["dates"][flight["date"]]
            if flight_date_data["status"] != "available":
                return f"Error: flight {flight_number} not available on date {flight['date']}"
            if flight_date_data["available_seats"][cabin] < len(passengers):
                return f"Error: not enough seats on flight {flight_number}"
            flight["price"] = flight_date_data["prices"][cabin]
            flight["origin"] = flight_data["origin"]
            flight["destination"] = flight_data["destination"]
            total_price += flight["price"] * len(passengers)

        if insurance == "yes":
            total_price += 30 * len(passengers)

        total_price += 50 * nonfree_baggages

        for payment_method in payment_methods:
            payment_id = payment_method["payment_id"]
            amount = payment_method["amount"]
            if payment_id not in user["payment_methods"]:
                return f"Error: payment method {payment_id} not found"
            if user["payment_methods"][payment_id]["source"] in [
                "gift_card",
                "certificate",
            ]:
                if user["payment_methods"][payment_id]["amount"] < amount:
                    return f"Error: not enough balance in payment method {payment_id}"
        if sum(payment["amount"] for payment in payment_methods) != total_price:
            return f"Error: payment amount does not add up, total price is {total_price}, but paid {sum(payment['amount'] for payment in payment_methods)}"

        # if checks pass, deduct payment and update seats
        for payment_method in payment_methods:
            payment_id = payment_method["payment_id"]
            amount = payment_method["amount"]
            if user["payment_methods"][payment_id]["source"] == "gift_card":
                user["payment_methods"][payment_id]["amount"] -= amount
            elif user["payment_methods"][payment_id]["source"] == "certificate":
                del user["payment_methods"][payment_id]

        reservations[reservation_id] = reservation
        user["reservations"].append(reservation_id)
        return json.dumps(reservation)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "book_reservation",
                "description": "Book a reservation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "The ID of the user to book the reservation, such as 'sara_doe_496'.",
                        },
                        "origin": {
                            "type": "string",
                            "description": "The IATA code for the origin city, such as 'SFO'.",
                        },
                        "destination": {
                            "type": "string",
                            "description": "The IATA code for the destination city, such as 'JFK'.",
                        },
                        "flight_type": {
                            "type": "string",
                            "enum": ["one_way", "round_trip"],
                        },
                        "cabin": {
                            "type": "string",
                            "enum": [
                                "basic_economy",
                                "economy",
                                "business",
                            ],
                        },
                        "flights": {
                            "type": "array",
                            "description": "An array of objects containing details about each piece of flight.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "flight_number": {
                                        "type": "string",
                                        "description": "Flight number, such as 'HAT001'.",
                                    },
                                    "date": {
                                        "type": "string",
                                        "description": "The date for the flight in the format 'YYYY-MM-DD', such as '2024-05-01'.",
                                    },
                                },
                                "required": ["flight_number", "date"],
                            },
                        },
                        "passengers": {
                            "type": "array",
                            "description": "An array of objects containing details about each passenger.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "first_name": {
                                        "type": "string",
                                        "description": "The first name of the passenger, such as 'Noah'.",
                                    },
                                    "last_name": {
                                        "type": "string",
                                        "description": "The last name of the passenger, such as 'Brown'.",
                                    },
                                    "dob": {
                                        "type": "string",
                                        "description": "The date of birth of the passenger in the format 'YYYY-MM-DD', such as '1990-01-01'.",
                                    },
                                },
                                "required": ["first_name", "last_name", "dob"],
                            },
                        },
                        "payment_methods": {
                            "type": "array",
                            "description": "An array of objects containing details about each payment method.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "payment_id": {
                                        "type": "string",
                                        "description": "The payment id stored in user profile, such as 'credit_card_7815826', 'gift_card_7815826', 'certificate_7815826'.",
                                    },
                                    "amount": {
                                        "type": "number",
                                        "description": "The amount to be paid.",
                                    },
                                },
                                "required": ["payment_id", "amount"],
                            },
                        },
                        "total_baggages": {
                            "type": "integer",
                            "description": "The total number of baggage items included in the reservation.",
                        },
                        "nonfree_baggages": {
                            "type": "integer",
                            "description": "The number of non-free baggage items included in the reservation.",
                        },
                        "insurance": {
                            "type": "string",
                            "enum": ["yes", "no"],
                        },
                    },
                    "required": [
                        "user_id",
                        "origin",
                        "destination",
                        "flight_type",
                        "cabin",
                        "flights",
                        "passengers",
                        "payment_methods",
                        "total_baggages",
                        "nonfree_baggages",
                        "insurance",
                    ],
                },
            },
        }
