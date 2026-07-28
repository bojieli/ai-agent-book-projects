"""
Event Client - Send test events to the event-triggered agent
"""

import requests
import json
import time
import argparse
from datetime import datetime
from event_types import EventType


class EventClient:
    """Client to send events to the event-triggered agent server"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        Initialize the client
        
        Args:
            server_url: URL of the event server
        """
        self.server_url = server_url.rstrip('/')
    
    def send_event(self, event_type: str, content: str, metadata: dict = None) -> dict:
        """
        Send an event to the agent
        
        Args:
            event_type: Type of event (e.g., 'web_message', 'im_message')
            content: Content of the event
            metadata: Additional metadata for the event
            
        Returns:
            Response from the server
        """
        event_data = {
            'event_type': event_type,
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat(),
            'event_id': f"evt_{int(time.time() * 1000)}"
        }
        
        print(f"\n{'='*80}")
        print(f"📤 SENDING EVENT")
        print(f"{'='*80}")
        print(f"Event Type: {event_type}")
        print(f"Content: {content}")
        if metadata:
            print(f"Metadata: {json.dumps(metadata, indent=2)}")
        print(f"{'='*80}\n")
        
        try:
            response = requests.post(
                f"{self.server_url}/event",
                json=event_data,
                headers={'Content-Type': 'application/json'},
                timeout=120
            )
            
            response.raise_for_status()
            result = response.json()
            
            print(f"\n{'='*80}")
            print(f"✅ EVENT SENT SUCCESSFULLY")
            print(f"{'='*80}")
            print(f"Response: {json.dumps(result, indent=2)}")
            print(f"{'='*80}\n")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error sending event: {e}")
            return {"error": str(e)}
    
    def reset_agent(self) -> dict:
        """Reset the agent state"""
        try:
            response = requests.post(f"{self.server_url}/agent/reset", timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def get_status(self) -> dict:
        """Get agent status"""
        try:
            response = requests.get(f"{self.server_url}/agent/status", timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def start_monitoring(self) -> dict:
        """Start system monitoring"""
        try:
            response = requests.post(f"{self.server_url}/monitoring/start", timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def stop_monitoring(self) -> dict:
        """Stop system monitoring"""
        try:
            response = requests.post(f"{self.server_url}/monitoring/stop", timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def register_process(self, process_id: str, name: str) -> dict:
        """Register a background process for monitoring"""
        try:
            response = requests.post(
                f"{self.server_url}/process/register",
                json={'process_id': process_id, 'name': name}, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def unregister_process(self, process_id: str) -> dict:
        """Unregister a background process"""
        try:
            response = requests.post(
                f"{self.server_url}/process/unregister",
                json={'process_id': process_id}, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}


def run_test_scenarios(client: EventClient):
    """Run various test scenarios"""
    
    print("\n" + "🧪"*40)
    print("  EVENT-TRIGGERED AGENT TEST SCENARIOS")
    print("🧪"*40 + "\n")
    
    # Scenario 1: Web message
    print("\n📋 Scenario 1: Web Interface Message")
    print("-"*80)
    client.send_event(
        event_type=EventType.WEB_MESSAGE.value,
        content="Hello! Can you create a simple Python script that prints 'Hello, World!'?",
        metadata={"user_id": "user123", "session_id": "session456"}
    )
    time.sleep(2)
    
    # Scenario 2: IM message
    print("\n📋 Scenario 2: Instant Message")
    print("-"*80)
    client.send_event(
        event_type=EventType.IM_MESSAGE.value,
        content="Can you list the files in the current directory?",
        metadata={"sender": "Alice", "platform": "Slack"}
    )
    time.sleep(2)
    
    # Scenario 3: Email reply
    print("\n📋 Scenario 3: Email Reply")
    print("-"*80)
    client.send_event(
        event_type=EventType.EMAIL_REPLY.value,
        content="Thanks for the report! Can you also check the disk usage?",
        metadata={
            "from": "bob@example.com",
            "subject": "Re: System Report",
            "thread_id": "thread789"
        }
    )
    time.sleep(2)
    
    # Scenario 4: GitHub PR update
    print("\n📋 Scenario 4: GitHub PR Review")
    print("-"*80)
    client.send_event(
        event_type=EventType.GITHUB_PR_UPDATE.value,
        content="Review comment: Please add unit tests for the new feature.",
        metadata={
            "pr_number": "42",
            "action": "review_requested",
            "reviewer": "code-reviewer",
            "repository": "ai-agent-project"
        }
    )
    time.sleep(2)
    
    # Scenario 5: Timer trigger
    print("\n📋 Scenario 5: Scheduled Timer")
    print("-"*80)
    client.send_event(
        event_type=EventType.TIMER_TRIGGER.value,
        content="Daily backup reminder - please check if backups are running correctly.",
        metadata={
            "timer_id": "daily_backup_check",
            "schedule": "daily at 09:00"
        }
    )
    time.sleep(2)
    
    # Scenario 6: System alert
    print("\n📋 Scenario 6: System Alert")
    print("-"*80)
    client.send_event(
        event_type=EventType.SYSTEM_ALERT.value,
        content="Memory usage has exceeded 80%. Please investigate.",
        metadata={
            "alert_type": "resource_usage",
            "severity": "warning",
            "memory_usage": "82%"
        }
    )
    time.sleep(2)
    
    # Scenario 7: Register background process
    print("\n📋 Scenario 7: Background Process Registration")
    print("-"*80)
    print("Registering background process...")
    result = client.register_process("proc_ml_training", "ML Model Training")
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Scenario 8: Start monitoring
    print("\n📋 Scenario 8: Start System Monitoring")
    print("-"*80)
    print("Starting system monitoring (will check for timeouts)...")
    result = client.start_monitoring()
    print(f"Result: {json.dumps(result, indent=2)}")
    print("\n⏰ Monitoring is now active. System will check for:")
    print("  - User timeout (no interaction for 1 minute)")
    print("  - Background process timeout (running for 30 seconds)")
    print("\n💡 Wait 1-2 minutes to see system reminder events trigger automatically...")
    
    # Get status
    print("\n📋 Current Agent Status")
    print("-"*80)
    status = client.get_status()
    print(json.dumps(status, indent=2))
    
    print("\n" + "✅"*40)
    print("  TEST SCENARIOS COMPLETED")
    print("✅"*40 + "\n")


def interactive_mode(client: EventClient):
    """Interactive mode for sending custom events"""
    print("\n" + "="*80)
    print("  INTERACTIVE EVENT CLIENT")
    print("="*80)
    print("\nAvailable event types:")
    for event_type in EventType:
        print(f"  - {event_type.value}")
    print("\nCommands:")
    print("  'status' - Get agent status")
    print("  'reset'  - Reset agent")
    print("  'monitor on' - Start monitoring")
    print("  'monitor off' - Stop monitoring")
    print("  'quit'   - Exit")
    print("\nOr send an event: <event_type> <content>")
    
    while True:
        try:
            print("\n" + "-"*60)
            user_input = input("Event > ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("👋 Goodbye!")
                break
            
            elif user_input.lower() == 'status':
                status = client.get_status()
                print(json.dumps(status, indent=2))
            
            elif user_input.lower() == 'reset':
                result = client.reset_agent()
                print(json.dumps(result, indent=2))
            
            elif user_input.lower() == 'monitor on':
                result = client.start_monitoring()
                print(json.dumps(result, indent=2))
            
            elif user_input.lower() == 'monitor off':
                result = client.stop_monitoring()
                print(json.dumps(result, indent=2))
            
            else:
                # Parse event command
                parts = user_input.split(' ', 1)
                if len(parts) < 2:
                    print("❌ Invalid format. Use: <event_type> <content>")
                    continue
                
                event_type = parts[0]
                content = parts[1]
                
                # Validate event type
                try:
                    EventType(event_type)
                except ValueError:
                    print(f"❌ Invalid event type: {event_type}")
                    continue
                
                # Send the event
                client.send_event(event_type, content)
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="事件客户端：向事件驱动 Agent 服务器发送事件。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例：
  python client.py --mode test                 # 依次发送多种事件，跑通全部场景
  python client.py --mode interactive          # 交互模式，手动输入事件
  python client.py --message "创建一个 hello world 脚本"   # 发送单条 web_message 事件
  python client.py --event-type timer_trigger --message "检查每日备份"   # 指定事件类型
""",
    )

    parser.add_argument(
        '--server',
        default='http://localhost:8000',
        help='服务器地址（默认：http://localhost:8000）'
    )

    parser.add_argument(
        '--mode',
        choices=['test', 'interactive'],
        default='test',
        help='模式：test（依次发送预置场景事件）或 interactive（交互式手动发送）'
    )

    parser.add_argument(
        '--message',
        default=None,
        help='发送单条事件的内容；提供该参数时忽略 --mode，发完即退出'
    )

    parser.add_argument(
        '--event-type',
        default=EventType.WEB_MESSAGE.value,
        choices=[e.value for e in EventType],
        help=f'--message 使用的事件类型（默认：{EventType.WEB_MESSAGE.value}）'
    )

    args = parser.parse_args()

    client = EventClient(server_url=args.server)

    # Check if server is running
    try:
        response = requests.get(f"{args.server}/health", timeout=5)
        response.raise_for_status()
        print(f"✅ Connected to server at {args.server}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server at {args.server}")
        print(f"   Error: {e}")
        print(f"\n💡 Make sure the server is running:")
        print(f"   python server.py")
        return

    if args.message is not None:
        client.send_event(event_type=args.event_type, content=args.message)
    elif args.mode == 'test':
        run_test_scenarios(client)
    else:
        interactive_mode(client)


if __name__ == "__main__":
    main()
