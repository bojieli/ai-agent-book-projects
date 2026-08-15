import json
import os.path
import traceback
from datetime import datetime
from typing import Dict, List, Any

from aworld import import_package
from aworld.core.agent.base import is_agent_by_name
from aworld.core.event.base import Message, Constants
from aworld.logs.util import logger
from aworld.replay_buffer.base import ReplayBuffer, DataRow, ExpMeta, Experience, InMemoryStorage, Storage
from aworld.runners.state_manager import RuntimeStateManager, EventRuntimeStateManager
from aworld.utils.serialized_util import to_serializable
from aworld.utils.common import get_local_ip


class EventReplayBuffer(ReplayBuffer):
    '''
    Event replay buffer for storing and sampling data.
    Adds the ability to build DataRow from messages and export data to files.
    '''
    def __init__(
        self,
        storage: Storage = InMemoryStorage()
    ):
        super().__init__(storage)
        self.task_agent_map = {}

    async def get_trajectory(self, messages: List[Message], task_id: str, state_mng: RuntimeStateManager = None) -> List[Dict[str, Any]] | None:
        if not messages:
            return None
        valid_agent_messages = await self._filter_replay_messages(messages, task_id)
        if not valid_agent_messages:
            return None
        data_rows = []
        try:
            for msg in valid_agent_messages:
                data_row = self.build_data_row_from_message(msg, state_mng)
                if data_row:
                    data_rows.append(data_row)
            if not data_rows:
                logger.warn(f"No valid agent messages found for task: {task_id}")
                return None

            self.store_batch(data_rows)
            trajectory = [to_serializable(data_row) for data_row in data_rows]

            self.export(data_rows, task_id)

            return trajectory
        except Exception as e:
            logger.error(f"Failed to save trajectories: {str(e)}.{traceback.format_exc()}")
            return None

    async def _filter_replay_messages(self, messages: List[Message], task_id: str) -> List[Message]:
        results = []
        logger.info(f"Retrieving agent messages for task: {task_id}")
        for message in messages:
            if message.task_id != task_id or message.category != Constants.AGENT:
                continue
            sender = message.sender
            receiver = message.receiver
            if not sender or not receiver or not is_agent_by_name(receiver):
                continue
            agent_as_tool = message.headers.get("agent_as_tool", False)
            if agent_as_tool:
                continue
            results.append(message)
        return results

    def build_data_row_from_message(self, message: Message, state_manager: RuntimeStateManager = None) -> DataRow:
        '''
        Build DataRow from a message.
        
        Args:
            message (Dict): Message data containing necessary metadata and experience data
            
        Returns:
            DataRow: The constructed data row
            
        Raises:
            ValueError: When the message is missing required fields
        '''
        if not message:
            raise ValueError("Message cannot be empty")

        agent_id = message.receiver
        task_id = message.context.task_id
        task_name = message.context.get_task().name
        pre_agent = message.sender
        task_agent_id = f"{task_id}_{agent_id}"
        if task_agent_id not in self.task_agent_map:
            self.task_agent_map[task_agent_id] = 0
        self.task_agent_map[task_agent_id] += 1
        id = f"{task_agent_id}_{self.task_agent_map[task_agent_id]}"

        # Build ExpMeta
        exp_meta = ExpMeta(
            task_id=task_id,
            task_name=task_name,
            agent_id=agent_id,
            step=self.task_agent_map[task_agent_id],
            execute_time=message.timestamp,
            pre_agent=pre_agent
        )

        if not state_manager:
            state_manager = EventRuntimeStateManager.instance()
        observation = message.payload
        node = state_manager._find_node(message.id)
        if node is None or not node.results:
            logger.error(f"Node result not found for message id: {message.id}, node: {node}")
            return None
        agent_results = []
        for handle_result in node.results:
            result = handle_result.result
            if isinstance(result, Message) and isinstance(result.payload, list):
                agent_results.extend(result.payload)
        messages = self._get_llm_messages_from_memory(message)

        # Build Experience
        exp_data = Experience(
            state=observation,
            actions=agent_results,
            messages=messages
        )
        
        # Build and return DataRow
        return DataRow(exp_meta=exp_meta, exp_data=exp_data, id=id)

    def _get_llm_messages_from_memory(self, message: Message):
        context = message.context
        return context.context_info.get("llm_input", [])

    def export(self, data_rows: List[DataRow], task_id: str) -> None:
        '''
        Export data rows to a specified file.
        
        Args:
            data_rows (List[DataRow]): List of data rows to export
            filepath (str): Path of the export file
            
        Raises:
            ValueError: When the data rows list is empty or the file path is invalid
        '''
        enable_file_export = os.getenv("EXPORT_REPLAY_FILES", "false").lower() == "true"
        enable_oss_export = os.getenv("EXPORT_REPLAY_TO_OSS", "false").lower() == "true"
        if not enable_file_export and not enable_oss_export:
            return

        if not data_rows:
            logger.warn("Data rows list cannot be empty")
            return

        try:
            # Convert data rows to dictionary list
            data_dicts = [to_serializable(data_row) for data_row in data_rows]

            timestamp = datetime.now().strftime("%Y%m%d")
            export_dir = os.getenv('REPLAY_EXPORT_DIRECTORY', None)
            replay_dir = os.path.join(export_dir or "./trace_data", timestamp, get_local_ip(), "replays")
            os.makedirs(replay_dir, exist_ok=True)
            filepath = os.path.join(replay_dir, f"task_replay_{task_id}.json")

            if enable_file_export:
                logger.info(f"Exporting {len(data_rows)} data rows to {filepath}")
                # Write to JSON file
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data_dicts, f, ensure_ascii=False, indent=2)
                logger.info(f"Successfully exported {len(data_rows)} data rows to {os.path.abspath(filepath)}")

            if enable_oss_export:
                logger.info(f"Exporting {len(data_rows)} data rows to oss")
                self.export_to_oss(data_dicts, filepath)
        except Exception as e:
            logger.error(f"Failed to export replay datas: {e}")
            raise

    def export_to_oss(self, datas, filepath):
        import_package("oss2")
        import oss2

        # Get OSS credentials from environment variables
        access_key_id = os.getenv('OSS_ACCESS_KEY_ID')
        access_key_secret = os.getenv('OSS_ACCESS_KEY_SECRET')
        endpoint = os.getenv('OSS_ENDPOINT')
        bucket_name = os.getenv('OSS_BUCKET_NAME')
        bucket = None

        if not all([access_key_id, access_key_secret, endpoint, bucket_name]):
            logger.warn("Missing required OSS environment variables")
            return
        else:
            try:
                # Initialize OSS client
                auth = oss2.Auth(access_key_id, access_key_secret)
                bucket = oss2.Bucket(auth, endpoint, bucket_name)
            except Exception as e:
                logger.warn(
                    f"Failed to initialize OSS client, endpoint: {endpoint}, bucket: {bucket_name}. Error: {str(e)}")
                return

        # Upload to OSS
        try:
            # Get the relative path
            abs_path = os.path.abspath(filepath)
            path_parts = abs_path.split(os.sep)
            if len(path_parts) >= 4:
                # Get the last 4 parts of the path
                relative_path = os.sep.join(path_parts[-4:])
                oss_key = relative_path
            else:
                oss_key = f"replay_buffer/{os.path.basename(filepath)}"
            logger.info(f"Uploading replay datas to OSS: {oss_key}")
            bucket.put_object_from_file(oss_key, filepath)
            logger.info(f"Successfully uploaded {filepath} to OSS: {oss_key}")
        except Exception as e:
            logger.warn(f"Failed to upload {filepath} to OSS: {str(e)}")
