
from aworld.core.agent.base import AgentFactory
from aworld.core.context.base import Context
from aworld.core.event.base import Message
from aworld.runners.hook.hooks import PreLLMCallHook, PostLLMCallHook
from aworld.runners.hook.hook_factory import HookFactory
from aworld.utils.common import convert_to_snake


@HookFactory.register(name="TestPreLLMHook", desc="Test pre-LLM hook")
class TestPreLLMHook(PreLLMCallHook):
    def name(self):
        return convert_to_snake("TestPreLLMHook")

    async def exec(self, message: Message, context: Context = None) -> Message:
        agent = AgentFactory.agent_instance(message.sender)
        context = message.context
        context.context_info.set('step', 1)
        return message


@HookFactory.register(name="TestPostLLMHook", desc="Test post-LLM hook")
class TestPostLLMHook(PostLLMCallHook):
    def name(self):
        return convert_to_snake("TestPostLLMHook")

    async def exec(self, message: Message, context: Context = None) -> Message:
        agent = AgentFactory.agent_instance(message.sender)
        context = message.context
        assert context.context_info.get('step') == 1
        return message
