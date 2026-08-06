"""
Demo script showcasing different extraction techniques
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from agent import MultimodalAgent, MultimodalContent
from config import ExtractionMode


class _Tee:
    """Duplicate stdout writes to a file so --output can save the transcript."""

    def __init__(self, stream, file_handle):
        self._stream = stream
        self._file = file_handle

    def write(self, data):
        self._stream.write(data)
        self._file.write(data)

    def flush(self):
        self._stream.flush()
        self._file.flush()


async def compare_extraction_modes(file_path: str, query: str, model: str = "gemini-3.5-flash"):
    """Compare different extraction modes for the same content"""
    
    print(f"\n{'='*80}")
    print(f"COMPARING EXTRACTION MODES")
    print(f"File: {file_path}")
    print(f"Query: {query}")
    print(f"{'='*80}\n")
    
    # Determine content type
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix == '.pdf':
        content_type = "pdf"
    elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        content_type = "image"
    elif suffix in ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg']:
        content_type = "audio"
    else:
        print(f"Unsupported file type: {suffix}")
        return
    
    # Test with native mode (Gemini)
    print("\n" + "-"*60)
    print(f"1. NATIVE MULTIMODAL MODE ({model})")
    print("-"*60)

    agent_native = MultimodalAgent(
        model=model,
        mode=ExtractionMode.NATIVE,
        enable_tools=False
    )
    
    content = MultimodalContent(type=content_type, path=file_path)
    
    try:
        result = await agent_native.process_multimodal_content(content, query)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with extract-to-text mode
    print("\n" + "-"*60)
    print("2. EXTRACT TO TEXT MODE")
    print("-"*60)
    
    agent_extract = MultimodalAgent(
        model=model,
        mode=ExtractionMode.EXTRACT_TO_TEXT,
        enable_tools=False
    )
    
    try:
        # First extract the content
        print("Extracting content to text...")
        extracted = await agent_extract._extract_single_content(content)
        print("\nExtracted text:")
        print(extracted)
        
        # Then answer the query
        print(f"\nAnswering query with extracted text...")
        result = await agent_extract._answer_with_context(extracted, query)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with extract-to-text + tools mode
    print("\n" + "-"*60)
    print("3. EXTRACT TO TEXT + MULTIMODAL TOOLS")
    print("-"*60)
    
    agent_tools = MultimodalAgent(
        model=model,
        mode=ExtractionMode.EXTRACT_TO_TEXT,
        enable_tools=True
    )
    
    try:
        print("Using extract-to-text with tools enabled for follow-up questions...")
        
        # Initial processing
        extracted = await agent_tools._extract_single_content(content)
        print(f"Extracted {len(extracted)} characters")
        
        # Simulate a conversation with follow-up
        async for chunk in agent_tools.chat(query, content, stream=True):
            print(chunk, end="", flush=True)
        print()
        
        # Follow-up question that might use tools
        if content_type == "image":
            follow_up = f"What colors are dominant in the image at {file_path}?"
        elif content_type == "pdf":
            follow_up = f"What specific data or figures are mentioned in the PDF at {file_path}?"
        else:  # audio
            follow_up = f"What is the tone or mood of the audio at {file_path}?"
            
        print(f"\nFollow-up question: {follow_up}")
        async for chunk in agent_tools.chat(follow_up, None, stream=True):
            print(chunk, end="", flush=True)
        print()
        
    except Exception as e:
        print(f"Error: {e}")


async def compare_models(file_path: str, query: str):
    """Compare different models for the same task"""
    
    print(f"\n{'='*80}")
    print(f"COMPARING MODELS")
    print(f"File: {file_path}")
    print(f"Query: {query}")
    print(f"{'='*80}\n")
    
    # Determine content type
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix == '.pdf':
        content_type = "pdf"
    elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        content_type = "image"
    elif suffix in ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg']:
        content_type = "audio"
    else:
        print(f"Unsupported file type: {suffix}")
        return
        
    content = MultimodalContent(type=content_type, path=file_path)
    
    # Test with different models
    models = ["gemini-3.5-flash", "gpt-5.6-luna", "doubao-1.6"]
    
    for model in models:
        print("\n" + "-"*60)
        print(f"Model: {model}")
        print("-"*60)
        
        try:
            # Skip if API key not configured
            from config import Config
            config = Config()
            
            if model == "gemini-3.5-flash" and not config.gemini_api_key:
                print("Skipping: Gemini API key not configured")
                continue
            elif model in ["gpt-5.6-luna", "gpt-5"] and not (config.openai_api_key or config.openrouter_api_key):
                print("Skipping: OpenAI API key not configured")
                continue
            elif model == "doubao-1.6" and not config.doubao_api_key:
                print("Skipping: Doubao API key not configured")
                continue
            
            agent = MultimodalAgent(
                model=model,
                mode=ExtractionMode.NATIVE if content_type != "audio" or model == "gemini-3.5-flash" else ExtractionMode.EXTRACT_TO_TEXT,
                enable_tools=False
            )
            
            result = await agent.process_multimodal_content(content, query)
            print(result)
            
        except Exception as e:
            print(f"Error: {e}")


async def demo_conversation_with_tools():
    """Demonstrate a conversation with multimodal tools"""
    
    print(f"\n{'='*80}")
    print("DEMO: CONVERSATION WITH MULTIMODAL TOOLS")
    print(f"{'='*80}\n")
    
    agent = MultimodalAgent(
        model="gemini-3.5-flash",
        mode=ExtractionMode.EXTRACT_TO_TEXT,
        enable_tools=True
    )
    
    # Simulate a conversation
    conversations = [
        ("I need help analyzing some documents. I have PDFs, images, and audio files.", None),
        ("Can you analyze the image at test_files/sample.jpg and tell me what you see?", None),
        ("Now analyze the PDF at test_files/document.pdf and summarize its main points.", None),
        ("What's in the audio file at test_files/recording.mp3?", None),
        ("Based on all these files, what's the common theme?", None)
    ]
    
    for message, content in conversations:
        print(f"\nUser: {message}")
        print("Assistant: ", end="", flush=True)
        
        try:
            async for chunk in agent.chat(message, content, stream=True):
                print(chunk, end="", flush=True)
            print()
        except Exception as e:
            print(f"\nError: {e}")
            print("(File might not exist - this is a demo)")


def build_parser() -> argparse.ArgumentParser:
    """构建实验 4-2 的命令行接口。"""
    parser = argparse.ArgumentParser(
        description=(
            "实验 4-2：多模态信息提取的三种技术范式对比（原生多模态 / 提取为文本 / 带工具）。\n"
            "将同一多模态文件和同一问题分别交给三种模式处理，观察表现差异。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  # 先离线生成含图表的样例（无需 API Key）\n"
            "  python demo.py --generate-sample\n"
            "  # 用生成的图表跑三种范式对比（需要 API Key）\n"
            "  python demo.py --file test_files/sample_chart.png \\\n"
            '      --query \"Which quarter had the highest revenue, and what was the exact value?\"\n'
            "  # 兼容旧写法（位置参数）\n"
            "  python demo.py document.pdf \"总结这份文档的要点\""
        ),
    )
    parser.add_argument(
        "file", nargs="?", default=None,
        help="要处理的多模态文件（图像 / PDF 文档 / 音频）。也可用 --file 指定",
    )
    parser.add_argument(
        "query", nargs="?", default=None,
        help="向该文件提出的问题。也可用 --query 指定",
    )
    parser.add_argument(
        "--file", dest="file_opt", default=None,
        help="要处理的多模态文件（等价于位置参数 file）",
    )
    parser.add_argument(
        "--query", dest="query_opt", default=None,
        help="向该文件提出的问题（等价于位置参数 query）",
    )
    parser.add_argument(
        "--model", default="gemini-3.5-flash",
        help="原生 / 提取模式使用的模型（默认：gemini-3.5-flash）",
    )
    parser.add_argument(
        "--skip-model-comparison", action="store_true",
        help="只跑三种范式对比，跳过跨模型对比",
    )
    parser.add_argument(
        "--generate-sample", action="store_true",
        help="离线生成含图表的样例文件到 test_files/ 后退出（无需 API Key）",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="将完整对比结果同时写入指定文件（如 result.txt）",
    )
    return parser


async def run_comparison(file_path: str, query: str, model: str, skip_model_comparison: bool):
    """运行三种范式对比，可选跨模型对比。"""
    print("="*80)
    print("MULTIMODAL AGENT DEMO")
    print("="*80)

    await compare_extraction_modes(file_path, query, model=model)
    if not skip_model_comparison:
        await compare_models(file_path, query)


async def main():
    """实验入口：解析参数并运行对比。"""
    parser = build_parser()
    args = parser.parse_args()

    # 离线样例生成：不需要 API Key，直接产出图表 + PDF 报告
    if args.generate_sample:
        import create_sample
        sys.argv = ["create_sample.py"]  # 用默认输出目录 test_files/
        create_sample.main()
        return

    file_path = args.file_opt or args.file
    query = args.query_opt or args.query

    # 缺少文件或问题时，回退到无需真实文件的对话演示
    if not file_path or not query:
        print("="*80)
        print("MULTIMODAL AGENT DEMO")
        print("="*80)
        print("\n未提供 <file> 与 <query>，改为运行对话演示。")
        print("用法：python demo.py --file <文件> --query <问题>")
        print("先生成样例：python demo.py --generate-sample\n")
        await demo_conversation_with_tools()
        return

    # 支持 --output：把整段对比结果同时落盘
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            original_stdout = sys.stdout
            sys.stdout = _Tee(original_stdout, fh)
            try:
                await run_comparison(file_path, query, args.model, args.skip_model_comparison)
            finally:
                sys.stdout = original_stdout
        print(f"\n完整对比结果已写入：{args.output}")
    else:
        await run_comparison(file_path, query, args.model, args.skip_model_comparison)


if __name__ == "__main__":
    asyncio.run(main())
