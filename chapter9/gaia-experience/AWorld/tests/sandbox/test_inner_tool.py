# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import logging


def run():
    from aworld.tools import get_function_tools

    aworldsearch_server = get_function_tools("aworldsearch_server")

    print(aworldsearch_server.list_tools())
    res = aworldsearch_server.call_tool("search", {"query_list": ["Tencent financial report", "Baidu financial report", "Alibaba financial report"],})
    print(res)

    another_server = get_function_tools("another-server")
    print(another_server.list_tools())


    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Step 1: Import different modules, which will automatically register their respective FunctionTools instances
    print("=== Step 1: Import modules, automatically register FunctionTools instances ===")
    # Import aworldsearch_function_tools module, which registers "aworldsearch-server"
    print("Imported aworldsearch_function_tools module")

    # Import another_function_tools module, which registers "another-server"

    print("Imported another_function_tools module")

    # Step 2: Get FunctionTools instances by name
    print("\n=== Step 2: Get FunctionTools instances by name ===")
    from aworld.tools import get_function_tools, list_function_tools

    # List all registered FunctionTools servers
    print(f"All registered servers: {list_function_tools()}")

    # Get server instance by specific name
    aworldsearch_server = get_function_tools("aworldsearch-server")
    print(f"Retrieved server: {aworldsearch_server.name}")
    print(f"Server description: {aworldsearch_server.description}")

    another_server = get_function_tools("another-server")
    print(f"Retrieved server: {another_server.name}")
    print(f"Server description: {another_server.description}")

    # Step 3: Use the retrieved instances to call methods
    print("\n=== Step 3: Use the retrieved instances to call methods ===")
    # List all tools of aworldsearch server
    print("aworldsearch-server tool list:")
    for tool in aworldsearch_server.list_tools():
        print(f"  - {tool.name}: {tool.description}")

    # List all tools of another server
    print("\nanother-server tool list:")
    for tool in another_server.list_tools():
        print(f"  - {tool.name}: {tool.description}")

    # Step 4: Call tools
    print("\n=== Step 4: Call tool examples ===")
    # Call aworldsearch server's tool
    if "demo_search" in [tool.name for tool in aworldsearch_server.list_tools()]:
        print("Calling demo_search tool:")
        result = aworldsearch_server.call_tool("demo_search", {"query_list": ["Test query"]})
        print(result)

    # Call another server's tool
    if "get_weather" in [tool.name for tool in another_server.list_tools()]:
        print("\nCalling get_weather tool:")
        result = another_server.call_tool("get_weather", {"city": "Beijing"})
        print(result)

if __name__ == "__main__":
    pass  # Main logic has already been executed at the module level 