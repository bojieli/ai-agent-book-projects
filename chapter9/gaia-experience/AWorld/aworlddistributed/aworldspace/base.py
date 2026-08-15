from typing import Optional

from pydantic import BaseModel, Field

from aworldspace.base_agent import AworldBaseAgent

"""
Agent Space 
"""

class AgentMeta(BaseModel):
    name: str = None
    desc: str = None



class AgentSpace(BaseModel):
    agent_modules: Optional[dict] = Field(default_factory=dict, description="agent module")
    agents_meta: Optional[dict] = Field(default_factory=dict, description="agents meta")

    def register(self, agent_name: str, agent_instance: AworldBaseAgent, metadata: dict=None):
        # Register agent metadata and instance
        self.agent_modules[agent_name] = agent_instance

    async def get_agent_modules(self):
        return self.agent_modules

    async def get_agents_meta(self):
        return self.agents_meta


AGENT_SPACE = AgentSpace()