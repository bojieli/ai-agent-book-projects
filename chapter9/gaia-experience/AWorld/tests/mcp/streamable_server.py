import random

import requests
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# Create server
mcp = FastMCP("streamable-server")


@mcp.tool(description="Perform addition operation")
def add(a: int=Field(
        description="First number",
    ), b: int=Field(
        description="Second number",
    )) -> int:
    """Add two numbers"""
    print(f"[debug-server] add({a}, {b})")
    return a + b


# @mcp.tool()
# def get_secret_word() -> str:
#     print("[debug-server] get_secret_word()")
#     return random.choice(["apple", "banana", "cherry"])


@mcp.tool(description="Get weather for a city")
def get_current_weather(city: str=Field(
        description="City name"
    )) -> str:
    print(f"[debug-server] get_current_weather({city})")

    endpoint = "https://wttr.in"
    response = requests.get(f"{endpoint}/{city}")
    return response.text


if __name__ == "__main__":
    # mcp.run(transport="streamable-http")
    pass