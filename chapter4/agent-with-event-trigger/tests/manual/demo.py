"""
Simple demo script to test the event-triggered agent locally
without needing the server/client architecture
"""

import os
import sys
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[2]
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

from agent import EventTriggeredAgent, SystemHintConfig
from event_types import Event, EventType


def _reasoning_safe_temperature(model, requested=1.0):
    """Reasoning models (Kimi K3, GPT-5, ...) only accept temperature=1.
    Return 1 for those; otherwise the requested value so non-reasoning
    providers (Doubao, DeepSeek, older Moonshot) are unchanged."""
    m = str(model or "").lower().replace("/", "-")
    return 1 if ("kimi-k3" in m or "gpt-5" in m) else requested


def main():
    """Run a simple demo of the event-triggered agent"""
    
    print("\n" + "="*80)
    print("🧪 EVENT-TRIGGERED AGENT DEMO")
    print("="*80)
    print()
    
    # Get provider and API key (matching conversational_agent.py)
    provider = os.getenv("LLM_PROVIDER", "kimi").lower()
    
    if provider == "siliconflow":
        api_key = os.getenv("SILICONFLOW_API_KEY")
    elif provider == "doubao":
        api_key = os.getenv("DOUBAO_API_KEY")
    elif provider in ["kimi", "moonshot"]:
        api_key = os.getenv("KIMI_API_KEY")
    elif provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
    else:
        print(f"❌ Error: Unsupported provider: {provider}")
        return
    
    if not api_key:
        print(f"❌ Error: Please set API key for provider '{provider}'")
        print(f"   export {provider.upper()}_API_KEY='your-api-key-here'")
        return
    
    # Get optional model override
    model = os.getenv("LLM_MODEL")
    
    # Create agent with full system hints (matching conversational_agent.py config)
    config = SystemHintConfig(
        enable_timestamps=True,
        enable_tool_counter=True,
        enable_todo_list=True,
        enable_detailed_errors=True,
        enable_system_state=True,
        save_trajectory=True,
        trajectory_file="demo_trajectory.json",
        temperature=_reasoning_safe_temperature(model, 0.7),  # Matching conversational_agent.py
        max_tokens=4096   # Matching conversational_agent.py
    )
    
    agent = EventTriggeredAgent(
        api_key=api_key,
        provider=provider,
        model=model,
        config=config,
        verbose=True
    )
    
    print("✅ Agent initialized\n")
    
    # Demo 1: Web message
    print("\n" + "-"*80)
    print("📋 Demo 1: Web Interface Message")
    print("-"*80)
    
    event1 = Event(
        event_type=EventType.WEB_MESSAGE,
        content="Create a simple Python script that prints 'Hello, Event-Triggered Agent!' and save it as demo_hello.py",
        metadata={"user_id": "demo_user"}
    )
    
    result1 = agent.handle_event(event1, max_iterations=10)
    print(f"\n✅ Event handled. Success: {result1['success']}")
    print(f"   Iterations: {result1['iterations']}")
    print(f"   Tool calls: {len(result1['tool_calls'])}")
    
    # Demo 2: IM message
    print("\n" + "-"*80)
    print("📋 Demo 2: Instant Message")
    print("-"*80)
    
    event2 = Event(
        event_type=EventType.IM_MESSAGE,
        content="Can you run the script you just created?",
        metadata={"sender": "Alice", "platform": "Slack"}
    )
    
    result2 = agent.handle_event(event2, max_iterations=10)
    print(f"\n✅ Event handled. Success: {result2['success']}")
    print(f"   Iterations: {result2['iterations']}")
    print(f"   Tool calls: {len(result2['tool_calls'])}")
    
    # Demo 3: System alert
    print("\n" + "-"*80)
    print("📋 Demo 3: System Alert")
    print("-"*80)
    
    event3 = Event(
        event_type=EventType.SYSTEM_ALERT,
        content="Please check the current directory and list all Python files.",
        metadata={"alert_type": "routine_check"}
    )
    
    result3 = agent.handle_event(event3, max_iterations=10)
    print(f"\n✅ Event handled. Success: {result3['success']}")
    print(f"   Iterations: {result3['iterations']}")
    print(f"   Tool calls: {len(result3['tool_calls'])}")
    
    # Summary
    print("\n" + "="*80)
    print("📊 DEMO SUMMARY")
    print("="*80)
    print(f"Total events processed: 3")
    print(f"Total tool calls: {len(agent.tool_calls)}")
    print(f"Total conversation messages: {len(agent.conversation_history)}")
    print(f"Trajectory saved to: {config.trajectory_file}")
    print()
    print("✅ Demo completed successfully!")
    print()
    print("💡 Next steps:")
    print("   - Check demo_hello.py to see the created file")
    print("   - View demo_trajectory.json to see the full conversation")
    print("   - Run 'python server.py' and 'python client.py' for the full system")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
