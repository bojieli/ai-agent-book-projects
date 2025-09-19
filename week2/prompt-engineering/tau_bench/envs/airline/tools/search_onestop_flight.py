# Copyright Sierra

import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool


class SearchOnestopFlight(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], origin: str, destination: str, date: str) -> str:
        flights = data["flights"]
        results = []
        for flight1 in flights.values():
            if flight1["origin"] == origin:
                for flight2 in flights.values():
                    if (
                        flight2["destination"] == destination
                        and flight1["destination"] == flight2["origin"]
                    ):
                        date2 = (
                            f"2024-05-{int(date[-2:])+1}"
                            if "+1" in flight1["scheduled_arrival_time_est"]
                            else date
                        )
                        if (
                            flight1["scheduled_arrival_time_est"]
                            > flight2["scheduled_departure_time_est"]
                        ):
                            continue
                        if date in flight1["dates"] and date2 in flight2["dates"]:
                            if (
                                flight1["dates"][date]["status"] == "available"
                                and flight2["dates"][date2]["status"] == "available"
                            ):
                                result1 = {
                                    k: v for k, v in flight1.items() if k != "dates"
                                }
                                result1.update(flight1["dates"][date])
                                result1["date"] = date
                                result2 = {
                                    k: v for k, v in flight2.items() if k != "dates"
                                }
                                result2.update(flight2["dates"][date])
                                result2["date"] = date2
                                results.append([result1, result2])
        return json.dumps(results)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "search_onestop_flight",
                "description": "Search direct flights between two cities on a specific date.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "The origin city airport in three letters, such as 'JFK'.",
                        },
                        "destination": {
                            "type": "string",
                            "description": "The destination city airport in three letters, such as 'LAX'.",
                        },
                        "date": {
                            "type": "string",
                            "description": "The date of the flight in the format 'YYYY-MM-DD', such as '2024-05-01'.",
                        },
                    },
                    "required": ["origin", "destination", "date"],
                },
            },
        }
