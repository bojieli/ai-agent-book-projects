"""Quick start example for Mem0 agent with Kimi K3."""

import asyncio
import os
from dotenv import load_dotenv
from rich.console import Console

from agent import Mem0Agent
from config import Config


# Load environment variables
load_dotenv()

console = Console()


async def basic_example():
    """Basic example of using Mem0 agent."""
    console.print("[bold cyan]Basic Mem0 Agent Example[/bold cyan]\n")
    
    # Initialize configuration
    config = Config.from_env()
    
    # Initialize agent
    console.print("[yellow]Initializing agent...[/yellow]")
    agent = Mem0Agent(config)
    
    # Create a session context
    session_id = "quickstart_session"
    user_id = "quickstart_user"
    agent_id = "quickstart_agent"
    
    context = agent.create_context(
        agent_id=agent_id,
        user_id=user_id,
        session_id=session_id
    )
    
    console.print(f"[green]Session created: {session_id}[/green]\n")
    
    # Example conversation
    conversations = [
        "Hello! I'm interested in learning about machine learning.",
        "I prefer Python for programming and have experience with scikit-learn.",
        "What would you recommend as the next step in my ML journey?",
        "Can you remind me what programming language I mentioned earlier?",
        "What libraries have I mentioned using?"
    ]
    
    for i, user_input in enumerate(conversations, 1):
        console.print(f"[bold]Turn {i} - User:[/bold] {user_input}")
        
        # Process the turn
        response, metrics = await agent.process_turn_async(session_id, user_input)
        
        console.print(f"[cyan]Agent:[/cyan] {response}")
        console.print(f"[dim]Response time: {metrics['generation_time']:.2f}s[/dim]\n")
        
        # Small delay for readability
        await asyncio.sleep(0.5)
    
    # Display final metrics
    console.print("\n[bold]Session Metrics:[/bold]")
    agent.display_metrics(session_id)
    
    # Show stored memories
    console.print("\n[bold]Stored Memories:[/bold]")
    memories = agent.get_all_memories(user_id)
    for memory in memories:
        console.print(f"- {memory.get('memory', memory.get('text', 'N/A'))}")


async def memory_pipeline_example(agent=None, user_id: str = "pipeline_user"):
    """Demonstrate Mem0 v3's ADD-only extraction and hybrid retrieval.

    The user first says they live in Beijing and later says they moved to
    Shanghai. Mem0 preserves both facts; retrieval is responsible for ranking
    the relevant, current one. The example also shows cross-session recall.

    Requires a working LLM API (KIMI_API_KEY) and vector store — Mem0's fact
    extraction and semantic retrieval are online model calls.
    """
    console.print("\n[bold cyan]Memory Pipeline Example (仅追加提取 + 混合检索)[/bold cyan]\n")

    if agent is None:
        agent = Mem0Agent(Config.from_env())

    def show_added(label, added):
        console.print(f"[bold]{label}[/bold]")
        if added:
            for memory in added:
                console.print(f"  [magenta][ADD][/magenta] {memory['memory']} "
                              f"[dim](id={memory['id']})[/dim]")
        else:
            console.print("  [dim](没有提取到需要追加的新事实)[/dim]")
        console.print()

    # --- Session 1: establish facts about the user ---------------------------
    console.print("[yellow]Session 1 —— 首次对话，建立用户画像[/yellow]")
    events = await asyncio.to_thread(
        agent.add_memory,
        "我住在北京，在一家 AI 创业公司做后端工程师。",
        user_id,
    )
    show_added("写入「我住在北京 / 后端工程师」后追加的事实：", events)

    events = await asyncio.to_thread(
        agent.add_memory,
        "我平时喜欢周末去爬山，也在学弹吉他。",
        user_id,
    )
    show_added("写入「爱好」后追加的事实：", events)

    # --- Recall the stored memory (used later, across the session) -----------
    console.print("[yellow]检索 —— 从记忆中回忆用户信息（跨轮次复用）[/yellow]")
    hits = await asyncio.to_thread(
        agent.search_memory, "这个用户住在哪座城市？做什么工作？", user_id
    )
    console.print(f"[bold]检索到 {len(hits)} 条相关记忆：[/bold]")
    for mem in hits:
        console.print(f"  - {mem.get('memory', mem.get('text', 'N/A'))}")
    console.print()

    # --- Session 2 (later): the new fact is appended, not overwritten --------
    console.print("[yellow]Session 2（一段时间后）—— 用户搬家，出现冲突信息[/yellow]")
    events = await asyncio.to_thread(
        agent.add_memory,
        "更新一下，我上个月从北京搬到上海了。",
        user_id,
    )
    show_added("写入「搬到上海」后追加的事实：", events)

    # --- Verify append-only history and current-state retrieval ---------------
    console.print("[yellow]核对 —— 旧事实保留，检索负责找出当前状态[/yellow]")
    memories = await asyncio.to_thread(agent.get_all_memories, user_id)
    console.print(f"[bold]用户 {user_id} 当前全部记忆（{len(memories)} 条）：[/bold]")
    for i, mem in enumerate(memories, 1):
        console.print(f"  {i}. {mem.get('memory', mem.get('text', 'N/A'))}")
    console.print()
    current = await asyncio.to_thread(agent.search_memory, "用户现在住在哪里？", user_id)
    console.print("[bold]查询当前居住地的排序结果：[/bold]")
    for mem in current:
        console.print(f"  - {mem.get('memory', mem.get('text', 'N/A'))}")
    console.print("[dim]提示：v3 可以保留北京与上海两条历史事实，并让时间感知检索优先返回当前事实。[/dim]")


async def multi_session_example():
    """Example showing memory persistence across sessions."""
    console.print("\n[bold cyan]Multi-Session Memory Example[/bold cyan]\n")
    
    # Initialize agent
    config = Config.from_env()
    agent = Mem0Agent(config)
    
    user_id = "persistent_user"
    
    # First session
    console.print("[yellow]Starting Session 1...[/yellow]")
    session1_id = "session_001"
    context1 = agent.create_context(
        agent_id="agent_001",
        user_id=user_id,
        session_id=session1_id
    )
    
    # First session conversation
    response1, _ = await agent.process_turn_async(
        session1_id, 
        "Hi! I'm working on a project about renewable energy, specifically solar panels."
    )
    console.print(f"[cyan]Session 1 Response:[/cyan] {response1}\n")
    
    response2, _ = await agent.process_turn_async(
        session1_id,
        "I need to analyze efficiency data from different manufacturers."
    )
    console.print(f"[cyan]Session 1 Response:[/cyan] {response2}\n")
    
    # Second session (different session, same user)
    console.print("[yellow]Starting Session 2 (after some time)...[/yellow]")
    session2_id = "session_002"
    context2 = agent.create_context(
        agent_id="agent_001",
        user_id=user_id,
        session_id=session2_id
    )
    
    # Second session should remember context from first session
    response3, _ = await agent.process_turn_async(
        session2_id,
        "What was I working on last time we talked?"
    )
    console.print(f"[cyan]Session 2 Response:[/cyan] {response3}\n")
    
    response4, _ = await agent.process_turn_async(
        session2_id,
        "Can you help me continue with that project?"
    )
    console.print(f"[cyan]Session 2 Response:[/cyan] {response4}\n")
    
    # Show all memories
    console.print("[bold]All Memories for User:[/bold]")
    memories = agent.get_all_memories(user_id)
    for memory in memories:
        console.print(f"- {memory.get('memory', memory.get('text', 'N/A'))}")


async def multi_agent_example():
    """Example with multiple agents collaborating."""
    console.print("\n[bold cyan]Multi-Agent Collaboration Example[/bold cyan]\n")
    
    # Initialize agent
    config = Config.from_env()
    agent = Mem0Agent(config)
    
    user_id = "collaboration_user"
    session_id = "collab_session"
    
    # Create contexts for multiple agents
    agents = ["researcher", "analyst", "advisor"]
    contexts = {}
    
    for agent_id in agents:
        contexts[agent_id] = agent.create_context(
            agent_id=agent_id,
            user_id=user_id,
            session_id=f"{session_id}_{agent_id}"
        )
        console.print(f"[green]Created context for {agent_id}[/green]")
    
    # Collaborative conversation
    console.print("\n[yellow]Starting collaborative discussion...[/yellow]\n")
    
    # Researcher starts
    response1, _ = await agent.process_turn_async(
        f"{session_id}_researcher",
        "I've found some interesting data on climate change impacts on agriculture."
    )
    console.print(f"[cyan]Researcher:[/cyan] {response1}\n")
    
    # Analyst responds
    response2, _ = await agent.process_turn_async(
        f"{session_id}_analyst",
        "Based on what the researcher mentioned, what are the key metrics we should analyze?"
    )
    console.print(f"[cyan]Analyst:[/cyan] {response2}\n")
    
    # Advisor provides guidance
    response3, _ = await agent.process_turn_async(
        f"{session_id}_advisor",
        "Considering both the research and analysis perspectives, what recommendations can we make?"
    )
    console.print(f"[cyan]Advisor:[/cyan] {response3}\n")
    
    # Show metrics for all agents
    console.print("[bold]Performance Metrics:[/bold]")
    for agent_id in agents:
        console.print(f"\n[yellow]{agent_id.capitalize()}:[/yellow]")
        summary = agent.get_performance_summary(f"{session_id}_{agent_id}")
        for key, value in summary.items():
            if isinstance(value, float):
                console.print(f"  {key}: {value:.3f}")
            else:
                console.print(f"  {key}: {value}")


async def main():
    """Run all examples."""
    console.print(Panel.fit(
        "[bold]Mem0 Agent Quickstart Examples[/bold]\n"
        "Demonstrating various capabilities of the Mem0 agent with Kimi K3",
        title="Welcome"
    ))
    
    # Check for API key
    if not os.getenv("KIMI_API_KEY"):
        console.print("[red]Error: KIMI_API_KEY not found in environment[/red]")
        console.print("Please set your Kimi API key in the .env file")
        return
    
    try:
        # Run examples
        await memory_pipeline_example()
        await asyncio.sleep(1)

        await basic_example()
        await asyncio.sleep(1)

        await multi_session_example()
        await asyncio.sleep(1)
        
        await multi_agent_example()
        
        console.print("\n[green]All examples completed successfully![/green]")
        
    except Exception as e:
        console.print(f"[red]Error running examples: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    from rich.panel import Panel
    asyncio.run(main())
