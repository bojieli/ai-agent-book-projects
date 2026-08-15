import json
import logging
import os
import re
import string
from pathlib import Path
from typing import Any, Dict, List, Optional

from tabulate import tabulate

logger = logging.getLogger(__name__)


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


def load_dataset_meta(path: str):
    # For IMO dataset, metadata.jsonl is directly placed in the imo folder
    data_dir = Path(path)
    
    dataset = []
    metadata_file = data_dir / "metadata.jsonl"
    
    if not metadata_file.exists():
        logger.error(f"Metadata file not found: {metadata_file}")
        return []
    
    with open(metadata_file, "r", encoding="utf-8") as metaf:
        lines = metaf.readlines()
        for line_num, line in enumerate(lines, 1):
            try:
                # Clean trailing commas at the end of lines
                line = line.strip().rstrip(',')
                if not line:
                    continue
                    
                data = json.loads(line)
                if data["task_id"] == "0-0-0-0-0":
                    continue
                # IMO dataset may not have file_name field
                if "file_name" in data and data["file_name"]:
                    data["file_name"] = data_dir / data["file_name"]
                dataset.append(data)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error at line {line_num}: {e}")
                logger.warning(f"Problematic line: {line[:100]}...")
                continue
            except Exception as e:
                logger.error(f"Error processing line {line_num}: {e}")
                continue
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


def add_file_path(task: Dict[str, Any], file_path: str = "./imo_dataset"):
    if "file_name" in task and task["file_name"]:
        # For IMO dataset, file paths may need adjustment
        base_path = Path(file_path)
        file_path = base_path / task["file_name"]
            
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
    logger.info(tabulate(overall_table, tablefmt="grid"))
    logger.info("")

    # Create level statistics table
    logger.info("Statistics by Level:")
    level_table = []
    headers = ["Level", "Total Entries", "Correct Answers", "Accuracy"]

    for level in sorted(level_stats.keys()):
        stats = level_stats[level]
        level_table.append([level, stats["total"], stats["correct"], f"{stats['accuracy']:.2f}%"])

    logger.info(tabulate(level_table, headers=headers, tablefmt="grid"))


def setup_logger(logger_name, output_folder_path, file_name="main.log"):
    """
    Set up a logger with the given name that writes to the specified file.
    Returns a configured logger instance.
    """
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    log_file = os.path.join(output_folder_path, file_name)

    # Check if the logger already has handlers to avoid duplicates
    logger = logging.getLogger(logger_name)

    # Remove existing handlers if any
    if logger.hasHandlers():
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    # Add file handler
    handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


def color_log(logger: logging.Logger, value: str, color: Optional[str], level: str | None = None):
    # Default to 'info' level if none specified
    if level is None:
        level = "info"

    # Format the message with color
    if color is None:
        message = f"{value}"
    else:
        message = f"{color}{value}"

    # Log according to the specified level
    level_lower = level.lower()
    if level_lower == "debug":
        logger.debug(message)
    elif level_lower == "info":
        logger.info(message)
    elif level_lower == "warning" or level_lower == "warn":
        logger.warning(message)
    elif level_lower == "error":
        logger.error(message)
    elif level_lower == "critical":
        logger.critical(message)
    else:
        # Default to info for unknown levels
        logger.info(message)
