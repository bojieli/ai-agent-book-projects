import argparse
import json
import logging
import os
import re
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from pathlib import Path

from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig, TaskConfig
from aworld.core.task import Task
from aworld.runner import Runners
from aworld.core.task import Task
from prompt import system_prompt
from utils import (
    add_file_path,
    load_dataset_meta,
)
from guard_tool_caller import GuardToolCaller

# Create log directory if it doesn't exist
if not os.path.exists(os.getenv("AWORLD_WORKSPACE", "~")):
    os.makedirs(os.getenv("AWORLD_WORKSPACE", "~"))

parser = argparse.ArgumentParser()
parser.add_argument(
    "--q",
    type=str,
    help="Question Index, e.g., imo6. Highest priority: override other arguments if provided.",
)
parser.add_argument(
    "--skip",
    action="store_true",
    help="Skip the question if it has been processed before.",
)
args = parser.parse_args()


def setup_logging():
    logging_logger = logging.getLogger()
    logging_logger.setLevel(logging.INFO)

    log_file_name = f"/solution_{args.q}.log" if args.q else f"/solution.log"
    file_handler = logging.FileHandler(
        os.getenv("AWORLD_WORKSPACE", "~") + log_file_name,
        mode="a",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    logging_logger.addHandler(file_handler)


class GuardRunner:
    """The guard tool runner"""
    
    def __init__(self, super_agent: Agent, guard_tool_caller: GuardToolCaller, original_task: str):
        self.super_agent = super_agent
        self.guard_tool_caller = guard_tool_caller
        self.original_task = original_task
        self.conversation_history = []
        self.max_iterations = 10  # max conversation rounds
        
    async def run_conversation(self, question: str) -> str:
        """run the conversation"""
        current_input = question
        iteration = 0
        
        while iteration < self.max_iterations:
            logging.info(f"=== The {iteration + 1} round of the conversation ===")
            
            # 1. Super-agent handles the current input
            logging.info(f"Super-agent input: {current_input[:100]}...")
            super_output = await self._call_super_agent(current_input)
            logging.info(f"Super-agent output: {super_output[:200]}...")
            
            # 2. Check if the output contains the final answer
            if self._has_final_answer(super_output) and iteration > 1:
                logging.info("find the final answer, the conversation should stop")
                return super_output
            
            if iteration == self.max_iterations - 1: 
                logging.info("reach the max conversation rounds, the conversation should stop and return the final answer")
                return super_output
            
            # 3. Call the guard tool
            logging.info("guard tool is being called...")
            guard_output = await self._call_guard_tool(super_output)
            logging.info(f"guard tool output: {guard_output[:200]}...")
            
            # 4. Record the current round of the conversation history (before preparing the next input)
            self.conversation_history.append({
                "iteration": iteration + 1,
                "super_input": current_input,
                "super_output": super_output,
                "guard_output": guard_output
            })
            
            # 5. Prepare the next input
            next_input = self._prepare_next_input(super_output, guard_output)
            current_input = next_input
            
            iteration += 1
            
            # Check if the conversation should continue
            if self._should_stop_conversation(super_output, guard_output):
                logging.info("the conversation should stop")
                break
        
        logging.info(f"the converstation finished, there are totally {iteration} rounds")
        return super_output
    
    async def _call_super_agent(self, input_text: str) -> str:
        """call the super-agent"""
        try:
            # create the task
            task = Task(
                input=input_text, 
                agent=self.super_agent, 
                conf=TaskConfig()
            )
            
            # run the task
            result = Runners.sync_run_task(task=task)
            
            # extract the answer
            if result and task.id in result:
                return result[task.id].answer
            else:
                return "Super-agent fail to return the result"
                
        except Exception as e:
            logging.error(f"fail to call the super-agent: {e}")
            return f"fail to call the super-agent: {str(e)}"
    
    async def _call_guard_tool(self, super_output: str) -> str:
        """call the guard tool"""
        try:
            # call the guard tool
            guard_result = await self.guard_tool_caller.call_guard_tool(super_output, self.original_task)
            return guard_result
            
        except Exception as e:
            logging.error(f"fail to call the guard tool: {e}")
            return f"fail to call the guard tool: {str(e)}"
    
    def _has_final_answer(self, output: str) -> bool:
        """check if the output contains the final answer"""
        answer_patterns = [
            r"<answer>.*?</answer>",
            r"Final answer[：:]\s*",
            r"final answer[：:]\s*",
            r"The final answer is[：:]\s*",
            r"the final answer is[：:]\s*",
            r"the final answer is\s*",
            r"I have successfully solved the problem."
        ]
        
        for pattern in answer_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return True
        return False
    
    def _prepare_next_input(self, super_output: str, guard_output: str) -> str:
        """Prepare for the next round with complete conversation history"""
        # build the complete conversation history
        conversation_text = ""
        
        # add the original task
        conversation_text += f"Original Task:\n{self.original_task}\n\n"
        
        # add all the history conversation rounds (not including the current round)
        for i, history in enumerate(self.conversation_history):
            round_num = history["iteration"]
            conversation_text += f"=== Round {round_num} ===\n"
            conversation_text += f"Previous solution:\n{history['super_output']}\n\n"
            conversation_text += f"IMO grader review:\n{history['guard_output']}\n\n"
        
        # build the final input
        combined_input = f"""
{conversation_text}
Please seriously consider all the above reviews from the IMO grader across all rounds, and provide a refined and improved solution that addresses all the issues identified.
"""
        return combined_input.strip()
    
    def _should_stop_conversation(self, super_output: str, guard_output: str) -> bool:
        """check if the conversation should stop"""
        # check if the guard tool thinks the conversation should stop
        stop_indicators = [
            "The answer is completed",
            "No need to further refine",
            "The question has been correctly solved",
            "No loopholes or oversights found"
        ]
        
        for indicator in stop_indicators:
            if indicator in guard_output:
                return True
        
        return False


if __name__ == "__main__":
    env_path = ".env"
    load_dotenv(env_path, override=True, verbose=True)
    setup_logging()

    imo_dataset_path = os.getenv("IMO_DATASET_PATH", "./imo_dataset")
    full_dataset = load_dataset_meta(imo_dataset_path)
    logging.info(f"Total questions: {len(full_dataset)}")

    # create the super-agent (without MCP tools)
    agent_config = AgentConfig(
        llm_provider="openai",
        llm_model_name=os.getenv("LLM_MODEL_NAME", "gpt-4o"),
        llm_api_key=os.getenv("LLM_API_KEY"),
        llm_base_url=os.getenv("LLM_BASE_URL"),
        llm_temperature=0.1,
    )
    super_agent = Agent(
        conf=agent_config,
        name="gaia_super_agent",
        system_prompt=system_prompt,
    )

    # create the guard tool caller
    guard_tool_caller = GuardToolCaller()

    # load results from the checkpoint file
    if os.path.exists(os.getenv("AWORLD_WORKSPACE", "~") + "/results.json"):
        with open(os.getenv("AWORLD_WORKSPACE", "~") + "/results.json", "r", encoding="utf-8") as results_f:
            results: List[Dict[str, Any]] = json.load(results_f)
    else:
        results: List[Dict[str, Any]] = []

    try:
        # appoint the task+id
        if args.q is not None:
            dataset_slice = [dataset_record for dataset_record in full_dataset if dataset_record["task_id"] == args.q]
            if not dataset_slice:
                logging.error(f"Task ID '{args.q}' not found in dataset")
                sys.exit()
        else:
            logging.error("Please specify a task_id using --q parameter")
            sys.exit()

        # main loop to execute questions
        for i, dataset_i in enumerate(dataset_slice):
            # run
            try:
                logging.info(f"Start to process: {dataset_i['task_id']}")
                logging.info(f"Question: {dataset_i['Question']}")

                question = add_file_path(dataset_i, file_path=imo_dataset_path)["Question"]

                # use the guard tool runner
                guard_runner = GuardRunner(
                    super_agent=super_agent,
                    guard_tool_caller=guard_tool_caller,
                    original_task=question
                )
                
                # run the conversation
                import asyncio
                result = asyncio.run(guard_runner.run_conversation(question))

                # Create the new result record
                new_result = {
                    "task_id": dataset_i["task_id"],
                    "question": question,
                    "response": result,
                    "conversation_history": guard_runner.conversation_history,
                }

                # Check if this task_id already exists in results
                existing_index = next(
                    (i for i, result in enumerate(results) if result.get("task_id") == dataset_i["task_id"]),
                    None,
                )

                if existing_index is not None:
                    # Update existing record
                    results[existing_index] = new_result
                    logging.info(f"Updated existing record for task_id: {dataset_i['task_id']}")
                else:
                    # Append new record
                    results.append(new_result)
                    logging.info(f"Added new record for task_id: {dataset_i['task_id']}")

            except Exception:
                logging.error(f"Error processing {i}: {traceback.format_exc()}")
                continue
    except KeyboardInterrupt:
        pass
    finally:
        # Save results to file
        with open(os.getenv("AWORLD_WORKSPACE", "~") + "/results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False) 
