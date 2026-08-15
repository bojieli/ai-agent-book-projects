import asyncio
import os
import uuid

from dotenv import load_dotenv

from aworld import trace
from examples.multi_agents.collaborative.debate.agent.debate_agent import DebateAgent
from examples.multi_agents.collaborative.debate.agent.main import DebateArena
from examples.multi_agents.collaborative.debate.agent.moderator_agent import ModeratorAgent
from examples.multi_agents.collaborative.debate.agent.prompts import generate_opinions_prompt
from aworld.config import AgentConfig
from aworld.output import WorkSpace

# os.environ["LLM_PROVIDER"] = "openai"
# os.environ["LLM_MODEL_NAME"] = "YOUR_LLM_MODEL_NAME"
# os.environ["LLM_BASE_URL"] = "YOUR_LLM_BASE_URL"
# os.environ["LLM_API_KEY"] = "YOUR_LLM_API_KEY"

if __name__ == '__main__':
    load_dotenv()
    trace.configure()

    base_config = {
        "llm_provider": os.getenv("LLM_PROVIDER"),
        "llm_model_name": os.environ['LLM_MODEL_NAME'],
        "llm_base_url": os.environ['LLM_BASE_URL'],
        "llm_api_key": os.environ['LLM_API_KEY'],
        "llm_temperature": os.getenv("LLM_TEMPERATURE", 0.0)
    }

    agentConfig = AgentConfig.model_validate(base_config)

    agent1 = DebateAgent(name="affirmativeSpeaker", stance="affirmative", conf=AgentConfig.model_validate(base_config))
    agent2 = DebateAgent(name="negativeSpeaker", stance="negative", conf=AgentConfig.model_validate(base_config))

    moderator_agent = ModeratorAgent(
        conf=AgentConfig.model_validate(base_config | {
            "name": "moderator_agent",
            "agent_prompt": generate_opinions_prompt
        }),
        name="moderator_agent"
    )

    debate_arena = DebateArena(affirmative_speaker=agent1, negative_speaker=agent2, moderator=moderator_agent,
                               workspace=WorkSpace.from_local_storages(str(uuid.uuid4())))


    async def start_debate(debate_arena, topic, rounds):
        speeches = debate_arena.async_run(topic=topic, rounds=rounds)
        async for speech in speeches:
            if speech.parts:
                async for part in speech.parts:
                    print(part.content, flush=True, end="")

            print(f"{speech.name}: {speech.content}")


    asyncio.run(start_debate(debate_arena, topic="张居正", rounds=3))
