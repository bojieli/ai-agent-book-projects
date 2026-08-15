# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import re
import string
from typing import List

from swift.plugin import ORM, orms, rm_plugins
from swift.utils import get_logger

logger = get_logger()
"""
Step 1: Define a Reward Class
    Implement your custom reward calculation logic within the __call__ method.
    The method accepts the model's output completions and dataset columns (passed as kwargs) as input parameters.

Step 2: Register the Reward Class in orms
    For example:
    python orms['external_math_acc'] = MathAccuracy

Step 3: Configure the Arguments
    Use the following arguments when running the script:
    bash --plugin /path/to/plugin.py --reward_funcs external_math_acc
"""


class GaiaAnswerMatch(ORM):
    def __call__(self, completions, solution, **kwargs) -> List[float]:
        pattern = r'<answer>(.*?)</answer>'
        rewards = []
        logger.info(f"GaiaAnswerMatch|completions:{completions}, comp_match:{solution}")
        for content, sol in zip(completions, solution):
            comp_match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            logger.info(f"GaiaAnswerMatch|content:{content}, comp_match:{comp_match}, sol:{sol}")
            if not comp_match:
                rewards.append(0.0)
                continue
            comp_answer = comp_match.group(1).strip()

            if question_scorer(comp_answer, sol):
                rewards.append(1.0)
            else:
                rewards.append(0.0)

        return rewards


class GaiaFormat(ORM):
    def __call__(self, completions, **kwargs) -> List[float]:
        """Reward function that checks if the completion has a specific format."""
        pattern = r'<answer>[\s\S]*?</answer>'
        matches = [re.search(pattern, content, re.DOTALL | re.MULTILINE) for content in completions]
        reward = [0.1 if match else 0.0 for match in matches]
        return reward


orms['external_gaia_answer_reward'] = GaiaAnswerMatch
orms['external_gaia_format_reward'] = GaiaFormat


def split_string(
        s: str,
        char_list: list[str] = [",", ";"],
) -> list[str]:
    pattern = f"[{''.join(char_list)}]"
    return re.split(pattern, s)


def normalize_str(input_str, remove_punct=True) -> str:
    no_spaces = re.sub(r"\s", "", input_str)

    # Remove punctuation, if specified.
    if remove_punct:
        translator = str.maketrans("", "", string.punctuation)
        return no_spaces.lower().translate(translator)
    else:
        return no_spaces.lower()


def normalize_number_str(number_str: str) -> float:
    # we replace these common units and commas to allow
    # conversion to float
    for char in ["$", "%", ","]:
        number_str = number_str.replace(char, "")
    try:
        return float(number_str)
    except ValueError:
        # print(f"String {number_str} cannot be normalized to number str.")
        return float("inf")


def question_scorer(
        model_answer: str,
        ground_truth: str,
) -> bool:
    def is_float(element: any) -> bool:
        try:
            float(element)
            return True
        except ValueError:
            return False

    if model_answer is None:
        model_answer = "None"

    # if gt is a number
    if is_float(ground_truth):
        # print(f"Evaluating {model_answer} as a number.")
        normalized_answer = normalize_number_str(model_answer)
        return normalized_answer == float(ground_truth)
    # if gt is a list
    elif any(char in ground_truth for char in [",", ";"]):
        # question with the fish: normalization removes punct
        gt_elems = split_string(ground_truth)
        ma_elems = split_string(model_answer)

        # check length is the same
        if len(gt_elems) != len(ma_elems):
            return False

        # compare each element as float or str
        comparisons = []
        for ma_elem, gt_elem in zip(ma_elems, gt_elems):
            if is_float(gt_elem):
                normalized_ma_elem = normalize_number_str(ma_elem)
                comparisons.append(normalized_ma_elem == float(gt_elem))
            else:
                # we do not remove punct since comparisons can include punct
                comparisons.append(
                    normalize_str(ma_elem, remove_punct=False)
                    == normalize_str(gt_elem, remove_punct=False)
                )
        return all(comparisons)
    # if gt is a str
    else:
        return normalize_str(model_answer) == normalize_str(ground_truth)
