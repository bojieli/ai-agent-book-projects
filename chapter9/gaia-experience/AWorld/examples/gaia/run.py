import argparse
import json
import logging
import os
import re
import traceback
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

from aworld.agents.llm_agent import Agent
from aworld.config.conf import AgentConfig, TaskConfig
from aworld.core.task import Task
from aworld.runner import Runners
from aworld.core.task import Task
from examples.gaia.prompt import system_prompt
from examples.gaia.utils import (
    add_file_path,
    load_dataset_meta,
    question_scorer,
    report_results,
)

# Create log directory if it doesn't exist
if not os.path.exists(os.getenv("AWORLD_WORKSPACE", "~")):
    os.makedirs(os.getenv("AWORLD_WORKSPACE", "~"))

parser = argparse.ArgumentParser()
parser.add_argument(
    "--start",
    type=int,
    default=0,
    help="Start index of the dataset",
)
parser.add_argument(
    "--end",
    type=int,
    default=20,
    help="End index of the dataset",
)
parser.add_argument(
    "--q",
    type=str,
    help="Question Index, e.g., 0-0-0-0-0. Highest priority: override other arguments if provided.",
)
parser.add_argument(
    "--skip",
    action="store_true",
    help="Skip the question if it has been processed before.",
)
parser.add_argument(
    "--split",
    type=str,
    default="validation",
    help="Split of the dataset, e.g., validation, test",
)
parser.add_argument(
    "--blacklist_file_path",
    type=str,
    nargs="?",
    help="Blacklist file path, e.g., blacklist.txt",
)
args = parser.parse_args()


def setup_logging():
    logging_logger = logging.getLogger()
    logging_logger.setLevel(logging.INFO)

    log_file_name = f"/super_agent_{args.q}.log" if args.q else f"/super_agent_{args.start}_{args.end}.log"
    file_handler = logging.FileHandler(
        os.getenv("AWORLD_WORKSPACE", "~") + log_file_name,
        mode="a",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    logging_logger.addHandler(file_handler)


if __name__ == "__main__":
    load_dotenv()
    setup_logging()

    gaia_dataset_path = os.getenv("GAIA_DATASET_PATH", "./gaia_dataset")
    full_dataset = load_dataset_meta(gaia_dataset_path, split=args.split)
    logging.info(f"Total questions: {len(full_dataset)}")

    try:
        with open(Path(__file__).parent / "mcp.json", mode="r", encoding="utf-8") as f:
            mcp_config: dict[dict[str, Any]] = json.loads(f.read())
            available_servers: list[str] = list(server_name for server_name in mcp_config.get("mcpServers", {}).keys())
            logging.info(f"🔧 MCP Available Servers: {available_servers}")
    except json.JSONDecodeError as e:
        logging.error(f"Error loading mcp_collections.json: {e}")
        mcp_config = {}

    agent_config = AgentConfig(
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        llm_model_name=os.getenv("LLM_MODEL_NAME", "gpt-4o"),
        llm_base_url=os.getenv("LLM_BASE_URL"),
        llm_api_key=os.getenv("LLM_API_KEY"),
        llm_temperature=os.getenv("LLM_TEMPERATURE", 0.0)
    )
    super_agent = Agent(
        conf=agent_config,
        name="gaia_super_agent",
        system_prompt=system_prompt,
        mcp_config=mcp_config,
        mcp_servers=available_servers,
    )

    # load results from the checkpoint file
    if os.path.exists(os.getenv("AWORLD_WORKSPACE", "~") + "/results.json"):
        with open(os.getenv("AWORLD_WORKSPACE", "~") + "/results.json", "r", encoding="utf-8") as results_f:
            results: List[Dict[str, Any]] = json.load(results_f)
    else:
        results: List[Dict[str, Any]] = []

    # load blacklist `task_id`
    if args.blacklist_file_path and os.path.exists(args.blacklist_file_path):
        with open(args.blacklist_file_path, "r", encoding="utf-8") as f:
            blacklist = set(f.read().splitlines())
    else:
        blacklist = set()  # Empty set if file doesn't exist

    try:
        # slice dataset by args.start and args.end, overrided by args.q (single `task_id`)
        dataset_slice = (
            [dataset_record for idx, dataset_record in enumerate(full_dataset) if dataset_record["task_id"] in args.q]
            if args.q is not None
            else full_dataset[args.start : args.end]
        )

        # main loop to execute questions
        for i, dataset_i in enumerate(dataset_slice):
            # specify `task_id`
            if args.q and args.q != dataset_i["task_id"]:
                continue
            # only valid for args.q==None
            if not args.q:
                # blacklist
                if dataset_i["task_id"] in blacklist:
                    continue

                # pass
                if any(
                    # Question Done and Correct
                    (result["task_id"] == dataset_i["task_id"] and result["is_correct"])
                    for result in results
                ) or any(
                    # Question Done and Incorrect, but Level is 3
                    (result["task_id"] == dataset_i["task_id"] and not result["is_correct"] and dataset_i["Level"] == 3)
                    for result in results
                ):
                    continue

                # skip
                if args.skip and any(
                    # Question Done and Correct
                    (result["task_id"] == dataset_i["task_id"])
                    for result in results
                ):
                    continue

            # run
            try:
                logging.info(f"Start to process: {dataset_i['task_id']}")
                logging.info(f"Detail: {dataset_i}")
                logging.info(f"Question: {dataset_i['Question']}")
                logging.info(f"Level: {dataset_i['Level']}")
                logging.info(f"Tools: {dataset_i['Annotator Metadata']['Tools']}")

                question = add_file_path(dataset_i, file_path=gaia_dataset_path, split=args.split)["Question"]

                task = Task(input=question, agent=super_agent, conf=TaskConfig())
                result = Runners.sync_run_task(task=task)

                match = re.search(r"<answer>(.*?)</answer>", result[task.id].answer)
                if match:
                    answer = match.group(1)
                    logging.info(f"Agent answer: {answer}")
                    logging.info(f"Correct answer: {dataset_i['Final answer']}")

                    if question_scorer(answer, dataset_i["Final answer"]):
                        logging.info(f"Question {i} Correct!")
                    else:
                        logging.info("Incorrect!")

                # Create the new result record
                new_result = {
                    "task_id": dataset_i["task_id"],
                    "level": dataset_i["Level"],
                    "question": question,
                    "answer": dataset_i["Final answer"],
                    "response": answer,
                    "is_correct": question_scorer(answer, dataset_i["Final answer"]),
                }

                # Check if this task_id already exists in results
                existing_index = next(
                    (i for i, result in enumerate(results) if result["task_id"] == dataset_i["task_id"]),
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
        # report
        report_results(results)
        with open(os.getenv("AWORLD_WORKSPACE", "~") + "/results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
