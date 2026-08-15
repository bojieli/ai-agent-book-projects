# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import json
from typing import Dict, Any, List, Optional

from pydantic import Field

from aworld.tools import FunctionTools

# Create another function tool server with a different name
function = FunctionTools("another-server", 
                         description="Another function tools server example")

@function.tool(description="Get weather information for a city")
def get_weather(
    city: str = Field(
        description="City name to get weather for"
    ),
    days: int = Field(
        3,
        description="Number of days for forecast"
    )
) -> Dict[str, Any]:
    """Get weather information for a city (simulated data)"""
    # Simulated weather data
    weather_types = ["Sunny", "Cloudy", "Rainy", "Windy", "Snowy"]
    import random
    
    forecast = []
    for i in range(days):
        forecast.append({
            "date": f"2023-06-{i+1:02d}",
            "weather": random.choice(weather_types),
            "temperature": {
                "min": random.randint(15, 25),
                "max": random.randint(26, 35)
            },
            "humidity": random.randint(30, 90)
        })
    
    return {
        "city": city,
        "country": "Sample Country",
        "forecast": forecast
    }

@function.tool(description="Convert currency from one to another")
def convert_currency(
    amount: float = Field(
        description="Amount to convert"
    ),
    from_currency: str = Field(
        description="Source currency code (e.g. USD)"
    ),
    to_currency: str = Field(
        description="Target currency code (e.g. EUR)"
    )
) -> Dict[str, Any]:
    """Currency conversion (simulated data)"""
    # Simulated exchange rate data
    rates = {
        "USD": 1.0,
        "EUR": 0.85,
        "GBP": 0.75,
        "JPY": 110.0,
        "CNY": 6.5
    }
    
    # Check if currencies are supported
    if from_currency not in rates:
        return {"error": f"Currency {from_currency} not supported"}
    if to_currency not in rates:
        return {"error": f"Currency {to_currency} not supported"}
    
    # Calculate conversion
    usd_amount = amount / rates[from_currency]
    converted_amount = usd_amount * rates[to_currency]
    
    return {
        "from": {
            "currency": from_currency,
            "amount": amount
        },
        "to": {
            "currency": to_currency,
            "amount": round(converted_amount, 2)
        },
        "rate": round(rates[to_currency] / rates[from_currency], 4)
    }

if __name__ == "__main__":
    # Test tools
    print("=== Testing get_weather tool ===")
    weather = function.call_tool("get_weather", {"city": "Beijing"})

    print("\n=== Testing convert_currency tool ===")
    conversion = function.call_tool("convert_currency", {
        "amount": 100,
        "from_currency": "USD",
        "to_currency": "EUR"
    })
    print(conversion)