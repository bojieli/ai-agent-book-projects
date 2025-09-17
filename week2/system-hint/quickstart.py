"""
Quick Start for System-Hint Enhanced Agent
Simple demonstration using the sample task
"""

import os
import sys
from pathlib import Path
from agent import SystemHintAgent, SystemHintConfig


def main():
    """Quick start demonstration"""
    
    # Check for API key
    api_key = os.getenv("KIMI_API_KEY")
    if not api_key:
        print("❌ Error: Please set KIMI_API_KEY environment variable")
        print("\nSetup instructions:")
        print("  1. Copy env.example to .env")
        print("  2. Add your Kimi API key to .env")
        print("  3. Run: export KIMI_API_KEY='your-api-key-here'")
        return
    
    print("\n" + "="*60)
    print("  🚀 System-Hint Agent Quick Start")
    print("="*60)
    
    # Sample task for analyzing projects
    task = """Analyze and summarize the AI Agent projects in week1 and week2 directories:

1. Navigate to the parent directory to access both week1 and week2 folders
2. For week1 directory:
   - List all project folders
   - Read the README.md or main.py from the 'context' project
   - Identify the key concepts implemented
3. For week2 directory:
   - List all project folders  
   - Read the README.md from one project
   - Understand the advanced features
4. Create a brief summary file 'quick_summary.txt' with your findings

Use the TODO list to organize and track your analysis steps."""
    
    print("\n📋 Task:")
    print("-"*60)
    print(task)
    print("-"*60)
    
    # Create agent with all features enabled
    print("\n🔧 Initializing agent with full system hints...")
    config = SystemHintConfig(
        enable_timestamps=True,
        enable_tool_counter=True,
        enable_todo_list=True,
        enable_detailed_errors=True,
        enable_system_state=True
    )
    
    agent = SystemHintAgent(
        api_key=api_key,
        provider="kimi",
        config=config,
        verbose=False  # Set to True to see full API interactions
    )
    
    # Set working directory to parent to access week1/week2
    agent.current_directory = str(Path(__file__).parent.parent)
    print(f"📁 Working directory: {agent.current_directory}")
    
    print("\n🚀 Executing task (this may take a moment)...")
    print("-"*60)
    
    # Execute the task
    result = agent.execute_task(task, max_iterations=25)
    
    # Display results
    print("\n" + "="*60)
    print("  📊 Results")
    print("="*60)
    
    if result.get('success'):
        print("\n✅ Task completed successfully!")
        
        if result.get('final_answer'):
            print("\n📝 Summary:")
            print("-"*40)
            answer = result['final_answer']
            # Display first 800 chars for readability
            if len(answer) > 800:
                print(answer[:800] + "...\n[Output truncated for display]")
            else:
                print(answer)
    else:
        print("\n⚠️ Task did not complete fully")
        if result.get('error'):
            print(f"Error: {result['error']}")
    
    # Statistics
    print("\n📈 Execution Statistics:")
    print(f"  • Iterations: {result.get('iterations', 0)}")
    print(f"  • Tool calls: {len(result.get('tool_calls', []))}")
    
    # Tool usage breakdown
    if result.get('tool_calls'):
        tool_counts = {}
        for call in result['tool_calls']:
            tool_counts[call.tool_name] = tool_counts.get(call.tool_name, 0) + 1
        
        print("\n🔧 Tools Used:")
        for tool, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {tool}: {count} call{'s' if count > 1 else ''}")
    
    # TODO list summary
    if result.get('todo_list'):
        completed = sum(1 for item in result['todo_list'] if item['status'] == 'completed')
        total = len(result['todo_list'])
        print(f"\n📋 TODO Progress: {completed}/{total} tasks completed")
        
        # Show first few TODO items
        print("\nTODO Items:")
        for item in result['todo_list'][:5]:
            status_symbol = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'cancelled': '❌'
            }.get(item['status'], '❓')
            # Truncate long content
            content = item['content']
            if len(content) > 60:
                content = content[:57] + "..."
            print(f"  {status_symbol} [{item['id']}] {content}")
        
        if total > 5:
            print(f"  ... and {total - 5} more items")
    
    print("\n" + "="*60)
    print("  ✨ Quick Start Complete!")
    print("="*60)
    print("\n💡 Tips:")
    print("  • Run 'python main.py' for interactive mode")
    print("  • Run 'python main.py --mode sample' to run this task again")
    print("  • Run 'python main.py --mode demo' for more demonstrations")
    print("  • Set verbose=True in the agent for detailed API logs")
    print("\n")


if __name__ == "__main__":
    main()