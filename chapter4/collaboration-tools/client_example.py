"""Example client showing how to use Collaboration Tools MCP Server.

This example demonstrates a real-world use case: monitoring a website
and notifying administrators when changes are detected.
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent
import sys

from result_parsing import parse_mapping


class CollaborationAgent:
    """An AI agent that uses collaboration tools."""
    
    def __init__(self):
        self.session = None
        
    async def connect(self):
        """Connect to the MCP server."""
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["src/main.py"]
        )
        
        print("🔌 Connecting to Collaboration Tools MCP Server...")
        
        self.read, self.write = await stdio_client(server_params).__aenter__()
        self.session = ClientSession(self.read, self.write)
        await self.session.__aenter__()
        await self.session.initialize()
        
        print("✅ Connected successfully\n")
        
    async def disconnect(self):
        """Disconnect from the server."""
        if self.session:
            await self.session.__aexit__(None, None, None)
            print("\n📴 Disconnected from server")
    
    async def call_tool(self, tool_name: str, arguments: dict):
        """Call a tool and return the result."""
        result = await self.session.call_tool(tool_name, arguments)
        text_content = [c.text for c in result.content if isinstance(c, TextContent)]
        return parse_mapping(text_content[0]) if text_content else {}
    
    async def monitor_website_workflow(self, url: str, check_interval: int = 300):
        """Monitor a website and notify on changes.
        
        Args:
            url: Website URL to monitor
            check_interval: Check interval in seconds
        """
        print(f"🔍 Starting website monitoring workflow for: {url}")
        print(f"   Check interval: {check_interval} seconds\n")
        
        # Step 1: Set up recurring timer for checks
        print("⏰ Setting up recurring monitoring timer...")
        timer_result = await self.call_tool(
            "mcp_set_recurring_timer",
            {
                "interval_seconds": check_interval,
                "max_occurrences": 5,  # Check 5 times for demo
                "timer_name": f"Monitor {url}",
                "callback_message": f"Time to check {url}"
            }
        )
        
        if timer_result.get("success"):
            print(f"✅ Timer set: {timer_result['timer_id']}")
            timer_id = timer_result['timer_id']
        else:
            print(f"❌ Failed to set timer: {timer_result}")
            return
        
        # Step 2: Take initial screenshot
        print("\n📸 Taking initial screenshot of the website...")
        await self.call_tool("mcp_browser_navigate", {"url": url})
        
        screenshot_result = await self.call_tool(
            "mcp_browser_screenshot",
            {"full_page": True}
        )
        
        if screenshot_result.get("success"):
            initial_screenshot = screenshot_result['path']
            print(f"✅ Screenshot saved: {initial_screenshot}")
        else:
            print(f"⚠️  Screenshot failed: {screenshot_result}")
            initial_screenshot = None
        
        # Step 3: Request admin approval for monitoring
        print("\n👤 Requesting admin approval to continue monitoring...")
        approval_result = await self.call_tool(
            "mcp_request_admin_approval",
            {
                "request_message": f"Approve continuous monitoring of {url}?",
                "context": {
                    "url": url,
                    "interval": check_interval,
                    "initial_screenshot": initial_screenshot
                },
                "timeout_seconds": 30,  # Short timeout for demo
                "urgent": False
            }
        )
        
        if approval_result.get("approved"):
            print("✅ Admin approved monitoring")
        elif approval_result.get("timeout"):
            print("⏱️  Admin approval timeout - proceeding anyway for demo")
        else:
            print("❌ Admin rejected monitoring - stopping")
            await self.call_tool("mcp_cancel_timer", {"timer_id": timer_id})
            return
        
        # Step 4: Send notification that monitoring started
        print("\n📧 Sending start notification...")
        await self.call_tool(
            "mcp_send_slack_message",
            {
                "message": f"🚀 Started monitoring {url}\nInterval: {check_interval}s",
                "username": "Monitor Bot"
            }
        )
        
        print("\n✨ Monitoring workflow initialized!")
        print(f"   Timer will check {url} every {check_interval} seconds")
        print(f"   Timer ID: {timer_id}")
        
        # Step 5: Simulate monitoring loop
        print("\n⏳ Monitoring in progress...")
        print("   (In a real application, timer callbacks would trigger checks)")
        
        # Wait a bit to show timer is active
        await asyncio.sleep(10)
        
        # Check timer status
        status = await self.call_tool("mcp_get_timer_status", {"timer_id": timer_id})
        print(f"\n📊 Timer status: {status.get('timer', {}).get('status')}")
        
        # List all active timers
        timers = await self.call_tool("mcp_list_timers", {"status": "active"})
        print(f"   Active timers: {timers.get('count', 0)}")


async def main():
    """Run the example client."""
    print("=" * 70)
    print("Collaboration Tools MCP Client Example")
    print("Website Monitoring Workflow Demo")
    print("=" * 70)
    print()
    
    agent = CollaborationAgent()
    
    try:
        await agent.connect()
        
        # Run the monitoring workflow
        await agent.monitor_website_workflow(
            url="https://example.com",
            check_interval=60  # Check every 60 seconds
        )
        
        # Additional examples
        print("\n" + "=" * 70)
        print("Additional Features Demo")
        print("=" * 70)
        
        # Example: Send email notification
        print("\n📧 Sending email notification example...")
        email_result = await agent.call_tool(
            "mcp_send_email",
            {
                "to_email": "admin@example.com",
                "subject": "Monitoring Report",
                "body": "Website monitoring is active and running smoothly.",
                "html": False
            }
        )
        print(f"   Result: {'✅ Sent' if email_result.get('success') else '⚠️ Not configured'}")
        
        # Example: Request admin input
        print("\n❓ Requesting admin input example...")
        print("   (This would normally wait for admin response)")
        
        print("\n✨ Demo complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await agent.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
