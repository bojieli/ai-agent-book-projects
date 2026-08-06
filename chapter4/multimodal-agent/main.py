"""
Main entry point for Multimodal Agent
Demonstrates different extraction modes and model capabilities
"""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import Optional

from agent import MultimodalAgent, MultimodalContent
from config import ExtractionMode, Config


class _Tee:
    """将 stdout 同时写入终端与文件，用于 --output。"""

    def __init__(self, stream, file_handle):
        self._stream = stream
        self._file = file_handle

    def write(self, data):
        self._stream.write(data)
        self._file.write(data)

    def flush(self):
        self._stream.flush()
        self._file.flush()


async def process_file(
    agent: MultimodalAgent,
    file_path: str,
    query: Optional[str] = None
) -> None:
    """Process a single file with the agent"""
    
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File '{file_path}' not found")
        return
        
    # Determine content type
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        content_type = "pdf"
    elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        content_type = "image"
    elif suffix in ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg']:
        content_type = "audio"
    else:
        print(f"Error: Unsupported file type '{suffix}'")
        return
        
    # Create multimodal content
    content = MultimodalContent(
        type=content_type,
        path=file_path
    )
    
    print(f"\n{'='*60}")
    print(f"Processing {content_type.upper()}: {path.name}")
    print(f"Mode: {agent.extraction_mode.value}")
    print(f"Model: {agent.current_model}")
    print(f"Multimodal Tools: {'Enabled' if agent.enable_multimodal_tools else 'Disabled'}")
    print(f"{'='*60}\n")
    
    try:
        # Process content
        if agent.extraction_mode == ExtractionMode.NATIVE:
            # Use native multimodal processing
            result = await agent.process_multimodal_content(content, query)
            print("Native Processing Result:")
            print("-" * 40)
            print(result)
        else:
            # Extract to text mode
            print("Extracting content to text...")
            extracted = await agent._extract_single_content(content)
            print("Extracted Text:")
            print("-" * 40)
            print(extracted[:1000] + "..." if len(extracted) > 1000 else extracted)
            
            if query:
                print(f"\nAnswering query: {query}")
                print("-" * 40)
                answer = await agent._answer_with_context(extracted, query)
                print(answer)
                
    except Exception as e:
        print(f"Error processing file: {e}")


async def interactive_chat(agent: MultimodalAgent) -> None:
    """Interactive chat session with the agent"""
    
    print("\n" + "="*60)
    print("Interactive Multimodal Chat")
    print(f"Model: {agent.current_model}")
    print(f"Mode: {agent.extraction_mode.value}")
    print(f"Multimodal Tools: {'Enabled' if agent.enable_multimodal_tools else 'Disabled'}")
    print("="*60)
    print("\nCommands:")
    print("  /file <path> - Load a multimodal file")
    print("  /mode <native|extract_to_text> - Switch extraction mode")
    print("  /model <model_name> - Switch model")
    print("  /tools <on|off> - Enable/disable multimodal tools")
    print("  /history - Show conversation history")
    print("  /clear - Clear conversation history")
    print("  /quit - Exit")
    print("\n")
    
    current_content = None
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
                
            # Handle commands
            if user_input.startswith("/"):
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command == "/quit":
                    print("Goodbye!")
                    break
                    
                elif command == "/file":
                    if not args:
                        print("Usage: /file <path>")
                        continue
                        
                    path = Path(args)
                    if not path.exists():
                        print(f"File not found: {args}")
                        continue
                        
                    # Determine content type
                    suffix = path.suffix.lower()
                    if suffix == '.pdf':
                        content_type = "pdf"
                    elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                        content_type = "image"
                    elif suffix in ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg']:
                        content_type = "audio"
                    else:
                        print(f"Unsupported file type: {suffix}")
                        continue
                        
                    current_content = MultimodalContent(
                        type=content_type,
                        path=args
                    )
                    
                    # Extract content immediately if in extract mode
                    result = await agent.load_and_extract_content(current_content)
                    print(result)
                    
                    # In extract mode, content is already extracted, no need to keep it
                    if agent.extraction_mode == ExtractionMode.EXTRACT_TO_TEXT:
                        current_content = None
                    
                elif command == "/mode":
                    if args == "native":
                        agent.extraction_mode = ExtractionMode.NATIVE
                        print("Switched to native multimodal mode")
                    elif args == "extract_to_text":
                        agent.extraction_mode = ExtractionMode.EXTRACT_TO_TEXT
                        print("Switched to extract-to-text mode")
                    else:
                        print("Usage: /mode <native|extract_to_text>")
                        
                elif command == "/model":
                    if args in agent.config.models:
                        agent.current_model = args
                        print(f"Switched to model: {args}")
                    else:
                        print(f"Available models: {', '.join(agent.config.models.keys())}")
                        
                elif command == "/tools":
                    if args == "on":
                        agent.set_multimodal_tools_enabled(True)
                        print("Multimodal tools enabled")
                    elif args == "off":
                        agent.set_multimodal_tools_enabled(False)
                        print("Multimodal tools disabled")
                    else:
                        print("Usage: /tools <on|off>")
                        
                elif command == "/history":
                    history = agent.get_conversation_history()
                    print("\nConversation History:")
                    print("-" * 40)
                    for msg in history:
                        role = msg["role"].upper()
                        content = msg["content"]
                        if isinstance(content, str):
                            preview = content[:200] + "..." if len(content) > 200 else content
                            print(f"{role}: {preview}")
                    print("-" * 40)
                    
                elif command == "/clear":
                    agent.reset_conversation()
                    current_content = None
                    print("Conversation history cleared")
                    
                else:
                    print(f"Unknown command: {command}")
                    
                continue
                
            # Regular chat message
            print("\nAssistant: ", end="", flush=True)
            
            try:
                async for chunk in agent.chat(user_input, current_content, stream=True):
                    print(chunk, end="", flush=True)
                print("\n")
                
                # Clear current content after first use
                current_content = None
                
            except Exception as e:
                print(f"\nError: {e}")
                
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type /quit to exit.")
            continue
        except Exception as e:
            print(f"Error: {e}")
            continue


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="多模态 Agent：对比原生多模态、提取为文本、带工具三种信息提取范式。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  # 处理图像并提问\n"
            "  python main.py --file test_files/sample_chart.png --query \"图中哪个季度营收最高？\"\n"
            "  # 处理 PDF 文档（提取为文本模式）\n"
            "  python main.py --mode extract_to_text --file report.pdf --query \"总结要点\"\n"
            "  # 进入交互式对话\n"
            "  python main.py --interactive"
        ),
    )
    parser.add_argument("--mode", choices=["native", "extract_to_text"], default="native",
                       help="提取模式：native（原生多模态）或 extract_to_text（提取为文本），默认 native")
    parser.add_argument("--model", default="gemini-3.5-flash",
                       help="使用的模型（默认：gemini-3.5-flash）")
    parser.add_argument("--tools", action="store_true",
                       help="启用多模态分析工具（analyze_image / analyze_audio / analyze_pdf）")
    parser.add_argument("--file", help="要处理的单个文件（图像 / PDF 文档 / 音频）")
    parser.add_argument("--query", help="向该文件提出的问题")
    parser.add_argument("--output", "-o", help="将处理结果同时写入指定文件")
    parser.add_argument("--interactive", action="store_true",
                       help="进入交互式对话会话")

    args = parser.parse_args()
    
    # Validate API keys
    config = Config()
    api_keys = config.validate_api_keys()
    
    print("API Key Status:")
    for provider, has_key in api_keys.items():
        status = "✓ Configured" if has_key else "✗ Not configured"
        print(f"  {provider.capitalize()}: {status}")
    
    # Create agent
    mode = ExtractionMode.NATIVE if args.mode == "native" else ExtractionMode.EXTRACT_TO_TEXT
    agent = MultimodalAgent(
        model=args.model,
        mode=mode,
        enable_tools=args.tools
    )
    
    # Process based on arguments
    if args.file:
        if args.output:
            # 将结果同时写入文件
            with open(args.output, "w", encoding="utf-8") as fh:
                original_stdout = sys.stdout
                sys.stdout = _Tee(original_stdout, fh)
                try:
                    await process_file(agent, args.file, args.query)
                finally:
                    sys.stdout = original_stdout
            print(f"\n处理结果已写入：{args.output}")
        else:
            await process_file(agent, args.file, args.query)
    elif args.interactive:
        await interactive_chat(agent)
    else:
        # Default to interactive mode
        await interactive_chat(agent)


if __name__ == "__main__":
    asyncio.run(main())
