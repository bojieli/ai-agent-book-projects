"""
Main entry point for System-Hint Enhanced Agent
Supports command-line tasks and interactive mode
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from agent import SystemHintAgent, SystemHintConfig, TodoStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_result(result: dict):
    """Print formatted result"""
    if result.get('success'):
        print("\n✅ Task completed successfully!")
        if result.get('final_answer'):
            print("\n📝 Final Answer:")
            print("-"*40)
            print(result['final_answer'])
    else:
        print("\n❌ Task failed!")
        if result.get('error'):
            print(f"Error: {result['error']}")
    
    print(f"\n📊 Statistics:")
    print(f"  - Iterations: {result.get('iterations', 0)}")
    print(f"  - Tool calls: {len(result.get('tool_calls', []))}")
    
    if result.get('trajectory_file'):
        print(f"\n💾 Trajectory saved to: {result['trajectory_file']}")
    
    if result.get('todo_list'):
        print(f"\n📋 Final TODO List:")
        for item in result['todo_list']:
            status_emoji = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'cancelled': '❌'
            }.get(item['status'], '❓')
            print(f"  [{item['id']}] {status_emoji} {item['content']} ({item['status']})")
    
    # Show tool call summary
    if result.get('tool_calls'):
        print(f"\n🔧 Tool Call Summary:")
        tool_summary = {}
        for call in result['tool_calls']:
            tool_name = call.tool_name
            if tool_name not in tool_summary:
                tool_summary[tool_name] = {
                    'count': 0,
                    'success': 0,
                    'failed': 0
                }
            tool_summary[tool_name]['count'] += 1
            if call.error:
                tool_summary[tool_name]['failed'] += 1
            else:
                tool_summary[tool_name]['success'] += 1
        
        for tool_name, stats in tool_summary.items():
            print(f"  - {tool_name}: {stats['count']} calls "
                  f"({stats['success']} success, {stats['failed']} failed)")


def get_sample_task() -> str:
    """Get the sample task for summarizing week1 and week2 projects"""
    return """Analyze and summarize the AI Agent projects in week1 and week2 directories. Create a comprehensive analysis file 'project_analysis_report.md' containing:

   - Overview of all the projects in week1 and week2 directories
   - What you have learned from the projects
    """


def execute_single_task(task: str, config: SystemHintConfig = None, verbose: bool = False,
                        provider: str = "kimi", model: str = None):
    """Execute a single task with the agent"""
    api_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: Please set KIMI_API_KEY environment variable")
        print("   export KIMI_API_KEY='your-api-key-here'")
        print("   （如果只想离线查看状态栏效果，请运行 python main.py --mode preview）")
        return None

    if config is None:
        config = SystemHintConfig(
            enable_timestamps=True,
            enable_tool_counter=True,
            enable_todo_list=True,
            enable_detailed_errors=True,
            enable_system_state=True
        )

    agent = SystemHintAgent(
        api_key=api_key,
        provider=provider,
        model=model,
        config=config,
        verbose=verbose
    )
    
    # For project analysis tasks, navigate to parent directory
    if "week1" in task.lower() and "week2" in task.lower():
        agent.current_directory = str(Path(__file__).parent.parent)
        print(f"📁 Working directory set to: {agent.current_directory}")
    
    print("\n🚀 Executing task...")
    result = agent.execute_task(task, max_iterations=30)
    return result


def interactive_mode():
    """Run the agent in interactive mode"""
    print_section("Interactive Mode - System-Hint Agent")
    
    api_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: Please set KIMI_API_KEY environment variable")
        print("   export KIMI_API_KEY='your-api-key-here'")
        return
    
    # Initialize agent with full features
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
        verbose=False
    )
    
    print("\n✅ Agent initialized with full system hints")
    print("\nAvailable commands:")
    print("  'sample' - Run the sample project analysis task")
    print("  'reset'  - Reset agent state and conversation")
    print("  'config' - Show current configuration")
    print("  'quit'   - Exit interactive mode")
    print("\nOr enter any task for the agent to complete.")
    
    while True:
        try:
            print("\n" + "-"*60)
            user_input = input("Task > ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("👋 Goodbye!")
                break
            
            elif user_input.lower() == 'sample':
                task = get_sample_task()
                print("\n📋 Running sample task:")
                print(task)
                
                # Navigate to parent directory for project analysis
                original_dir = agent.current_directory
                agent.current_directory = str(Path(__file__).parent.parent)
                
                result = agent.execute_task(task, max_iterations=100)
                print_result(result)
                
                # Restore directory
                agent.current_directory = original_dir
                
            elif user_input.lower() == 'reset':
                agent.reset()
                print("✅ Agent state reset")
                
            elif user_input.lower() == 'config':
                print("\n📋 Current Configuration:")
                print(f"  - Timestamps: {'✅' if config.enable_timestamps else '❌'}")
                print(f"  - Tool Counter: {'✅' if config.enable_tool_counter else '❌'}")
                print(f"  - TODO List: {'✅' if config.enable_todo_list else '❌'}")
                print(f"  - Detailed Errors: {'✅' if config.enable_detailed_errors else '❌'}")
                print(f"  - System State: {'✅' if config.enable_system_state else '❌'}")
                print(f"  - Current Directory: {agent.current_directory}")
                
            else:
                # Execute user task
                result = agent.execute_task(user_input, max_iterations=25)
                print_result(result)
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            logger.error(f"Error in interactive mode: {e}", exc_info=True)


def demo_basic_features():
    """Demonstrate basic system hint features"""
    print_section("Demo: Basic System Hint Features")
    
    api_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Please set KIMI_API_KEY environment variable")
        return
    
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
        verbose=False
    )
    
    task = """Please complete the following tasks:
    1. Create a test directory called 'demo_output'
    2. Write a Python script that counts files in the current directory
    3. Execute the script and save the output
    4. Create a summary report of what was done
    
    Use the TODO list to track your progress."""
    
    result = agent.execute_task(task)
    print_result(result)


def demo_tool_loop_prevention():
    """Demonstrate tool call loop prevention"""
    print_section("Demo: Tool Call Loop Prevention")
    
    api_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Please set KIMI_API_KEY environment variable")
        return
    
    config = SystemHintConfig(
        enable_timestamps=False,
        enable_tool_counter=True,
        enable_todo_list=False,
        enable_detailed_errors=True,
        enable_system_state=False
    )
    
    agent = SystemHintAgent(
        api_key=api_key,
        provider="kimi",
        config=config,
        verbose=False
    )
    
    task = """Try to read a file called 'nonexistent_file.txt' up to 3 times.
    After each failed attempt, note the failure and stop after 3 attempts."""
    
    result = agent.execute_task(task, max_iterations=10)
    print_result(result)
    
    if result.get('tool_calls'):
        read_file_calls = [c for c in result['tool_calls'] if c.tool_name == 'read_file']
        print(f"\n🛡️ Tool counter prevented loop: {len(read_file_calls)} read_file attempts")
        for call in read_file_calls:
            print(f"  - Call #{call.call_number}: {'Failed' if call.error else 'Success'}")


def demo_comparison():
    """Compare with and without system hints"""
    print_section("Demo: System Hints Comparison")
    
    api_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Please set KIMI_API_KEY environment variable")
        return
    
    task = """Create a simple Python script that prints 'Hello World' and save it as 'hello.py'."""
    
    # With system hints
    print("\n📋 WITH System Hints:")
    config_with = SystemHintConfig(
        enable_timestamps=True,
        enable_tool_counter=True,
        enable_todo_list=True,
        enable_detailed_errors=True,
        enable_system_state=True
    )
    
    agent_with = SystemHintAgent(
        api_key=api_key,
        provider="kimi",
        config=config_with,
        verbose=False
    )
    
    result_with = agent_with.execute_task(task, max_iterations=10)
    print(f"  - Success: {result_with.get('success')}")
    print(f"  - Iterations: {result_with.get('iterations')}")
    print(f"  - Tool calls: {len(result_with.get('tool_calls', []))}")
    
    # Without system hints
    print("\n📋 WITHOUT System Hints:")
    config_without = SystemHintConfig(
        enable_timestamps=False,
        enable_tool_counter=False,
        enable_todo_list=False,
        enable_detailed_errors=False,
        enable_system_state=False
    )
    
    agent_without = SystemHintAgent(
        api_key=api_key,
        provider="kimi",
        config=config_without,
        verbose=False
    )
    
    result_without = agent_without.execute_task(task, max_iterations=10)
    print(f"  - Success: {result_without.get('success')}")
    print(f"  - Iterations: {result_without.get('iterations')}")
    print(f"  - Tool calls: {len(result_without.get('tool_calls', []))}")
    
    print("\n💡 System hints typically lead to more efficient task completion!")


def preview_status_bar(config: SystemHintConfig):
    """离线预览：展示五种状态栏（system hint）技术如何改变模型看到的上下文。

    对应书中实验 2-9 的五种技术。整个过程在本地渲染，**不发起任何 LLM 调用，
    因此无需 API Key**。每个案例都做一次“无状态栏 vs 有状态栏”的对照，
    直观地展示 Agent 框架在上下文末尾注入的显式状态。
    """
    from datetime import datetime as _dt

    print_section("离线预览：Agent 状态栏（System Hint）如何改变上下文")
    print(
        "说明：以下每个案例对比【无状态栏】（模型只能看到原始轨迹）与\n"
        "      【有状态栏】（框架把隐式状态提炼成显式知识注入上下文末尾）。\n"
        "      场景取自书中的 Xfinity 退款案例，全部在本地渲染，不调用任何 API。"
    )

    # 用占位 Key 构造 Agent；构造过程不联网。固定模拟时间以便输出稳定可复现。
    agent = SystemHintAgent(
        api_key="offline-preview",
        provider="kimi",
        config=config,
        verbose=False,
    )
    agent.config.simulate_time_delay = True
    agent.simulated_time = _dt(2025, 9, 14, 10, 30, 45)

    enabled = []

    # --- 案例 1：时间戳跟踪 -------------------------------------------------
    if config.enable_timestamps:
        enabled.append("时间戳跟踪")
        print("\n【案例 1 · 时间戳跟踪】为用户消息与工具结果加上时间前缀")
        follow_up = "Can you call them again to follow up?"
        print("-" * 60)
        print("  无状态栏：" + follow_up)
        print("  有状态栏：" + f"[{agent._get_timestamp()}] " + follow_up)
        print("  → Agent 能理解“昨天的文件”与“今天的修改”之间的时序关系。")

    # --- 案例 2：工具调用计数器 -------------------------------------------
    if config.enable_tool_counter:
        enabled.append("工具调用计数器")
        print("\n【案例 2 · 工具调用计数器】在工具结果上标注第几次调用")
        raw_result = json.dumps({"success": True, "output": "Call connected, no answer"})
        # 复用 execute_task 中的元信息拼装格式
        metadata = []
        if config.enable_timestamps:
            metadata.append(f"[{agent._get_timestamp()}]")
        metadata.append("[Tool call #3 for 'phone_call']")
        print("-" * 60)
        print("  无状态栏：" + raw_result)
        print("  有状态栏：" + " ".join(metadata) + "\n            " + raw_result)
        print("  → 显式计数触发模型的模式识别：到达 3/3 上限时主动停止，不再重复拨打。")

    # --- 案例 3：TODO 列表管理 -------------------------------------------
    if config.enable_todo_list:
        enabled.append("TODO 列表管理")
        print("\n【案例 3 · TODO 列表管理】把多步任务分解并持续复述")
        agent._tool_rewrite_todo_list(items=[
            "拨打 Xfinity 客服核实退款政策",
            "提交退款申请",
            "确认退款到账",
        ])
        agent._tool_update_todo_status(updates=[
            {"id": 1, "status": "completed"},
            {"id": 2, "status": "in_progress"},
        ])
        print("-" * 60)
        print("  无状态栏：（模型需自行从长轨迹中回忆还剩哪些子任务，易遗漏）")
        print("  有状态栏：")
        for line in agent._format_todo_list().splitlines():
            print("    " + line)
        print("  → TODO 列表充当外部记忆，确保行动与总体规划保持一致。")

    # --- 案例 4：详细错误信息 -------------------------------------------
    if config.enable_detailed_errors:
        enabled.append("详细错误信息")
        print("\n【案例 4 · 详细错误信息】把裸异常升级为带修复建议的诊断")
        exc = FileNotFoundError("File not found: /home/user/refund_policy.txt")
        detailed = agent._get_detailed_error(
            exc, "read_file", {"file_path": "refund_policy.txt"}
        )
        print("-" * 60)
        print("  无状态栏：" + str(exc))
        print("  有状态栏：")
        for line in detailed.splitlines():
            print("    " + line)
        print("  → Agent 从盲目重试转向分析性的问题解决（验证路径、检查目录、用绝对路径）。")

    # --- 案例 5：系统状态感知 -------------------------------------------
    if config.enable_system_state:
        enabled.append("系统状态感知")
        print("\n【案例 5 · 系统状态感知】注入当前时间、目录、操作系统、Shell、Python 版本")
        print("-" * 60)
        print("  无状态栏：（模型不知道自己身处哪个目录、哪种操作系统）")
        print("  有状态栏：")
        for line in agent._get_system_state().splitlines():
            print("    " + line)
        print("  → 操作系统信息让 Agent 做出平台相关决策（Linux 用 apt、macOS 用 brew）。")

    # --- 汇总：实际注入上下文末尾的完整状态栏 ---------------------------
    print_section("实际追加到上下文末尾的状态栏（一条 role=user 的消息）")
    hint = agent._get_system_hint()
    if hint:
        print(hint)
        print(
            "\n注意：这条消息的 role 是 user，但内容由 Agent 框架自动生成，"
            "追加在上下文最末尾——\n紧邻模型即将生成的新 token，因此获得最高注意力权重；"
            "且因为是“追加”而非\n“修改”，前面已缓存的 KV Cache 前缀不受影响。"
        )
    else:
        print("（当前配置下系统状态与 TODO 均被禁用，无状态栏可注入。）")

    print("\n本次预览启用的技术：" + ("、".join(enabled) if enabled else "（全部禁用）"))
    print("提示：用 --no-timestamps / --no-counter / --no-todo / --no-errors / --no-state")
    print("      可分别关闭某一类，观察上下文的差异。")


def main():
    """Main function with command-line argument support"""
    parser = argparse.ArgumentParser(
        description=(
            "System-Hint Enhanced AI Agent（对应书中实验 2-9 “Agent 状态栏”）\n"
            "演示五种状态栏技术如何把上下文里的隐式状态提炼为显式知识，"
            "从而改变 Agent 的行为。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  # 离线预览状态栏效果（无需 API Key，推荐先跑这个）\n"
            "  python main.py --mode preview\n"
            "  # 只看某一类技术的前后对比（例如关闭其它四类）\n"
            "  python main.py --mode preview --no-todo --no-errors --no-state --no-timestamps\n"
            "  # 用真实模型执行单个任务（需要 KIMI_API_KEY）\n"
            "  python main.py --mode single --task \"创建一个 hello world 脚本\"\n"
            "  # 对比“启用/禁用状态栏”的实际执行效果\n"
            "  python main.py --mode demo --demo comparison\n"
        ),
    )

    parser.add_argument(
        "--mode",
        choices=["preview", "single", "interactive", "demo", "sample"],
        default="interactive",
        help=(
            "执行模式：preview=离线预览状态栏（无需 API Key）；"
            "single=执行单个任务；interactive=交互模式（默认）；"
            "demo=运行内置演示；sample=运行示例任务"
        )
    )

    parser.add_argument(
        "--task",
        type=str,
        help="要执行的任务描述（single 模式必填）"
    )

    parser.add_argument(
        "--demo",
        choices=["basic", "loop", "comparison"],
        help="指定要运行的演示（demo 模式）：basic=综合演示，loop=循环防护，comparison=启用/禁用状态栏对比"
    )

    parser.add_argument(
        "--provider",
        type=str,
        default="kimi",
        help="LLM 提供方（默认：kimi，兼容 moonshot）"
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="模型名称覆盖（默认由 provider 决定，如 kimi-k3）"
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="轨迹输出文件路径（默认：trajectory.json）"
    )

    parser.add_argument(
        "--no-timestamps",
        action="store_true",
        help="关闭时间戳跟踪"
    )

    parser.add_argument(
        "--no-counter",
        action="store_true",
        help="关闭工具调用计数器"
    )

    parser.add_argument(
        "--no-todo",
        action="store_true",
        help="关闭 TODO 列表管理"
    )

    parser.add_argument(
        "--no-errors",
        action="store_true",
        help="关闭详细错误信息"
    )

    parser.add_argument(
        "--no-state",
        action="store_true",
        help="关闭系统状态感知"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="输出详细日志"
    )

    args = parser.parse_args()

    # Configure based on command-line flags
    config = SystemHintConfig(
        enable_timestamps=not args.no_timestamps,
        enable_tool_counter=not args.no_counter,
        enable_todo_list=not args.no_todo,
        enable_detailed_errors=not args.no_errors,
        enable_system_state=not args.no_state
    )
    if args.output:
        config.trajectory_file = args.output

    print("\n" + "🤖"*40)
    print("  SYSTEM-HINT ENHANCED AGENT")
    print("🤖"*40)

    if args.mode == "preview":
        preview_status_bar(config)

    elif args.mode == "single":
        if not args.task:
            print("❌ Error: --task required for single mode")
            print("Example: python main.py --mode single --task 'Create a hello world script'")
            sys.exit(1)
        
        result = execute_single_task(args.task, config, verbose=args.verbose,
                                     provider=args.provider, model=args.model)
        if result:
            print_result(result)

    elif args.mode == "sample":
        # Run the sample task
        task = get_sample_task()
        print("\n📋 Running sample task:")
        print("-"*60)
        print(task)
        print("-"*60)

        result = execute_single_task(task, config, verbose=args.verbose,
                                     provider=args.provider, model=args.model)
        if result:
            print_result(result)
    
    elif args.mode == "demo":
        if args.demo == "basic":
            demo_basic_features()
        elif args.demo == "loop":
            demo_tool_loop_prevention()
        elif args.demo == "comparison":
            demo_comparison()
        else:
            # Run all demos
            print("\nRunning all demonstrations...")
            demo_basic_features()
            input("\nPress Enter to continue...")
            demo_tool_loop_prevention()
            input("\nPress Enter to continue...")
            demo_comparison()
    
    else:  # interactive mode
        interactive_mode()
    
    print("\n👋 Thank you for using System-Hint Enhanced Agent!")


if __name__ == "__main__":
    main()
