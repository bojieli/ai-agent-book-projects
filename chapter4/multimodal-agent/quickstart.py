"""
Quickstart script for testing multimodal agent
Creates sample files and demonstrates capabilities
"""

import asyncio
import base64
from pathlib import Path
import os

from agent import MultimodalAgent, MultimodalContent
from config import ExtractionMode, Config


def create_sample_files():
    """Create sample files for testing"""
    
    # Create test_files directory
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # Create a simple text-based "image" (SVG)
    svg_content = """<?xml version="1.0" encoding="UTF-8"?>
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect x="10" y="10" width="180" height="180" fill="lightblue" stroke="black" stroke-width="2"/>
        <circle cx="100" cy="100" r="50" fill="yellow" stroke="orange" stroke-width="3"/>
        <text x="100" y="105" text-anchor="middle" font-size="20" fill="black">Hello AI!</text>
    </svg>
    """
    
    svg_path = test_dir / "sample.svg"
    svg_path.write_text(svg_content)
    print(f"Created: {svg_path}")
    
    # Create a simple text file that we'll treat as a "document"
    doc_content = """
    # Sample Document for Multimodal Agent Testing
    
    ## Introduction
    This is a test document created for demonstrating the multimodal agent's capabilities.
    The agent can process this document in different modes:
    
    1. **Native Mode**: Direct processing using the model's built-in capabilities
    2. **Extract to Text**: Convert to text first, then analyze
    3. **With Tools**: Use specialized tools for detailed analysis
    
    ## Key Features
    - Support for multiple file formats (PDF, images, audio)
    - Multiple AI model providers (Gemini, OpenAI, Doubao)
    - Streaming responses for better user experience
    - Tool calling for advanced analysis
    
    ## Technical Details
    The system uses a unified message format compatible with OpenAI's API structure,
    making it easy to switch between different providers while maintaining consistency.
    
    ## Conclusion
    This multimodal agent demonstrates state-of-the-art AI capabilities for
    content understanding and analysis across different modalities.
    """
    
    doc_path = test_dir / "sample_document.txt"
    doc_path.write_text(doc_content)
    print(f"Created: {doc_path}")
    
    return test_dir


async def test_basic_functionality():
    """Test basic agent functionality"""
    
    print("\n" + "="*60)
    print("QUICKSTART: Testing Multimodal Agent")
    print("="*60)
    
    # Check API keys
    config = Config()
    api_keys = config.validate_api_keys()
    
    print("\n1. API Key Status:")
    print("-" * 40)
    for provider, has_key in api_keys.items():
        status = "✅ Configured" if has_key else "❌ Not configured"
        print(f"   {provider.capitalize()}: {status}")
    
    if not any(api_keys.values()):
        print("\n⚠️  Warning: No API keys configured!")
        print("Please copy env.example to .env and add your API keys.")
        return
    
    # Create sample files
    print("\n2. Creating Sample Files:")
    print("-" * 40)
    test_dir = create_sample_files()
    
    # Test with available model
    if api_keys["gemini"]:
        model = "gemini-3.5-flash"
        print(f"\n3. Testing with {model}:")
        print("-" * 40)
        
        agent = MultimodalAgent(
            model=model,
            mode=ExtractionMode.EXTRACT_TO_TEXT,
            enable_tools=False
        )
        
        # Process the text document
        doc_path = test_dir / "sample_document.txt"
        content = MultimodalContent(
            type="text",
            path=str(doc_path),
            data=doc_path.read_bytes()
        )
        
        print("Processing sample document...")
        try:
            # Simulate as if it's a PDF for demonstration
            content.type = "pdf"
            result = await agent._extract_pdf_to_text(content)
            print("Extracted content preview:")
            print(result[:300] + "..." if len(result) > 300 else result)
            
            # Answer a question
            print("\nAsking a question about the document...")
            answer = await agent._answer_with_context(
                result,
                "What are the three modes mentioned in the document?"
            )
            print("Answer:", answer)
            
        except Exception as e:
            print(f"Error: {e}")
    
    elif api_keys["openai"]:
        model = "gpt-5.6-luna"
        print(f"\n3. Testing with {model}:")
        print("-" * 40)
        
        agent = MultimodalAgent(
            model=model,
            mode=ExtractionMode.EXTRACT_TO_TEXT,
            enable_tools=False
        )
        
        print("Note: OpenAI models work best with images.")
        print("For document processing, Gemini is recommended.")
        
    else:
        print("\n3. Skipping tests - no API keys configured")


async def test_conversation_mode():
    """Test conversation mode with streaming"""
    
    config = Config()
    if not config.gemini_api_key and not config.openai_api_key:
        print("\nSkipping conversation test - no API keys configured")
        return
        
    print("\n" + "="*60)
    print("4. Testing Conversation Mode")
    print("="*60)
    
    # Use available model
    if config.gemini_api_key:
        model = "gemini-3.5-flash"
    else:
        model = "gpt-5.6-luna"
        
    agent = MultimodalAgent(
        model=model,
        mode=ExtractionMode.EXTRACT_TO_TEXT,
        enable_tools=True
    )
    
    print(f"Using model: {model}")
    print("Tools: Enabled")
    print("\nStarting conversation...")
    print("-" * 40)
    
    # Simulate a conversation
    messages = [
        "Hello! I'm testing the multimodal agent. Can you explain what you can do?",
        "What types of files can you process?",
        "How do the different extraction modes work?"
    ]
    
    for message in messages:
        print(f"\nUser: {message}")
        print("Assistant: ", end="", flush=True)
        
        try:
            response_text = ""
            async for chunk in agent.chat(message, stream=True):
                print(chunk, end="", flush=True)
                response_text += chunk
            print()
            
            # Small delay for readability
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"\nError: {e}")
            break


async def main():
    """Run all quickstart tests"""
    
    print("🚀 Multimodal Agent Quickstart")
    print("=" * 60)
    
    # Run basic tests
    await test_basic_functionality()
    
    # Run conversation test
    await test_conversation_mode()
    
    print("\n" + "="*60)
    print("✅ Quickstart Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Add your API keys to .env file")
    print("2. Try with your own files: python main.py --file <path> --query <question>")
    print("3. Start interactive mode: python main.py --interactive")
    print("4. Run comparisons: python demo.py <file> <query>")


if __name__ == "__main__":
    asyncio.run(main())
