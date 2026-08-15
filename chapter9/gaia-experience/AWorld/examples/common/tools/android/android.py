# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import traceback
from pathlib import Path
from typing import Any, Tuple, List, Dict

from examples.common.tools.tool_action import AndroidAction
from aworld.core.common import ActionModel, Observation, ActionResult
from aworld.logs.util import logger
from examples.common.tools.android.action.adb_controller import ADBController
from examples.common.tools.android.action.executor import AndroidToolActionExecutor
from examples.common.tools.conf import AndroidToolConfig
from aworld.core.tool.base import ToolFactory, Tool
from aworld.tools.utils import build_observation

ALL_UNICODE_CHARS = frozenset(chr(i) for i in range(0x10FFFF + 1))


@ToolFactory.register(name="android",
                      desc="android",
                      supported_action=AndroidAction,
                      conf_file_name=f'android_tool.yaml',
                      dir=f"{Path(__file__).parent.absolute()}")
class AndroidTool(Tool):

    def __init__(self, conf: AndroidToolConfig, **kwargs):
        super(AndroidTool, self).__init__(conf, **kwargs)
        self.controller = ADBController(avd_name=self.conf.get('avd_name'),
                                        adb_path=self.conf.get('adb_path'),
                                        emulator_path=self.conf.get('emulator_path'))

        if self.conf.get("custom_executor"):
            self.action_executor = AndroidToolActionExecutor(self.controller)

    def reset(self, *, seed: int | None = None, options: Dict[str, str] | None = None) -> Tuple[
        Observation, Dict[str, Any]]:
        # self.controller.stop_emulator()
        # self.controller.start_emulator()
        self.controller.setup_connection()
        logger.info("start emulator successfully...")
        # snapshot screen and annotate
        xml, pic_base64 = self.get_observation()
        action_result_list = [ActionResult(content='start', keep=True)]
        return build_observation(observer=self.name(),
                                 ability='',
                                 dom_tree=xml,
                                 image=pic_base64,
                                 action_result=action_result_list), {}

    def do_step(self, action_list: List[ActionModel], **kwargs) -> Tuple[
        Observation, float, bool, bool, Dict[str, Any]]:

        exec_state = 0
        fail_error = ""
        action_result_list = None
        try:
            action_result_list = self.action_executor.execute_action(action_list, **kwargs)
            exec_state = 1
        except Exception as e:
            traceback.print_exc()
            fail_error = str(e)

        terminated = kwargs.get("terminated", False)
        if action_result_list:
            for action_result in action_result_list:
                if action_result.is_done:
                    terminated = action_result.is_done
                    self._finish = True

        info = {"exception": fail_error}
        info.update(kwargs)
        xml, pic_base64 = self.get_observation()

        return (build_observation(observer=self.name(),
                                  ability=action_list[-1].action_name,
                                  dom_tree=xml,
                                  image=pic_base64,
                                  action_result=action_result_list),
                exec_state,
                terminated,
                kwargs.get("truncated", False),
                info)

    def close(self):
        self.controller.stop_emulator()

    def get_controller(self):
        return self.controller

    def get_observation(self) -> Observation:
        return self.controller.screenshot_and_annotate()
