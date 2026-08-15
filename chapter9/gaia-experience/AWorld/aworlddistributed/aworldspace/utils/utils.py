import json
import re
import string
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from tabulate import tabulate


def normalize_str(input_str, remove_punct=True) -> str:
    no_spaces = re.sub(r"\s", "", input_str)
    if remove_punct:
        translator = str.maketrans("", "", string.punctuation)
        return no_spaces.lower().translate(translator)
    else:
        return no_spaces.lower()


def split_string(s: str, char_list: Optional[List[str]] = None) -> list[str]:
    if char_list is None:
        char_list = [",", ";"]
    pattern = f"[{''.join(char_list)}]"
    return re.split(pattern, s)


def normalize_number_str(number_str: str) -> float:
    for char in ["$", "%", ","]:
        number_str = number_str.replace(char, "")
    try:
        return float(number_str)
    except ValueError:
        logger.error(f"String {number_str} cannot be normalized to number str.")
        return float("inf")


def question_scorer(model_answer: str, ground_truth: str) -> bool:
    def is_float(element: Any) -> bool:
        try:
            float(element)
            return True
        except ValueError:
            return False

    try:
        if is_float(ground_truth):
            logger.info(f"Evaluating {model_answer} as a number.")
            normalized_answer = normalize_number_str(model_answer)
            return normalized_answer == float(ground_truth)

        elif any(char in ground_truth for char in [",", ";"]):
            logger.info(f"Evaluating {model_answer} as a comma separated list.")
            gt_elems = split_string(ground_truth)
            ma_elems = split_string(model_answer)

            if len(gt_elems) != len(ma_elems):
                logger.warning("Answer lists have different lengths, returning False.")
                return False

            comparisons = []
            for ma_elem, gt_elem in zip(ma_elems, gt_elems):
                if is_float(gt_elem):
                    normalized_ma_elem = normalize_number_str(ma_elem)
                    comparisons.append(normalized_ma_elem == float(gt_elem))
                else:
                    ma_elem = normalize_str(ma_elem, remove_punct=False)
                    gt_elem = normalize_str(gt_elem, remove_punct=False)
                    comparisons.append(ma_elem == gt_elem)
            return all(comparisons)
        else:
            logger.info(f"Evaluating {model_answer} as a string.")
            ma_elem = normalize_str(model_answer)
            gt_elem = normalize_str(ground_truth)
            return ma_elem == gt_elem
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        return False


def load_dataset_meta(path: str, split: str = "validation"):
    data_dir = Path(path) / split

    dataset = []
    with open(data_dir / "metadata.jsonl", "r", encoding="utf-8") as metaf:
        lines = metaf.readlines()
        for line in lines:
            data = json.loads(line)
            if data["task_id"] == "0-0-0-0-0":
                continue
            if data["file_name"]:
                data["file_name"] = data_dir / data["file_name"]
            dataset.append(data)
    return dataset


def load_dataset_meta_dict(path: str, split: str = "validation"):
    data_dir = Path(path) / split

    dataset = {}
    with open(data_dir / "metadata.jsonl", "r", encoding="utf-8") as metaf:
        lines = metaf.readlines()
        for line in lines:
            data = json.loads(line)
            if data["task_id"] == "0-0-0-0-0":
                continue
            if data["file_name"]:
                data["file_name"] = data_dir / data["file_name"]
            dataset[data["task_id"]] = data
    return dataset


def add_file_path(
    task: Dict[str, Any], file_path: str = "./gaia_dataset", split: str = "validation"
):
    if task["file_name"]:
        file_path = Path(f"{file_path}/{split}") / task["file_name"]
        if file_path.suffix in [".pdf", ".docx", ".doc", ".txt"]:
            task["Question"] += f" Here are the necessary document files: {file_path}"

        elif file_path.suffix in [".jpg", ".jpeg", ".png"]:
            task["Question"] += f" Here are the necessary image files: {file_path}"

        elif file_path.suffix in [".xlsx", "xls", ".csv"]:
            task["Question"] += (
                f" Here are the necessary table files: {file_path}, for processing excel file,"
                " you can use the excel tool or write python code to process the file"
                " step-by-step and get the information."
            )
        elif file_path.suffix in [".py"]:
            task["Question"] += f" Here are the necessary python files: {file_path}"

        else:
            task["Question"] += f" Here are the necessary files: {file_path}"

    return task


def report_results(entries):
    # Initialize counters
    total_entries = len(entries)
    total_correct = 0

    # Initialize level statistics
    level_stats = {}

    # Process each entry
    for entry in entries:
        level = entry.get("level")
        is_correct = entry.get("is_correct", False)

        # Initialize level stats if not already present
        if level not in level_stats:
            level_stats[level] = {"total": 0, "correct": 0, "accuracy": 0}

        # Update counters
        level_stats[level]["total"] += 1
        if is_correct:
            total_correct += 1
            level_stats[level]["correct"] += 1

    # Calculate accuracy for each level
    for level, stats in level_stats.items():
        if stats["total"] > 0:
            stats["accuracy"] = (stats["correct"] / stats["total"]) * 100

    # Print overall statistics with colorful logging
    logger.info("Overall Statistics:")
    overall_accuracy = (total_correct / total_entries) * 100

    # Create overall statistics table
    overall_table = [
        ["Total Entries", total_entries],
        ["Total Correct", total_correct],
        ["Overall Accuracy", f"{overall_accuracy:.2f}%"],
    ]
    logger.success(tabulate(overall_table, tablefmt="grid"))
    logger.info("")

    # Create level statistics table
    logger.info("Statistics by Level:")
    level_table = []
    headers = ["Level", "Total Entries", "Correct Answers", "Accuracy"]

    for level in sorted(level_stats.keys()):
        stats = level_stats[level]
        level_table.append(
            [level, stats["total"], stats["correct"], f"{stats['accuracy']:.2f}%"]
        )

    logger.success(tabulate(level_table, headers=headers, tablefmt="grid"))


import uuid
import time

from typing import List

import inspect
from typing import get_type_hints, Tuple


def stream_message_template(model: str, message: str):
    return {
        "id": f"{model}-{str(uuid.uuid4())}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {"content": message},
                "logprobs": None,
                "finish_reason": None,
            }
        ],
    }


def get_last_user_message(messages: List[dict]) -> str:
    for message in reversed(messages):
        if message["role"] == "user":
            if isinstance(message["content"], list):
                for item in message["content"]:
                    if item["type"] == "text":
                        return item["text"]
            return message["content"]
    return None


def get_last_assistant_message(messages: List[dict]) -> str:
    for message in reversed(messages):
        if message["role"] == "assistant":
            if isinstance(message["content"], list):
                for item in message["content"]:
                    if item["type"] == "text":
                        return item["text"]
            return message["content"]
    return None


def get_system_message(messages: List[dict]) -> dict:
    for message in messages:
        if message["role"] == "system":
            return message
    return None


def remove_system_message(messages: List[dict]) -> List[dict]:
    return [message for message in messages if message["role"] != "system"]


def pop_system_message(messages: List[dict]) -> Tuple[dict, List[dict]]:
    return get_system_message(messages), remove_system_message(messages)


def add_or_update_system_message(content: str, messages: List[dict]) -> List[dict]:
    """
    Adds a new system message at the beginning of the messages list
    or updates the existing system message at the beginning.

    :param msg: The message to be added or appended.
    :param messages: The list of message dictionaries.
    :return: The updated list of message dictionaries.
    """

    if messages and messages[0].get("role") == "system":
        messages[0]["content"] += f"{content}\n{messages[0]['content']}"
    else:
        # Insert at the beginning
        messages.insert(0, {"role": "system", "content": content})

    return messages


def doc_to_dict(docstring):
    lines = docstring.split("\n")
    description = lines[1].strip()
    param_dict = {}

    for line in lines:
        if ":param" in line:
            line = line.replace(":param", "").strip()
            param, desc = line.split(":", 1)
            param_dict[param.strip()] = desc.strip()
    ret_dict = {"description": description, "params": param_dict}
    return ret_dict


def get_tools_specs(tools) -> List[dict]:
    function_list = [
        {"name": func, "function": getattr(tools, func)}
        for func in dir(tools)
        if callable(getattr(tools, func)) and not func.startswith("__")
    ]

    specs = []

    for function_item in function_list:
        function_name = function_item["name"]
        function = function_item["function"]

        function_doc = doc_to_dict(function.__doc__ or function_name)
        specs.append(
            {
                "name": function_name,
                # TODO: multi-line desc?
                "description": function_doc.get("description", function_name),
                "parameters": {
                    "type": "object",
                    "properties": {
                        param_name: {
                            "type": param_annotation.__name__.lower(),
                            **(
                                {
                                    "enum": (
                                        param_annotation.__args__
                                        if hasattr(param_annotation, "__args__")
                                        else None
                                    )
                                }
                                if hasattr(param_annotation, "__args__")
                                else {}
                            ),
                            "description": function_doc.get("params", {}).get(
                                param_name, param_name
                            ),
                        }
                        for param_name, param_annotation in get_type_hints(
                            function
                        ).items()
                        if param_name != "return"
                    },
                    "required": [
                        name
                        for name, param in inspect.signature(
                            function
                        ).parameters.items()
                        if param.default is param.empty
                    ],
                },
            }
        )

    return specs
