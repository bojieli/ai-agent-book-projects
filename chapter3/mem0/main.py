"""Main entry point for the Mem0 agent with Kimi K3."""

import asyncio
import argparse
import json
import os
from pathlib import Path
from typing import Optional
import sys

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown

from agent import Mem0Agent
from config import Config


console = Console()


class InteractiveSession:
    """Interactive session manager for Mem0 agent."""
    
    def __init__(self, agent: Mem0Agent):
        self.agent = agent
        self.current_session = None
        self.current_user = None
        self.current_agent_id = None
        
    def start_session(self) -> None:
        """Start a new interactive session."""
        console.print(Panel.fit(
            "[bold cyan]Mem0 Agent Interactive Session[/bold cyan]\n"
            "Type 'help' for commands, 'exit' to quit",
            title="Welcome"
        ))
        
        # Get session details
        self.current_user = Prompt.ask("Enter user ID", default="user_001")
        self.current_agent_id = Prompt.ask("Enter agent ID", default="agent_001")
        session_id = Prompt.ask("Enter session ID", default="session_001")
        
        # Create context
        context = self.agent.create_context(
            agent_id=self.current_agent_id,
            user_id=self.current_user,
            session_id=session_id
        )
        self.current_session = session_id
        
        console.print(f"[green]Session started:[/green] {session_id}")
        console.print(f"[green]User:[/green] {self.current_user}")
        console.print(f"[green]Agent:[/green] {self.current_agent_id}")
        
    def show_help(self) -> None:
        """Display help information."""
        help_text = """
# Available Commands

- **help** - Show this help message
- **exit/quit** - Exit the session
- **clear** - Clear the screen
- **metrics** - Show performance metrics
- **memories** - Show stored memories
- **save** - Save conversation state
- **load** - Load conversation state
- **reset** - Reset the agent state
- **new** - Start a new session
        """
        console.print(Markdown(help_text))
    
    def show_memories(self) -> None:
        """Display stored memories."""
        if not self.current_user:
            console.print("[yellow]No active session[/yellow]")
            return
        
        memories = self.agent.get_all_memories(user_id=self.current_user)

        if not memories:
            console.print("[yellow]No memories found[/yellow]")
            return
        
        console.print(f"\n[cyan]Memories for {self.current_user}:[/cyan]")
        for i, memory in enumerate(memories, 1):
            console.print(f"{i}. {memory.get('memory', memory.get('text', 'N/A'))}")
    
    def save_state(self) -> None:
        """Save the current state."""
        filepath = Prompt.ask("Enter filepath to save", default="state.json")
        self.agent.save_state(filepath)
        console.print(f"[green]State saved to {filepath}[/green]")
    
    def load_state(self) -> None:
        """Load a saved state."""
        filepath = Prompt.ask("Enter filepath to load", default="state.json")
        if Path(filepath).exists():
            self.agent.load_state(filepath)
            console.print(f"[green]State loaded from {filepath}[/green]")
        else:
            console.print(f"[red]File not found: {filepath}[/red]")
    
    async def run(self) -> None:
        """Run the interactive session."""
        self.start_session()
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold]You[/bold]")
                
                # Check for commands
                if user_input.lower() in ["exit", "quit"]:
                    if Confirm.ask("Are you sure you want to exit?"):
                        break
                elif user_input.lower() == "help":
                    self.show_help()
                    continue
                elif user_input.lower() == "clear":
                    console.clear()
                    continue
                elif user_input.lower() == "metrics":
                    self.agent.display_metrics(self.current_session)
                    continue
                elif user_input.lower() == "memories":
                    self.show_memories()
                    continue
                elif user_input.lower() == "save":
                    self.save_state()
                    continue
                elif user_input.lower() == "load":
                    self.load_state()
                    continue
                elif user_input.lower() == "reset":
                    if Confirm.ask("Reset agent state?"):
                        self.agent.reset()
                        console.print("[green]Agent state reset[/green]")
                    continue
                elif user_input.lower() == "new":
                    self.start_session()
                    continue
                
                # Process the input through the agent
                console.print("[dim]Processing...[/dim]")
                response, metrics = await self.agent.process_turn_async(
                    self.current_session, 
                    user_input
                )
                
                # Display response
                console.print(f"\n[bold cyan]Agent[/bold cyan]: {response}")
                
                # Display metrics (optional)
                if metrics.get("generation_time"):
                    console.print(
                        f"[dim]Generated in {metrics['generation_time']:.2f}s | "
                        f"Turn {metrics['turn_count']} | "
                        f"Memories: {metrics['memory_count']}[/dim]"
                    )
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                if Confirm.ask("Exit session?"):
                    break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        
        console.print("\n[cyan]Session ended. Goodbye![/cyan]")


async def run_batch_mode(agent: Mem0Agent, input_file: Path, output_file: Path) -> None:
    """Run the agent in batch mode."""
    console.print(f"[yellow]Processing batch file: {input_file}[/yellow]")
    
    # Read input file
    with open(input_file, "r") as f:
        batch_data = f.read()
    
    # Parse batch data (assuming JSON format)
    import json
    try:
        sessions = json.loads(batch_data)
    except json.JSONDecodeError:
        console.print("[red]Invalid JSON in input file[/red]")
        return
    
    results = []
    
    # Process each session
    for session_data in sessions:
        session_id = session_data.get("session_id", "batch_session")
        user_id = session_data.get("user_id", "batch_user")
        agent_id = session_data.get("agent_id", "batch_agent")
        turns = session_data.get("turns", [])
        
        # Create context
        context = agent.create_context(
            agent_id=agent_id,
            user_id=user_id,
            session_id=session_id
        )
        
        session_results = {
            "session_id": session_id,
            "user_id": user_id,
            "agent_id": agent_id,
            "turns": []
        }
        
        # Process turns
        for turn in turns:
            response, metrics = await agent.process_turn_async(session_id, turn)
            session_results["turns"].append({
                "input": turn,
                "response": response,
                "metrics": metrics
            })
        
        results.append(session_results)
    
    # Save results
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    console.print(f"[green]Results saved to {output_file}[/green]")


def _load_add_messages(text: str):
    """Resolve the --text argument for a memory add operation.

    If it points to an existing JSON file, load it (expects a message list
    or a string); otherwise treat the argument itself as a user utterance.
    """
    if os.path.exists(text):
        with open(text, "r", encoding="utf-8") as f:
            return json.load(f)
    return text


async def run_memory_op(agent: Mem0Agent, args) -> None:
    """Run a single direct memory operation (add/search/get-all/history/delete).

    This exposes mem0 v3's ADD-only ingestion and retrieval API independently
    of the chat loop.
    """
    op = args.op
    if not op:
        console.print("[red]memory 模式需要 --op 参数（add/search/get-all/history/delete）[/red]")
        sys.exit(1)

    result = None

    if op == "add":
        if not args.text:
            console.print("[red]add 操作需要 --text 参数（一段对话文本，或 JSON 消息文件路径）[/red]")
            sys.exit(1)
        messages = _load_add_messages(args.text)
        added = await asyncio.to_thread(agent.add_memory, messages, args.user_id, args.agent_id)
        console.print("[green]写入完成，ADD-only 提取追加的事实：[/green]")
        if added:
            for memory in added:
                console.print(f"  [ADD] {memory['memory']}  [dim](id={memory['id']})[/dim]")
        else:
            console.print("  [dim]（没有提取到需要追加的新事实）[/dim]")
        result = {"op": "add", "user_id": args.user_id, "added_memories": added}

    elif op == "search":
        if not args.query:
            console.print("[red]search 操作需要 --query 参数[/red]")
            sys.exit(1)
        hits = await asyncio.to_thread(agent.search_memory, args.query, args.user_id, args.agent_id)
        console.print(f"[green]检索到 {len(hits)} 条相关记忆：[/green]")
        for mem in hits:
            console.print(f"  - {mem.get('memory', mem.get('text', 'N/A'))}  [dim](id={mem.get('id','')})[/dim]")
        result = {"op": "search", "query": args.query, "user_id": args.user_id, "memories": hits}

    elif op == "get-all":
        memories = await asyncio.to_thread(agent.get_all_memories, args.user_id, args.agent_id)
        console.print(f"[green]用户 {args.user_id} 共有 {len(memories)} 条记忆：[/green]")
        for i, mem in enumerate(memories, 1):
            console.print(f"  {i}. {mem.get('memory', mem.get('text', 'N/A'))}  [dim](id={mem.get('id','')})[/dim]")
        result = {"op": "get-all", "user_id": args.user_id, "memories": memories}

    elif op == "history":
        if not args.memory_id:
            console.print("[red]history 操作需要 --memory-id 参数[/red]")
            sys.exit(1)
        history = await asyncio.to_thread(agent.memory_history, args.memory_id)
        console.print(f"[green]记忆 {args.memory_id} 的修改历史：[/green]")
        for entry in history:
            console.print(f"  - {entry}")
        result = {"op": "history", "memory_id": args.memory_id, "history": history}

    elif op == "delete":
        if not args.memory_id:
            console.print("[red]delete 操作需要 --memory-id 参数[/red]")
            sys.exit(1)
        await asyncio.to_thread(agent.delete_memory, args.memory_id)
        console.print(f"[green]已删除记忆 {args.memory_id}[/green]")
        result = {"op": "delete", "memory_id": args.memory_id}

    if args.output and result is not None:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        console.print(f"[green]结果已写入 {args.output}[/green]")


CLI_EPILOG = """\
示例：
  python main.py                              # 默认进入交互式对话（记忆随对话自动写入/检索）
  python main.py --mode demo --user-id u1     # 运行“北京→上海”的 ADD-only + 混合检索演示
  python main.py --mode memory --op add   --text "我住在北京，是一名后端工程师" --user-id u1
  python main.py --mode memory --op search --query "这个用户住在哪里？" --user-id u1
  python main.py --mode memory --op get-all --user-id u1 --output mem.json
  python main.py --mode batch  --input conversations.json --output results.json
  python main.py --mode benchmark --model kimi-k3

说明：memory / demo / interactive / batch / benchmark 均需要可用的 LLM API（KIMI_API_KEY）
及向量存储；Mem0 的记忆提取与检索依赖在线模型调用。
"""


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Mem0 记忆智能体（Kimi K3）— 演示 Mem0 v3 的 ADD-only 提取与混合检索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=CLI_EPILOG,
    )
    parser.add_argument(
        "--mode",
        choices=["interactive", "batch", "benchmark", "memory", "demo"],
        default="interactive",
        help="运行模式：interactive 交互对话（默认）/ batch 批量对话 / benchmark 跑 LOCOMO 基准 / "
             "memory 直接调用记忆操作 / demo 记忆流水线演示",
    )
    parser.add_argument(
        "--op",
        choices=["add", "search", "get-all", "history", "delete"],
        help="memory 模式下的记忆操作：add 写入 / search 检索 / get-all 列出全部 / "
             "history 查看某条记忆的修改历史 / delete 删除",
    )
    parser.add_argument("--text", type=str,
                        help="add 操作的对话输入：一段文本，或指向 JSON 消息列表文件的路径")
    parser.add_argument("--query", type=str, help="search 操作的查询语句")
    parser.add_argument("--memory-id", type=str, help="history / delete 操作针对的记忆 ID")
    parser.add_argument("--user-id", type=str, default="user_001",
                        help="记忆归属的用户 ID（默认 user_001）")
    parser.add_argument("--agent-id", type=str, default="agent_001",
                        help="智能体 ID（默认 agent_001）")
    parser.add_argument("--model", type=str,
                        help="覆盖 MODEL_NAME，指定对话模型（如 kimi-k3）")
    parser.add_argument("--input", type=str, help="batch 模式的输入 JSON 文件")
    parser.add_argument("--output", type=str,
                        help="将结果写入的 JSON 文件（memory / batch 模式）")
    parser.add_argument("--config", type=str, help="配置文件路径（预留）")
    args = parser.parse_args()

    # Initialize configuration
    config = Config.from_env()
    if args.model:
        config.kimi.model_name = args.model

    # Initialize agent
    console.print("[yellow]Initializing Mem0 agent...[/yellow]")
    try:
        agent = Mem0Agent(config)
        console.print("[green]Agent initialized successfully[/green]")
    except Exception as e:
        console.print(f"[red]Failed to initialize agent: {e}[/red]")
        sys.exit(1)

    # Run based on mode
    if args.mode == "interactive":
        session = InteractiveSession(agent)
        await session.run()
    elif args.mode == "batch":
        if not args.input or not args.output:
            console.print("[red]Batch mode requires --input and --output arguments[/red]")
            sys.exit(1)
        await run_batch_mode(agent, Path(args.input), Path(args.output))
    elif args.mode == "memory":
        await run_memory_op(agent, args)
    elif args.mode == "demo":
        from quickstart import memory_pipeline_example
        await memory_pipeline_example(agent=agent, user_id=args.user_id)
    elif args.mode == "benchmark":
        # Import and run benchmark
        from experiment import LOCOMOBenchmark
        benchmark = LOCOMOBenchmark(agent, config)
        results = await benchmark.run_benchmark(num_scenarios=3)
        benchmark.display_overall_results(results)


if __name__ == "__main__":
    asyncio.run(main())
