# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import asyncio
from asyncio.log import logger
from datetime import datetime

from dotenv import load_dotenv

from tests.memory.agent.self_evolving_agent import SuperAgent
from tests.memory.utils import init_postgres_memory


async def _run_single_session_examples() -> None:
    """
    Run examples within a single session.
    Demonstrates a complete learning session about reinforcement learning concepts.
    """
    # await init_dataset()
    salt = datetime.now().strftime("%Y%m%d%H%M%S")
    super_agent = SuperAgent(id="super_agent", name="super_agent")
    user_id = "zues"
    session_id = f"session#foo_{salt}"
    logger.info(f"🚀 Running session {session_id}")
    
    # Task 1: Research on Mem0
    user_input_1 = """Conduct a comprehensive analysis of the Mem0 memory system (Part 1 of 4):

Research Focus Areas:
- System Overview and Core Principles
- Architectural Design and Implementation
- Key Features and Capabilities
- Use Cases and Applications
- Integration Patterns
- Performance Characteristics

Requirements:
- Utilize authoritative sources (GitHub, arXiv, etc.)
- Include code examples and implementation details
- Analyze real-world applications
- Format as a well-structured Markdown report
- Prepare for comparison with other memory systems in subsequent analysis
"""

    # Task 2: Research on MemoryBank
    user_input_2 = """Conduct a comprehensive analysis of the MemoryBank system (Part 2 of 4):

Research Focus Areas:
- System Overview and Core Principles
- Architectural Design and Implementation
- Key Features and Capabilities
- Use Cases and Applications
- Integration Patterns
- Performance Characteristics
- Comparative Analysis with Mem0

Requirements:
- Build upon previous Mem0 analysis
- Focus on unique features and differentiators
- Include practical implementation examples
- Document integration capabilities
- Format as a well-structured Markdown report
"""

    # Task 3: Research on MemoryOS
    user_input_3 = """Conduct a comprehensive analysis of the MemoryOS system (Part 3 of 4):

Research Focus Areas:
- System Overview and Core Principles
- Architectural Design and Implementation
- Key Features and Capabilities
- Use Cases and Applications
- Integration Patterns
- Performance Characteristics
- Comparative Analysis with Mem0 and MemoryBank

Requirements:
- Build upon previous analyses
- Highlight unique operating system integration aspects
- Include practical implementation examples
- Analyze scalability and performance
- Format as a well-structured Markdown report
"""

    # Task 4: Research on MemoryAgent
    user_input_4 = """Conduct a comprehensive analysis of the MemoryAgent system (Part 4 of 4):

Research Focus Areas:
- System Overview and Core Principles
- Architectural Design and Implementation
- Key Features and Capabilities
- Use Cases and Applications
- Integration Patterns
- Performance Characteristics
- Comprehensive Comparative Analysis
- Future Development Trends

Requirements:
- Synthesize findings from all previous analyses
- Create a comparative matrix of all systems
- Identify best practices and recommendations
- Discuss future trends and potential improvements
- Format as a well-structured Markdown report
"""

    # Execute tasks sequentially
    await super_agent.async_run(user_id=user_id, session_id=session_id, task_id=f"zues:session#foo:task#1_{salt}",
                              user_input=user_input_1)
    
    await super_agent.async_run(user_id=user_id, session_id=session_id, task_id=f"zues:session#foo:task#2_{salt}",
                              user_input=user_input_2)
    
    await super_agent.async_run(user_id=user_id, session_id=session_id, task_id=f"zues:session#foo:task#3_{salt}",
                              user_input=user_input_3)
    
    await super_agent.async_run(user_id=user_id, session_id=session_id, task_id=f"zues:session#foo:task#4_{salt}",
                              user_input=user_input_4)

    # Final task: Add AWorld comparison
    await super_agent.async_run(user_id=user_id, session_id=session_id, task_id=f"zues:session#foo:task#5_{salt}",
                              user_input="""Please extend the comparative analysis section to include AWorld's Memory Module [https://github.com/inclusionAI/AWorld/].

Focus on:
- Integration with the overall AWorld architecture
- Unique features and capabilities
- Performance characteristics
- Implementation differences
- Potential advantages and limitations
- Comparative analysis with all previously analyzed systems
""")

    logger.info(f"✅ Session {session_id} completed")
    

# if __name__ == '__main__':
#     load_dotenv()
#
#     init_postgres_memory()
#     # Run the multi-session example with concrete learning tasks
#     asyncio.run(_run_single_session_examples())

