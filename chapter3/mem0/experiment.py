"""LOCOMO benchmark experiment runner for Mem0 agent."""

import asyncio
import json
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import argparse

import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
import matplotlib.pyplot as plt
import seaborn as sns

from agent import Mem0Agent, AgentContext
from config import Config


console = Console()


class LOCOMOBenchmark:
    """LOCOMO benchmark implementation for evaluating long-context multi-agent communication."""
    
    def __init__(self, agent: Mem0Agent, config: Config):
        self.agent = agent
        self.config = config
        self.results = []
        self.scenario_data = []
        
    def generate_scenario(self, scenario_id: int, num_agents: int = 3) -> Dict[str, Any]:
        """Generate a LOCOMO benchmark scenario."""
        scenarios = [
            {
                "type": "collaborative_planning",
                "description": "Multiple agents collaborate to plan a complex project",
                "topics": ["project timeline", "resource allocation", "task dependencies", "risk assessment"],
                "context_requirements": ["maintain consistency across planning decisions", "remember previous constraints", "coordinate between agents"]
            },
            {
                "type": "information_sharing",
                "description": "Agents share and synthesize information across sessions",
                "topics": ["research findings", "data analysis", "hypothesis formation", "conclusion drawing"],
                "context_requirements": ["retain factual information", "build upon previous insights", "cross-reference between sources"]
            },
            {
                "type": "problem_solving",
                "description": "Agents work together to solve multi-step problems",
                "topics": ["problem decomposition", "solution strategies", "intermediate results", "final synthesis"],
                "context_requirements": ["remember partial solutions", "maintain logical consistency", "track progress across sessions"]
            },
            {
                "type": "negotiation",
                "description": "Agents engage in multi-round negotiations",
                "topics": ["initial positions", "concessions", "agreements", "conflict resolution"],
                "context_requirements": ["remember previous offers", "maintain negotiation stance", "track agreement points"]
            },
            {
                "type": "teaching_learning",
                "description": "Agents engage in educational dialogue",
                "topics": ["concept explanation", "question answering", "knowledge verification", "skill progression"],
                "context_requirements": ["track learning progress", "adapt to understanding level", "remember misconceptions"]
            }
        ]
        
        scenario = scenarios[scenario_id % len(scenarios)].copy()
        scenario["scenario_id"] = f"scenario_{scenario_id:03d}"
        scenario["num_agents"] = num_agents
        scenario["agents"] = [f"agent_{i:02d}" for i in range(num_agents)]
        scenario["num_sessions"] = random.randint(3, 8)
        scenario["turns_per_session"] = random.randint(5, 15)
        
        return scenario
    
    def generate_conversation_prompts(self, scenario: Dict[str, Any], session_num: int) -> List[str]:
        """Generate conversation prompts for a scenario session."""
        prompts = []
        topic = random.choice(scenario["topics"])
        
        base_prompts = {
            "collaborative_planning": [
                f"Let's discuss the {topic} for our project. What are your thoughts?",
                f"Based on our previous discussion, how should we adjust the {topic}?",
                f"Can you summarize what we've decided about {topic} so far?",
                f"What challenges do you foresee with the current {topic}?",
                f"How does the {topic} align with our overall objectives?"
            ],
            "information_sharing": [
                f"What new information do you have about {topic}?",
                f"How does this relate to what we discussed about {topic} before?",
                f"Can you integrate the findings about {topic} with our previous data?",
                f"What patterns are emerging from our {topic} analysis?",
                f"What conclusions can we draw about {topic} at this point?"
            ],
            "problem_solving": [
                f"What's our current approach to {topic}?",
                f"Have we made progress on {topic} since last time?",
                f"What obstacles are we facing with {topic}?",
                f"Can you propose an alternative solution for {topic}?",
                f"How can we validate our solution for {topic}?"
            ],
            "negotiation": [
                f"What's your position on {topic}?",
                f"Can we find middle ground on {topic}?",
                f"What concessions are you willing to make regarding {topic}?",
                f"How does this affect our previous agreement on {topic}?",
                f"Let's finalize our agreement on {topic}."
            ],
            "teaching_learning": [
                f"Can you explain {topic} in simple terms?",
                f"What questions do you have about {topic}?",
                f"How would you apply {topic} in practice?",
                f"What did we learn about {topic} last time?",
                f"Can you give an example of {topic}?"
            ]
        }
        
        scenario_prompts = base_prompts.get(scenario["type"], base_prompts["information_sharing"])
        
        # Add session-specific context
        for i in range(scenario["turns_per_session"]):
            if session_num == 0:
                prompt = f"[Session {session_num + 1}, Turn {i + 1}] {random.choice(scenario_prompts)}"
            else:
                prompt = f"[Session {session_num + 1}, Turn {i + 1}] Continuing from our previous session, {random.choice(scenario_prompts)}"
            prompts.append(prompt)
        
        return prompts
    
    async def run_scenario_session(self, scenario: Dict[str, Any], session_num: int) -> Dict[str, Any]:
        """Run a single session of a scenario."""
        session_id = f"{scenario['scenario_id']}_session_{session_num:02d}"
        user_id = f"user_{scenario['scenario_id']}"
        
        # Create contexts for all agents
        agent_contexts = {}
        for agent_id in scenario["agents"]:
            context = self.agent.create_context(
                agent_id=agent_id,
                user_id=user_id,
                session_id=f"{session_id}_{agent_id}"
            )
            agent_contexts[agent_id] = context
        
        # Generate conversation prompts
        prompts = self.generate_conversation_prompts(scenario, session_num)
        
        session_results = {
            "session_id": session_id,
            "session_num": session_num,
            "turns": [],
            "metrics": {}
        }
        
        # Run conversation turns
        for turn_idx, prompt in enumerate(prompts):
            # Randomly select which agent responds
            responding_agent = random.choice(scenario["agents"])
            agent_session_id = f"{session_id}_{responding_agent}"
            
            # Process turn
            response, metrics = await self.agent.process_turn_async(agent_session_id, prompt)
            
            session_results["turns"].append({
                "turn": turn_idx,
                "agent": responding_agent,
                "prompt": prompt,
                "response": response,
                "metrics": metrics
            })
            
            # Small delay to simulate realistic conversation
            await asyncio.sleep(0.1)
        
        # Calculate session-level metrics
        session_results["metrics"] = {
            "total_turns": len(prompts),
            "avg_response_time": np.mean([t["metrics"]["generation_time"] for t in session_results["turns"]]),
            "avg_response_length": np.mean([t["metrics"]["response_length"] for t in session_results["turns"]]),
            "consistency_scores": {
                agent_id: self.agent.evaluate_consistency(f"{session_id}_{agent_id}")
                for agent_id in scenario["agents"]
            },
            "coherence_scores": {
                agent_id: self.agent.evaluate_coherence(f"{session_id}_{agent_id}")
                for agent_id in scenario["agents"]
            }
        }
        
        return session_results
    
    async def run_scenario(self, scenario_id: int) -> Dict[str, Any]:
        """Run a complete LOCOMO scenario."""
        scenario = self.generate_scenario(scenario_id)
        
        console.print(f"\n[cyan]Running Scenario {scenario['scenario_id']}[/cyan]")
        console.print(f"Type: {scenario['type']}")
        console.print(f"Agents: {', '.join(scenario['agents'])}")
        console.print(f"Sessions: {scenario['num_sessions']}")
        
        scenario_results = {
            "scenario": scenario,
            "sessions": [],
            "start_time": datetime.now().isoformat()
        }
        
        # Run all sessions
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Running {scenario['num_sessions']} sessions...",
                total=scenario["num_sessions"]
            )
            
            for session_num in range(scenario["num_sessions"]):
                session_results = await self.run_scenario_session(scenario, session_num)
                scenario_results["sessions"].append(session_results)
                progress.update(task, advance=1)
                
                # Delay between sessions
                await asyncio.sleep(0.5)
        
        scenario_results["end_time"] = datetime.now().isoformat()
        
        # Calculate scenario-level metrics
        scenario_results["overall_metrics"] = self.calculate_scenario_metrics(scenario_results)
        
        return scenario_results
    
    def calculate_scenario_metrics(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall metrics for a scenario."""
        all_turns = []
        for session in scenario_results["sessions"]:
            all_turns.extend(session["turns"])
        
        consistency_scores = []
        coherence_scores = []
        for session in scenario_results["sessions"]:
            consistency_scores.extend(list(session["metrics"]["consistency_scores"].values()))
            coherence_scores.extend(list(session["metrics"]["coherence_scores"].values()))
        
        metrics = {
            "total_turns": len(all_turns),
            "total_sessions": len(scenario_results["sessions"]),
            "avg_response_time": np.mean([t["metrics"]["generation_time"] for t in all_turns]),
            "std_response_time": np.std([t["metrics"]["generation_time"] for t in all_turns]),
            "avg_response_length": np.mean([t["metrics"]["response_length"] for t in all_turns]),
            "avg_consistency": np.mean(consistency_scores) if consistency_scores else 0,
            "avg_coherence": np.mean(coherence_scores) if coherence_scores else 0,
            "memory_utilization": len(self.agent.get_all_memories(
                f"user_{scenario_results['scenario']['scenario_id']}", top_k=100
            ))
        }
        
        return metrics
    
    async def run_benchmark(self, num_scenarios: int = 5) -> Dict[str, Any]:
        """Run the complete LOCOMO benchmark."""
        console.print(Panel.fit(
            f"[bold cyan]LOCOMO Benchmark[/bold cyan]\n"
            f"Scenarios: {num_scenarios}\n"
            f"Model: {self.config.kimi.model_name}\n"
            f"Memory Backend: {self.config.mem0.backend}",
            title="Benchmark Configuration"
        ))
        
        benchmark_results = {
            "config": self.config.to_dict(),
            "start_time": datetime.now().isoformat(),
            "scenarios": []
        }
        
        for i in range(num_scenarios):
            scenario_results = await self.run_scenario(i)
            benchmark_results["scenarios"].append(scenario_results)
            self.results.append(scenario_results)
            
            # Display interim results
            self.display_scenario_results(scenario_results)
        
        benchmark_results["end_time"] = datetime.now().isoformat()
        benchmark_results["overall_metrics"] = self.calculate_overall_metrics(benchmark_results)
        
        return benchmark_results
    
    def calculate_overall_metrics(self, benchmark_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall benchmark metrics."""
        all_metrics = [s["overall_metrics"] for s in benchmark_results["scenarios"]]
        
        return {
            "total_scenarios": len(benchmark_results["scenarios"]),
            "avg_response_time": np.mean([m["avg_response_time"] for m in all_metrics]),
            "std_response_time": np.std([m["avg_response_time"] for m in all_metrics]),
            "avg_consistency": np.mean([m["avg_consistency"] for m in all_metrics]),
            "std_consistency": np.std([m["avg_consistency"] for m in all_metrics]),
            "avg_coherence": np.mean([m["avg_coherence"] for m in all_metrics]),
            "std_coherence": np.std([m["avg_coherence"] for m in all_metrics]),
            "avg_memory_utilization": np.mean([m["memory_utilization"] for m in all_metrics]),
            "total_turns": sum([m["total_turns"] for m in all_metrics])
        }
    
    def display_scenario_results(self, scenario_results: Dict[str, Any]) -> None:
        """Display results for a single scenario."""
        metrics = scenario_results["overall_metrics"]
        
        table = Table(title=f"Scenario {scenario_results['scenario']['scenario_id']} Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Type", scenario_results["scenario"]["type"])
        table.add_row("Sessions", str(metrics["total_sessions"]))
        table.add_row("Total Turns", str(metrics["total_turns"]))
        table.add_row("Avg Response Time", f"{metrics['avg_response_time']:.3f}s")
        table.add_row("Consistency Score", f"{metrics['avg_consistency']:.3f}")
        table.add_row("Coherence Score", f"{metrics['avg_coherence']:.3f}")
        table.add_row("Memory Utilization", str(metrics["memory_utilization"]))
        
        console.print(table)
    
    def display_overall_results(self, benchmark_results: Dict[str, Any]) -> None:
        """Display overall benchmark results."""
        metrics = benchmark_results["overall_metrics"]
        
        console.print("\n")
        console.print(Panel.fit(
            f"[bold green]Benchmark Complete![/bold green]\n"
            f"Total Scenarios: {metrics['total_scenarios']}\n"
            f"Total Turns: {metrics['total_turns']}\n"
            f"Avg Response Time: {metrics['avg_response_time']:.3f}s ± {metrics['std_response_time']:.3f}s\n"
            f"Avg Consistency: {metrics['avg_consistency']:.3f} ± {metrics['std_consistency']:.3f}\n"
            f"Avg Coherence: {metrics['avg_coherence']:.3f} ± {metrics['std_coherence']:.3f}\n"
            f"Avg Memory Utilization: {metrics['avg_memory_utilization']:.1f}",
            title="Overall Results"
        ))
    
    def save_results(self, benchmark_results: Dict[str, Any], filepath: Path) -> None:
        """Save benchmark results to file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(benchmark_results, f, indent=2)
        console.print(f"[green]Results saved to {filepath}[/green]")
    
    def generate_report(self, benchmark_results: Dict[str, Any], output_dir: Path) -> None:
        """Generate a detailed report with visualizations."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract data for visualization
        scenarios_df = pd.DataFrame([
            {
                "scenario_id": s["scenario"]["scenario_id"],
                "type": s["scenario"]["type"],
                "consistency": s["overall_metrics"]["avg_consistency"],
                "coherence": s["overall_metrics"]["avg_coherence"],
                "response_time": s["overall_metrics"]["avg_response_time"],
                "memory_utilization": s["overall_metrics"]["memory_utilization"]
            }
            for s in benchmark_results["scenarios"]
        ])
        
        # Create visualizations
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Consistency scores by scenario type
        sns.boxplot(data=scenarios_df, x="type", y="consistency", ax=axes[0, 0])
        axes[0, 0].set_title("Consistency Scores by Scenario Type")
        axes[0, 0].set_xticklabels(axes[0, 0].get_xticklabels(), rotation=45)
        
        # Coherence scores by scenario type
        sns.boxplot(data=scenarios_df, x="type", y="coherence", ax=axes[0, 1])
        axes[0, 1].set_title("Coherence Scores by Scenario Type")
        axes[0, 1].set_xticklabels(axes[0, 1].get_xticklabels(), rotation=45)
        
        # Response time distribution
        axes[1, 0].hist(scenarios_df["response_time"], bins=20, edgecolor='black')
        axes[1, 0].set_title("Response Time Distribution")
        axes[1, 0].set_xlabel("Response Time (s)")
        axes[1, 0].set_ylabel("Frequency")
        
        # Memory utilization vs performance
        axes[1, 1].scatter(scenarios_df["memory_utilization"], 
                          scenarios_df["consistency"], 
                          alpha=0.6, label="Consistency")
        axes[1, 1].scatter(scenarios_df["memory_utilization"], 
                          scenarios_df["coherence"], 
                          alpha=0.6, label="Coherence")
        axes[1, 1].set_title("Memory Utilization vs Performance")
        axes[1, 1].set_xlabel("Memory Utilization")
        axes[1, 1].set_ylabel("Score")
        axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig(output_dir / "benchmark_results.png", dpi=300)
        console.print(f"[green]Report generated in {output_dir}[/green]")


async def main():
    """Main function to run the LOCOMO benchmark."""
    parser = argparse.ArgumentParser(description="Run LOCOMO benchmark for Mem0 agent")
    parser.add_argument("--scenarios", type=int, default=5, help="Number of scenarios to run")
    parser.add_argument("--output", type=str, default="results", help="Output directory for results")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    args = parser.parse_args()
    
    # Initialize configuration
    config = Config.from_env()
    
    # Initialize agent
    console.print("[yellow]Initializing Mem0 agent...[/yellow]")
    agent = Mem0Agent(config)
    
    # Initialize benchmark
    benchmark = LOCOMOBenchmark(agent, config)
    
    # Run benchmark
    console.print(f"[yellow]Starting benchmark with {args.scenarios} scenarios...[/yellow]")
    benchmark_results = await benchmark.run_benchmark(num_scenarios=args.scenarios)
    
    # Save results
    output_dir = Path(args.output)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"locomo_results_{timestamp}.json"
    benchmark.save_results(benchmark_results, results_file)
    
    # Generate report
    report_dir = output_dir / f"report_{timestamp}"
    benchmark.generate_report(benchmark_results, report_dir)
    
    # Display overall results
    benchmark.display_overall_results(benchmark_results)


if __name__ == "__main__":
    asyncio.run(main())
