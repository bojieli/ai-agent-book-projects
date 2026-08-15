import logging
import json
import traceback

from aworld.core.context.base import Context
# from fastmcp.server.middleware import Middleware, MiddlewareContext


from aworld.utils.common import sync_exec

from aworld.events.util import send_message

from aworld.core.event.base import Message, Constants
from typing_extensions import Optional, List, Dict, Any

from aworld.mcp_client.utils import mcp_tool_desc_transform, call_api, get_server_instance, cleanup_server, \
    call_function_tool, mcp_tool_desc_transform_v2
from mcp.types import TextContent, ImageContent

from aworld.core.common import ActionResult
from aworld.output import Output


class McpServers:

    def __init__(
            self,
            mcp_servers: Optional[List[str]] = None,
            mcp_config: Dict[str, Any] = None,
            sandbox=None,
            black_tool_actions: Dict[str, List[str]] = None,
    ) -> None:
        self.mcp_servers = mcp_servers
        self.mcp_config = mcp_config
        self.sandbox = sandbox
        # Dictionary to store server instances {server_name: server_instance}
        self.server_instances = {}
        self.tool_list = None
        self.black_tool_actions = black_tool_actions or {}

    async def list_tools(self, context: Context = None) -> List[Dict[str, Any]]:
        if self.tool_list:
            return self.tool_list
        if not self.mcp_servers or not self.mcp_config:
            return []
        try:
            #self.tool_list = await mcp_tool_desc_transform(self.mcp_servers, self.mcp_config)
            self.tool_list = await mcp_tool_desc_transform_v2(self.mcp_servers, self.mcp_config,context,self.server_instances,self.black_tool_actions)
            return self.tool_list
        except Exception as e:
            traceback.print_exc()
            logging.warning(f"Failed to list tools: {e}")
            return []

    async def check_tool_params(self, context: Context, server_name: str, tool_name: str,
                                parameter: Dict[str, Any]) -> Any:
        """
        Check tool parameters and automatically supplement session_id, task_id and other parameters from context
        
        Args:
            context: Context object containing session_id, task_id and other information
            server_name: Server name
            tool_name: Tool name
            parameter: Parameter dictionary, will be modified
            
        Returns:
            bool: Whether parameter check passed
        """
        # Ensure tool_list is loaded
        if not self.tool_list or not context:
            return False

        if not self.mcp_servers or not self.mcp_config:
            return False

        try:
            # Build unique identifier for the tool
            tool_identifier = f"mcp__{server_name}__{tool_name}"

            # Find corresponding tool in tool_list
            target_tool = None
            for tool in self.tool_list:
                if tool.get("type") == "function" and tool.get("function", {}).get("name") == tool_identifier:
                    target_tool = tool
                    break

            if not target_tool:
                logging.warning(f"Tool not found: {tool_identifier}")
                return False

            # Get tool parameter definitions
            function_info = target_tool.get("function", {})
            tool_parameters = function_info.get("parameters", {})
            properties = tool_parameters.get("properties", {})

            # Check if session_id or task_id parameters are needed
            # Check if session_id is needed
            if "session_id" in properties:
                if hasattr(context, 'session_id') and context.session_id:
                    parameter["session_id"] = context.session_id
                    logging.info(f"Auto-added session_id: {context.session_id}")

            # Check if task_id is needed
            if "task_id" in properties:
                if hasattr(context, 'task_id') and context.task_id:
                    parameter["task_id"] = context.task_id
                    logging.info(f"Auto-added task_id: {context.task_id}")

            return True

        except Exception as e:
            logging.warning(f"Error checking tool parameters: {e}")
            return False

    async def call_tool(
            self,
            action_list: List[Dict[str, Any]] = None,
            task_id: str = None,
            session_id: str = None,
            context: Context = None
    ) -> List[ActionResult]:
        results = []
        if not action_list:
            return None

        try:
            for action in action_list:
                if not isinstance(action, dict):
                    action_dict = vars(action)
                else:
                    action_dict = action

                # Get values from dictionary
                server_name = action_dict.get("tool_name")
                tool_name = action_dict.get("action_name")
                parameter = action_dict.get("params", {})
                result_key = f"{server_name}__{tool_name}"

                operation_info = {
                    "server_name": server_name,
                    "tool_name": tool_name,
                    "params": parameter
                }

                if not server_name or not tool_name:
                    continue

                # Check server type
                server_type = None
                if self.mcp_config and self.mcp_config.get("mcpServers"):
                    server_config = self.mcp_config.get("mcpServers").get(server_name, {})
                    server_type = server_config.get("type", "")

                if server_type == "function_tool":
                    try:
                        call_result = await call_function_tool(
                            server_name, tool_name, parameter, self.mcp_config
                        )
                        results.append(call_result)

                        self._update_metadata(result_key, call_result, operation_info)
                    except Exception as e:
                        logging.warning(f"Error calling function_tool tool: {e}")
                        self._update_metadata(result_key, {"error": str(e)}, operation_info)
                    continue

                # For API type servers, use call_api function directly
                if server_type == "api":
                    try:
                        call_result = await call_api(
                            server_name, tool_name, parameter, self.mcp_config
                        )
                        results.append(call_result)

                        self._update_metadata(result_key, call_result, operation_info)
                    except Exception as e:
                        logging.warning(f"Error calling API tool: {e}")
                        self._update_metadata(result_key, {"error": str(e)}, operation_info)
                    continue

                # Prioritize using existing server instances
                server = self.server_instances.get(server_name)
                if server is None:
                    # If it doesn't exist, create a new instance and save it
                    server = await get_server_instance(server_name, self.mcp_config,context)
                    if server:
                        self.server_instances[server_name] = server
                        logging.info(f"Created and cached new server instance for {server_name}")
                    else:
                        logging.warning(f"Created new server failed: {server_name}, session_id: {session_id}, tool_name: {tool_name}")

                        self._update_metadata(result_key, {"error": "Failed to create server instance"}, operation_info)
                        continue

                # Use server instance to call the tool
                call_result_raw = None
                action_result = ActionResult(
                    tool_name=server_name,
                    action_name=tool_name,
                    content="",
                    keep=True
                )
                max_retry = 3
                for i in range(max_retry):
                    try:
                        async def progress_callback(
                                progress: float, total: float | None, message: str | None
                        ):
                            try:
                                output = Output()
                                output.data = message
                                tool_output_message = Message(
                                    category=Constants.OUTPUT,
                                    payload=output,
                                    sender=f"{server_name}__{tool_name}",
                                    session_id=context.session_id if context else "",
                                    headers={"context": context}
                                )
                                sync_exec(send_message, tool_output_message)
                            except BaseException as e:
                                logging.warning(f"Error calling progress callback: {e}")

                        await self.check_tool_params(context=context, server_name=server_name, tool_name=tool_name,
                                                     parameter=parameter)
                        call_result_raw = await server.call_tool(tool_name=tool_name, arguments=parameter,
                                                                 progress_callback=progress_callback)
                        break
                    except BaseException as e:
                        logging.warning(
                            f"Error calling tool error: {e}. Extra info: session_id = {session_id}, tool_name = {tool_name}."
                            f"Traceback:\n{traceback.format_exc()}"
                        )
                logging.info(f"tool_name:{server_name},action_name:{tool_name} finished.")
                logging.debug(f"tool_name:{server_name},action_name:{tool_name} call-mcp-tool-result: {call_result_raw}")
                if not call_result_raw:
                    logging.warning(f"Error calling tool with cached server")

                    self._update_metadata(result_key, {"error": str(e)}, operation_info)

                    # If using cached server instance fails, try to clean up and recreate
                    if server_name in self.server_instances:
                        try:
                            await cleanup_server(self.server_instances[server_name])
                            del self.server_instances[server_name]
                        except Exception as e:
                            logging.warning(f"Failed to cleanup server {server_name}: {e}")
                else:
                    if call_result_raw and call_result_raw.content:
                        metadata = call_result_raw.content[0].model_extra.get("metadata", {})
                        artifact_datas = []

                        content_list: list[str] = []
                        for content in call_result_raw.content:
                            if isinstance(call_result_raw.content[0], TextContent):
                                content_list.append(content.text)
                                _metadata = content.model_extra.get("metadata", {})
                                if "artifact_data" in _metadata and isinstance(_metadata["artifact_data"], dict):
                                    artifact_datas.append({
                                        "artifact_type": _metadata["artifact_type"],
                                        "artifact_data": _metadata["artifact_data"]
                                    })
                            elif isinstance(call_result_raw.content[0], ImageContent):
                                content_list.append(f"data:image/jpeg;base64,{content.data}")
                                _metadata = content.model_extra.get("metadata", {})
                                if "artifact_data" in _metadata and isinstance(_metadata["artifact_data"], dict):
                                    artifact_datas.append({
                                        "artifact_type": _metadata["artifact_type"],
                                        "artifact_data": _metadata["artifact_data"]
                                    })
                    if metadata and artifact_datas:
                        metadata["artifacts"] = artifact_datas

                    action_result = ActionResult(
                        tool_name=server_name,
                        action_name=tool_name,
                        content=json.dumps(content_list, ensure_ascii=False),
                        keep=True,
                        metadata=metadata,
                        parameter=parameter
                    )
                    results.append(action_result)
                    self._update_metadata(result_key, action_result, operation_info)

        except Exception as e:
            logging.warning(f"Failed to call_tool: {e}.Extra info: session_id = {session_id}, action_list = {action_list}")
            return None

        return results

    def _update_metadata(self, result_key: str, result: Any, operation_info: Dict[str, Any]):
        """
        Update sandbox metadata with a single tool call result

        Args:
            result_key: The key name in metadata
            result: Tool call result
            operation_info: Operation information
        """
        if not self.sandbox or not hasattr(self.sandbox, '_metadata'):
            return

        try:
            metadata = self.sandbox._metadata.get("mcp_metadata", {})
            tmp_data = {
                "input": operation_info,
                "output": result
            }
            if not metadata:
                metadata["mcp_metadata"] = {}
                metadata["mcp_metadata"][result_key] = [tmp_data]
                self.sandbox._metadata["mcp_metadata"] = metadata
                return

            _metadata = metadata.get(result_key, [])
            if not _metadata:
                _metadata[result_key] = [_metadata]
            else:
                _metadata[result_key].append(tmp_data)
            metadata[result_key] = _metadata
            self.sandbox._metadata["mcp_metadata"] = metadata
            return

        except Exception as e:
            logging.debug(f"Failed to update sandbox metadata: {e}")

    # Add cleanup method, called when Sandbox is destroyed
    async def cleanup(self):
        """Clean up all server connections"""
        for server_name, server in list(self.server_instances.items()):
            try:
                await cleanup_server(server)
                del self.server_instances[server_name]
                logging.info(f"Cleaned up server instance for {server_name}")
            except Exception as e:
                logging.warning(f"Failed to cleanup server {server_name}: {e}")
