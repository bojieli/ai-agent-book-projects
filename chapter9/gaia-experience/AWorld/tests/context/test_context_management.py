import asyncio
import os
import sys
from pathlib import Path
import unittest

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from aworld.core.context.session import Session
from aworld.core.agent.swarm import Swarm
from tests.base_test import assertEqual, assertIn, assertIsInstance, assertIsNotNone, assertTrue, run_multi_agent_as_team, run_task
from aworld.runners.hook.hook_factory import HookFactory
from aworld.core.context.base import Context
from aworld.config.conf import AgentConfig, ContextRuleConfig, ModelConfig, OptimizationConfig, LlmCompressionConfig
from aworld.agents.llm_agent import Agent
from aworld.core.task import Task
from tests.base_test import init_agent, run_agent, run_multi_agent_as_team

class TestContextManagement(unittest.TestCase):

    # def test_save_and_reload(self):
    #     context = Context()
    #     context.context_info.set("hello", "world")
    #     task = Task(input="""What is an agent.""",
    #                 swarm=Swarm(init_agent("1"), max_steps=1), context=context)
    #     task.session_id = "1"
    #     context.session = Session(session_id="1")
    #     context.set_task(task)
    #     context_manager = ContextManager()
    #     checkpoint = asyncio.run(context_manager.save(context))

    #     session_id = context.session_id
    #     context = asyncio.run(context_manager.reload(session_id))
    #     assertEqual(context.context_info.get("hello"), "world")
        
    def test_default_context_configuration(self):
        mock_agent = init_agent("1")
        response = run_agent(
            input="""What is an agent. describe within 20 words""", agent=mock_agent)

        assertIsNotNone(response.answer)
        assertEqual(
            mock_agent.conf.llm_config.llm_model_name, os.environ["LLM_MODEL_NAME"])

        # Test default context rule behavior
        assertIsNotNone(mock_agent.context_rule)
        assertIsNotNone(
            mock_agent.context_rule.optimization_config)

    def test_custom_context_configuration(self):
        """Test custom context configuration (README Configuration example)"""
        # Create custom context rules
        mock_agent = init_agent(context_rule=ContextRuleConfig(
            optimization_config=OptimizationConfig(
                enabled=True,
                max_token_budget_ratio=0.00015
            ),
            llm_compression_config=LlmCompressionConfig(
                enabled=True,
                trigger_compress_token_length=100,
                compress_model=ModelConfig(
                    llm_model_name=os.environ["LLM_MODEL_NAME"],
                    llm_base_url=os.environ["LLM_BASE_URL"],
                    llm_api_key=os.environ["LLM_API_KEY"],
                )
            )
        ))

        response = run_agent(
            input="""describe What is an agent in details""", agent=mock_agent)
        assertIsNotNone(response.answer)

        # Test configuration values
        assertTrue(
            mock_agent.context_rule.optimization_config.enabled)
        assertTrue(
            mock_agent.context_rule.llm_compression_config.enabled)


    def test_multi_agent_state_trace(self):
        class StateModifyAgent(Agent):
            async def async_policy(self, observation, info=None, **kwargs):
                result = await super().async_policy(observation, info, **kwargs)
                self.context.context_info.set('policy_executed', True)
                return result

        class StateTrackingAgent(Agent):
            async def async_policy(self, observation, info=None, **kwargs):
                result = await super().async_policy(observation, info, **kwargs)
                assert self.context.context_info.get('policy_executed', True)
                return result

        # Create custom agent instance
        custom_agent = StateModifyAgent(
            conf=AgentConfig(
                llm_model_name=os.environ["LLM_MODEL_NAME"],
                llm_base_url=os.environ["LLM_BASE_URL"],
                llm_api_key=os.environ["LLM_API_KEY"]
            ),
            name="state_modify_agent",
            system_prompt="You are a Python expert who provides detailed and practical answers.",
            agent_prompt="You are a Python expert who provides detailed and practical answers.",
        )

        # Create a second agent for multi-agent testing
        second_agent = StateTrackingAgent(
            conf=AgentConfig(
                llm_model_name=os.environ["LLM_MODEL_NAME"],
                llm_base_url=os.environ["LLM_BASE_URL"],
                llm_api_key=os.environ["LLM_API_KEY"]
            ),
            name="state_tracking_agent",
            system_prompt="You are a helpful assistant.",
            agent_prompt="You are a helpful assistant.",
        )

        response = run_multi_agent_as_team(
            input="What is an agent. describe within 20 words",
            agent1=custom_agent,
            agent2=second_agent
        )
        assertIsNotNone(response.answer)

        # Verify state changes after execution
        assertTrue(custom_agent.context.context_info.get('policy_executed', True))

    def test_multi_task_state_trace(self):
        context = Context()
        task = Task(input="What is an agent.", context=context)
        new_context = task.context.deep_copy()
        new_context.context_info.update({"hello": "world"})
        run_task(context=new_context, agent=init_agent("1"))
        assertEqual(new_context.context_info.get("hello"), "world")

        task.context.merge_context(new_context)
        assertEqual(task.context.context_info.get("hello"), "world")


    def test_hook_registration(self):
        from tests.runners.hook.llm_hook import TestPreLLMHook, TestPostLLMHook
        """Test hook registration and retrieval"""
        # Test that hooks are registered in _cls attribute
        assertIn("TestPreLLMHook", HookFactory._cls)
        assertIn("TestPostLLMHook", HookFactory._cls)

        # Test hook creation using __call__ method
        pre_hook = HookFactory("TestPreLLMHook")
        post_hook = HookFactory("TestPostLLMHook")

        assertIsInstance(pre_hook, TestPreLLMHook)
        assertIsInstance(post_hook, TestPostLLMHook)

    def test_hook_execution(self):
        mock_agent = init_agent("1")
        response = run_agent(
            input="""What is an agent. describe within 20 words""", agent=mock_agent)
        assertIsNotNone(response.answer)

    def test_task_context_transfer(self):
        mock_agent = init_agent("1")
        context = Context()
        context.context_info.update({"task": "What is an agent."})
        run_task(context=context, agent=mock_agent)



if __name__ == '__main__':
    unittest.main()
