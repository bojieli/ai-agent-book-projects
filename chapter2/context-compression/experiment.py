#!/usr/bin/env python3
"""
Context Compression Strategies Comparison Experiment
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import asdict
from colorama import init, Fore, Style
from tqdm import tqdm

from config import Config
from agent import ResearchAgent
from compression_strategies import CompressionStrategy

# Initialize colorama for colored output
init(autoreset=True)


# Short CLI aliases -> compression strategy (order matches the book's 实验 2-10)
STRATEGY_CHOICES = {
    "no_compression": CompressionStrategy.NO_COMPRESSION,
    "individual": CompressionStrategy.NON_CONTEXT_AWARE_INDIVIDUAL,
    "combined": CompressionStrategy.NON_CONTEXT_AWARE_COMBINED,
    "context_aware": CompressionStrategy.CONTEXT_AWARE,
    "citations": CompressionStrategy.CONTEXT_AWARE_CITATIONS,
    "windowed": CompressionStrategy.WINDOWED_CONTEXT,
}

ALL_STRATEGIES = list(STRATEGY_CHOICES.values())


class ExperimentRunner:
    """Runs experiments comparing different compression strategies"""
    
    def __init__(self, api_key: str, results_file: Optional[str] = None,
                 enable_streaming: bool = False):
        """
        Initialize the experiment runner

        Args:
            api_key: API key for Kimi/Moonshot
            results_file: Optional explicit path for the results JSON (default: results/experiment_TIMESTAMP.json)
            enable_streaming: Stream compression/model output to the console during the run
        """
        self.api_key = api_key
        self.results = []
        self.enable_streaming = enable_streaming

        # Create results directory
        Config.create_directories()

        # Results file
        if results_file:
            self.results_file = results_file
            parent = os.path.dirname(self.results_file)
            if parent:
                os.makedirs(parent, exist_ok=True)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.results_file = os.path.join(Config.RESULTS_DIR, f"experiment_{timestamp}.json")

    def run_single_strategy(self, strategy: CompressionStrategy, verbose: bool = False) -> Dict[str, Any]:
        """
        Run experiment with a single compression strategy
        
        Args:
            strategy: Compression strategy to test
            verbose: Enable verbose output
            
        Returns:
            Experiment results
        """
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}Testing Strategy: {Fore.YELLOW}{strategy.value}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        
        # Create agent with the strategy
        agent = ResearchAgent(
            api_key=self.api_key,
            compression_strategy=strategy,
            verbose=verbose,
            enable_streaming=self.enable_streaming  # Off by default for cleaner experiment output
        )
        
        start_time = time.time()
        
        try:
            # Execute the research task
            result = agent.execute_research(max_iterations=Config.MAX_ITERATIONS)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Analyze results
            trajectory = result.get('trajectory')
            
            # Calculate metrics
            metrics = {
                'strategy': strategy.value,
                'success': result.get('success', False),
                'iterations': result.get('iterations', 0),
                'tool_calls': len(trajectory.tool_calls) if trajectory else 0,
                'context_overflows': trajectory.context_overflows if trajectory else 0,
                'execution_time': execution_time,
                'total_tokens': trajectory.total_tokens_used if trajectory else 0,
                'error': result.get('error'),
                'final_answer_length': len(result.get('final_answer', '')) if result.get('final_answer') else 0
            }
            
            # Calculate compression ratios
            if trajectory and trajectory.tool_calls:
                total_original = 0
                total_compressed = 0
                
                for call in trajectory.tool_calls:
                    if call.compressed_result:
                        total_original += call.compressed_result.original_length
                        total_compressed += call.compressed_result.compressed_length
                    elif call.result and call.tool_name == 'search_web':
                        # No compression - count full size
                        content = json.dumps(call.result)
                        total_original += len(content)
                        total_compressed += len(content)
                
                if total_original > 0:
                    metrics['compression_ratio'] = round(total_compressed / total_original, 3)
                    metrics['total_original_size'] = total_original
                    metrics['total_compressed_size'] = total_compressed
                else:
                    metrics['compression_ratio'] = 1.0
                    metrics['total_original_size'] = 0
                    metrics['total_compressed_size'] = 0
            
            # Print summary
            self._print_summary(metrics)
            
            # Store full result
            full_result = {
                'metrics': metrics,
                'final_answer': result.get('final_answer'),
                'timestamp': datetime.now().isoformat()
            }
            
            return full_result
            
        except Exception as e:
            print(f"{Fore.RED}Error during experiment: {str(e)}{Style.RESET_ALL}")
            
            return {
                'metrics': {
                    'strategy': strategy.value,
                    'success': False,
                    'error': str(e),
                    'execution_time': time.time() - start_time
                },
                'timestamp': datetime.now().isoformat()
            }
    
    def _print_summary(self, metrics: Dict[str, Any]):
        """Print a summary of the metrics"""
        print(f"\n{Fore.GREEN}📊 Results Summary:{Style.RESET_ALL}")
        print(f"  Success: {self._format_bool(metrics['success'])}")
        print(f"  Iterations: {metrics['iterations']}")
        print(f"  Tool Calls: {metrics['tool_calls']}")
        print(f"  Execution Time: {metrics['execution_time']:.2f}s")
        print(f"  Total Tokens: {metrics.get('total_tokens', 0):,}")

        if 'compression_ratio' in metrics:
            print(f"  Compression Ratio: {metrics['compression_ratio']:.1%}")
            print(f"  Original Size: {metrics['total_original_size']:,} chars")
            print(f"  Compressed Size: {metrics['total_compressed_size']:,} chars")
        
        if metrics.get('context_overflows', 0) > 0:
            print(f"  {Fore.YELLOW}Context Overflows: {metrics['context_overflows']}{Style.RESET_ALL}")
        
        if metrics.get('error'):
            print(f"  {Fore.RED}Error: {metrics['error'][:100]}...{Style.RESET_ALL}")
    
    def _format_bool(self, value: bool) -> str:
        """Format boolean value with color"""
        if value:
            return f"{Fore.GREEN}✓ Yes{Style.RESET_ALL}"
        else:
            return f"{Fore.RED}✗ No{Style.RESET_ALL}"
    
    def run_all_strategies(self, strategies: Optional[List[CompressionStrategy]] = None) -> None:
        """Run experiments for the given compression strategies (default: all six)"""
        if strategies is None:
            strategies = list(ALL_STRATEGIES)

        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}CONTEXT COMPRESSION STRATEGIES COMPARISON EXPERIMENT")
        print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
        print(f"\nTesting {len(strategies)} compression strategies...")
        print(f"Task: Research current affiliations of OpenAI co-founders")
        
        # Run each strategy
        for strategy in tqdm(strategies, desc="Running experiments"):
            result = self.run_single_strategy(strategy)
            self.results.append(result)
            
            # Save intermediate results
            self._save_results()
            
            # Small delay between experiments
            time.sleep(2)
        
        # Print final comparison
        self._print_comparison()
    
    def _save_results(self):
        """Save results to JSON file"""
        with open(self.results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {self.results_file}")
    
    def _print_comparison(self):
        """Print comparison table of all strategies"""
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}FINAL COMPARISON")
        print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
        
        # Create comparison table
        print(f"\n{'Strategy':<38} {'Success':<9} {'Time':<9} {'Tokens':<11} {'Compress':<10} {'Overflows':<10}")
        print("-" * 90)

        for result in self.results:
            metrics = result['metrics']
            strategy = metrics['strategy'][:36]
            success = "✓" if metrics['success'] else "✗"
            time_str = f"{metrics.get('execution_time', 0):.1f}s"
            tokens = f"{metrics.get('total_tokens', 0):,}" if metrics.get('total_tokens') else "N/A"
            compress = f"{metrics.get('compression_ratio', 1.0):.1%}" if 'compression_ratio' in metrics else "N/A"
            overflows = str(metrics.get('context_overflows', 0))

            # Color code success
            color = Fore.GREEN if metrics['success'] else Fore.RED
            print(f"{color}{strategy:<38} {success:<9} {time_str:<9} {tokens:<11} {compress:<10} {overflows:<10}{Style.RESET_ALL}")

        print("\n" + "="*90)
        
        # Analysis summary
        self._print_analysis()
    
    def _print_analysis(self):
        """Print analysis of the results"""
        print(f"\n{Fore.CYAN}📈 Analysis:{Style.RESET_ALL}")
        
        successful = [r for r in self.results if r['metrics']['success']]
        failed = [r for r in self.results if not r['metrics']['success']]
        
        print(f"\n  Successful Strategies: {len(successful)}/{len(self.results)}")
        
        if successful:
            # Find best performing
            fastest = min(successful, key=lambda x: x['metrics']['execution_time'])
            most_efficient = min(successful, key=lambda x: x['metrics'].get('total_compressed_size', float('inf')))
            
            print(f"  Fastest: {fastest['metrics']['strategy']} ({fastest['metrics']['execution_time']:.1f}s)")
            print(f"  Most Efficient: {most_efficient['metrics']['strategy']} ({most_efficient['metrics'].get('total_compressed_size', 0):,} chars)")
        
        if failed:
            print(f"\n  Failed Strategies:")
            for r in failed:
                # error may be present-but-None when a strategy fails by hitting the
                # iteration cap (rather than raising), so coalesce before slicing.
                err = r['metrics'].get('error') or 'No final answer within max iterations'
                print(f"    - {r['metrics']['strategy']}: {err[:50]}...")
        
        # Key findings
        print(f"\n{Fore.CYAN}🔍 Key Findings:{Style.RESET_ALL}")
        print("  1. No Compression: Expected to fail with context overflow ✓")
        print("  2. Non-Context-Aware: May lose important context details")
        print("  3. Context-Aware: Better relevance preservation")
        print("  4. With Citations: Enables follow-up questions")
        print("  5. Windowed Context: Balance between detail and efficiency")


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="experiment.py",
        description="上下文压缩策略对比实验（对应《深入理解 AI Agent》实验 2-10）。\n"
                    "对同一个研究任务（追踪 OpenAI 联合创始人的现状）分别运行多种压缩策略，"
                    "输出 token 用量 / 压缩率 / 成功率对比表，并保存 JSON 结果。",
        epilog="示例：\n"
               "  python experiment.py                       # 运行全部 6 种策略并对比\n"
               "  python experiment.py -s context_aware      # 只运行“上下文感知压缩”\n"
               "  python experiment.py -s individual combined # 只对比两种非任务感知策略\n"
               "  python experiment.py --model kimi-k3 -o results/k2.json\n"
               "  python experiment.py --list-strategies     # 查看可选策略名",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-s", "--strategy", nargs="+", choices=list(STRATEGY_CHOICES.keys()), metavar="NAME",
        help="要运行的压缩策略（可指定多个，默认运行全部 6 种）。可选值："
             + ", ".join(STRATEGY_CHOICES.keys()),
    )
    parser.add_argument(
        "-m", "--model", default=None,
        help=f"覆盖使用的模型名称（默认读取环境变量 MODEL_NAME，当前为 {Config.MODEL_NAME}）",
    )
    parser.add_argument(
        "-o", "--output", default=None, metavar="PATH",
        help="结果 JSON 的保存路径（默认 results/experiment_<时间戳>.json）",
    )
    parser.add_argument(
        "-n", "--max-iterations", type=int, default=None, metavar="N",
        help=f"每个策略允许的最大迭代（工具调用轮数），默认 {Config.MAX_ITERATIONS}",
    )
    parser.add_argument(
        "--streaming", action="store_true",
        help="实时流式打印模型与压缩过程的输出（默认关闭，以获得更整洁的对比输出）",
    )
    parser.add_argument(
        "--list-strategies", action="store_true",
        help="列出所有可选的压缩策略名称后退出",
    )
    return parser


def main():
    """Main entry point"""
    parser = build_parser()
    args = parser.parse_args()

    if args.list_strategies:
        print("可选的压缩策略（--strategy 的取值）：")
        for alias, strat in STRATEGY_CHOICES.items():
            print(f"  {alias:<16} -> {strat.value}")
        return

    # Apply CLI overrides onto the shared Config
    if args.model:
        Config.MODEL_NAME = args.model
    if args.max_iterations is not None:
        Config.MAX_ITERATIONS = args.max_iterations

    # Resolve which strategies to run
    if args.strategy:
        strategies = [STRATEGY_CHOICES[name] for name in args.strategy]
    else:
        strategies = list(ALL_STRATEGIES)

    # Check configuration
    if not Config.validate():
        print(f"\n{Fore.RED}Configuration validation failed!{Style.RESET_ALL}")
        print("\nPlease set up your .env file with:")
        print("  MOONSHOT_API_KEY=your_api_key_here")
        print("  SERPER_API_KEY=your_api_key_here (optional)")
        sys.exit(1)

    # Print configuration
    Config.print_config()

    # Create runner
    runner = ExperimentRunner(
        Config.MOONSHOT_API_KEY,
        results_file=args.output,
        enable_streaming=args.streaming,
    )

    # Run experiments
    try:
        runner.run_all_strategies(strategies)
        print(f"\n{Fore.GREEN}✅ Experiment completed successfully!{Style.RESET_ALL}")
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Experiment interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Experiment failed: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
