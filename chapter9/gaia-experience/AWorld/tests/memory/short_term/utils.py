import json
import logging

from aworld.core.memory import MemoryBase, AgentMemoryConfig
from aworld.memory.models import MemoryAIMessage, MemoryToolMessage, MessageMetadata, MemorySystemMessage, \
    MemoryHumanMessage
from aworld.models.model_response import Function, ToolCall


async def add_mock_messages(memory: MemoryBase, metadata: MessageMetadata, memory_config: AgentMemoryConfig = AgentMemoryConfig()):
    # Add system message 🤖
    system_content = """
            <system_instruction>
    You are an advanced AI assistant powered by a large language model, operating within the AWorld framework. Your purpose is to assist users with a wide range of tasks by leveraging your knowledge and capabilities.

    ## Core Capabilities
    You are designed to:
    1. **Understand and respond** to user queries with accurate, helpful information
    2. **Reason** through complex problems step by step
    3. **Generate** creative content based on user requirements
    4. **Execute** tasks using available tools when appropriate
    5. **Learn** from interactions to better serve users over time

    ## Task Approach
    When addressing user requests:
    1. **Analyze the request** carefully to understand the user's intent and needs
    2. **Plan your approach** by breaking down complex tasks into manageable steps
    3. **Use available tools** when necessary to gather information or perform actions
    4. **Provide clear explanations** of your reasoning and actions
    5. **Verify your responses** for accuracy, relevance, and completeness before delivering them

    ## Communication Guidelines
    1. **Be concise** but thorough in your responses
    2. **Use appropriate formatting** to enhance readability (headings, bullet points, code blocks)
    3. **Adapt your tone** to match the context and user's communication style
    4. **Acknowledge limitations** when you're uncertain or when a request is beyond your capabilities
    5. **Seek clarification** when user requests are ambiguous or incomplete

    ## Tool Usage
    When using tools:
    1. **Select the appropriate tool** based on the task requirements
    2. **Explain your reasoning** for using a particular tool
    3. **Use tools efficiently** to minimize unnecessary operations
    4. **Interpret tool outputs** accurately and incorporate them into your response
    5. **Handle errors gracefully** if tools fail or return unexpected results
    6. save file use tool[filesystem]
            <agent_experiences>
            []
            </agent_experiences>

            <history>

            </history>

            <cur_time>
            2025-07-07 17:06:25
            </cur_time>
    </system_instruction>
    """
    await memory.add(MemorySystemMessage(content=system_content, metadata=metadata), agent_memory_config=memory_config)

    # Add user message 👤
    user_content = """
    <user_profiles>
    []
    </user_profiles>

    <similar_messages_history>
    []
    </similar_messages_history>

    <knowledge_base>
    </knowledge_base>

    I like play outdoor sports(basketball, tennis, golf, etc.), please recommend some outdoor sports, save it use markdown
    """
    await memory.add(MemoryHumanMessage(content=user_content, metadata=metadata), agent_memory_config=memory_config)

    # Add assistant message 🤖
    assistant_content = "I'll recommend some popular outdoor sports and save them in a markdown file for you. Here are some great outdoor sports activities:"

    # Create ToolCall object
    function = Function(
        name="mcp__filesystem__write_file",
        arguments=json.dumps({
            "path": "outdoor_sports_recommendations.md",
            "content": "# Outdoor Sports Recommendations\n\nHere are some excellent outdoor sports to try:\n\n## Team Sports\n- Soccer\n- Ultimate Frisbee\n- Beach Volleyball\n- Rugby\n\n## Water Sports\n- Kayaking\n- Stand-up Paddleboarding (SUP)\n- Surfing\n- Open Water Swimming\n\n## Adventure Sports\n- Rock Climbing\n- Mountain Biking\n- Trail Running\n- Orienteering\n\n## Winter Sports\n- Skiing (Alpine/Cross-country)\n- Snowboarding\n- Ice Climbing\n- Snowshoeing\n\n## Individual Sports\n- Golf\n- Tennis\n- Archery\n- Disc Golf\n\n## Extreme Sports\n- Paragliding\n- Bungee Jumping\n- Whitewater Rafting\n- Skydiving\n\nRemember to always use proper safety equipment and get proper training before trying new sports!"
        })
    )

    tool_call = ToolCall(
        id="fc-249231de-7efb-4741-b659-2ab8696065cc",
        type="function",
        function=function
    )

    await memory.add(MemoryAIMessage(content=assistant_content, tool_calls=[tool_call], metadata=metadata), agent_memory_config=memory_config)



    # Add tool response message 🛠️
    tool_content = "Successfully wrote to outdoor_sports_recommendations.md"
    await memory.add(MemoryToolMessage(
        content=tool_content,
        tool_call_id="fc-249231de-7efb-4741-b659-2ab8696065cc",
        status="success",
        metadata=metadata
    ), agent_memory_config=memory_config)

    logging.info("mock messages added")