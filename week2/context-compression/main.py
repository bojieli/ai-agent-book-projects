#!/usr/bin/env python3
"""
Interactive demo for context compression strategies
"""

import os
import sys
import argparse
from colorama import init, Fore, Style

from config import Config
from agent import ResearchAgent
from compression_strategies import CompressionStrategy

# Initialize colorama
init(autoreset=True)


def print_banner():
    """Print demo banner"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}CONTEXT COMPRESSION RESEARCH AGENT - INTERACTIVE DEMO")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print("\nThis demo allows you to test different compression strategies")
    print("for researching OpenAI co-founders' current affiliations.\n")


def select_strategy() -> CompressionStrategy:
    """Let user select a compression strategy"""
    print(f"{Fore.YELLOW}Available Compression Strategies:{Style.RESET_ALL}")
    print("1. No Compression (expected to fail with large contexts)")
    print("2. Non-Context-Aware: Individual Summaries (summarize each page, then concatenate)")
    print("3. Non-Context-Aware: Combined Summary (concatenate all pages, then summarize once)")
    print("4. Context-Aware Summarization")
    print("5. Context-Aware with Citations")
    print("6. Windowed Context (only compress when approaching context limit)")
    
    while True:
        try:
            choice = input(f"\n{Fore.GREEN}Select strategy (1-6): {Style.RESET_ALL}")
            strategies = [
                CompressionStrategy.NO_COMPRESSION,
                CompressionStrategy.NON_CONTEXT_AWARE_INDIVIDUAL,
                CompressionStrategy.NON_CONTEXT_AWARE_COMBINED,
                CompressionStrategy.CONTEXT_AWARE,
                CompressionStrategy.CONTEXT_AWARE_CITATIONS,
                CompressionStrategy.WINDOWED_CONTEXT
            ]
            return strategies[int(choice) - 1]
        except (ValueError, IndexError):
            print(f"{Fore.RED}Invalid choice. Please enter 1-6.{Style.RESET_ALL}")


def run_demo(enable_streaming=True):
    """Run the interactive demo
    
    Args:
        enable_streaming: Whether to enable streaming output (default: True)
    """
    print_banner()
    
    # Check configuration
    if not Config.validate():
        print(f"\n{Fore.RED}Configuration validation failed!{Style.RESET_ALL}")
        print("\nPlease set up your .env file with:")
        print("  MOONSHOT_API_KEY=your_api_key_here")
        print("  SERPER_API_KEY=your_api_key_here (optional, will use mock data)")
        sys.exit(1)
    
    # Select strategy
    strategy = select_strategy()
    
    print(f"\n{Fore.CYAN}Selected: {strategy.value}{Style.RESET_ALL}")
    
    # Display streaming status
    streaming_status = "ENABLED" if enable_streaming else "DISABLED"
    print(f"{Fore.YELLOW}Streaming output: {streaming_status}{Style.RESET_ALL}")
    
    # Create agent
    print(f"\n{Fore.YELLOW}Initializing agent...{Style.RESET_ALL}")
    agent = ResearchAgent(
        api_key=Config.MOONSHOT_API_KEY,
        compression_strategy=strategy,
        verbose=False,
        enable_streaming=enable_streaming
    )
    
    print(f"\n{Fore.CYAN}Starting research task...{Style.RESET_ALL}")
    print("Task: Find current affiliations of all OpenAI co-founders\n")
    print("-" * 70)
    
    try:
        # Execute research
        result = agent.execute_research(max_iterations=Config.MAX_ITERATIONS)
        
        # Print results
        print("\n" + "="*70)
        print(f"{Fore.GREEN}RESEARCH COMPLETE{Style.RESET_ALL}")
        print("="*70)
        
        if result.get('success'):
            print(f"\n{Fore.GREEN}✅ Success!{Style.RESET_ALL}")
            print(f"\nFinal Answer:\n{result.get('final_answer', 'No answer found')}")
        else:
            print(f"\n{Fore.RED}❌ Failed{Style.RESET_ALL}")
            if result.get('error'):
                print(f"Error: {result['error']}")
        
        # Print statistics
        trajectory = result.get('trajectory')
        if trajectory:
            print(f"\n{Fore.CYAN}📊 Statistics:{Style.RESET_ALL}")
            print(f"  Tool Calls: {len(trajectory.tool_calls)}")
            print(f"  Context Overflows: {trajectory.context_overflows}")
            print(f"  Execution Time: {result.get('execution_time', 0):.2f}s")
            print(f"  Total Tokens Used: {trajectory.total_tokens_used:,}")
            print(f"    - Prompt Tokens: {trajectory.prompt_tokens_used:,}")
            print(f"    - Completion Tokens: {trajectory.completion_tokens_used:,}")
            
            # Calculate compression stats
            if trajectory.tool_calls:
                total_original = 0
                total_compressed = 0
                
                for call in trajectory.tool_calls:
                    if call.compressed_result:
                        total_original += call.compressed_result.original_length
                        total_compressed += call.compressed_result.compressed_length
                
                if total_original > 0:
                    ratio = total_compressed / total_original
                    print(f"  Compression Ratio: {ratio:.1%}")
                    print(f"  Space Saved: {total_original - total_compressed:,} chars")
        
        # Follow-up question demo (for citation strategy)
        if strategy == CompressionStrategy.CONTEXT_AWARE_CITATIONS and result.get('success'):
            print(f"\n{Fore.YELLOW}This strategy supports follow-up questions!{Style.RESET_ALL}")
            follow_up = input("\nAsk a follow-up question (or press Enter to skip): ")
            
            if follow_up:
                print(f"\n{Fore.CYAN}Processing follow-up...{Style.RESET_ALL}")
                # Add follow-up to conversation
                agent.conversation_history.append({"role": "user", "content": follow_up})
                
                # Get response (simplified for demo)
                messages = agent.conversation_history.copy()
                
                if enable_streaming:
                    message = agent._stream_response(messages)
                else:
                    message = agent._non_streaming_response(messages)
                
                if message.get('content'):
                    print(f"\n{Fore.GREEN}Follow-up Answer:{Style.RESET_ALL}")
                    print(message['content'])
    
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Demo interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")


def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Context Compression Research Agent Demo')
    parser.add_argument(
        '--no-streaming',
        action='store_true',
        help='Disable streaming output (default: streaming enabled)'
    )
    args = parser.parse_args()
    
    # Determine streaming preference
    enable_streaming = not args.no_streaming
    
    try:
        run_demo(enable_streaming=enable_streaming)
        
        # Ask if user wants to try another strategy
        while True:
            again = input(f"\n{Fore.GREEN}Try another strategy? (y/n): {Style.RESET_ALL}")
            if again.lower() == 'y':
                run_demo(enable_streaming=enable_streaming)
            else:
                print(f"\n{Fore.CYAN}Thank you for using the demo!{Style.RESET_ALL}")
                break
                
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
        sys.exit(0)


if __name__ == "__main__":
    main()
