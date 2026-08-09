"""
Example demonstrating the Event-Triggered Agent with MCP tools
"""

import os
import asyncio
from dotenv import load_dotenv
from agent import EventTriggeredAgent, SystemHintConfig, resolve_provider_and_key
from event_types import Event, EventType

# Load environment variables
load_dotenv()


async def main():
    """Main example function"""
    print("=" * 80)
    print("Event-Triggered Agent with MCP Tools Example")
    print("=" * 80)
    print()
    
    # Get API credentials
    provider = os.getenv("LLM_PROVIDER", "kimi")
    provider, api_key = resolve_provider_and_key(provider)
    
    if not api_key:
        print("❌ Please set the provider API key in your .env file (DASHSCOPE_API_KEY for dashscope/qwen/bailian)")
        return
    
    # Create agent configuration
    config = SystemHintConfig(
        enable_timestamps=True,
        enable_tool_counter=True,
        enable_todo_list=True,
        enable_detailed_errors=True,
        enable_system_state=True,
        save_trajectory=True,
        trajectory_file="example_trajectory.json",
        use_mcp_servers=True  # Enable MCP servers
    )
    
    # Initialize agent
    print("Initializing agent...")
    agent = EventTriggeredAgent(
        api_key=api_key,
        provider=provider,
        config=config,
        verbose=True
    )
    
    # Load MCP tools
    print("\nLoading MCP tools...")
    await agent.load_mcp_tools()
    
    print("\n" + "=" * 80)
    print("Testing Event Processing")
    print("=" * 80)
    print()
    
    # Create a test event
    event = Event(
        event_type=EventType.WEB_MESSAGE,
        content="Search the web for 'Python async programming best practices' and summarize the top 3 results.",
        metadata={
            "source": "web_interface",
            "user_id": "demo_user",
            "session_id": "test_session_001"
        }
    )
    
    # Handle the event
    try:
        result = agent.handle_event(event, max_iterations=15)
        
        print("\n" + "=" * 80)
        print("Result Summary")
        print("=" * 80)
        print(f"Success: {result['success']}")
        print(f"Iterations: {result['iterations']}")
        print(f"Tool Calls: {len(result['tool_calls'])}")
        
        if result.get('final_answer'):
            print(f"\nFinal Answer:\n{result['final_answer']}")
        
        if result.get('trajectory_file'):
            print(f"\nTrajectory saved to: {result['trajectory_file']}")
            
    except Exception as e:
        print(f"\n❌ Error processing event: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup MCP connections
        print("\nCleaning up MCP connections...")
        await agent.mcp_manager.disconnect_all()
        print("✅ Cleanup complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
