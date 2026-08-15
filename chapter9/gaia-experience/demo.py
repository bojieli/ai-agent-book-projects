"""
Demo script for Experience Learning System
This script demonstrates all features of the experience learning system.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import yaml
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from experience_agent import ExperienceAgent
from knowledge_base import KnowledgeBase
from trajectory_summarizer import TrajectorySummarizer
from llm_env import resolve_llm, DEFAULT_MODEL
from AWorld.aworld.config.conf import AgentConfig, TaskConfig
from AWorld.aworld.core.task import Task

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExperienceLearningDemo:
    """Demo class for experience learning system."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize demo with configuration."""
        self.config = self.load_config(config_path)
        self.setup_environment()
        self.knowledge_base = None
        self.summarizer = None
        self.agent = None
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return {}
    
    def setup_environment(self):
        """Setup environment and directories."""
        load_dotenv()
        
        # Create necessary directories
        os.makedirs("./logs", exist_ok=True)
        os.makedirs("./kb_index", exist_ok=True)
        os.makedirs("./experiences", exist_ok=True)
        
    async def demo_knowledge_base_indexing(self):
        """Demonstrate knowledge base indexing."""
        print("\n" + "="*60)
        print("DEMO 1: Knowledge Base Indexing")
        print("="*60)
        
        # Initialize knowledge base
        kb_config = self.config.get('knowledge_base', {})
        self.knowledge_base = KnowledgeBase(
            index_path=kb_config.get('index', {}).get('path', './kb_index'),
            model_name=kb_config.get('index', {}).get('embedding_model', 'all-MiniLM-L6-v2')
        )
        
        # Check if validation file exists
        validation_file = self.config.get('dataset', {}).get('validation_file', 'gaia-validation.jsonl')
        
        if os.path.exists(validation_file):
            print(f"\n📚 Indexing GAIA validation data from {validation_file}...")
            self.knowledge_base.index_gaia_validation(validation_file)
            
            # Show statistics
            stats = self.knowledge_base.get_statistics()
            print(f"\n✅ Indexing complete!")
            print(f"   - Total documents: {stats['total_documents']}")
            print(f"   - Has embeddings: {stats['has_embeddings']}")
            print(f"   - Sources: {stats['sources']}")
            
            # Demo search
            test_query = "How to find information about scientific papers on arXiv?"
            print(f"\n🔍 Testing search with query: '{test_query}'")
            results = self.knowledge_base.search(test_query, top_k=3)
            
            print(f"\n📋 Found {len(results)} relevant experiences:")
            for i, result in enumerate(results, 1):
                print(f"\n   {i}. Question: {result.get('question', 'N/A')[:100]}...")
                print(f"      Approach: {result.get('approach', 'N/A')[:100]}...")
                if result.get('tools_used'):
                    print(f"      Tools: {', '.join(result['tools_used'][:3])}")
        else:
            print(f"\n⚠️  Validation file not found: {validation_file}")
            print("   Creating synthetic experiences for demo...")
            
            # Add synthetic experiences
            synthetic_experiences = [
                {
                    'question': "How to search for papers on arXiv?",
                    'approach': "Use web search to find arXiv, then use their search functionality",
                    'tools_used': ["web_browser", "search_engine"],
                    'answer': "Navigate to arxiv.org and use the search bar"
                },
                {
                    'question': "Calculate the distance between Earth and Moon",
                    'approach': "Search for astronomical data and perform calculations",
                    'tools_used': ["calculator", "web_search"],
                    'answer': "384,400 km average distance"
                }
            ]
            
            for exp in synthetic_experiences:
                self.knowledge_base.add_experience(exp['question'], exp)
            
            print(f"✅ Added {len(synthetic_experiences)} synthetic experiences")
    
    async def demo_trajectory_summarization(self):
        """Demonstrate trajectory summarization."""
        print("\n" + "="*60)
        print("DEMO 2: Trajectory Summarization")
        print("="*60)
        
        # Initialize summarizer（OpenAI 直连，缺 Key 时 OpenRouter 兜底）
        summarizer_model = self.config.get('learning', {}).get('summarizer', {}).get('model', DEFAULT_MODEL)
        llm_kwargs = resolve_llm(model_override=summarizer_model)
        agent_config = AgentConfig(**llm_kwargs)

        self.summarizer = TrajectorySummarizer(
            llm_config=agent_config,
            model_name=llm_kwargs["llm_model_name"]
        )
        
        # Create sample trajectory
        sample_trajectory = [
            {
                'action': {
                    'tool_name': 'web_search',
                    'params': {'query': 'arxiv.org AI regulation 2022'}
                }
            },
            {
                'action': {
                    'tool_name': 'browser_navigate',
                    'params': {'url': 'https://arxiv.org/search'}
                }
            },
            {
                'action': {
                    'tool_name': 'browser_click',
                    'params': {'element': 'advanced_search'}
                }
            },
            {
                'action': {
                    'tool_name': 'browser_fill',
                    'params': {'field': 'date_range', 'value': '2022-06-01 to 2022-07-01'}
                }
            }
        ]
        
        # Create mock response
        class MockResponse:
            def __init__(self):
                self.answer = "The paper shows a figure with three axes labeled: deontological, egalitarian, utilitarian"
        
        print("\n📝 Summarizing sample trajectory...")
        print(f"   Trajectory has {len(sample_trajectory)} steps")
        
        summary = await self.summarizer.summarize(
            question="Find AI regulation paper from June 2022 on arXiv",
            response=MockResponse(),
            trajectory=sample_trajectory
        )
        
        print("\n✅ Summary generated:")
        print(f"   - Summary: {summary.get('summary', 'N/A')}")
        print(f"   - Approach: {summary.get('approach', 'N/A')}")
        print(f"   - Tools used: {', '.join(summary.get('tools_used', []))}")
        
        if summary.get('key_insights'):
            print(f"   - Key insights:")
            for insight in summary['key_insights']:
                print(f"      • {insight}")
    
    async def demo_experience_agent(self):
        """Demonstrate the experience agent."""
        print("\n" + "="*60)
        print("DEMO 3: Experience Agent")
        print("="*60)
        
        # Initialize agent with all features（OpenAI 直连，缺 Key 时 OpenRouter 兜底）
        agent_config = AgentConfig(
            **resolve_llm(),
            llm_temperature=0.0
        )
        
        # Basic system prompt
        system_prompt = """You are an intelligent agent capable of learning from experience.
        When solving problems, you can leverage past experiences to find better solutions.
        Always provide your answer in the format: <answer>YOUR_ANSWER</answer>"""
        
        self.agent = ExperienceAgent(
            conf=agent_config,
            name="demo_experience_agent",
            system_prompt=system_prompt,
            learning_mode=True,
            apply_experience=True,
            experience_db_path="./experiences/demo_experiences.json",
            knowledge_base=self.knowledge_base,
            summarizer=self.summarizer
        )
        
        print("\n🤖 Experience Agent initialized with:")
        print(f"   - Learning mode: {self.agent.learning_mode}")
        print(f"   - Apply experience: {self.agent.apply_experience}")
        print(f"   - Existing experiences: {len(self.agent.experiences)}")
        
        # Test questions
        test_questions = [
            "What is the capital of France?",
            "How many days are there in February during a leap year?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📌 Test Question {i}: {question}")
            
            # Check for relevant experiences
            relevant_exp = self.agent._get_relevant_experiences(question)
            if relevant_exp:
                print(f"   Found {len(relevant_exp)} relevant experiences")
            else:
                print("   No relevant experiences found")
            
            # Create task
            task = Task(
                input=question,
                agent=self.agent,
                conf=TaskConfig()
            )
            
            try:
                # Execute task
                print("   Executing task...")
                response = await self.agent.execute_task(task)
                
                if response and response.answer:
                    print(f"   ✅ Answer: {response.answer[:100]}...")
                else:
                    print("   ❌ No answer generated")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Show learned experiences
        if self.agent.experiences:
            print(f"\n📚 Learned Experiences ({len(self.agent.experiences)} total):")
            for exp_id, exp in list(self.agent.experiences.items())[:3]:
                print(f"\n   Experience ID: {exp_id[:8]}...")
                print(f"   Question: {exp.get('question', 'N/A')[:80]}...")
                print(f"   Summary: {exp.get('summary', 'N/A')[:80]}...")
    
    async def demo_workflow(self):
        """Demonstrate complete workflow."""
        print("\n" + "="*60)
        print("COMPLETE EXPERIENCE LEARNING WORKFLOW DEMO")
        print("="*60)
        
        # Step 1: Index knowledge base
        await self.demo_knowledge_base_indexing()
        
        # Step 2: Setup summarizer
        await self.demo_trajectory_summarization()
        
        # Step 3: Run agent with experience learning
        await self.demo_experience_agent()
        
        print("\n" + "="*60)
        print("DEMO COMPLETE!")
        print("="*60)
        
        # Summary statistics
        if self.knowledge_base:
            kb_stats = self.knowledge_base.get_statistics()
            print(f"\n📊 Final Statistics:")
            print(f"   - Knowledge base documents: {kb_stats['total_documents']}")
        
        if self.agent:
            print(f"   - Learned experiences: {len(self.agent.experiences)}")
            print(f"   - Experience DB: {self.agent.experience_db_path}")
    
    async def run_interactive_mode(self):
        """Run interactive mode for testing."""
        print("\n" + "="*60)
        print("INTERACTIVE MODE")
        print("="*60)
        print("\nCommands:")
        print("  1. Index knowledge base")
        print("  2. Test trajectory summarization")
        print("  3. Run experience agent")
        print("  4. Run complete workflow")
        print("  5. Exit")
        
        while True:
            try:
                choice = input("\nEnter command (1-5): ").strip()
                
                if choice == "1":
                    await self.demo_knowledge_base_indexing()
                elif choice == "2":
                    await self.demo_trajectory_summarization()
                elif choice == "3":
                    await self.demo_experience_agent()
                elif choice == "4":
                    await self.demo_workflow()
                elif choice == "5":
                    print("\nGoodbye!")
                    break
                else:
                    print("Invalid choice. Please enter 1-5.")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted by user.")
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}")
                print(f"\n❌ Error: {e}")


async def main():
    """Main entry point for demo."""
    demo = ExperienceLearningDemo()
    
    # Check for command line arguments
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            await demo.run_interactive_mode()
        elif sys.argv[1] == "--kb":
            await demo.demo_knowledge_base_indexing()
        elif sys.argv[1] == "--summarize":
            await demo.demo_trajectory_summarization()
        elif sys.argv[1] == "--agent":
            await demo.demo_experience_agent()
        else:
            await demo.demo_workflow()
    else:
        # Run complete workflow by default
        await demo.demo_workflow()


if __name__ == "__main__":
    print("\n🚀 Experience Learning System Demo")
    print("=" * 60)
    
    # Run the demo
    asyncio.run(main())
