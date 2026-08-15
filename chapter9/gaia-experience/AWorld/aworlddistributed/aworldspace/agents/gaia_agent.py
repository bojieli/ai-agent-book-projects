import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from aworld.config import ModelConfig
from aworld.config.conf import AgentConfig, TaskConfig, ClientType
from aworld.core.task import Task
from aworld.output import Outputs, Output, StreamingOutputs
from aworld.utils.common import get_local_ip
from datasets import load_dataset, concatenate_datasets
from pydantic import BaseModel, Field

from aworldspace.base_agent import AworldBaseAgent
from aworldspace.utils.mcp_utils import load_all_mcp_config
from aworldspace.utils.utils import question_scorer

GAIA_SYSTEM_PROMPT = f"""You are an all-capable AI assistant, aimed at solving any task presented by the user. You have various tools at your disposal that you can call upon to efficiently complete complex requests. Whether it's programming, information retrieval, file processing, or web browsing, you can handle it all.
Please note that the task may be complex. Do not attempt to solve it all at once. You should break the task down and use different tools step by step to solve it. After using each tool, clearly explain the execution results and suggest the next steps.
Please utilize appropriate tools for the task, analyze the results obtained from these tools, and provide your reasoning. Always use available tools such as browser, calcutor, etc. to verify correctness rather than relying on your internal knowledge.
If you believe the problem has been solved, please output the `final answer`. The `final answer` should be given in <answer></answer> format, while your other thought process should be output in <think></think> tags.
Your `final answer` should be a number OR as few words as possible OR a comma separated list of numbers and/or strings. If you are asked for a number, don't use comma to write your number neither use units such as $ or percent sign unless specified otherwise. If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities), and write the digits in plain text unless specified otherwise. If you are asked for a comma separated list, apply the above rules depending of whether the element to be put in the list is a number or a string.

Here are some tips to help you give better instructions: 
<tips>
1. Do not use any tools outside of the provided tools list.
2. Even if the task is complex, there is always a solution. If you can’t find the answer using one method, try another approach or use different tools to find the solution.
3. When using browser `playwright_click` tool, you need to check if the element exists and is clickable before clicking it. 
4. Before providing the `final answer`, carefully reflect on whether the task has been fully solved. If you have not solved the task, please provide your reasoning and suggest the next steps.
5. Due to context length limitations, always try to complete browser-based tasks with the minimal number of steps possible.
6. When providing the `final answer`, answer the user's question directly and precisely. For example, if asked "what animal is x?" and x is a monkey, simply answer "monkey" rather than "x is a monkey".
7. When you need to process excel file, prioritize using the `excel` tool instead of writing custom code with `terminal-controller` tool.
8. If you need to download a file, please use the `terminal-controller` tool to download the file and save it to the specified path.
9. The browser doesn't support direct searching on www.google.com. Use the `google-search` to get the relevant website URLs or contents instead of `ms-playwright` directly.
10. Always use only one tool at a time in each step of your execution.
11. Using `mcp__ms-playwright__browser_pdf_save` tool to save the pdf file of URLs to the specified path.
12. Using `mcp__terminal-controller__execute_command` tool to set the timeout to 300 seconds when downloading large files such as pdf.
13. Using `mcp__ms-playwright__browser_take_screenshot` tool to save the screenshot of URLs to the specified path when you need to understand the gif / jpg of the URLs.
14. When there are questions related to YouTube video comprehension, use tools in `youtube_download_server` and `video_server` to analyze the video content by the given question.
</tips>

Now, here is the task. Stay focused and complete it carefully using the appropriate tools!
"""

class Pipeline(AworldBaseAgent):
    class Valves(BaseModel):
        llm_provider: Optional[str] = Field(default=None, description="llm_model_name")
        llm_model_name: Optional[str] = Field(default=None, description="llm_model_name")
        llm_base_url: Optional[str] = Field(default=None,description="llm_base_urly")
        llm_api_key: Optional[str] = Field(default=None,description="llm api key" )
        system_prompt: str = Field(default=GAIA_SYSTEM_PROMPT,description="system_prompt")
        history_messages: int = Field(default=100, description="rounds of history messages")

    def __init__(self):
        self.valves = self.Valves()
        self.gaia_files = os.path.abspath(os.path.join(os.path.curdir, "aworldspace", "datasets", "gaia_dataset"))
        logging.info(f"gaia_files path {self.gaia_files}")
        self.full_dataset = load_dataset(
            os.path.join(self.gaia_files, "GAIA.py"),
            name="2023_all",
            trust_remote_code=True
        )
        self.full_dataset = concatenate_datasets([self.full_dataset['validation'], self.full_dataset['test']])
        
        # Create task_id to index mapping for improved lookup performance
        self.task_id_to_index = {}
        for i, task in enumerate(self.full_dataset):
            self.task_id_to_index[task['task_id']] = i
        
        logging.info(f"Loaded {len(self.full_dataset)} tasks, created task_id mapping")
        logging.info("gaia_agent init success")

    async def get_custom_input(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> Any:
        task = await self.get_gaia_task(user_message)
        logging.info(f"🌈 -----------------------------------------------")
        logging.info(f"🚀 Start to process: gaia_task_{task['task_id']}")
        logging.info(f"📝 Detail: {task}")
        logging.info(f"❓ Question: {task['Question']}")
        logging.info(f"⭐ Level: {task['Level']}")
        logging.info(f"🛠️ Tools: {task['Annotator Metadata']['Tools']}")
        logging.info(f"🌈 -----------------------------------------------")
        return task['Question']

    async def get_agent_config(self, body):
        default_llm_provider = self.valves.llm_provider if self.valves.llm_provider else os.environ.get("LLM_PROVIDER")
        llm_model_name = self.valves.llm_model_name if self.valves.llm_model_name else os.environ.get("LLM_MODEL_NAME")
        llm_api_key = self.valves.llm_api_key if self.valves.llm_api_key else os.environ.get("LLM_API_KEY")
        llm_base_url = self.valves.llm_base_url if self.valves.llm_base_url else os.environ.get("LLM_BASE_URL")
        system_prompt = self.valves.system_prompt if self.valves.system_prompt else GAIA_SYSTEM_PROMPT

        task = await self.get_task_from_body(body)
        if task:
            logging.info(f"task llm config is: {task.llm_provider}, {task.llm_model_name}, {task.llm_api_key}, {task.llm_base_url}")

        llm_config = ModelConfig(
            llm_provider=task.llm_provider if task and task.llm_provider else default_llm_provider,
            llm_model_name=task.llm_model_name if task and task.llm_model_name else llm_model_name,
            llm_api_key=task.llm_api_key if task and task.llm_api_key else llm_api_key,
            llm_base_url=task.llm_base_url if task and task.llm_base_url else llm_base_url,
            max_retries=task.max_retries if task and task.max_retries else 3
        )

        return AgentConfig(
            name=self.agent_name(),
            llm_config=llm_config,
            system_prompt=task.task_system_prompt if task and task.task_system_prompt else system_prompt
        )

    def agent_name(self) -> str:
        return "GaiaAgent"

    async def get_mcp_servers(self, body) -> list[str]:
        task = await self.get_task_from_body(body)
        if task and task.mcp_servers:
            logging.info(f"mcp_servers from task: {task.mcp_servers}")
            return task.mcp_servers

        return [
            "e2b-server",
            "terminal-controller",
            "excel",
            "calculator",
            "ms-playwright",
            "audio_server",
            "image_server",
            "video_server",
            "search_server",
            "download_server",
            "document_server",
            "youtube_server",
            "reasoning_server",
        ]

    async def get_gaia_task(self, task_id: str) -> dict:
        """
        Get GAIA task by task_id
        Args:
            task_id: Unique identifier of the task
        Returns:
            Corresponding task dictionary
        """

        # Search by task_id
        if task_id in self.task_id_to_index:
            index = self.task_id_to_index[task_id]
            gaia_task = self.full_dataset[index]
        else:
            raise ValueError(f"Task with task_id '{task_id}' not found in dataset")

        return self.add_file_path(gaia_task)

    def get_all_task_ids(self) -> List[str]:
        """
        Get list of all available task_ids
        Returns:
            List of all task_ids
        """
        return list(self.task_id_to_index.keys())
    
    def get_task_count(self) -> int:
        """
        Get total number of tasks
        Returns:
            Total task count
        """
        return len(self.full_dataset)
    
    def get_task_index_by_id(self, task_id: str) -> int:
        """
        Get task index in dataset by task_id
        Args:
            task_id: Unique identifier of the task
        Returns:
            Index of the task in the dataset
        """
        if task_id in self.task_id_to_index:
            return self.task_id_to_index[task_id]
        else:
            raise ValueError(f"Task with task_id '{task_id}' not found in dataset")

    async def custom_output_before_task(self, outputs: Outputs, chat_id: str, task: Task) -> None:
        task_config:TaskConfig = task.conf
        gaia_task = await self.get_gaia_task(task_config.ext['origin_message'])

        result = f"\n\n`{get_local_ip()}` execute `GAIA TASK#{task_config.ext['origin_message']}`:\n\n---\n\n"
        result += f"**Question**: {gaia_task['Question']}\n"
        result += f"**Answer**: {gaia_task['Final answer']}\n"
        result += f"**Level**: {gaia_task['Level']}\n"
        result += f"**Tools**: \n {gaia_task['Annotator Metadata']['Tools']}\n"
        result += f"\n\n-----\n\n"
        await outputs.add_output(Output(data = result))

    async def custom_output_after_task(self, outputs: Outputs, chat_id: str, task: Task):
        """
        check gaia task output
        Args:
            outputs:
            chat_id:
            task:

        Returns:

        """
        task_config: TaskConfig = task.conf
        gaia_task_id = task_config['ext']['origin_message']
        gaia_task = await self.get_gaia_task(gaia_task_id)
        agent_result = ""
        if isinstance(outputs, StreamingOutputs):
            agent_result = await outputs._visited_outputs[-2].get_finished_response() # read llm result
        match = re.search(r"<answer>(.*?)</answer>", agent_result)
        answer = agent_result
        if match:
            answer = match.group(1)

        logging.info(f"🤖 Agent answer: {answer}")
        logging.info(f"👨‍🏫 Correct answer: {gaia_task['Final answer']}")
        is_correct = question_scorer(answer, gaia_task["Final answer"])

        if is_correct:
            logging.info(f"📝Question {gaia_task_id} Correct! 🎉")
            result = f"\n\n📝 **Question: {gaia_task_id} -> Agent Answer:[{answer}] is `Correct`**"
        else:
            logging.info(f"📝Question {gaia_task_id} Incorrect! ❌")
            result = f"\n\n📝 **Question: {gaia_task_id} -> Agent Answer:`{answer}` != Correct answer: `{gaia_task['Final answer']}` is `Incorrect` ❌**"

        metadata = await outputs.get_metadata()
        if not metadata:
            await outputs.set_metadata({})
            metadata = await outputs.get_metadata()
        metadata['gaia_correct'] = is_correct
        metadata['gaia_result'] = result
        metadata['agent_answer'] = answer
        metadata['correct_answer'] = gaia_task['Final answer']
        return result



    def add_file_path(self, task: Dict[str, Any]
                      ):
        split = "validation" if task["Annotator Metadata"]["Steps"] != "" else "test"

        if task["file_name"]:
            file_path = Path(f"{self.gaia_files}/2023/{split}/" + task["file_name"])
            if file_path.suffix in [".pdf", ".docx", ".doc", ".txt"]:
                task["Question"] += f" Here are the necessary document files: {file_path}"

            elif file_path.suffix in [".jpg", ".jpeg", ".png"]:
                task["Question"] += f" Here are the necessary image files: {file_path}"

            elif file_path.suffix in [".xlsx", "xls", ".csv"]:
                task[
                    "Question"
                ] += f" Here are the necessary table files: {file_path}, for processing excel file, you can use the excel tool or write python code to process the file step-by-step and get the information."

            elif file_path.suffix in [".py"]:
                task["Question"] += f" Here are the necessary python files: {file_path}"

            else:
                task["Question"] += f" Here are the necessary files: {file_path}"

        return task
    async def load_mcp_config(self) -> dict:
        return load_all_mcp_config()