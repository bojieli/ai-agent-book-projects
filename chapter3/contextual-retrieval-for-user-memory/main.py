#!/usr/bin/env python3
"""Main entry point for Contextual Retrieval + Advanced Memory Cards System

This demonstrates the dual-layer memory system combining:
1. Contextual chunking for conversation history
2. Advanced JSON cards for structured facts
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import Config
from contextual_evaluator import ContextualMemoryEvaluator
from contextual_indexer import ContextualMemoryIndexer
from contextual_agent import ContextualUserMemoryAgent
from advanced_memory_manager import AdvancedMemoryCard, create_sample_cards
from chunker import ConversationChunker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rich console for better output
console = Console()


class InteractiveContextualRAG:
    """Interactive interface for the contextual RAG system"""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the interactive system"""
        self.config = config or Config.from_env()
        self.evaluator = ContextualMemoryEvaluator(self.config)
        self.current_user = "demo_user"
        self.indexer = None
        self.agent = None
        
    def run(self):
        """Run the interactive session"""
        console.print(Panel.fit(
            "[bold cyan]Contextual RAG + Advanced Memory Cards System[/bold cyan]\n"
            "双层记忆系统：上下文感知检索 + 结构化记忆卡片\n"
            "[dim]LLM Judge enabled for automatic evaluation[/dim]",
            border_style="cyan"
        ))
        
        while True:
            self.show_menu()
            choice = Prompt.ask(
                "Select an option",
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "0"],
                default="1"
            )
            
            if choice == "1":
                self.demo_mode()
            elif choice == "2":
                self.load_and_index_conversations()
            elif choice == "3":
                self.manage_memory_cards()
            elif choice == "4":
                self.test_query()
            elif choice == "5":
                self.evaluate_test_cases()
            elif choice == "6":
                self.evaluate_specific_test_case()
            elif choice == "7":
                self.show_statistics()
            elif choice == "8":
                self.configure_settings()
            elif choice == "0":
                if Confirm.ask("Are you sure you want to exit?"):
                    console.print("[yellow]Goodbye![/yellow]")
                    break
    
    def show_menu(self):
        """Display the main menu"""
        console.print("\n[bold]Main Menu:[/bold]")
        console.print("1. 🚀 Demo Mode (Quick Start)")
        console.print("2. 📚 Load & Index Conversations")
        console.print("3. 🎴 Manage Memory Cards")
        console.print("4. 🔍 Test Query")
        console.print("5. 📊 Evaluate All Test Cases (by Category) [LLM Judge]")
        console.print("6. 🎯 Evaluate Specific Test Case [LLM Judge]")
        console.print("7. 📈 Show Statistics")
        console.print("8. ⚙️  Configure Settings")
        console.print("0. Exit")
    
    def demo_mode(self):
        """Run a quick demo with sample data"""
        console.print("\n[cyan]Demo Mode - Quick Start[/cyan]")
        
        # Initialize components
        user_id = "demo_user"
        self.indexer = ContextualMemoryIndexer(
            user_id=user_id,
            use_contextual=True
        )
        
        # Create sample memory cards
        console.print("\n[yellow]Creating sample memory cards...[/yellow]")
        sample_cards = create_sample_cards()
        for card in sample_cards:
            self.indexer.memory_manager.add_card(card)
        console.print(f"[green]✓ Added {len(sample_cards)} memory cards[/green]")
        
        # Create sample conversation chunks
        console.print("\n[yellow]Creating sample conversation chunks...[/yellow]")
        sample_chunks = self._create_sample_chunks()
        
        # Process with contextual chunking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing conversations...", total=None)
            
            result = self.indexer.process_conversation_history(
                chunks=sample_chunks,
                conversation_id="demo_conv",
                generate_summary_cards=False
            )
            
            progress.update(task, completed=True)
        
        console.print(f"[green]✓ Indexed {result['contextual_chunks']} contextual chunks[/green]")
        
        # Initialize agent
        self.agent = ContextualUserMemoryAgent(
            indexer=self.indexer,
            config=self.config
        )
        
        # Show memory status
        console.print("\n[bold]Memory System Status:[/bold]")
        console.print(f"  Memory Cards: {sum(len(cards) for cards in self.indexer.memory_manager.categories.values())}")
        console.print(f"  Contextual Chunks: {len(self.indexer.contextual_chunks)}")
        
        # Test queries
        test_queries = [
            "我的护照什么时候过期？",
            "我一月份的东京之行需要准备什么？",
            "我的医疗信息有哪些？"
        ]
        
        console.print("\n[bold]Test Queries:[/bold]")
        for i, query in enumerate(test_queries, 1):
            console.print(f"\n[cyan]Query {i}:[/cyan] {query}")
            
            if Confirm.ask("Run this query?", default=True):
                trajectory = self.agent.answer_question(
                    question=query,
                    test_id=f"demo_{i}",
                    stream=False
                )
                
                console.print(Panel(
                    trajectory.final_answer or "No answer generated",
                    title="Answer",
                    border_style="green"
                ))
                
                if trajectory.memory_cards_used:
                    console.print(f"  Memory cards used: {', '.join(trajectory.memory_cards_used)}")
                if trajectory.chunks_retrieved:
                    console.print(f"  Chunks retrieved: {len(trajectory.chunks_retrieved)}")
    
    def _create_sample_chunks(self):
        """Create sample conversation chunks for demo"""
        from chunker import ConversationChunk, ConversationMessage
        
        chunks = []
        
        # Sample conversation about travel
        messages = [
            ConversationMessage("user", "我想订一张去东京的机票", 1),
            ConversationMessage("assistant", "好的，请问您什么时候出发？", 2),
            ConversationMessage("user", "1月25日出发，2月1日返回", 3),
            ConversationMessage("assistant", "让我为您查询1月25日到2月1日的东京往返机票", 4),
        ]
        
        chunk = ConversationChunk(
            chunk_id="demo_chunk_001",
            conversation_id="demo_conv",
            test_id="demo",
            chunk_index=0,
            start_round=1,
            end_round=2,
            messages=messages,
            metadata={"topic": "travel"}
        )
        chunks.append(chunk)
        
        # Sample conversation about passport
        messages2 = [
            ConversationMessage("user", "我的护照快过期了，什么时候需要续签？", 5),
            ConversationMessage("assistant", "您的护照将于2025年2月18日过期，建议提前3-6个月办理续签", 6),
            ConversationMessage("user", "好的，我会尽快去办理", 7),
            ConversationMessage("assistant", "建议您在出国前确保护照有效期至少6个月", 8),
        ]
        
        chunk2 = ConversationChunk(
            chunk_id="demo_chunk_002",
            conversation_id="demo_conv",
            test_id="demo",
            chunk_index=1,
            start_round=3,
            end_round=4,
            messages=messages2,
            metadata={"topic": "passport"}
        )
        chunks.append(chunk2)
        
        return chunks
    
    def load_and_index_conversations(self):
        """Load and index conversation histories"""
        console.print("\n[cyan]Load & Index Conversations[/cyan]")
        
        # Get user ID
        user_id = Prompt.ask("Enter user ID", default=self.current_user)
        self.current_user = user_id
        
        # Initialize indexer
        self.indexer = ContextualMemoryIndexer(
            user_id=user_id,
            use_contextual=Confirm.ask("Enable contextual chunking?", default=True)
        )
        
        # Load conversation files
        conv_dir = Prompt.ask(
            "Enter conversation directory path",
            default="../../week2/user-memory-evaluation/conversations"
        )
        
        conv_path = Path(conv_dir)
        if not conv_path.exists():
            console.print(f"[red]Directory not found: {conv_path}[/red]")
            return
        
        # Process conversation files
        json_files = list(conv_path.glob("*.json"))
        console.print(f"Found {len(json_files)} conversation files")
        
        if not json_files:
            console.print("[yellow]No JSON files found[/yellow]")
            return
        
        # Process each file
        chunker = ConversationChunker(self.config.chunking)
        all_chunks = []
        
        with Progress(console=console) as progress:
            task = progress.add_task("Processing files...", total=len(json_files))
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extract conversations
                    conversations = data if isinstance(data, dict) else {"conv": data}
                    
                    for conv_id, messages in conversations.items():
                        chunks = chunker.chunk_conversation(
                            messages=messages,
                            conversation_id=conv_id,
                            test_id=json_file.stem
                        )
                        all_chunks.extend(chunks)
                    
                    progress.advance(task)
                    
                except Exception as e:
                    console.print(f"[red]Error processing {json_file}: {e}[/red]")
        
        console.print(f"[green]Created {len(all_chunks)} chunks[/green]")
        
        # Index with contextual processing
        if all_chunks:
            result = self.indexer.process_conversation_history(
                chunks=all_chunks,
                conversation_id="batch_index",
                generate_summary_cards=Confirm.ask("Generate summary cards?", default=True)
            )
            
            console.print(f"[green]✓ Indexed {result['contextual_chunks']} contextual chunks[/green]")
            console.print(f"[green]✓ Total memory cards: {result['memory_cards_after']}[/green]")
    
    def manage_memory_cards(self):
        """Manage advanced memory cards"""
        if not self.indexer:
            console.print("[yellow]Please initialize the system first (option 1 or 2)[/yellow]")
            return
        
        console.print("\n[cyan]Memory Card Management[/cyan]")
        
        # Show current cards
        stats = self.indexer.memory_manager.get_statistics()
        console.print(f"\nCurrent cards: {stats['total_cards']}")
        
        for category, info in stats['categories'].items():
            console.print(f"  {category}: {info['count']} cards")
        
        # Options
        console.print("\n1. View all cards")
        console.print("2. Add new card")
        console.print("3. Search cards")
        console.print("4. Delete card")
        console.print("5. Back")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            # View all cards
            context = self.indexer.memory_manager.get_context_string()
            console.print(Panel(context, title="Memory Cards", border_style="cyan"))
            
        elif choice == "2":
            # Add new card
            category = Prompt.ask("Category")
            card_key = Prompt.ask("Card key")
            backstory = Prompt.ask("Backstory")
            person = Prompt.ask("Person", default="User")
            relationship = Prompt.ask("Relationship", default="primary")
            
            # Get additional data fields
            data = {}
            while True:
                field = Prompt.ask("Add data field (empty to finish)")
                if not field:
                    break
                value = Prompt.ask(f"Value for {field}")
                data[field] = value
            
            # Create and add card
            card = AdvancedMemoryCard(
                category=category,
                card_key=card_key,
                backstory=backstory,
                date_created=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                person=person,
                relationship=relationship,
                data=data
            )
            
            memory_id = self.indexer.memory_manager.add_card(card)
            console.print(f"[green]✓ Added card: {memory_id}[/green]")
            
        elif choice == "3":
            # Search cards
            query = Prompt.ask("Search query")
            results = self.indexer.memory_manager.search_cards(query)
            
            if results:
                console.print(f"\n[green]Found {len(results)} cards:[/green]")
                for memory_id, card in results:
                    console.print(f"\n{memory_id}:")
                    console.print(f"  Backstory: {card.backstory}")
                    console.print(f"  Person: {card.person}")
            else:
                console.print("[yellow]No cards found[/yellow]")
                
        elif choice == "4":
            # Delete card
            category = Prompt.ask("Category")
            card_key = Prompt.ask("Card key")
            
            if Confirm.ask(f"Delete {category}.{card_key}?"):
                if self.indexer.memory_manager.delete_card(category, card_key):
                    console.print("[green]✓ Card deleted[/green]")
                else:
                    console.print("[red]Card not found[/red]")
    
    def test_query(self):
        """Test a query against the system"""
        if not self.indexer:
            console.print("[yellow]Please initialize the system first (option 1 or 2)[/yellow]")
            return
        
        if not self.agent:
            self.agent = ContextualUserMemoryAgent(
                indexer=self.indexer,
                config=self.config
            )
        
        console.print("\n[cyan]Test Query[/cyan]")
        
        # Show current memory status
        console.print(f"\nMemory Status:")
        console.print(f"  Cards: {sum(len(cards) for cards in self.indexer.memory_manager.categories.values())}")
        console.print(f"  Chunks: {len(self.indexer.contextual_chunks)}")
        
        # Get query
        query = Prompt.ask("\nEnter your question")
        
        # Process query
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing...", total=None)
            
            trajectory = self.agent.answer_question(
                question=query,
                test_id="interactive",
                stream=False
            )
            
            progress.update(task, completed=True)
        
        # Display results
        console.print(Panel(
            trajectory.final_answer or "No answer generated",
            title="Answer",
            border_style="green"
        ))
        
        # Show details
        console.print(f"\n[bold]Query Details:[/bold]")
        console.print(f"  Iterations: {len(trajectory.iterations)}")
        console.print(f"  Tool calls: {len(trajectory.tool_calls)}")
        
        if trajectory.memory_cards_used:
            console.print(f"\n[bold]Memory Cards Used:[/bold]")
            for card_id in trajectory.memory_cards_used:
                console.print(f"  • {card_id}")
        
        if trajectory.chunks_retrieved:
            console.print(f"\n[bold]Chunks Retrieved:[/bold] {len(trajectory.chunks_retrieved)}")
            
            if Confirm.ask("Show chunk details?"):
                for chunk_id in trajectory.chunks_retrieved[:3]:
                    if chunk_id in self.indexer.contextual_chunks:
                        chunk = self.indexer.contextual_chunks[chunk_id]
                        console.print(f"\n  Chunk: {chunk_id}")
                        console.print(f"  Context: {chunk.context[:200]}...")
    
    def evaluate_specific_test_case(self):
        """Evaluate a specific test case selected by the user"""
        console.print("\n[cyan]Evaluate Specific Test Case[/cyan]")
        
        # First, load all test cases to show to the user
        console.print("\nLoading available test cases...")
        
        # Load all categories
        all_test_cases = []
        categories = ["layer1", "layer2", "layer3"]
        
        for category in categories:
            test_cases = self.evaluator.load_test_cases(category)
            for test_id in test_cases:
                test_case = self.evaluator.test_cases[test_id]
                all_test_cases.append({
                    "id": test_id,
                    "category": category,
                    "title": test_case.title,
                    "conversations": len(test_case.conversation_histories)
                })
        
        if not all_test_cases:
            console.print("[yellow]No test cases found[/yellow]")
            return
        
        # Sort test cases by test ID (name)
        all_test_cases.sort(key=lambda x: x["id"])
        
        console.print(f"\n[green]Found {len(all_test_cases)} test cases[/green]")
        
        # Create a table to display test cases
        table = Table(title="Available Test Cases (Sorted by Name)", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Test ID", style="cyan", width=25)
        table.add_column("Category", style="magenta", width=8)
        table.add_column("Title", style="green", width=50)
        table.add_column("Conv.", justify="right", width=5)
        
        for idx, test_info in enumerate(all_test_cases, 1):
            title = test_info["title"][:47] + "..." if len(test_info["title"]) > 50 else test_info["title"]
            table.add_row(
                str(idx),
                test_info["id"],
                test_info["category"],
                title,
                str(test_info["conversations"])
            )
        
        console.print(table)
        
        # Let user select a test case
        console.print("\n[bold]Select a test case to evaluate:[/bold]")
        console.print("Enter the number (#) or the Test ID directly")
        
        user_input = Prompt.ask("Your choice")
        
        # Find the selected test case
        selected_test_id = None
        
        # Check if user entered a number
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(all_test_cases):
                selected_test_id = all_test_cases[idx]["id"]
            else:
                console.print(f"[red]Invalid number: {user_input}[/red]")
                return
        else:
            # Check if user entered a test ID
            for test_info in all_test_cases:
                if test_info["id"] == user_input:
                    selected_test_id = user_input
                    break
            
            if not selected_test_id:
                console.print(f"[red]Test case not found: {user_input}[/red]")
                return
        
        # Get the test case details
        test_case = self.evaluator.test_cases[selected_test_id]
        
        # Show test case details
        console.print(Panel(
            f"[bold]{test_case.title}[/bold]\n\n"
            f"Category: {test_case.category}\n"
            f"Description: {test_case.description}\n\n"
            f"[yellow]User Question:[/yellow]\n{test_case.user_question}\n\n"
            f"[green]Evaluation Criteria:[/green]\n{test_case.evaluation_criteria[:200]}...\n\n"
            f"Conversations: {len(test_case.conversation_histories)}",
            title=selected_test_id,
            border_style="cyan"
        ))
        
        # Run evaluation
        console.print(f"\n[cyan]Evaluating {selected_test_id}...[/cyan]")
        console.print(f"[dim]Using LLM Judge for automatic evaluation[/dim]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing...", total=None)
            
            try:
                result = self.evaluator.evaluate_test_case(selected_test_id)
                progress.update(task, completed=True)
                
                # Display result
                status = "✓ Success" if result.success else "✗ Failed"
                console.print(f"\n[{'green' if result.success else 'red'}]{status}[/{'green' if result.success else 'red'}]")
                
                console.print("\n[bold]Agent Answer:[/bold]")
                console.print(Panel(result.agent_answer or "No answer generated", border_style="cyan"))
                
                console.print("\n[bold]Evaluation Criteria:[/bold]")
                console.print(Panel(result.evaluation_criteria, border_style="green"))
                
                # Display LLM evaluation if available
                if result.llm_evaluation:
                    console.print("\n[bold cyan]LLM Judge Evaluation:[/bold cyan]")
                    llm_eval = result.llm_evaluation
                    reward = llm_eval.get('reward', 0)
                    passed = llm_eval.get('passed', False)
                    
                    # Format reward with color based on score
                    if reward >= 0.8:
                        reward_color = "green"
                    elif reward >= 0.6:
                        reward_color = "yellow"
                    else:
                        reward_color = "red"
                    
                    console.print(f"  Reward Score: [{reward_color}]{reward:.3f}/1.000[/{reward_color}]")
                    console.print(f"  Passed: [{'green' if passed else 'red'}]{'Yes' if passed else 'No'}[/{'green' if passed else 'red'}]")
                    
                    if 'reasoning' in llm_eval:
                        console.print(f"\n[bold]Reasoning:[/bold]")
                        console.print(Panel(llm_eval['reasoning'], border_style="cyan"))
                    
                    if 'required_info_found' in llm_eval and llm_eval['required_info_found']:
                        console.print(f"\n[bold]Required Information Found:[/bold]")
                        for key, found in llm_eval['required_info_found'].items():
                            status = "✓" if found else "✗"
                            color = "green" if found else "red"
                            console.print(f"  [{color}]{status}[/{color}] {key}")
                
                console.print(f"\n[bold]Statistics:[/bold]")
                console.print(f"  Iterations: {result.iterations}")
                console.print(f"  Tool Calls: {result.tool_calls}")
                console.print(f"  Memory Cards Used: {len(result.memory_cards_used)}")
                console.print(f"  Chunks Retrieved: {len(result.chunks_retrieved)}")
                console.print(f"  Contextual Chunks: {result.contextual_chunks_count}")
                console.print(f"  Processing Time: {result.processing_time:.2f}s")
                console.print(f"  Context Generation Time: {result.context_generation_time:.2f}s")
                
                if result.error:
                    console.print(f"\n[red]Error: {result.error}[/red]")
                
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]Error evaluating test case: {e}[/red]")
    
    def evaluate_test_cases(self):
        """Run evaluation on all test cases in a category"""
        console.print("\n[cyan]Evaluate All Test Cases (by Category)[/cyan]")
        
        # Load test cases
        category = Prompt.ask(
            "Select category",
            choices=["all", "layer1", "layer2", "layer3"],
            default="layer1"
        )
        
        test_cases = self.evaluator.load_test_cases(
            category=None if category == "all" else category
        )
        
        # Sort test cases by ID
        test_cases = sorted(test_cases)
        
        console.print(f"[green]Loaded {len(test_cases)} test cases (sorted by name)[/green]")
        console.print(f"[dim]Using LLM Judge for automatic evaluation[/dim]\n")
        
        # Run evaluation
        if Confirm.ask("Run evaluation?"):
            with Progress(console=console) as progress:
                task = progress.add_task("Evaluating...", total=len(test_cases))
                
                for test_id in test_cases:
                    try:
                        result = self.evaluator.evaluate_test_case(test_id)
                        progress.advance(task)
                    except Exception as e:
                        console.print(f"[red]Error evaluating {test_id}: {e}[/red]")
                        progress.advance(task)
            
            # Show results
            report = self.evaluator.generate_report()
            console.print("\n" + report)
            
            # Save results
            if Confirm.ask("Save results to file?"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"results/evaluation_{timestamp}.json"
                self.evaluator.save_results(output_file)
                console.print(f"[green]✓ Results saved to {output_file}[/green]")
    
    def show_statistics(self):
        """Show system statistics"""
        console.print("\n[cyan]System Statistics[/cyan]")
        
        if self.indexer:
            stats = self.indexer.get_statistics()
            
            # Create statistics table
            table = Table(title="Contextual Memory Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right")
            
            # Indexer stats
            table.add_row("Indexed Chunks", str(stats.get("chunks_indexed", 0)))
            table.add_row("Memory Cards", str(stats.get("memory_cards", 0)))
            table.add_row("Indexing Time", f"{stats.get('indexing_time', 0):.2f}s")
            
            # Chunker stats
            if "chunker_stats" in stats:
                cs = stats["chunker_stats"]
                table.add_row("Contextual Chunks", str(cs.get("contextual_chunks", 0)))
                table.add_row("Context Tokens", str(cs.get("total_context_tokens", 0)))
                table.add_row("Cache Hit Rate", f"{cs.get('cache_hit_rate', 0):.1%}")
                table.add_row("Est. Cost", f"${cs.get('estimated_cost', 0):.3f}")
            
            # Memory stats
            if "memory_stats" in stats:
                ms = stats["memory_stats"]
                table.add_row("Total Cards", str(ms.get("total_cards", 0)))
                for cat, info in ms.get("categories", {}).items():
                    table.add_row(f"  {cat}", str(info.get("count", 0)))
            
            console.print(table)
        else:
            console.print("[yellow]System not initialized[/yellow]")
    
    def configure_settings(self):
        """Configure system settings"""
        console.print("\n[cyan]Configuration Settings[/cyan]")
        
        # Show current settings
        console.print(f"\nCurrent Settings:")
        console.print(f"  LLM Provider: {self.config.llm.provider}")
        console.print(f"  LLM Model: {self.config.llm.model}")
        console.print(f"  Chunking: {self.config.chunking.rounds_per_chunk} rounds/chunk")
        console.print(f"  Index Mode: {self.config.index.mode}")
        
        if Confirm.ask("\nModify settings?"):
            # LLM settings
            if Confirm.ask("Change LLM provider?"):
                provider = Prompt.ask(
                    "Provider",
                    choices=["kimi", "doubao", "siliconflow", "openai"],
                    default=self.config.llm.provider
                )
                self.config.llm.provider = provider
            
            # Chunking settings
            if Confirm.ask("Change chunking settings?"):
                rounds = Prompt.ask(
                    "Rounds per chunk",
                    default=str(self.config.chunking.rounds_per_chunk)
                )
                self.config.chunking.rounds_per_chunk = int(rounds)
            
            console.print("[green]✓ Settings updated[/green]")


def main():
    """主入口：实验 3-11 上下文感知检索增强用户记忆"""
    parser = argparse.ArgumentParser(
        description=(
            "实验 3-11：利用上下文感知检索增强用户记忆。\n"
            "在把对话记忆块送入嵌入/索引前先生成『上下文前缀』，"
            "提升脱离上下文的孤立片段（如『好的，就订这个吧』）的召回。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python main.py --mode compare                 # 离线对比上下文化 vs 原始块（无需 API）\n"
            "  python main.py --mode compare --query '我的护照什么时候过期？'  # 单条查询离线检索对比\n"
            "  python main.py --mode compare --output results/compare.json    # 保存对比结果\n"
            "  python main.py --mode evaluate --category layer1               # 端到端评估（需 API/检索服务）\n"
            "  python main.py --mode interactive             # 交互式界面（默认，需 API）\n"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["interactive", "evaluate", "demo", "compare"],
        default="interactive",
        help="运行模式：interactive 交互式(默认) / evaluate 端到端评估 / demo 演示 / compare 离线对比(无需 API)",
    )
    parser.add_argument(
        "--category",
        choices=["layer1", "layer2", "layer3"],
        help="评估的测试分类（layer1 基础回忆 / layer2 多会话检索 / layer3 主动服务）",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="配置文件（JSON）路径",
    )
    # 离线对比（compare 模式）相关参数
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="compare 模式使用的记忆问答对照集 JSON（默认：memory_qa_eval.json）",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="compare 模式下对单条查询做离线检索对比（plain vs contextual 的 Top-K）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="将 compare / evaluate 的结果保存为 JSON 的路径",
    )
    # 配置覆盖项（可选，覆盖环境变量/配置文件；不改变默认行为）
    parser.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="用户标识（写入输出结果作为标签，便于区分多用户记忆）",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="覆盖 LLM 模型名（默认取环境变量/提供商默认值）",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="覆盖 LLM 提供商（kimi / doubao / siliconflow / openai 等）",
    )
    parser.add_argument(
        "--store-path",
        type=str,
        default=None,
        help="记忆块存储（chunk_store）路径，覆盖默认 data/chunk_store.json",
    )
    contextual_group = parser.add_mutually_exclusive_group()
    contextual_group.add_argument(
        "--contextual",
        dest="contextual",
        action="store_true",
        default=None,
        help="启用上下文化（索引前为每块生成上下文前缀，默认开启）",
    )
    contextual_group.add_argument(
        "--no-contextual",
        dest="contextual",
        action="store_false",
        help="关闭上下文化（直接索引原始对话块，用于对照）",
    )

    args = parser.parse_args()

    # compare 模式：完全离线，无需加载 LLM / 检索服务配置
    if args.mode == "compare":
        from contextual_compare import (
            run_comparison,
            single_query,
            DEFAULT_DATASET,
        )
        dataset = args.dataset or DEFAULT_DATASET
        if args.query:
            single_query(dataset, args.query)
        else:
            run_comparison(dataset, output_path=args.output)
        return

    # Load configuration
    if args.config:
        config = Config.load(args.config)
    else:
        config = Config.from_env()

    # 应用命令行覆盖项
    if args.provider:
        config.llm.provider = args.provider
    if args.model:
        config.llm.model = args.model
    if args.store_path:
        config.index.chunk_store_path = args.store_path
    if args.contextual is not None:
        config.index.enable_contextual = args.contextual

    if args.mode == "interactive":
        # Interactive mode
        app = InteractiveContextualRAG(config)
        app.run()
    
    elif args.mode == "evaluate":
        # Evaluation mode
        evaluator = ContextualMemoryEvaluator(config)
        test_cases = evaluator.load_test_cases(args.category)
        
        console.print(f"[cyan]Evaluating {len(test_cases)} test cases[/cyan]")
        
        for test_id in test_cases:
            try:
                result = evaluator.evaluate_test_case(test_id)
                status = "✓" if result.success else "✗"
                console.print(f"{status} {test_id}: {result.processing_time:.2f}s")
            except Exception as e:
                console.print(f"✗ {test_id}: Error - {e}")
        
        # Generate report
        report = evaluator.generate_report()
        console.print("\n" + report)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"results/evaluation_{timestamp}.json"
        Path("results").mkdir(exist_ok=True)
        evaluator.save_results(output_file)
        console.print(f"[green]Results saved to {output_file}[/green]")
    
    elif args.mode == "demo":
        # Demo mode
        app = InteractiveContextualRAG(config)
        app.demo_mode()


if __name__ == "__main__":
    main()