"""
This code is adapted from AgentS2 (https://github.com/simular-ai/Agent-S)
with modifications to suit specific requirements.
"""
import re
import base64
from aworld.core.common import Observation, ActionModel
from aworld.models.model_response import ModelResponse
from aworld.core.agent.base import AgentResult
from aworld.memory.main import InMemoryMemoryStore

def encode_image(image_content):
    # if image_content is a path to an image file, check type of the image_content to verify
    if isinstance(image_content, str):
        with open(image_content, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    else:
        return base64.b64encode(image_content).decode("utf-8")


def extract_first_agent_function(code_string):
    # Regular expression pattern to match 'agent' functions with any arguments, including nested parentheses
    pattern = r'agent\.[a-zA-Z_]+\((?:[^()\'"]|\'[^\']*\'|"[^"]*")*\)'

    # Find all matches in the string
    matches = re.findall(pattern, code_string)

    # Return the first match if found, otherwise return None
    return matches[0] if matches else None


def parse_single_code_from_string(input_string):
    input_string = input_string.strip()
    if input_string.strip() in ["WAIT", "DONE", "FAIL"]:
        return input_string.strip()

    # This regular expression will match both ```code``` and ```python code```
    # and capture the `code` part. It uses a non-greedy match for the content inside.
    pattern = r"```(?:\w+\s+)?(.*?)```"
    # Find all non-overlapping matches in the string
    matches = re.findall(pattern, input_string, re.DOTALL)

    # The regex above captures the content inside the triple backticks.
    # The `re.DOTALL` flag allows the dot `.` to match newline characters as well,
    # so the code inside backticks can span multiple lines.

    # matches now contains all the captured code snippets

    codes = []

    for match in matches:
        match = match.strip()
        commands = [
            "WAIT",
            "DONE",
            "FAIL",
        ]  # fixme: updates this part when we have more commands

        if match in commands:
            codes.append(match.strip())
        elif match.split("\n")[-1] in commands:
            if len(match.split("\n")) > 1:
                codes.append("\n".join(match.split("\n")[:-1]))
            codes.append(match.split("\n")[-1])
        else:
            codes.append(match)

    if len(codes) <= 0:
        return "fail"
    return codes[0]


def sanitize_code(code):
    # This pattern captures the outermost double-quoted text
    if "\n" in code:
        pattern = r'(".*?")'
        # Find all matches in the text
        matches = re.findall(pattern, code, flags=re.DOTALL)
        if matches:
            # Replace the first occurrence only
            first_match = matches[0]
            code = code.replace(first_match, f'"""{first_match[1:-1]}"""', 1)
    return code

def prune_image_messages(memory_store: InMemoryMemoryStore, max_trajectory_length: int):
    """
    检查 memory_store 中的消息，并仅保留最新的 max_trajectory_length 个包含图片的消息。
    对于更早的包含图片的消息，会从其 content 中移除图片部分。

    Args:
        memory_store (InMemoryMemoryStore): 内存存储的对象实例。
        max_trajectory_length (int): 希望保留的含图片消息的最大数量。
    """
    # 步骤 1: 使用 memory_store 的 get_all 方法获取所有消息
    all_items = memory_store.get_all()

    # 步骤 2: 筛选出所有包含图片内容的消息
    image_messages = []
    for item in all_items:
        if isinstance(item.content, list):
            if any(isinstance(part, dict) and part.get('type') == 'image_url' for part in item.content):
                image_messages.append(item)

    # 步骤 3: 检查包含图片的消息数量是否超过限制
    if len(image_messages) <= max_trajectory_length:
        print("Number of image messages does not exceed the limit. No pruning needed.")
        return

    # 步骤 4: 确定需要移除图片的旧消息
    # 由于 get_all() 返回的列表是按添加顺序排列的，所以列表前面的项就是最旧的
    num_to_prune = len(image_messages) - max_trajectory_length
    messages_to_prune = image_messages[:num_to_prune]

    print(f"Found {len(image_messages)} image messages. Pruning the oldest {num_to_prune}.")

    # 步骤 5: 遍历需要修剪的消息，更新其 content，并使用 store 的 update 方法保存
    for item_to_prune in messages_to_prune:

        # 创建一个新的 content 列表，仅包含非图片部分
        new_content = [
            part for part in item_to_prune.content
            if not (isinstance(part, dict) and part.get('type') == 'image_url')
        ]

        # 可选：如果 new_content 中只剩下一个文本元素，可以将其简化为字符串
        if len(new_content) == 1 and new_content[0].get('type') == 'text':
            final_content = new_content[0].get('text', '')
        else:
            final_content = new_content

        # 更新消息对象的 content 属性
        item_to_prune.content = final_content

        # 使用 memory_store 的 update 方法将更改持久化到 store 中
        memory_store.update(item_to_prune)

        print(f"Pruned image from message with ID: {item_to_prune.id}")

def reps_action_result(resp: ModelResponse) -> AgentResult:
    try:
        full_response = resp.content
        # Extract thoughts section
        thoughts_match = re.search(
            r"<thoughts>(.*?)</thoughts>", full_response, re.DOTALL
        )
        thoughts = thoughts_match.group(1).strip()
        # Extract answer section
        answer_match = re.search(r"<answer>(.*?)</answer>", full_response, re.DOTALL)
        answer = answer_match.group(1).strip()
        action = ActionModel(action_name=answer, policy_info=thoughts)
        return AgentResult(actions=[action], current_state=None)
    except Exception as e:
        action = ActionModel(action_name=resp.content, policy_info="")
        return AgentResult(actions=[action], current_state=None)

def parse_single_code_from_string(input_string):
    input_string = input_string.strip()
    if input_string.strip() in ["WAIT", "DONE", "FAIL"]:
        return input_string.strip()

    # This regular expression will match both ```code``` and ```python code```
    # and capture the `code` part. It uses a non-greedy match for the content inside.
    pattern = r"```(?:\w+\s+)?(.*?)```"
    # Find all non-overlapping matches in the string
    matches = re.findall(pattern, input_string, re.DOTALL)

    # The regex above captures the content inside the triple backticks.
    # The `re.DOTALL` flag allows the dot `.` to match newline characters as well,
    # so the code inside backticks can span multiple lines.

    # matches now contains all the captured code snippets

    codes = []

    for match in matches:
        match = match.strip()
        commands = [
            "WAIT",
            "DONE",
            "FAIL",
        ]  # fixme: updates this part when we have more commands

        if match in commands:
            codes.append(match.strip())
        elif match.split("\n")[-1] in commands:
            if len(match.split("\n")) > 1:
                codes.append("\n".join(match.split("\n")[:-1]))
            codes.append(match.split("\n")[-1])
        else:
            codes.append(match)

    if len(codes) <= 0:
        return "fail"
    return codes[0]