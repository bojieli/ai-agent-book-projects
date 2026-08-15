import logging
import os
from datetime import datetime

from aworld.models.model_response import ModelResponse

from base import AworldTask, AworldTaskResult
from config import ROOT_LOG


class TaskLogger:
    """任务提交日志记录器"""

    def __init__(self, log_file: str = "aworld_task_submissions.log"):
        self.log_file = os.path.join(ROOT_LOG, 'task_logs' , log_file)
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self):
        """确保日志文件存在"""
        if not os.path.exists(self.log_file):
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("# Aworld Task Submission Log\n")
                f.write(
                    "# Format: [timestamp] task_id | agent_id | server | status | agent_answer | correct_answer | is_correct | details\n\n")

    def log_task_submission(self, task: AworldTask, status: str, details: str = "",
                            task_result: AworldTaskResult = None):
        """记录任务提交日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {task.task_id} | {task.agent_id} | {task.node_id} | {status} | {task_result.data.get('agent_answer') if task_result and task_result.data else None} | {task_result.data.get('correct_answer') if task_result and task_result.data else None} | {task_result.data.get('gaia_correct') if task_result and task_result.data else None} |{details}\n"

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            logging.error(f"Failed to write task submission log: {e}")

    def log_task_result(self, task: AworldTask, result: ModelResponse):
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            result_dir = os.path.join(ROOT_LOG, 'task_logs', 'result', date_str)
            os.makedirs(result_dir, exist_ok=True)

            md_file = f"{result_dir}/{task.task_id}.md"

            content_parts = []
            if hasattr(result, 'content') and result.content:
                if isinstance(result.content, list):
                    content_parts.extend(result.content)
                else:
                    content_parts.append(str(result.content))

            file_exists = os.path.exists(md_file)
            with open(md_file, 'a', encoding='utf-8') as f:
                if not file_exists:
                    f.write(f"# Task Result: {task.task_id}\n\n")
                    f.write(f"**Agent ID:** {task.agent_id}\n\n")
                    f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("## Content\n\n")

                if content_parts:
                    for i, content in enumerate(content_parts, 1):
                        f.write(f"{content}\n\n")
                else:
                    f.write("No content available.\n\n")

            return md_file

        except Exception as e:
            logging.error(f"Failed to write task result log: {e}")
            return None


task_logger = TaskLogger(log_file=f"aworld_task_submissions_{datetime.now().strftime('%Y%m%d')}.log")
