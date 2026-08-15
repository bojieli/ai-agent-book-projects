import aworld.trace as trace
import aworld.trace.instrumentation.semconv as semconv
from aworld.trace.server import get_trace_server
from aworld.trace.server.util import build_trace_tree
from aworld.core.tool.base import AsyncTool, AgentInput, ToolFactory
from examples.common.tools.tool_action import GetTraceAction
from aworld.tools.utils import build_observation
from aworld.config.conf import ToolConfig
from aworld.core.common import Observation, ActionModel, ActionResult
from typing import Tuple, Dict, Any, List
from aworld.logs.util import logger


@ToolFactory.register(name="trace",
                      desc="Get the trace of the current execution.",
                      supported_action=GetTraceAction,
                      conf_file_name=f'trace_tool.yaml')
class TraceTool(AsyncTool):
    def __init__(self,
                 conf: ToolConfig,
                 **kwargs) -> None:
        """
        Initialize the TraceTool
        Args:
            conf: tool config
            **kwargs: -
        Return:
            None
        """
        super(TraceTool, self).__init__(conf, **kwargs)
        self.type = "function"
        self.get_trace_url = self.conf.get('get_trace_url')

    async def reset(self,
              *,
              seed: int | None = None,
              options: Dict[str, str] | None = None) -> Tuple[AgentInput, dict[str, Any]]:
        """
        Reset the executor
        Args:
            seed: -
            options: -
        Returns:
            AgentInput, dict[str, Any]: -
        """
        self._finished = False
        return build_observation(observer=self.name(),
                                 ability=GetTraceAction.GET_TRACE.value.name), {}

    async def close(self) -> None:
        """
        Close the executor
        Returns:
            None
        """
        self._finished = True

    async def do_step(self,
                actions: List[ActionModel],
                **kwargs) -> Tuple[Observation, float, bool, bool, dict[str, Any]]:
        reward = 0
        fail_error = ""
        observation = build_observation(observer=self.name(),
                                        ability=GetTraceAction.GET_TRACE.value.name)
        results = []
        try:
            if not actions:
                return (observation, reward,
                        kwargs.get("terminated",
                                   False), kwargs.get("truncated", False), {
                            "exception": "actions is empty"
                        })
            for action in actions:
                trace_id = action.params.get("trace_id", "")
                if not trace_id:
                    current_span = trace.get_current_span()
                    if current_span:
                        trace_id = current_span.get_trace_id()
                if not trace_id:
                    logger.warning(f"{action} no trace_id to fetch.")
                    observation.action_result.append(
                        ActionResult(is_done=True,
                                     success=False,
                                     content="",
                                     error="no trace_id to fetch",
                                     keep=False))
                    continue
                try:
                    trace_data = self.fetch_trace_data(trace_id)
                    # logger.info(f"trace_data={trace_data}")
                    error = ""
                except Exception as e:
                    error = str(e)
                results.append(trace_data)
                observation.action_result.append(
                    ActionResult(is_done=True,
                                 success=False if error else True,
                                 content=f"{trace_data}",
                                 error=f"{error}",
                                 keep=False))

            observation.content = f"{results}"
            reward = 1
        except Exception as e:
            fail_error = str(e)
        finally:
            self._finished = True

        info = {"exception": fail_error}
        info.update(kwargs)
        return (observation, reward, kwargs.get("terminated", False),
                kwargs.get("truncated", False), info)

    def fetch_trace_data(self, trace_id=None):
        '''
            fetch trace data from trace server.
            return trace data, like:
            {
                'trace_id': trace_id,
                'root_span': [],
            }
        '''
        trace_data = {"trace_id": trace_id, "root_span": []}
        try:
            if trace_id:
                trace_server = get_trace_server()
                if not trace_server:
                    logger.error("No memory trace server has been set.")
                else:
                    trace_storage = trace_server.get_storage()
                    spans = trace_storage.get_all_spans(trace_id)
                    if spans:
                        trace_data["root_span"] = build_trace_tree(spans)
                        return self.proccess_trace(trace_data)
            return trace_data
        except Exception as e:
            import traceback
            logger.error(
                f"Error fetching trace data traceback: {traceback.format_exc()}")
            return trace_data

    def proccess_trace(self, trace_data):
        root_spans = trace_data.get("root_span")
        for span in root_spans:
            self.choose_attribute(span)
        return trace_data

    def choose_attribute(self, span):
        include_attr = [semconv.GEN_AI_USAGE_INPUT_TOKENS,
                        semconv.GEN_AI_USAGE_OUTPUT_TOKENS, semconv.GEN_AI_USAGE_TOTAL_TOKENS,
                        semconv.GEN_AI_COMPLETION_TOOL_CALLS, "event.id"]
        result_attributes = {}
        origin_attributes = span.get("attributes") or {}
        for key, value in origin_attributes.items():
            if key in include_attr:
                result_attributes[key] = value
        span["attributes"] = result_attributes
        if span.get("children"):
            for child in span.get("children"):
                self.choose_attribute(child)
