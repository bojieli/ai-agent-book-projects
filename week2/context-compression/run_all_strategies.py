#!/usr/bin/env python3
"""
Script to run all compression strategies sequentially and save results to log
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

from agent import ResearchAgent
from compression_strategies import CompressionStrategy, ContextCompressor
from config import Config
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

class StrategyRunner:
    """Runs all compression strategies and logs results"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize the strategy runner
        
        Args:
            log_dir: Directory to save log files
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"strategy_run_{timestamp}.log")
        self.json_file = os.path.join(log_dir, f"strategy_results_{timestamp}.json")
        
        # Configure logging
        self.setup_logging()
        
        # Results storage
        self.results = []
        
    def setup_logging(self):
        """Configure logging to file and console"""
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Console handler - with custom filter for cleaner output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        # Use a simpler format for console
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Configure root logger
        self.logger = logging.getLogger('StrategyRunner')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def log_banner(self, message: str, char: str = "=", width: int = 70):
        """Log a banner message"""
        border = char * width
        self.logger.info(border)
        self.logger.info(message.center(width))
        self.logger.info(border)
        
    def run_strategy(self, strategy: CompressionStrategy) -> Dict[str, Any]:
        """
        Run a single compression strategy
        
        Args:
            strategy: The compression strategy to test
            
        Returns:
            Dictionary with results
        """
        self.log_banner(f"Testing: {strategy.value}", char="-")
        self.logger.info(f"Strategy: {strategy.value}")
        
        result = {
            'strategy': strategy.value,
            'start_time': datetime.now().isoformat(),
            'success': False,
            'error': None,
            'metrics': {}
        }
        
        try:
            # Create agent with the strategy
            self.logger.info("Creating agent...")
            agent = ResearchAgent(
                api_key=Config.MOONSHOT_API_KEY,
                compression_strategy=strategy,
                verbose=False,
                enable_streaming=True  # Enable streaming to see compressions
            )
            
            # Execute research task
            self.logger.info("Starting research task...")
            start_time = time.time()
            
            # Custom stream handler to capture and log streaming output
            class StreamCapture:
                def __init__(self, logger, original_stdout):
                    self.logger = logger
                    self.original_stdout = original_stdout
                    self.buffer = []
                    self.current_line = []
                
                def write(self, text):
                    # Accumulate text
                    self.current_line.append(text)
                    
                    # If we have a newline, log the complete line
                    if '\n' in text:
                        full_line = ''.join(self.current_line)
                        lines = full_line.split('\n')
                        
                        # Log all complete lines through logger (will go to both console and file)
                        for line in lines[:-1]:
                            if line.strip():
                                # Use INFO level for important summaries, DEBUG for other output
                                if any(keyword in line for keyword in ['📝', '🎯', '📚', '📄', 'Summarizing:', 'Creating']):
                                    self.logger.info(f"[COMPRESSION] {line}")
                                else:
                                    self.logger.debug(f"[AGENT] {line}")
                                self.buffer.append(line)
                        
                        # Keep any partial line for next write
                        self.current_line = [lines[-1]] if lines[-1] else []
                
                def flush(self):
                    # Flush any remaining partial line
                    if self.current_line:
                        remaining = ''.join(self.current_line)
                        if remaining.strip():
                            self.logger.debug(f"[AGENT] {remaining}")
                            self.buffer.append(remaining)
                            self.current_line = []
                    
                def get_output(self):
                    # Ensure any remaining content is flushed
                    self.flush()
                    return '\n'.join(self.buffer)
            
            # Capture streaming output
            original_stdout = sys.stdout
            stream_capture = StreamCapture(self.logger, original_stdout)
            
            try:
                sys.stdout = stream_capture
                research_result = agent.execute_research(max_iterations=Config.MAX_ITERATIONS)
            finally:
                sys.stdout = original_stdout
            
            execution_time = time.time() - start_time
            
            # Get the complete captured output for storage
            output = stream_capture.get_output()
            
            # Store output in result for later analysis
            result['agent_output'] = output
            
            # Process results
            trajectory = research_result.get('trajectory')
            
            if research_result.get('success'):
                result['success'] = True
                result['final_answer'] = research_result.get('final_answer', 'No answer found')
                self.logger.info("✅ Strategy completed successfully")
            else:
                result['error'] = research_result.get('error', 'Unknown error')
                self.logger.warning(f"⚠️ Strategy failed: {result['error']}")
            
            # Collect metrics
            if trajectory:
                result['metrics'] = {
                    'execution_time': execution_time,
                    'tool_calls': len(trajectory.tool_calls),
                    'context_overflows': trajectory.context_overflows,
                    'total_tokens': trajectory.total_tokens_used,
                    'prompt_tokens': trajectory.prompt_tokens_used,
                    'completion_tokens': trajectory.completion_tokens_used
                }
                
                # Calculate compression statistics
                total_original = 0
                total_compressed = 0
                
                for call in trajectory.tool_calls:
                    if call.compressed_result:
                        total_original += call.compressed_result.original_length
                        total_compressed += call.compressed_result.compressed_length
                
                if total_original > 0:
                    compression_ratio = total_compressed / total_original
                    result['metrics']['compression_ratio'] = compression_ratio
                    result['metrics']['total_original_size'] = total_original
                    result['metrics']['total_compressed_size'] = total_compressed
                    result['metrics']['space_saved'] = total_original - total_compressed
                
                # Log metrics
                self.logger.info(f"Execution time: {execution_time:.2f}s")
                self.logger.info(f"Tool calls: {result['metrics']['tool_calls']}")
                self.logger.info(f"Context overflows: {result['metrics']['context_overflows']}")
                self.logger.info(f"Total tokens: {result['metrics']['total_tokens']:,}")
                
                if 'compression_ratio' in result['metrics']:
                    self.logger.info(f"Compression ratio: {result['metrics']['compression_ratio']:.1%}")
                    self.logger.info(f"Space saved: {result['metrics']['space_saved']:,} chars")
                    
                # Log compression details for each tool call
                self.logger.debug("\nCompression details by tool call:")
                for i, call in enumerate(trajectory.tool_calls, 1):
                    if call.compressed_result:
                        self.logger.debug(f"  Tool call {i}: {call.tool_name}")
                        self.logger.debug(f"    - Original: {call.compressed_result.original_length:,} chars")
                        self.logger.debug(f"    - Compressed: {call.compressed_result.compressed_length:,} chars")
                        self.logger.debug(f"    - Strategy: {call.compressed_result.strategy.value}")
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"❌ Error running strategy: {e}", exc_info=True)
        
        result['end_time'] = datetime.now().isoformat()
        return result
    
    def run_all_strategies(self):
        """Run all compression strategies"""
        strategies = [
            CompressionStrategy.NO_COMPRESSION,
            CompressionStrategy.NON_CONTEXT_AWARE_INDIVIDUAL,
            CompressionStrategy.NON_CONTEXT_AWARE_COMBINED,
            CompressionStrategy.CONTEXT_AWARE,
            CompressionStrategy.CONTEXT_AWARE_CITATIONS,
            CompressionStrategy.WINDOWED_CONTEXT
        ]
        
        self.log_banner("COMPRESSION STRATEGIES TEST RUN", char="=")
        self.logger.info(f"Testing {len(strategies)} strategies")
        self.logger.info(f"Log file: {self.log_file}")
        self.logger.info(f"JSON results: {self.json_file}")
        
        # Run each strategy
        for i, strategy in enumerate(strategies, 1):
            self.logger.info(f"\n[{i}/{len(strategies)}] Running {strategy.value}")
            result = self.run_strategy(strategy)
            self.results.append(result)
            
            # Small delay between strategies
            if i < len(strategies):
                time.sleep(2)
        
        # Generate summary
        self.generate_summary()
        
        # Save results to JSON
        self.save_json_results()
        
        self.log_banner("TEST RUN COMPLETE", char="=")
        self.logger.info(f"Results saved to:")
        self.logger.info(f"  - Log: {self.log_file}")
        self.logger.info(f"  - JSON: {self.json_file}")
    
    def generate_summary(self):
        """Generate and log a summary of all results"""
        self.log_banner("RESULTS SUMMARY", char="=")
        
        # Create comparison table
        self.logger.info("\nStrategy Comparison:")
        self.logger.info("-" * 100)
        self.logger.info(f"{'Strategy':<40} {'Success':<10} {'Time(s)':<10} {'Tokens':<12} {'Compression':<12} {'Overflows':<10}")
        self.logger.info("-" * 100)
        
        for result in self.results:
            strategy = result['strategy'][:38]  # Truncate if too long
            success = "✅ Yes" if result['success'] else "❌ No"
            
            metrics = result.get('metrics', {})
            exec_time = f"{metrics.get('execution_time', 0):.2f}" if metrics else "N/A"
            tokens = f"{metrics.get('total_tokens', 0):,}" if metrics else "N/A"
            compression = f"{metrics.get('compression_ratio', 0):.1%}" if metrics.get('compression_ratio') else "N/A"
            overflows = str(metrics.get('context_overflows', 0)) if metrics else "N/A"
            
            self.logger.info(f"{strategy:<40} {success:<10} {exec_time:<10} {tokens:<12} {compression:<12} {overflows:<10}")
        
        self.logger.info("-" * 100)
        
        # Summary statistics
        successful = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - successful
        
        self.logger.info(f"\nOverall Results:")
        self.logger.info(f"  - Successful: {successful}/{len(self.results)}")
        self.logger.info(f"  - Failed: {failed}/{len(self.results)}")
        
        # Find best performers
        if successful > 0:
            # Best compression ratio
            compressed_results = [r for r in self.results if r.get('metrics', {}).get('compression_ratio')]
            if compressed_results:
                best_compression = min(compressed_results, key=lambda r: r['metrics']['compression_ratio'])
                self.logger.info(f"  - Best compression: {best_compression['strategy']} ({best_compression['metrics']['compression_ratio']:.1%})")
            
            # Fastest execution
            timed_results = [r for r in self.results if r.get('metrics', {}).get('execution_time')]
            if timed_results:
                fastest = min(timed_results, key=lambda r: r['metrics']['execution_time'])
                self.logger.info(f"  - Fastest: {fastest['strategy']} ({fastest['metrics']['execution_time']:.2f}s)")
            
            # Most tokens used
            token_results = [r for r in self.results if r.get('metrics', {}).get('total_tokens')]
            if token_results:
                most_tokens = max(token_results, key=lambda r: r['metrics']['total_tokens'])
                least_tokens = min(token_results, key=lambda r: r['metrics']['total_tokens'])
                self.logger.info(f"  - Most tokens: {most_tokens['strategy']} ({most_tokens['metrics']['total_tokens']:,})")
                self.logger.info(f"  - Least tokens: {least_tokens['strategy']} ({least_tokens['metrics']['total_tokens']:,})")
    
    def save_json_results(self):
        """Save results to JSON file"""
        try:
            with open(self.json_file, 'w') as f:
                json.dump({
                    'run_date': datetime.now().isoformat(),
                    'config': {
                        'model': Config.MODEL_NAME,
                        'max_iterations': Config.MAX_ITERATIONS,
                        'context_window': Config.CONTEXT_WINDOW_SIZE,
                        'summary_max_tokens': Config.SUMMARY_MAX_TOKENS
                    },
                    'results': self.results
                }, f, indent=2)
            self.logger.info(f"JSON results saved to {self.json_file}")
        except Exception as e:
            self.logger.error(f"Failed to save JSON results: {e}")


def main():
    """Main entry point"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}COMPRESSION STRATEGIES AUTOMATED TEST RUNNER")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
    
    # Validate configuration
    if not Config.validate():
        print(f"{Fore.RED}Configuration validation failed!{Style.RESET_ALL}")
        print("\nPlease set up your .env file with:")
        print("  MOONSHOT_API_KEY=your_api_key_here")
        print("  SERPER_API_KEY=your_api_key_here (optional)")
        sys.exit(1)
    
    # Create directories
    Config.create_directories()
    
    # Run all strategies
    runner = StrategyRunner()
    
    try:
        print(f"{Fore.YELLOW}Starting test run...{Style.RESET_ALL}")
        print(f"Log file: {runner.log_file}\n")
        
        runner.run_all_strategies()
        
        print(f"\n{Fore.GREEN}✅ Test run complete!{Style.RESET_ALL}")
        print(f"\nResults saved to:")
        print(f"  📄 Log: {runner.log_file}")
        print(f"  📊 JSON: {runner.json_file}")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test run interrupted by user{Style.RESET_ALL}")
        runner.logger.warning("Test run interrupted by user")
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error: {e}{Style.RESET_ALL}")
        runner.logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
