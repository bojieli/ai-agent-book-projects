#!/usr/bin/env python3
"""
Main Entry Point for Tool Calling Demo
Automatically selects the best backend based on your platform:
- Linux/Windows with NVIDIA GPU: Uses vLLM
- Mac/Windows/Linux without GPU: Uses Ollama
"""

import os
import sys
import platform
import logging
from typing import Optional, Dict, Any, List
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ToolCallingAgent:
    """
    Universal tool calling agent that works on all platforms
    Automatically selects vLLM (if GPU available) or Ollama
    """
    
    def __init__(self, backend: Optional[str] = None):
        """
        Initialize with automatic backend detection
        
        Args:
            backend: Force a specific backend ('vllm', 'ollama', or None for auto)
        """
        self.agent = None
        self.backend_type = backend or self._detect_best_backend()
        
        logger.info(f"Initializing on {platform.system()} with {self.backend_type}")
        self._initialize_backend()
    
    def _detect_best_backend(self) -> str:
        """Detect the best backend for current platform"""
        system = platform.system()
        
        # Check for CUDA support (Linux/Windows with NVIDIA GPU)
        if system in ["Linux", "Windows"]:
            try:
                import torch
                if torch.cuda.is_available():
                    logger.info("CUDA detected - will use vLLM")
                    return "vllm"
            except ImportError:
                pass
        
        # Default to Ollama for Mac or systems without CUDA
        logger.info(f"Using Ollama on {system}")
        return "ollama"
    
    def _initialize_backend(self):
        """Initialize the selected backend"""
        if self.backend_type == "vllm":
            self._init_vllm()
        else:
            self._init_ollama()
    
    def _init_vllm(self):
        """Initialize vLLM backend"""
        try:
            # Check if vLLM server is running
            import requests
            from config import VLLM_HOST, VLLM_PORT
            
            server_url = f"http://{VLLM_HOST}:{VLLM_PORT}/health"
            
            try:
                response = requests.get(server_url, timeout=1)
                if response.status_code != 200:
                    raise ConnectionError("vLLM server not responding")
            except:
                # Try to start the server
                logger.info("Starting vLLM server...")
                from server import VLLMServer
                server = VLLMServer()
                server.start(wait_for_ready=True)
            
            # Initialize vLLM agent
            from agent import VLLMToolAgent
            from config import OPENAI_API_BASE, OPENAI_API_KEY
            
            self.agent = VLLMToolAgent(
                api_base=OPENAI_API_BASE,
                api_key=OPENAI_API_KEY
            )
            logger.info("✅ vLLM agent initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize vLLM: {e}")
            logger.info("Falling back to Ollama")
            self.backend_type = "ollama"
            self._init_ollama()
    
    def _init_ollama(self):
        """Initialize Ollama backend"""
        try:
            import ollama
            from ollama_native import OllamaNativeAgent
            
            # Check if Ollama is running
            client = ollama.Client()
            try:
                models_response = client.list()
                available_models = []
                if hasattr(models_response, 'models'):
                    available_models = [m.model for m in models_response.models]
                
                if not available_models:
                    logger.error("No Ollama models installed")
                    logger.info("Install a model with: ollama pull qwen3:0.6b")
                    sys.exit(1)
                
                # Use qwen3:0.6b as the default model
                model = "qwen3:0.6b"
                
                # Check if qwen3:0.6b is available
                if model not in available_models:
                    logger.warning(f"Recommended model {model} not found in available models")
                    logger.info("Install with: ollama pull qwen3:0.6b")
                    # Fall back to first available model if qwen3:0.6b is not installed
                    model = available_models[0]
                    logger.info(f"Using fallback model: {model}")
                
                logger.info(f"Using Ollama model: {model}")
                self.agent = OllamaNativeAgent(model=model)
                
            except Exception as e:
                logger.error(f"Ollama is not running: {e}")
                logger.info("\nPlease start Ollama:")
                
                system = platform.system()
                if system == "Darwin":  # Mac
                    logger.info("  brew services start ollama")
                    logger.info("  or: ollama serve")
                elif system == "Windows":
                    logger.info("  Start Ollama from the system tray")
                    logger.info("  or run: ollama serve")
                else:  # Linux
                    logger.info("  systemctl start ollama")
                    logger.info("  or: ollama serve")
                
                sys.exit(1)
                
        except ImportError:
            logger.error("Ollama not installed")
            logger.info("Install with: pip install ollama")
            sys.exit(1)
    
    def chat(self, message: str, use_tools: bool = True, stream: bool = False, **kwargs) -> str:
        """
        Send a message to the agent
        
        Args:
            message: User message
            use_tools: Whether to enable tool calling
            stream: Whether to stream the response
            **kwargs: Additional backend-specific parameters
            
        Returns:
            Agent response (or generator if streaming)
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized")
        
        return self.agent.chat(message, use_tools=use_tools, stream=stream, **kwargs)
    
    def reset_conversation(self):
        """Reset conversation history"""
        if hasattr(self.agent, 'reset_conversation'):
            self.agent.reset_conversation()


def get_sample_tasks() -> List[Dict[str, str]]:
    """Get sample tasks for demonstration"""
    return [
        {
            "name": "🕐 Current Time Check",
            "description": "Get the current time in a specific city",
            "task": "What is the current time in Vancouver?"
        },
        {
            "name": "☀️ Simple Weather Check",
            "description": "Get current weather for a single city",
            "task": "What's the weather like in Vancouver right now?"
        },
        {
            "name": "☀️ Time and Weather Check",
            "description": "Get current time and weather for a single city",
            "task": "What's the current time and weather like in Vancouver right now?"
        },
        {
            "name": "💵 Compound Interest Calculation",
            "description": "Calculate compound interest using code interpreter",
            "task": "Calculate the compound interest on $5,000 invested at 6% annual interest rate for 30 years, compounded monthly."
        },

        {
            "name": "🌡️ Multi-City Weather Analysis",
            "description": "Compare weather across multiple cities using real-time data",
            "task": """Get the current weather for Tokyo, New York, London, Sydney, and Dubai. 
Then:
1. Which city has the highest temperature?
2. Which city has the lowest humidity?
3. Convert all temperatures to Fahrenheit for comparison
4. Calculate the average temperature across all cities"""
        },
        {
            "name": "💰 Complex Financial Analysis",
            "description": "Multi-step financial calculation with currency conversion",
            "task": """A company has the following quarterly revenues:
- Q1: $2,500,000 USD
- Q2: €2,100,000 EUR
- Q3: £1,800,000 GBP
- Q4: ¥380,000,000 JPY

Please:
1. Convert all revenues to USD
2. Calculate the total annual revenue in USD
3. Determine the average quarterly revenue
4. Find which quarter had the highest revenue
5. If the company has a 20% profit margin, calculate the annual profit in USD"""
        },
        {
            "name": "⏰ Global Time Zone Coordination",
            "description": "Coordinate meeting times across time zones",
            "task": """We need to schedule a global meeting with offices in:
- San Francisco (PST)
- New York (EST)
- London (GMT/BST)
- Tokyo (JST)
- Sydney (AEST)

If the meeting is at 2 PM London time:
1. What time would it be in each city?
2. Is this during normal business hours (9 AM - 5 PM) for each location?
3. Suggest a better time that works for most offices"""
        },
    ]


def run_single_task(agent: ToolCallingAgent, task: str, stream: bool = True):
    """Run a single task with optional streaming"""
    print("\n" + "="*60)
    print("TASK EXECUTION")
    print("="*60)
    print(f"\n📋 Task: {task}")
    print("-"*60)
    
    try:
        if stream:
            print("\n⏳ Processing (streaming)...\n")
            
            response_chunks = []
            thinking_shown = False
            tools_shown = False
            response_started = False
            last_chunk_type = None
            
            for chunk in agent.chat(task, stream=True):
                chunk_type = chunk.get("type")
                content = chunk.get("content", "")
                
                if chunk_type == "thinking":
                    if not thinking_shown:
                        print("🧠 Thinking: ", end="", flush=True)
                        thinking_shown = True
                    # Stream thinking character by character in gray
                    print(f"\033[90m{content}\033[0m", end="", flush=True)
                
                elif chunk_type == "tool_call":
                    if not tools_shown:
                        print("\n\n🔧 Tool Calls:")
                        tools_shown = True
                    # Display tool call info
                    tool_info = content
                    print(f"  → {tool_info.get('name', 'unknown')}: {tool_info.get('arguments', {})}")
                    # Reset response_started flag after tool calls
                    response_started = False
                
                elif chunk_type == "tool_result":
                    # Display tool result
                    result_str = str(content)
                    print(f"    ✓ {result_str}")
                    # Reset response_started flag after tool results
                    response_started = False
                
                elif chunk_type == "content":
                    if not response_started:
                        # Check if this is content after tool execution
                        if last_chunk_type in ["tool_result", "tool_call"]:
                            print("\n🤖 Assistant: ", end="", flush=True)
                        elif thinking_shown or tools_shown:
                            print("\n\n🤖 Assistant: ", end="", flush=True)
                        else:
                            print("🤖 Assistant: ", end="", flush=True)
                        response_started = True
                    # Stream the actual response content
                    print(content, end="", flush=True)
                    response_chunks.append(content)
                
                elif chunk_type == "error":
                    print(f"\n❌ Error: {content}")
                
                last_chunk_type = chunk_type
            
            print("\n" + "-"*40)
            
        else:
            print("\n⏳ Processing...")
            response = agent.chat(task, stream=False)
            
            print("\n✅ Response:")
            print("-"*40)
            print(response)
            print("-"*40)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.exception("Task execution failed")


def interactive_mode(agent: ToolCallingAgent, stream: bool = True):
    """Run interactive chat mode with optional streaming"""
    print("\n" + "="*60)
    print("💬 INTERACTIVE MODE" + (" (STREAMING)" if stream else ""))
    print("="*60)
    print("\nYou can now chat with the AI agent. It has access to various tools:")
    
    # Show available tools
    from tools import ToolRegistry
    registry = ToolRegistry()
    tools = registry.get_tool_schemas()
    
    print("\n📦 Available Tools:")
    for i, tool in enumerate(tools, 1):
        func = tool["function"]
        print(f"  {i}. {func['name']}: {func['description']}")
    
    print("\n💡 Commands:")
    print("  /reset      - Reset conversation")
    print("  /tools      - Show available tools")
    print("  /samples    - Show sample tasks")
    print("  /sample <n> - Run sample task number n")
    print("  /stream     - Toggle streaming mode")
    print("  /help       - Show this help")
    print("  /exit       - Exit the program")
    print("-"*60)
    
    streaming_enabled = stream
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() == "/exit" or user_input.lower() == "quit":
                print("👋 Goodbye!")
                break
            
            elif user_input.lower() == "/reset":
                agent.reset_conversation()
                print("✅ Conversation reset")
                continue
            
            elif user_input.lower() == "/tools":
                print("\n📦 Available Tools:")
                for i, tool in enumerate(tools, 1):
                    func = tool["function"]
                    print(f"  {i}. {func['name']}: {func['description']}")
                continue
            
            elif user_input.lower() == "/samples":
                print("\n📋 Sample Tasks:")
                sample_tasks = get_sample_tasks()
                for i, sample in enumerate(sample_tasks, 1):
                    print(f"  {i}. {sample['name']}")
                    # Show first 100 chars of task for readability
                    task_preview = sample['task'].replace('\n', ' ')[:100]
                    if len(sample['task']) > 100:
                        task_preview += "..."
                    print(f"     {task_preview}")
                print("\n💡 Tip: Use /sample <n> to run a specific sample (e.g., /sample 1)")
                continue
            
            elif user_input.lower().startswith("/sample "):
                # Extract the sample number
                try:
                    sample_num = int(user_input.split()[1])
                    sample_tasks = get_sample_tasks()
                    
                    if 1 <= sample_num <= len(sample_tasks):
                        selected_sample = sample_tasks[sample_num - 1]
                        print(f"\n🎯 Running Sample: {selected_sample['name']}")
                        print("-"*60)
                        print(f"Task: {selected_sample['task']}")
                        print("-"*60)
                        
                        # Process the sample task as regular input
                        user_input = selected_sample['task']
                        # Don't continue - let it fall through to normal processing
                    else:
                        print(f"❌ Invalid sample number. Please choose between 1 and {len(sample_tasks)}")
                        print("Use /samples to see available samples")
                        continue
                except (ValueError, IndexError):
                    print("❌ Invalid format. Use: /sample <number> (e.g., /sample 1)")
                    continue
            
            elif user_input.lower() == "/help":
                print("\n💡 Commands:")
                print("  /reset      - Reset conversation")
                print("  /tools      - Show available tools")
                print("  /samples    - Show sample tasks")
                print("  /sample <n> - Run sample task number n")
                print("  /stream     - Toggle streaming mode")
                print("  /help       - Show this help")
                print("  /exit       - Exit the program")
                continue
            
            elif user_input.lower() == "/stream":
                streaming_enabled = not streaming_enabled
                print(f"✅ Streaming {'enabled' if streaming_enabled else 'disabled'}")
                continue
            
            # Process user input
            if streaming_enabled:
                print("\n⏳ Processing (streaming)...\n")
                
                response_chunks = []
                thinking_shown = False
                tools_shown = False
                response_started = False
                last_chunk_type = None
                
                for chunk in agent.chat(user_input, stream=True):
                    chunk_type = chunk.get("type")
                    content = chunk.get("content", "")
                    
                    if chunk_type == "thinking":
                        if not thinking_shown:
                            print("🧠 Thinking: ", end="", flush=True)
                            thinking_shown = True
                        # Stream thinking character by character in gray
                        print(f"\033[90m{content}\033[0m", end="", flush=True)
                    
                    elif chunk_type == "tool_call":
                        if not tools_shown:
                            print("\n🔧 Tool Calls:")
                            tools_shown = True
                        tool_info = content
                        print(f"  → {tool_info.get('name', 'unknown')}: {tool_info.get('arguments', {})}")
                        # Reset response_started flag after tool calls so the next content gets a label
                        response_started = False
                    
                    elif chunk_type == "tool_result":
                        result_str = str(content)
                        print(f"    ✓ {result_str}")
                        # Reset response_started flag after tool results
                        response_started = False
                    
                    elif chunk_type == "content":
                        # If we're starting a new content section after tool results
                        if not response_started:
                            if last_chunk_type in ["tool_result", "tool_call"]:
                                # This is a response after tool execution
                                print("\n🤖 Assistant: ", end="", flush=True)
                            elif thinking_shown or tools_shown:
                                print("\n🤖 Assistant: ", end="", flush=True)
                            else:
                                print("🤖 Assistant: ", end="", flush=True)
                            response_started = True
                        print(content, end="", flush=True)
                        response_chunks.append(content)
                    
                    elif chunk_type == "error":
                        print(f"\n❌ Error: {content}")
                    
                    last_chunk_type = chunk_type
                
                print()  # New line after streaming
            else:
                print("\n⏳ Processing...")
                response = agent.chat(user_input, stream=False)
                
                print(f"🤖 Assistant: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.exception("Error in interactive mode")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Universal Tool Calling Agent - Works on all platforms"
    )
    parser.add_argument(
        "--mode",
        choices=["single", "interactive"],
        default="interactive",
        help="Execution mode (default: interactive)"
    )
    parser.add_argument(
        "--task",
        type=str,
        help="Task to execute (for single mode)"
    )
    parser.add_argument(
        "--backend",
        choices=["vllm", "ollama", "auto"],
        default="auto",
        help="Backend to use (default: auto-detect)"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show system information and exit"
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        default=True,
        help="Enable streaming mode (default: True)"
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming mode"
    )
    
    args = parser.parse_args()
    
    # Header
    print("="*60)
    print("🚀 Universal Tool Calling Agent")
    print("="*60)
    
    # Show system info if requested
    if args.info:
        print("\n📊 System Information:")
        print(f"  Platform: {platform.system()} {platform.release()}")
        print(f"  Architecture: {platform.machine()}")
        print(f"  Python: {sys.version.split()[0]}")
        
        # Check CUDA
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                print(f"  CUDA: ✅ Available (GPU: {torch.cuda.get_device_name(0)})")
            else:
                print("  CUDA: ❌ Not available")
        except ImportError:
            print("  CUDA: ❌ PyTorch not installed")
        
        # Check Ollama
        try:
            import ollama
            print("  Ollama: ✅ Package installed")
        except ImportError:
            print("  Ollama: ❌ Package not installed")
        
        return 0
    
    # Initialize agent
    print("\n⚙️  Initializing agent...")
    
    backend = None if args.backend == "auto" else args.backend
    
    try:
        agent = ToolCallingAgent(backend=backend)
    except SystemExit:
        return 1
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return 1
    
    print(f"✅ Agent ready! Using {agent.backend_type} backend")
    
    # Execute based on mode
    if args.mode == "single":
        if not args.task:
            # Show sample tasks for selection
            print("\n" + "="*60)
            print("SINGLE TASK MODE - No task provided")
            print("="*60)
            
            sample_tasks = get_sample_tasks()
            print("\n📋 Available sample tasks:")
            for i, sample in enumerate(sample_tasks, 1):
                print(f"\n{i}. {sample['name']}")
                print(f"   {sample['description']}")
            
            print("\n" + "="*60)
            try:
                choice = input(f"\nSelect a task number (1-{len(sample_tasks)}) or 'q' to quit: ").strip()
                if choice.lower() == 'q':
                    return 0
                
                task_num = int(choice)
                if 1 <= task_num <= len(sample_tasks):
                    selected_task = sample_tasks[task_num - 1]
                    print(f"\n✅ Selected: {selected_task['name']}")
                    print("\nTask details:")
                    print("-"*40)
                    print(selected_task['task'])
                    print("-"*40)
                    
                    confirm = input("\nRun this task? (y/n): ").strip().lower()
                    if confirm == 'y':
                        stream_enabled = not args.no_stream if hasattr(args, 'no_stream') else True
                        run_single_task(agent, selected_task['task'], stream=stream_enabled)
                    else:
                        print("Task cancelled.")
                else:
                    print(f"Invalid selection. Please choose 1-{len(sample_tasks)}")
                    return 1
            except (ValueError, KeyboardInterrupt):
                print("\nExiting...")
                return 0
        else:
            stream_enabled = not args.no_stream if hasattr(args, 'no_stream') else True
            run_single_task(agent, args.task, stream=stream_enabled)
    
    else:  # interactive mode
        stream_enabled = not args.no_stream if hasattr(args, 'no_stream') else True
        interactive_mode(agent, stream=stream_enabled)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())