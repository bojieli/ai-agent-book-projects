# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from pathlib import Path
from typing import Dict, Any, Tuple, SupportsFloat, Union, List

from pydantic import BaseModel

from aworld.config import ConfigDict
from examples.common.tools.tool_action import GymAction
from aworld.core.common import ActionModel, Observation, ActionResult
from aworld.core.tool.base import AsyncTool, ToolFactory
from aworld.utils.import_package import import_packages
from aworld.tools.utils import build_observation


class ActionType(object):
    DISCRETE = 'discrete'
    CONTINUOUS = 'continuous'


@ToolFactory.register(name="openai_gym",
                      desc="gym classic control game",
                      asyn=True,
                      supported_action=GymAction,
                      conf_file_name=f'openai_gym_tool.yaml',
                      dir=f"{Path(__file__).parent.absolute()}")
class OpenAIGym(AsyncTool):
    def __init__(self, conf: Union[Dict[str, Any], ConfigDict, BaseModel], **kwargs) -> None:
        """Gym environment constructor.

        Args:
            env_id: gym environment full name
            wrappers: gym environment wrapper list
        """
        import_packages(['pygame', 'gymnasium'])
        super(OpenAIGym, self).__init__(conf, **kwargs)
        self.env_id = self.conf.get("env_id")
        self._render = self.conf.get('render', True)
        if self._render:
            kwargs['render_mode'] = self.conf.get('render_mode', True)
        kwargs.pop('name', None)
        self.env = self._gym_env_wrappers(self.env_id, self.conf.get("wrappers", []), **kwargs)
        self.action_space = self.env.action_space

    async def do_step(self, actions: List[ActionModel], **kwargs) -> Tuple[
        Observation, SupportsFloat, bool, bool, Dict[str, Any]]:
        if self._render:
            await self.render()
        action = actions[0].params['result']
        action = OpenAIGym.transform_action(action=action)
        state, reward, terminal, truncate, info = self.env.step(action)
        info.update(kwargs)
        self._finished = terminal

        action_results = []
        for _ in actions:
            action_results.append(ActionResult(content=OpenAIGym.transform_state(state=state), success=True))
        return (build_observation(observer=self.name(),
                                  action_result=action_results,
                                  ability=GymAction.PLAY.value.name,
                                  content=OpenAIGym.transform_state(state=state),
                                  env_id=self.env_id,
                                  done=terminal,
                                  **kwargs),
                reward,
                terminal,
                truncate,
                info)

    async def render(self):
        return self.env.render()

    async def close(self):
        if self.env:
            self.env.close()
        self.env = None

    async def reset(self, *, seed: int | None = None, options: Dict[str, str] | None = None) -> Tuple[
        Any, Dict[str, Any]]:
        state = self.env.reset()
        return build_observation(observer=self.name(),
                                 ability=GymAction.PLAY.value.name,
                                 content=OpenAIGym.transform_state(state=state),
                                 env_id=self.env_id,
                                 done=False), {}

    def _action_dim(self):
        from gymnasium import spaces

        if isinstance(self.env.action_space, spaces.Discrete):
            self.action_type = ActionType.DISCRETE
            return self.env.action_space.n
        elif isinstance(self.env.action_space, spaces.Box):
            self.action_type = ActionType.CONTINUOUS
            return self.env.action_space.shape[0]
        else:
            raise Exception('unsupported env.action_space: {}'.format(self.env.action_space))

    def _state_dim(self):
        if len(self.env.observation_space.shape) == 1:
            return self.env.observation_space.shape[0]
        else:
            raise Exception('unsupported observation_space.shape: {}'.format(self.env.observation_space))

    def _gym_env_wrappers(self, env_id, wrappers: list = [], **kwargs):
        import gymnasium

        env = gymnasium.make(env_id, **kwargs)

        if wrappers:
            for wrapper in wrappers:
                env = wrapper(env)

        return env

    @staticmethod
    def transform_state(state: Any):
        if isinstance(state, tuple):
            states = dict()
            for n, state in enumerate(state):
                state = OpenAIGym.transform_state(state=state)
                if isinstance(state, dict):
                    for name, state in state.items():
                        states['gym{}-{}'.format(n, name)] = state
                else:
                    states['gym{}'.format(n)] = state
            return states
        elif isinstance(state, dict):
            states = dict()
            for state_name, state in state.items():
                state = OpenAIGym.transform_state(state=state)
                if isinstance(state, dict):
                    for name, state in state.items():
                        states['{}-{}'.format(state_name, name)] = state
                else:
                    states['{}'.format(state_name)] = state
            return states
        else:
            return state

    @staticmethod
    def transform_action(action: Any):
        if not isinstance(action, dict):
            return action
        else:
            actions = dict()
            for name, action in action.items():
                if '-' in name:
                    name, inner_name = name.split('-', 1)
                    if name not in actions:
                        actions[name] = dict()
                    actions[name][inner_name] = action
                else:
                    actions[name] = action
            for name, action in actions.items():
                if isinstance(action, dict):
                    actions[name] = OpenAIGym.transform_action(action=action)
            return actions
