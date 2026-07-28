"""Quick start demo for Collaboration Tools MCP Server.

This script demonstrates how to use the MCP server as a client.
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent
import sys
import json

from result_parsing import parse_mapping


async def run_demo():
    """Run a demonstration of all collaboration tools."""
    print("=" * 70)
    print("Collaboration Tools MCP Server - Quick Start Demo")
    print("=" * 70)
    
    # Connect to the MCP server
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["src/main.py"]
    )
    
    print("\n🔌 Connecting to MCP server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools
            print("\n📦 Discovering available tools...")
            tools_result = await session.list_tools()
            tools = {tool.name: tool for tool in tools_result.tools}
            
            print(f"✅ Found {len(tools)} tools:")
            for tool_name in sorted(tools.keys()):
                print(f"  - {tool_name}")
            
            # Demo 1: Timer Tools
            print("\n" + "=" * 70)
            print("Demo 1: Timer Management")
            print("=" * 70)
            
            print("\n⏰ Setting a 10-second timer...")
            result = await session.call_tool(
                "mcp_set_timer",
                {
                    "duration_seconds": 10,
                    "timer_name": "Demo Timer",
                    "callback_message": "Demo timer completed!"
                }
            )
            timer_result = _extract_result(result)
            print(f"Result: {timer_result}")
            
            if "timer_id" in str(timer_result):
                # Parse timer_id from result
                timer_data = parse_mapping(timer_result)
                timer_id = timer_data.get("timer_id")
                
                print(f"\n📋 Checking timer status...")
                result = await session.call_tool(
                    "mcp_get_timer_status",
                    {"timer_id": timer_id}
                )
                print(f"Status: {_extract_result(result)}")
            
            print("\n📋 Listing all active timers...")
            result = await session.call_tool("mcp_list_timers", {"status": "active"})
            print(f"Active timers: {_extract_result(result)}")
            
            # Demo 2: Notification Tools (if configured)
            print("\n" + "=" * 70)
            print("Demo 2: Notifications")
            print("=" * 70)
            
            print("\n📧 Testing Slack notification (if configured)...")
            result = await session.call_tool(
                "mcp_send_slack_message",
                {
                    "message": "🤖 Test message from Collaboration Tools MCP Server!",
                    "username": "Demo Bot"
                }
            )
            print(f"Result: {_extract_result(result)}")
            
            # Demo 3: HITL Tools
            print("\n" + "=" * 70)
            print("Demo 3: Human-in-the-Loop")
            print("=" * 70)
            
            print("\n👤 Listing pending admin requests...")
            result = await session.call_tool("mcp_list_pending_requests", {})
            print(f"Pending requests: {_extract_result(result)}")
            
            # Note: We won't actually request approval in the demo
            # as it would block waiting for admin response
            print("\nℹ️  Skipping approval request demo (would block for timeout)")
            print("   Use mcp_request_admin_approval() in your application")
            
            # Demo 4: Browser Tools (if configured)
            print("\n" + "=" * 70)
            print("Demo 4: Browser Automation")
            print("=" * 70)
            
            print("\n🌐 Testing browser navigation...")
            print("   (This may take a moment to initialize the browser)")
            
            try:
                result = await session.call_tool(
                    "mcp_browser_navigate",
                    {"url": "https://example.com", "new_tab": False}
                )
                print(f"Navigation result: {_extract_result(result)}")
                
                print("\n📄 Getting page content...")
                result = await session.call_tool(
                    "mcp_browser_get_content",
                    {}
                )
                content = _extract_result(result)
                if len(content) > 200:
                    content = content[:200] + "..."
                print(f"Content preview: {content}")
                
                print("\n📸 Taking a screenshot...")
                result = await session.call_tool(
                    "mcp_browser_screenshot",
                    {"full_page": False}
                )
                print(f"Screenshot result: {_extract_result(result)}")
                
            except Exception as e:
                print(f"⚠️  Browser demo skipped: {e}")
                print("   Make sure Playwright is installed: playwright install chromium")
            
            # Summary
            print("\n" + "=" * 70)
            print("✨ Demo Complete!")
            print("=" * 70)
            print("\nYou can now use these tools in your AI agent applications.")
            print("See README.md for more examples and configuration options.")


def _extract_result(result):
    """Extract text content from MCP result."""
    if hasattr(result, 'content'):
        text_content = [c.text for c in result.content if isinstance(c, TextContent)]
        return text_content[0] if text_content else str(result.content)
    return str(result)


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
