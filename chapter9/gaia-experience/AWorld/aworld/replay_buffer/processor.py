# coding: utf-8
"""
processor.py
Used to clean raw trace data into standard storage structure for reinforcement learning training.
"""
import json
import os
import datetime
from typing import Any
import threading

from aworld.utils import import_package
from aworld.replay_buffer.base import DataRow, Experience, ExpMeta
from aworld.logs.util import logger
from aworld.utils.common import get_local_ip


class ReplayBufferExporter:
    def __init__(self):
        """Initialize ReplayBufferExporter instance"""
        self._file_locks = {}
        self._lock_dict_lock = threading.Lock()
        self._task_output_paths = {}

    def _get_file_lock(self, file_path):
        """Get the lock for the specified file"""
        with self._lock_dict_lock:
            if file_path not in self._file_locks:
                self._file_locks[file_path] = threading.Lock()
            return self._file_locks[file_path]

    def replay_buffer_exporter(self, spans: list[dict[str, Any]], output_dir: str):
        """
        Process spans, only process spans with 'step_execution_' prefix, and group by task_id to output to different files

        Args:
            spans: span data list
            output_dir: output directory path
        """
        # Ensure output directory exists
        import_package("oss2")
        import oss2

        os.makedirs(output_dir, exist_ok=True)

        # Get OSS credentials from environment variables
        enable_oss_export = os.getenv("EXPORT_REPLAY_TRACE_TO_OSS", "false").lower() == "true"
        access_key_id = os.getenv('OSS_ACCESS_KEY_ID')
        access_key_secret = os.getenv('OSS_ACCESS_KEY_SECRET')
        endpoint = os.getenv('OSS_ENDPOINT')
        bucket_name = os.getenv('OSS_BUCKET_NAME')
        bucket = None

        if not all([access_key_id, access_key_secret, endpoint, bucket_name]):
            enable_oss_export = False
            logger.warn("Missing required OSS environment variables")
        else:
            try:
                # Initialize OSS client
                auth = oss2.Auth(access_key_id, access_key_secret)
                bucket = oss2.Bucket(auth, endpoint, bucket_name)
            except Exception as e:
                enable_oss_export = False
                logger.warn(f"Failed to initialize OSS client, endpoint: {endpoint}, bucket: {bucket_name}. Error: {str(e)}")

        # Group by task_id
        task_groups = {}

        for span_data in spans:
            # Only process spans with 'step_execution_' prefix
            if not span_data['name'].startswith('step_execution_'):
                continue

            attr = span_data.get('attributes', {})
            exp_id = attr.get('exp_id')
            task_id = attr.get('task_id', '')

            if not exp_id or not task_id:
                continue

            if task_id not in task_groups:
                task_groups[task_id] = {}

            if exp_id not in task_groups[task_id]:
                task_groups[task_id][exp_id] = {
                    'exp_meta': None,
                    'exp_data': None
                }

            # Process step_execution span
            task_name = attr.get('task_name', '')
            agent_id = attr.get('agent_id', '')
            step = attr.get('step', 0)
            execute_time = float(span_data.get('start_time', 0).split('.')[0].replace(' ', '').replace('-', '').replace(':', ''))

            observation = {}
            action = []
            messages = []
            pre_agent = None
            if 'observation' in attr:
                try:
                    observation = json.loads(attr['observation'])
                except:
                    observation = attr['observation']

            if 'actions' in attr:
                try:
                    action = json.loads(attr['actions'])
                except:
                    action = attr['actions']

            if 'messages' in attr:
                try:
                    messages = json.loads(attr['messages'])
                except:
                    messages = attr['messages']

            pre_agent = attr.get('pre_agent', '')
            reward = attr.get('reward', 0.0)
            adv = attr.get('adv_t', 0.0)
            v = attr.get('v_t', 0.0)

            exp_meta = ExpMeta(task_id, task_name, agent_id, step, execute_time, pre_agent)
            exp_data = Experience(observation, action, reward, adv, v, messages)

            task_groups[task_id][exp_id]['exp_meta'] = exp_meta
            task_groups[task_id][exp_id]['exp_data'] = exp_data

        # Process data for each task_id
        for task_id, exp_groups in task_groups.items():
            # Merge data and generate final Experience object
            data_rows = []

            # Read existing data (if any)
            output_path = self._task_output_paths.get(task_id)
            if not output_path:
                timestamp = datetime.datetime.now().strftime("%Y%m%d")
                replay_dir = os.path.join(output_dir or "./trace_data", timestamp, get_local_ip(), "replays")
                replay_dataset_path = os.getenv("REPLAY_TRACE_DATASET_PATH", replay_dir)
                export_dir = os.path.abspath(replay_dataset_path)
                os.makedirs(export_dir, exist_ok=True)
                output_path = os.path.join(export_dir, f"task_replay_{task_id}.json")
                self._task_output_paths[task_id] = output_path

            # Use thread lock to protect read and write operations
            file_lock = self._get_file_lock(output_path)
            with file_lock:
                if os.path.exists(output_path):
                    try:
                        with open(output_path, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                            data_rows.extend([DataRow(
                                ExpMeta(**row['exp_meta']),
                                Experience(**row['exp_data']),
                                row['id']
                            ) for row in existing_data])
                    except Exception as e:
                        print(f"Failed to read existing file {output_path}: {str(e)}")

                # Add new data
                for exp_id, group in exp_groups.items():
                    if group['exp_meta'] and group['exp_data']:
                        row = DataRow(group['exp_meta'], group['exp_data'], exp_id)
                        data_rows.append(row)

                # Sort by execute_time
                data_rows.sort(key=lambda x: x.exp_meta.execute_time)

                # Export to json
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump([row.to_dict() for row in data_rows], f, ensure_ascii=False, indent=2)
                logger.info(f"Processing completed, exported {len(data_rows)} experiences to {output_path}")

                if enable_oss_export:
                    # Upload to OSS
                    try:
                        # Get the relative path
                        abs_path = os.path.abspath(output_path)
                        path_parts = abs_path.split(os.sep)
                        if len(path_parts) >= 4:
                            # Get the last 4 parts of the path
                            relative_path = os.sep.join(path_parts[-4:])
                            oss_key = relative_path
                        else:
                            oss_key = f"replay_buffer/{os.path.basename(output_path)}"
                        bucket.put_object_from_file(oss_key, output_path)
                        logger.info(f"Successfully uploaded {output_path} to OSS: {oss_key}")
                    except Exception as e:
                        logger.warn(f"Failed to upload {output_path} to OSS: {str(e)}")

