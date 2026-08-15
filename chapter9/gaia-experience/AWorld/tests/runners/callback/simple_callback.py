# coding: utf-8
# Copyright (c) 2025 inclusionAI.

"""
Simple tool callback example, demonstrating the basic functionality of callback registration and execution.
"""

# Import business package, its __init__.py will automatically import and register callback functions
import business
from aworld.runners.callback.decorator import reg_callback, CallbackRegistry


# Import CallbackRegistry


@reg_callback("mcp_server__action")
def simple_callback(content):
    """Simple callback function, prints content and returns it

    Args:
        content: Content to print

    Returns:
        The input content
    """
    print(f"Callback function received content: {content}")
    return content

def main():
    """Main function, demonstrating how to get and execute callback functions"""
    # List all registered callback functions
    # print("\n===== Registered Callback Functions =====")
    # business.list_all_callbacks()
    
    # Get and execute print_content callback function
    print("\n===== Execute print_content Callback Function =====")
    callback_func = CallbackRegistry.get("mcp_server__action")
    
    if callback_func:
        print("Callback function found, executing...")
        result = callback_func("Hello, Callback!!!!!")
        print(f"Callback function execution result: {result}")
    else:
        print("print_content callback function not found")


if __name__ == "__main__":
    main() 