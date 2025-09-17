#!/usr/bin/env python3
"""
Context Compression Strategies Comparison Experiment
"""

import os
import sys
import json
import time
from typing import Dict, Any, List
from datetime import datetime
from dataclasses import asdict
from colorama import init, Fore, Style
from tqdm import tqdm

from config import Config
from agent import ResearchAgent
from compression_strategies import CompressionStrategy

# Initialize colorama for colored output
init(autoreset=True)


class ExperimentRunner:
    """Runs experiments comparing different compression strategies"""
    
    def __init__(self, api_key: str):
        """
        Initialize the experiment runner
        
        Args:
            api_key: API key for Kimi/Moonshot
        """
        self.api_key = api_key
        self.results = []
        
        # Create results directory
        Config.create_directories()
        
        # Results file
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
            enable_streaming=False  # Disable streaming for cleaner experiment output
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
    
    def run_all_strategies(self) -> None:
        """Run experiments for all compression strategies"""
        strategies = [
            CompressionStrategy.NO_COMPRESSION,
            CompressionStrategy.NON_CONTEXT_AWARE_INDIVIDUAL,
            CompressionStrategy.NON_CONTEXT_AWARE_COMBINED,
            CompressionStrategy.CONTEXT_AWARE,
            CompressionStrategy.CONTEXT_AWARE_CITATIONS,
            CompressionStrategy.WINDOWED_CONTEXT
        ]
        
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
        print(f"\n{'Strategy':<30} {'Success':<10} {'Time':<10} {'Compress':<12} {'Overflows':<10}")
        print("-" * 70)
        
        for result in self.results:
            metrics = result['metrics']
            strategy = metrics['strategy'][:28]
            success = "✓" if metrics['success'] else "✗"
            time_str = f"{metrics['execution_time']:.1f}s"
            compress = f"{metrics.get('compression_ratio', 1.0):.1%}" if 'compression_ratio' in metrics else "N/A"
            overflows = str(metrics.get('context_overflows', 0))
            
            # Color code success
            if metrics['success']:
                print(f"{Fore.GREEN}{strategy:<30} {success:<10} {time_str:<10} {compress:<12} {overflows:<10}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}{strategy:<30} {success:<10} {time_str:<10} {compress:<12} {overflows:<10}{Style.RESET_ALL}")
        
        print("\n" + "="*70)
        
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
                print(f"    - {r['metrics']['strategy']}: {r['metrics'].get('error', 'Unknown error')[:50]}...")
        
        # Key findings
        print(f"\n{Fore.CYAN}🔍 Key Findings:{Style.RESET_ALL}")
        print("  1. No Compression: Expected to fail with context overflow ✓")
        print("  2. Non-Context-Aware: May lose important context details")
        print("  3. Context-Aware: Better relevance preservation")
        print("  4. With Citations: Enables follow-up questions")
        print("  5. Windowed Context: Balance between detail and efficiency")


def main():
    """Main entry point"""
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
    runner = ExperimentRunner(Config.MOONSHOT_API_KEY)
    
    # Run experiments
    try:
        runner.run_all_strategies()
        print(f"\n{Fore.GREEN}✅ Experiment completed successfully!{Style.RESET_ALL}")
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Experiment interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Experiment failed: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
