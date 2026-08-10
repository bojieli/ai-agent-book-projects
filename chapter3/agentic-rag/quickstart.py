#!/usr/bin/env python3
"""Quick start script for Agentic RAG system"""

import os
import sys
import json
from pathlib import Path


def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment...")
    
    # Check for .env file
    if not Path(".env").exists() and Path(".env.example").exists():
        print("📝 Creating .env from .env.example")
        import shutil
        shutil.copy(".env.example", ".env")
        print("⚠️  Please edit .env and add your API keys")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for at least one API key
    providers = ["MOONSHOT_API_KEY", "ARK_API_KEY", "DASHSCOPE_API_KEY", "SILICONFLOW_API_KEY",
                 "OPENAI_API_KEY", "OPENROUTER_API_KEY"]
    
    has_key = False
    for provider in providers:
        if os.getenv(provider):
            has_key = True
            print(f"✅ Found {provider}")
            break
    
    if not has_key:
        print("❌ No API keys found. Please set at least one in .env file:")
        print("   - MOONSHOT_API_KEY for Kimi")
        print("   - ARK_API_KEY for Doubao")
        print("   - SILICONFLOW_API_KEY for SiliconFlow")
        print("   - OPENAI_API_KEY for OpenAI")
        return False
    
    return True


def setup_demo_documents():
    """Create demo documents if they don't exist"""
    print("\n📚 Setting up demo documents...")
    
    eval_dir = Path("evaluation")
    eval_dir.mkdir(exist_ok=True)
    
    # Check if documents already exist
    doc_file = eval_dir / "legal_documents.json"
    dataset_file = eval_dir / "legal_qa_dataset.json"
    
    if not doc_file.exists() or not dataset_file.exists():
        print("📄 Generating legal documents and dataset...")
        os.chdir("evaluation")
        os.system("python dataset_builder.py")
        os.chdir("..")
        print("✅ Documents generated")
    else:
        print("✅ Documents already exist")
    
    return doc_file, dataset_file


def check_retrieval_pipeline():
    """Check if local retrieval pipeline is running"""
    print("\n🔌 Checking retrieval pipeline...")
    
    kb_type = os.getenv("KB_TYPE", "local")
    
    if kb_type == "local":
        import requests
        try:
            response = requests.get("http://localhost:4242/health", timeout=2)
            if response.status_code == 200:
                print("✅ Local retrieval pipeline is running")
                return True
        except Exception:
            pass
        
        print("⚠️  Local retrieval pipeline is not running")
        print("    Please run in another terminal:")
        print("    cd ../retrieval-pipeline && python main.py")
        print("\n    Or use Dify by setting KB_TYPE=dify in .env")
        return False
    else:
        print(f"✅ Using {kb_type} knowledge base")
        return True


def index_documents(doc_file):
    """Index documents into knowledge base"""
    print("\n📝 Indexing documents...")
    
    # Check if already indexed
    store_file = Path("document_store.json")
    if store_file.exists():
        with open(store_file, 'r', encoding='utf-8') as f:
            store = json.load(f)
            if len(store) > 0:
                print(f"✅ Found {len(store)} documents already indexed")
                return True
    
    print("🔄 Indexing legal documents...")
    result = os.system(f"python chunking.py {doc_file}")
    
    if result == 0:
        print("✅ Documents indexed successfully")
        return True
    else:
        print("❌ Failed to index documents")
        return False


def run_demo():
    """Run interactive demo"""
    print("\n" + "="*60)
    print("🚀 Starting Agentic RAG Demo")
    print("="*60)
    
    print("\nDemo queries you can try:")
    print("1. 故意杀人罪判几年？")
    print("2. 盗窃罪的立案标准是什么？")
    print("3. 醉酒驾驶如何处罚？")
    print("4. 张某持刀入室抢劫并造成他人重伤，应如何定罪量刑？")
    
    print("\nCommands:")
    print("- 'mode' to switch between agentic/non-agentic")
    print("- 'clear' to clear conversation history")
    print("- 'quit' to exit")
    
    print("\nStarting in interactive mode...")
    print("-"*60)
    
    os.system("python main.py")


def run_comparison_demo():
    """Run comparison between agentic and non-agentic modes"""
    print("\n" + "="*60)
    print("🔄 Running Comparison Demo")
    print("="*60)
    
    queries = [
        "故意杀人罪判几年？",
        "张某因经济纠纷持刀闯入李某家中，刺伤李某致重伤并拿走5万元现金，应如何定罪？"
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        os.system(f'python main.py --mode compare --query "{query}"')
        input("\nPress Enter to continue...")


def main():
    """Main quickstart function"""
    print("🎯 Agentic RAG System - Quick Start")
    print("="*60)
    
    # Check environment
    if not check_environment():
        print("\n❌ Please configure your environment first")
        sys.exit(1)
    
    # Setup demo documents
    doc_file, dataset_file = setup_demo_documents()
    
    # Check retrieval pipeline
    if not check_retrieval_pipeline():
        print("\n⚠️  Warning: Retrieval pipeline not available")
        print("    The system may not work properly")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Index documents
    if not index_documents(doc_file):
        print("\n❌ Failed to index documents")
        sys.exit(1)
    
    # Menu
    print("\n" + "="*60)
    print("📋 Select an option:")
    print("="*60)
    print("1. Interactive Demo (chat with the system)")
    print("2. Comparison Demo (see agentic vs non-agentic)")
    print("3. Run Full Evaluation")
    print("4. Exit")
    
    choice = input("\nYour choice (1-4): ")
    
    if choice == "1":
        run_demo()
    elif choice == "2":
        run_comparison_demo()
    elif choice == "3":
        print("\n📊 Running full evaluation...")
        os.chdir("evaluation")
        os.system("python evaluate.py")
        os.chdir("..")
    elif choice == "4":
        print("\n👋 Goodbye!")
    else:
        print("\n❌ Invalid choice")


if __name__ == "__main__":
    # Install dependencies if needed
    try:
        import openai
        import requests
        from dotenv import load_dotenv
    except ImportError:
        print("📦 Installing required packages...")
        os.system("pip install -r requirements.txt")
        print("✅ Packages installed")
    
    main()
