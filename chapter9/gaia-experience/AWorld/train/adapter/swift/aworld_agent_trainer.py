# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import abc
import asyncio
import json
import re
from typing import List, Optional, Dict, Any, Union

from aworld.agents.llm_agent import Agent
from aworld.core.agent.swarm import Swarm
from aworld.core.task import TaskResponse
from aworld.runner import Runners
from aworld.utils.common import sync_exec
from swift.llm import RequestConfig
from swift.llm.infer.protocol import ChatCompletionResponse
from swift.trainers.rlhf_trainer.grpo_trainer import InputsType, GRPOTrainer, logger
from transformers import AutoTokenizer
from trl.extras.profiling import profiling_context


class AworldTrainer(GRPOTrainer):
    def _engine_infer(
            self,
            infer_requests: InputsType,
            request_config: Optional[RequestConfig] = None,
            *,
            use_tqdm: Optional[bool] = False,
    ) -> List[ChatCompletionResponse]:
        with profiling_context(self, 'generate'):
            if self.vllm_mode != 'server':
                return self.engine.infer(infer_requests, request_config, use_tqdm=use_tqdm)

            request_keys = ['messages', 'images', 'audios', 'videos', 'tools', 'objects']

            infer_requests = [{
                **{k: request[k]
                   for k in request_keys if k in request},
                **({
                       'data_dict': {k: request[k]
                                     for k in request if k not in request_keys}
                   } if self.multi_turn_scheduler and self.vllm_use_async_engine else {})
            } for request in infer_requests]

            self._process_infer_requests_images(infer_requests)
            return self.run_infer(infer_requests)

    def run_infer(self, infer_requests: List[Dict[str, Any]]) -> List[ChatCompletionResponse]:
        workers = [asyncio.create_task(self._rollout(req)) for req in infer_requests]
        results = sync_exec(asyncio.gather, *workers)
        return self.convert_agent_output(results, infer_requests)

    async def _rollout(self, req: Dict[str, Any]):
        agent = self.build_agents()
        result = await self.run_agents(req, agent)
        return result

    @abc.abstractmethod
    def build_agents(self) -> Union[Agent, Swarm]:
        """Build single- or multi-agent"""

    async def run_agents(self, input, agent):
        # collect trajectory
        if isinstance(agent, Swarm):
            result = Runners.sync_run(input=input, swarm=agent)
        else:
            result = Runners.sync_run(input=input, agent=agent)
        return result

    def convert_agent_output(self,
                             results: List[TaskResponse],
                             infer_requests: List[Dict[str, Any]]) -> List[ChatCompletionResponse]:
        message_final_merge = []
        for result in results:
            trajectory = result.trajectory
            last_exp_data = trajectory[-1]['exp_data']
            task_id = trajectory[0]['exp_meta']['task_id'].split('_')[1]
            message_final = []
            message = last_exp_data["messages"]
            answer_flag = 0

            for i in range(len(message)):
                actions = last_exp_data.get('actions', [])
                if actions:
                    actions_str = json.dumps(actions)
                    if '<answer>' in actions_str and '</answer>' in actions_str:
                        match = re.search(r'<answer>(.*?)</answer>', actions_str, re.DOTALL)
                        if match:
                            answer_flag = 1
                            logger.info(f"{task_id} answer content: {match.group(1)}")
                        else:
                            logger.warning(f"{task_id} no answer content found.")

                if message[i]["role"] in ["system", "user"]:
                    message_final.append(
                        {
                            "role": message[i]["role"],
                            "content": message[i]["content"],
                        }
                    )
                elif message[i]["role"] == "assistant" and "tool_calls" in message[i].keys():
                    if message[i]["tool_calls"][0]["function"]["arguments"]:
                        arguments = json.loads(message[i]["tool_calls"][0]["function"]["arguments"])
                    else:
                        arguments = ""
                    function_call = {
                        "name": message[i]["tool_calls"][0]["function"]["name"],
                        "arguments": arguments
                    }
                    if message[i]["content"] != "" and message[i]["content"] is not None:
                        message_final.append(
                            {
                                "role": "assistant",
                                "content": message[i]["content"],
                            }
                        )
                    message_final.append(
                        {
                            "role": "tool_call",
                            "content": json.dumps(function_call, ensure_ascii=False),
                        }
                    )
                elif message[i]["role"] == "tool":
                    last_content = message[i - 1]["content"]
                    if last_content is None:
                        last_content = ""
                    message_final.append(
                        {
                            "role": "tool",
                            "content": message[i]["content"].replace(last_content, ""),
                        }
                    )
                else:
                    logger.warning(f"Unknown message role: {message[i]['role']}")

            tokenizer = AutoTokenizer.from_pretrained(self.args.model_init_kwargs)
            try:
                response = last_exp_data["actions"][0]["policy_info"]
                if response:
                    message_final.append(
                        {
                            "role": "assistant",
                            "content": response
                        }
                    )
                else:
                    message_final.append(
                        {
                            "role": "assistant",
                            "content": "No response was received. Please try again later."
                        }
                    )
                message_final = truncate_messages_fast(message_final, tokenizer)

                status = "success" if answer_flag == 1 else "length"
                message_final_merge.append((message_final, status, task_id))
            except:
                message_final.append({
                    "role": "assistant",
                    "content": "No response was received. Please try again later."
                })
                message_final = truncate_messages_fast(message_final, tokenizer)
                message_final_merge.append((message_final, "length", task_id))

        return self.pad_list_to_length(message_final_merge, infer_requests)

    def pad_list_to_length(self, message_final_merge, infer_requests) -> List[ChatCompletionResponse]:
        unique_task_ids = []
        for msg in message_final_merge:
            task_id = msg[2]
            if task_id not in unique_task_ids:
                unique_task_ids.append(task_id)
        # Group by task_id
        task_groups = {task_id: [] for task_id in unique_task_ids}
        for item in message_final_merge:
            messages, status, task_id = item
            if task_id in task_groups:
                task_groups[task_id].append(item)

        # Ensure each group has exactly num_generations samples
        for task_id in unique_task_ids:
            # If this task_id has no samples, construct fallback data
            if len(task_groups[task_id]) == 0:
                for _infer_request in infer_requests:
                    # Check if the first message content matches the task_id
                    if task_id == _infer_request["messages"][0]["content"]:
                        fallback_completion = {
                            "role": "assistant",
                            "content": "No response was received. Please try again later."
                        }
                        new_messages = _infer_request["messages"].copy()[1:]
                        new_messages.append(fallback_completion)
                        task_groups[task_id].append((new_messages, "length", task_id))

                        break

            # # Ensure we have exactly num_generations samples
            # while len(task_groups[task_id]) < num_generations/len(unique_task_ids):
            #     success_samples = [item for item in task_groups[task_id] if item[1] == "success"]
            #     if success_samples:
            #         task_groups[task_id].append(random.choice(success_samples))
            #     else:
            #         task_groups[task_id].append(random.choice(task_groups[task_id]))

            num_generations = len(infer_requests)
            current_count = len(task_groups[task_id])
            if current_count >= num_generations / len(unique_task_ids):
                continue

            # Get success samples if available, otherwise use all samples
            success_samples = [item for item in task_groups[task_id] if item[1] == "success"]
            samples_to_cycle = success_samples if success_samples else task_groups[task_id]

            # Calculate how many more we need
            needed = int(num_generations / len(unique_task_ids)) - current_count

            # Add samples in a cycling manner
            for i in range(int(needed)):
                task_groups[task_id].append(samples_to_cycle[i % len(samples_to_cycle)])

        # Combine all groups and convert back to 2-tuples for final output
        final_result = []
        for task_id in unique_task_ids:
            for item in task_groups[task_id]:
                messages, status, _ = item
                final_result.append((messages, status))

        return final_result


def truncate_messages_fast(
        messages: List[Dict[str, Any]],
        tokenizer: Any,
        max_length: int = 131072,
        tools: Optional[List] = None
) -> List[Dict[str, Any]]:
    """Simplifies message list truncation by removing entire messages from the end
    to fit within max_length, with a final role check.

    Core Logic:
    1.  First, removes messages from the end of the list one by one until the
        total token count is within `max_length`.
    2.  After ensuring the length is acceptable, it performs a final check on the
        last remaining message.
    3.  If the last message's role is not 'assistant' or 'tool_call', it is
        also removed. This check is repeated until the last message has a valid
        role or the list becomes empty.
    4.  This function does not partially truncate message content.

    Args:
        messages (List[Dict[str, Any]]): A list of message dictionaries.
        tokenizer: The tokenizer instance to calculate token count.
        max_length (int, optional): The target maximum number of tokens. Defaults to 131072.
        tools (Optional[List], optional): A list of tools that might be needed when applying
                                          the chat template. Defaults to None.

    Returns:
        List[Dict[str, Any]]: The truncated list of messages.
    """
    truncated_messages = list(messages)

    def get_current_tokens(msgs: List[Dict[str, Any]]) -> int:
        if not msgs:
            return 0
        # The return value of apply_chat_template can be a list of token IDs or a string
        # We use len() to get the count, which works for both cases.
        return len(tokenizer.apply_chat_template(msgs, tools=tools, add_generation_prompt=False))

    # 1. Truncate from the end based on length
    # The `and truncated_messages` ensures we don't pop from an empty list
    while get_current_tokens(truncated_messages) > max_length and truncated_messages:
        truncated_messages.pop()  # pop() removes the last item

    # 2. Ensure the last remaining message has a valid role ('assistant' or 'tool_call')
    # This loop handles cases where multiple invalid messages are at the end (e.g., ..., tool, user)
    while truncated_messages:
        last_message_role = truncated_messages[-1].get("role")
        if last_message_role in ('assistant', 'tool_call'):
            # The last message is valid, so we are done.
            break
        else:
            # The last message is not of the required role, remove it and check again.
            truncated_messages.pop()

    return truncated_messages
