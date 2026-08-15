"""
This code is adapted from AgentS2 (https://github.com/simular-ai/Agent-S)
with modifications to suit specific requirements.
"""
import ast
import re
import textwrap
from collections import defaultdict
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple, Union

import pytesseract
from PIL import Image
from pytesseract import Output

from aworld.models.llm import get_llm_model, call_llm_model
from aworld.config.conf import AgentConfig

from aworldAgent.utils import encode_image, parse_single_code_from_string

class ACI:
    def __init__(self):
        self.notes: List[str] = []


# Agent action decorator
def agent_action(func):
    func.is_agent_action = True
    return func


UBUNTU_APP_SETUP = f"""import subprocess;
import difflib;
import pyautogui;
pyautogui.press('escape');
time.sleep(0.5);
output = subprocess.check_output(['wmctrl', '-lx']);
output = output.decode('utf-8').splitlines();
window_titles = [line.split(None, 4)[2] for line in output];
closest_matches = difflib.get_close_matches('APP_NAME', window_titles, n=1, cutoff=0.1);
if closest_matches:
    closest_match = closest_matches[0];
    for line in output:
        if closest_match in line:
            window_id = line.split()[0]
            break;
subprocess.run(['wmctrl', '-ia', window_id])
subprocess.run(['wmctrl', '-ir', window_id, '-b', 'add,maximized_vert,maximized_horz'])
"""


SET_CELL_VALUES_CMD = """import uno
import subprocess

def identify_document_type(component):
    if component.supportsService("com.sun.star.sheet.SpreadsheetDocument"):
        return "Calc"

    if component.supportsService("com.sun.star.text.TextDocument"):
        return "Writer"

    if component.supportsService("com.sun.star.sheet.PresentationDocument"):
        return "Impress"

    return None

def cell_ref_to_indices(cell_ref):
    column_letters = ''.join(filter(str.isalpha, cell_ref))
    row_number = ''.join(filter(str.isdigit, cell_ref))

    col = sum((ord(char.upper()) - ord('A') + 1) * (26**idx) for idx, char in enumerate(reversed(column_letters))) - 1
    row = int(row_number) - 1
    return col, row

def set_cell_values(new_cell_values: dict[str, str], app_name: str = "Untitled 1", sheet_name: str = "Sheet1"):
    new_cell_values_idx = {{}}
    for k, v in new_cell_values.items():
        try:
            col, row = cell_ref_to_indices(k)
        except:
            col = row = None

        if col is not None and row is not None:
            new_cell_values_idx[(col, row)] = v

    # Clean up previous TCP connections.
    # subprocess.run(
    #     'echo \"osworld-public-evaluation\" | sudo -S ss --kill --tcp state TIME-WAIT sport = :2002',
    #     shell=True,
    #     check=True,
    #     text=True,
    #     capture_output=True
    # )

    # Dynamically allow soffice to listen on port 2002.
    subprocess.run(
        [
            "soffice",
            "--accept=socket,host=localhost,port=2002;urp;StarOffice.Service"
        ]
    )

    local_context = uno.getComponentContext()
    resolver = local_context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_context
    )
    context = resolver.resolve(
        f"uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"
    )
    desktop = context.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.Desktop", context
    )

    # Collect all LibreOffice-related opened windows.
    documents = []
    for i, component in enumerate(desktop.Components):
        title = component.Title
        doc_type = identify_document_type(component)
        documents.append((i, component, title, doc_type))

    # Find the LibreOffice Calc app and the sheet of interest.
    spreadsheet = [doc for doc in documents if doc[3] == "Calc"]
    selected_spreadsheet = [doc for doc in spreadsheet if doc[2] == app_name]
    if spreadsheet:
        try:
            if selected_spreadsheet:
                spreadsheet = selected_spreadsheet[0][1]
            else:
                spreadsheet = spreadsheet[0][1]

            sheet = spreadsheet.Sheets.getByName(sheet_name)
        except:
            raise ValueError(f"Could not find sheet {{sheet_name}} in {{app_name}}.")

        for (col, row), value in new_cell_values_idx.items():
            cell = sheet.getCellByPosition(col, row)

            # Set the cell value.
            if isinstance(value, (int, float)):
                cell.Value = value
            elif isinstance(value, str):
                if value.startswith("="):
                    cell.Formula = value
                else:
                    cell.String = value
            elif isinstance(value, bool):
                cell.Value = 1 if value else 0
            elif value is None:
                cell.clearContents(0)
            else:
                raise ValueError(f"Unsupported cell value type: {{type(value)}}")

    else:
        raise ValueError(f"Could not find LibreOffice Calc app corresponding to {{app_name}}.")

set_cell_values(new_cell_values={cell_values}, app_name="{app_name}", sheet_name="{sheet_name}")        
"""


# ACI primitives are parameterized by description, and coordinate generation uses a pretrained grounding model
class OSWorldACI(ACI):
    def __init__(
        self,
        platform: str,
        engine_params_for_generation: Dict,
        engine_params_for_grounding: Dict,
        width: int = 1920,
        height: int = 1080,
    ):
        self.platform = (
            platform  # Dictates how the switch_applications agent action works.
        )

        # Configure scaling
        self.width = width
        self.height = height

        # Maintain state for save_to_knowledge
        self.notes = []

        # Coordinates used during ACI execution
        self.coords1 = None
        self.coords2 = None

        # Configure the visual grounding model responsible for coordinate generation
        llm_config = AgentConfig(
            llm_provider=engine_params_for_grounding.get("engine_type", "openai"),
            llm_model_name=engine_params_for_grounding.get("model", "bytedance/ui-tars-1.5-7b"),
            llm_temperature=1,
            llm_base_url=engine_params_for_grounding.get("base_url", "https://openrouter.ai/api/v1"),
            llm_api_key=engine_params_for_grounding.get("api_key", "")
        )

        self.grounding_model = get_llm_model(llm_config)
        self.engine_params_for_grounding = engine_params_for_grounding

        # Configure text grounding agent
        self.text_span_model = get_llm_model(llm_config)

    # Given the state and worker's referring expression, use the grounding model to generate (x,y)
    def generate_coords(self, ref_expr: str, obs: Dict) -> List[int]:

        # Reset the grounding model state
        # self.grounding_model.reset()

        # Configure the context, UI-TARS demo does not use system prompt
        prompt = f"Query:{ref_expr}\nOutput only the coordinate of one point in your response.\n"
        # self.grounding_model.add_message(
        #     text_content=prompt, image_content=obs["screenshot"], put_text_last=True
        # )

        grounding_message = [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                 },
                {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/png;base64," + encode_image(obs["screenshot"])
                }
            }
        ]
        }]

        response = call_llm_model(
            llm_model=self.grounding_model,
            messages=grounding_message
        ).content


        # Generate and parse coordinates
        # response = call_llm_safe(self.grounding_model)
        print("RAW GROUNDING MODEL RESPONSE:", response)
        numericals = re.findall(r"\d+", response)
        assert len(numericals) >= 2
        return [int(numericals[0]), int(numericals[1])]

    # Calls pytesseract to generate word level bounding boxes for text grounding
    def get_ocr_elements(self, b64_image_data: str) -> Tuple[str, List]:
        image = Image.open(BytesIO(b64_image_data))
        image_data = pytesseract.image_to_data(image, output_type=Output.DICT)

        # Clean text by removing leading and trailing spaces and non-alphabetical characters, but keeping punctuation
        for i, word in enumerate(image_data["text"]):
            image_data["text"][i] = re.sub(
                r"^[^a-zA-Z\s.,!?;:\-\+]+|[^a-zA-Z\s.,!?;:\-\+]+$", "", word
            )

        ocr_elements = []
        ocr_table = "Text Table:\nWord id\tText\n"
        # Obtain the <id, text, group number, word number> for each valid element
        grouping_map = defaultdict(list)
        ocr_id = 0
        for i in range(len(image_data["text"])):
            block_num = image_data["block_num"][i]
            if image_data["text"][i]:
                grouping_map[block_num].append(image_data["text"][i])
                ocr_table += f"{ocr_id}\t{image_data['text'][i]}\n"
                ocr_elements.append(
                    {
                        "id": ocr_id,
                        "text": image_data["text"][i],
                        "group_num": block_num,
                        "word_num": len(grouping_map[block_num]),
                        "left": image_data["left"][i],
                        "top": image_data["top"][i],
                        "width": image_data["width"][i],
                        "height": image_data["height"][i],
                    }
                )
                ocr_id += 1

        return ocr_table, ocr_elements
    # Given the state and worker's text phrase, generate the coords of the first/last word in the phrase
    def generate_text_coords(
        self, phrase: str, obs: Dict, alignment: str = ""
    ) -> List[int]:

        ocr_table, ocr_elements = self.get_ocr_elements(obs["screenshot"])

        PHRASE_TO_WORD_COORDS_PROMPT = textwrap.dedent(
            """
    You are an expert in graphical user interfaces. Your task is to process a phrase of text, and identify the most relevant word on the computer screen.
    You are provided with a phrase, a table with all the text on the screen, and a screenshot of the computer screen. You will identify the single word id that is best associated with the provided phrase.
    This single word must be displayed on the computer screenshot, and its location on the screen should align with the provided phrase.
    Each row in the text table provides 2 pieces of data in the following order. 1st is the unique word id. 2nd is the corresponding word.

    To be successful, it is very important to follow all these rules:
    1. First, think step by step and generate your reasoning about which word id to click on.
    2. Then, output the unique word id. Remember, the word id is the 1st number in each row of the text table.
    3. If there are multiple occurrences of the same word, use the surrounding context in the phrase to choose the correct one. Pay very close attention to punctuation and capitalization.

    """
        )


        grounding_message = []
        system_message = {
            "role": "system",
            "content": [{
                    "type": "text",
                    "text": PHRASE_TO_WORD_COORDS_PROMPT
        }]}

        grounding_message.append(system_message)

        alignment_prompt = ""
        if alignment == "start":
            alignment_prompt = "**Important**: Output the word id of the FIRST word in the provided phrase.\n"
        elif alignment == "end":
            alignment_prompt = "**Important**: Output the word id of the LAST word in the provided phrase.\n"

        # Load LLM prompt
        # self.text_span_agent.reset()
        grounding_message.append(
            {
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": alignment_prompt + "Phrase: " + phrase + "\n" + ocr_table
                }]}
        )

        # Obtain the target element
        # response = call_llm_safe(self.text_span_agent)
        response = call_llm_model(
            llm_model=self.text_span_model,
            messages=grounding_message
        ).content

        print("TEXT SPAN AGENT RESPONSE:", response)
        numericals = re.findall(r"\d+", response)
        if len(numericals) > 0:
            text_id = int(numericals[-1])
        else:
            text_id = 0
        elem = ocr_elements[text_id]

        # Compute the element coordinates
        if alignment == "start":
            coords = [elem["left"], elem["top"] + (elem["height"] // 2)]
        elif alignment == "end":
            coords = [elem["left"] + elem["width"], elem["top"] + (elem["height"] // 2)]
        else:
            coords = [
                elem["left"] + (elem["width"] // 2),
                elem["top"] + (elem["height"] // 2),
            ]
        return coords

    # Takes a description based action and assigns the coordinates for any coordinate based action
    # Raises an error if function can't be parsed
    def assign_coordinates(self, plan: str, obs: Dict):

        # Reset coords from previous action generation
        self.coords1, self.coords2 = None, None

        try:
            # Extract the function name and args
            action = parse_single_code_from_string(plan.split("Grounded Action")[-1])
            function_name = re.match(r"(\w+\.\w+)\(", action).group(1)
            args = self.parse_function_args(action)
        except Exception as e:
            raise RuntimeError(f"Error in parsing grounded action: {e}") from e

        # arg0 is a description
        if (
            function_name in ["agent.click", "agent.type", "agent.scroll"]
            and len(args) >= 1
            and args[0] != None
        ):
            self.coords1 = self.generate_coords(args[0], obs)
        # arg0 and arg1 are descriptions
        elif function_name == "agent.drag_and_drop" and len(args) >= 2:
            self.coords1 = self.generate_coords(args[0], obs)
            self.coords2 = self.generate_coords(args[1], obs)
        # arg0 and arg1 are text phrases
        elif function_name == "agent.highlight_text_span" and len(args) >= 2:
            self.coords1 = self.generate_text_coords(args[0], obs, alignment="start")
            self.coords2 = self.generate_text_coords(args[1], obs, alignment="end")

    # Resize from grounding model dim into OSWorld dim (1920 * 1080)
    def resize_coordinates(self, coordinates: List[int]) -> List[int]:
        grounding_width = self.engine_params_for_grounding["grounding_width"]
        grounding_height = self.engine_params_for_grounding["grounding_height"]

        return [
            round(coordinates[0] * self.width / grounding_width),
            round(coordinates[1] * self.height / grounding_height),
        ]

    # Given a generated ACI function, returns a list of argument values, where descriptions are at the front of the list
    def parse_function_args(self, function: str) -> List[str]:
        tree = ast.parse(function)
        call_node = tree.body[0].value

        def safe_eval(node):
            if isinstance(
                node, ast.Constant
            ):  # Handles literals like numbers, strings, etc.
                return node.value
            else:
                return ast.unparse(node)  # Return as a string if not a literal

        positional_args = [safe_eval(arg) for arg in call_node.args]
        keyword_args = {kw.arg: safe_eval(kw.value) for kw in call_node.keywords}

        res = []

        for key, val in keyword_args.items():
            if "description" in key:
                res.append(val)

        for arg in positional_args:
            res.append(arg)

        return res

    @agent_action
    def click(
        self,
        element_description: str,
        num_clicks: int = 1,
        button_type: str = "left",
        hold_keys: List = [],
    ):
        """Click on the element
    Args:
        element_description:str, a detailed descriptions of which element to click on. This description should be at least a full sentence.
        num_clicks:int, number of times to click the element
        button_type:str, which mouse button to press can be "left", "middle", or "right"
        hold_keys:List, list of keys to hold while clicking
    """
        x, y = self.resize_coordinates(self.coords1)
        command = "import pyautogui; "

        # TODO: specified duration?
        for k in hold_keys:
            command += f"pyautogui.keyDown({repr(k)}); "
        command += f"""import pyautogui; pyautogui.click({x}, {y}, clicks={num_clicks}, button={repr(button_type)}); """
        for k in hold_keys:
            command += f"pyautogui.keyUp({repr(k)}); "

        # === 新增代码：在这里添加1秒的等待 ===
        command += "time.sleep(2); "
        # Return pyautoguicode to click on the element
        return command

    @agent_action
    def switch_applications(self, app_code):
        """Switch to a different application that is already open
    Args:
        app_code:str the code name of the application to switch to from the provided list of open applications
    """
        if self.platform == "darwin":
            return f"import pyautogui; import time; pyautogui.hotkey('command', 'space', interval=0.5); pyautogui.typewrite({repr(app_code)}); pyautogui.press('enter'); time.sleep(1.0)"
        elif self.platform == "linux":
            return UBUNTU_APP_SETUP.replace("APP_NAME", app_code)
        elif self.platform == "windows":
            return f"import pyautogui; import time; pyautogui.hotkey('win', 'd', interval=0.5); pyautogui.typewrite({repr(app_code)}); pyautogui.press('enter'); time.sleep(1.0)"

    @agent_action
    def open(self, app_or_filename: str):
        """Open any application or file with name app_or_filename. Use this action to open applications or files on the desktop, do not open manually.
    Args:
        app_or_filename:str, the name of the application or filename to open
    """
        if self.platform == "linux":
            return f"import pyautogui; pyautogui.hotkey('win'); time.sleep(0.5); pyautogui.write({repr(app_or_filename)}); time.sleep(1.0); pyautogui.hotkey('enter'); time.sleep(0.5)"
        elif self.platform == "darwin":
            return f"import pyautogui; import time; pyautogui.hotkey('command', 'space', interval=0.5); pyautogui.typewrite({repr(app_or_filename)}); pyautogui.press('enter'); time.sleep(1.0)"

    @agent_action
    def type(
        self,
        element_description: Optional[str] = None,
        text: str = "",
        overwrite: bool = False,
        enter: bool = False,
    ):
        """Type text into a specific element
    Args:
        element_description:str, a detailed description of which element to enter text in. This description should be at least a full sentence.
        text:str, the text to type
        overwrite:bool, Assign it to True if the text should overwrite the existing text, otherwise assign it to False. Using this argument clears all text in an element.
        enter:bool, Assign it to True if the enter key should be pressed after typing the text, otherwise assign it to False.
    """

        select_mod = "command" if self.platform == "darwin" else "ctrl"

        if self.coords1 is not None:
            # If a node is found, retrieve its coordinates and size
            # Start typing at the center of the element

            x, y = self.resize_coordinates(self.coords1)

            command = "import pyautogui; "
            # command += f"pyautogui.click({x}, {y}); "
            # 修改成double click
            command += f"pyautogui.doubleClick({x}, {y}); "

            if overwrite:
                command += (
                    f"pyautogui.hotkey({repr(select_mod)}, 'a'); "
                    "pyautogui.press('backspace'); "
                )

            command += f"pyautogui.write({repr(text)}); "

            if enter:
                command += "pyautogui.press('enter'); "
        else:
            # If no element is found, start typing at the current cursor location
            command = "import pyautogui; "

            if overwrite:
                command += (
                    f"pyautogui.hotkey({repr(select_mod)}, 'a'); "
                    "pyautogui.press('backspace'); "
                )

            command += f"pyautogui.write({repr(text)}); "

            if enter:
                command += "pyautogui.press('enter'); "

        # === 新增代码：在这里添加1秒的等待 ===
        command += "time.sleep(2); "

        return command

    @agent_action
    def save_to_knowledge(self, text: List[str]):
        """Save facts, elements, texts, etc. to a long-term knowledge bank for reuse during this task. Can be used for copy-pasting text, saving elements, etc.
    Args:
        text:List[str] the text to save to the knowledge
    """
        self.notes.extend(text)
        return """WAIT"""

    @agent_action
    def drag_and_drop(
        self, starting_description: str, ending_description: str, hold_keys: List = []
    ):
        """Drag from the starting description to the ending description
    Args:
        starting_description:str, a very detailed description of where to start the drag action. This description should be at least a full sentence.
        ending_description:str, a very detailed description of where to end the drag action. This description should be at least a full sentence.
        hold_keys:List list of keys to hold while dragging
    """
        x1, y1 = self.resize_coordinates(self.coords1)
        x2, y2 = self.resize_coordinates(self.coords2)

        command = "import pyautogui; "

        command += f"pyautogui.moveTo({x1}, {y1}); "
        # TODO: specified duration?
        for k in hold_keys:
            command += f"pyautogui.keyDown({repr(k)}); "
        command += f"pyautogui.dragTo({x2}, {y2}, duration=1., button='left'); pyautogui.mouseUp(); "
        for k in hold_keys:
            command += f"pyautogui.keyUp({repr(k)}); "

        # Return pyautoguicode to drag and drop the elements

        # === 新增代码：在这里添加1秒的等待 ===
        command += "time.sleep(2); "

        return command

    @agent_action
    def highlight_text_span(
        self, starting_phrase: str, ending_phrase: str, button: str = "left"
    ):
        """Highlight a text span between a provided starting phrase and ending phrase. Use this to highlight words, lines, and paragraphs.
    Args:
        starting_phrase:str, the phrase that denotes the start of the text span you want to highlight. If you only want to highlight one word, just pass in that single word.
        ending_phrase:str, the phrase that denotes the end of the text span you want to highlight. If you only want to highlight one word, just pass in that single word.
        button:str, the button to use to highlight the text span. Defaults to "left". Can be "left", "right", or "middle".
    """

        x1, y1 = self.coords1
        x2, y2 = self.coords2

        command = "import pyautogui; "
        command += f"pyautogui.moveTo({x1}, {y1}); "
        command += f"pyautogui.dragTo({x2}, {y2}, duration=1., button='{button}'); pyautogui.mouseUp(); "

        # Return pyautoguicode to drag and drop the elements

        # === 新增代码：在这里添加1秒的等待 ===
        command += "time.sleep(2); "

        return command

    @agent_action
    def set_cell_values(
        self, cell_values: Dict[str, Any], app_name: str, sheet_name: str
    ):
        """Use this to set individual cell values in a spreadsheet. For example, setting A2 to "hello" would be done by passing {"A2": "hello"} as cell_values. The sheet must be opened before this command can be used.
    Args:
        cell_values: Dict[str, Any], A dictionary of cell values to set in the spreadsheet. The keys are the cell coordinates in the format "A1", "B2", etc.
            Supported value types include: float, int, string, bool, formulas.
        app_name: str, The name of the spreadsheet application. For example, "Some_sheet.xlsx".
        sheet_name: str, The name of the sheet in the spreadsheet. For example, "Sheet1".
    """
        return SET_CELL_VALUES_CMD.format(
            cell_values=cell_values, app_name=app_name, sheet_name=sheet_name
        )

    @agent_action
    def scroll(self, element_description: str, clicks: int, shift: bool = False):
        """Scroll the element in the specified direction
    Args:
        element_description:str, a very detailed description of which element to enter scroll in. This description should be at least a full sentence.
        clicks:int, the number of clicks to scroll can be positive (up) or negative (down).
        shift:bool, whether to use shift+scroll for horizontal scrolling
    """

        x, y = self.resize_coordinates(self.coords1)

        if shift:
            return f"import pyautogui; import time; pyautogui.moveTo({x}, {y}); time.sleep(0.5); pyautogui.hscroll({clicks})"
        else:
            return f"import pyautogui; import time; pyautogui.moveTo({x}, {y}); time.sleep(0.5); pyautogui.vscroll({clicks})"

    @agent_action
    def hotkey(self, keys: List):
        """Press a hotkey combination
    Args:
        keys:List the keys to press in combination in a list format (e.g. ['ctrl', 'c'])
    """
        # add quotes around the keys
        keys = [f"'{key}'" for key in keys]
        return f"import pyautogui; pyautogui.hotkey({', '.join(keys)}); time.sleep(2);"


    @agent_action
    def hold_and_press(self, hold_keys: List, press_keys: List):
        """Hold a list of keys and press a list of keys
    Args:
        hold_keys:List, list of keys to hold
        press_keys:List, list of keys to press in a sequence
    """

        press_keys_str = "[" + ", ".join([f"'{key}'" for key in press_keys]) + "]"
        command = "import pyautogui; "
        for k in hold_keys:
            command += f"pyautogui.keyDown({repr(k)}); "
        command += f"pyautogui.press({press_keys_str}); "
        for k in hold_keys:
            command += f"pyautogui.keyUp({repr(k)}); "

        return command

    @agent_action
    def wait(self, time: float):
        """Wait for a specified amount of time
    Args:
        time:float the amount of time to wait in seconds
    """
        return f"""import time; time.sleep({time})"""

    @agent_action
    def done(
        self,
        return_value: Optional[Union[Dict, str, List, Tuple, int, float, bool]] = None,
    ):
        """End the current task with a success and the required return value"""
        self.returned_info = return_value
        return """DONE"""

    @agent_action
    def fail(self):
        """End the current task with a failure, and replan the whole task."""
        return """FAIL"""

    CODE_LAUNCH_VSCODE_CMD = """import json
import os
import subprocess
from pathlib import Path
ret = ""

def code_launch_vscode(path):
    global ret
    try:
        subprocess.run(["code", "-r", path], check=True)
        ret = "Successfully launched VS Code"
    except subprocess.CalledProcessError as e:
        ret = f"Error launching VS Code: {{e}}"
    except Exception as e:
        ret = f"Unexpected error: {{e}}"

    return ret
code_launch_vscode(path={path})
print(ret)
"""

    @agent_action
    def code_launch_vscode(self, path):

        return self.CODE_LAUNCH_VSCODE_CMD.format(path=repr(path))

    CODE_COMPARE_FILES_CMD = """import json
import os
import subprocess
from pathlib import Path
ret = ""

def code_compare_files(file1, file2):
    global ret
    try:
        # 获取compare结果
        subprocess.run(["code", "-d", file1, file2], check=True)
        ret = "The compared files are opened in VSCode"
    except subprocess.CalledProcessError as e:
        ret = f"Error comparing files: {{e}}"
    except Exception as e:
        ret = f"Unexpected error: {{e}}"

    return ret
code_compare_files(file1={file1}, file2={file2})
print(ret)
"""

    @agent_action
    def code_compare_files(self, file1, file2):

        return self.CODE_COMPARE_FILES_CMD.format(file1=repr(file1), file2=repr(file2))

    CODE_ADD_FOLDER_CMD = """import json
import os
import subprocess
from pathlib import Path
ret = ""

def code_add_folder(folder):
    global ret
    try:
        subprocess.run(["code", "-a", folder], check=True)
        ret = "Successfully added folder"
    except subprocess.CalledProcessError as e:
        ret = f"Error adding folder: {{e}}"
    except Exception as e:
        ret = f"Unexpected error: {{e}}"

    return ret
code_add_folder(folder={folder})
print(ret)
"""

    @agent_action
    def code_add_folder(self, folder):

        return self.CODE_ADD_FOLDER_CMD.format(folder=repr(folder))

    CODE_GOTO_FILE_CMD = """import json
import os
import subprocess
from pathlib import Path
ret = ""

def code_goto_file(file_path, line=1, character=1):
    global ret
    try:
        command = f"{{file_path}}:{{line}}:{{character}}"
        subprocess.run(["code", "-g", command], check=True)
        ret = "Successfully opened file, line: {{}}, character: {{}}".format(line, character)
    except subprocess.CalledProcessError as e:
        ret = f"Error going to file: {{e}}"
    except Exception as e:
        ret = f"Unexpected error: {{e}}"

    return ret
code_goto_file(file_path={file_path}, line={line}, character={character})
print(ret)
"""

    @agent_action
    def code_goto_file(self, file_path, line, character):

        return self.CODE_GOTO_FILE_CMD.format(file_path=repr(file_path), line=repr(line), character=repr(character))

    LIBREOFFICE_CALC_SET_COLUMN_AS_TEXT_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_get_column_index(column_name):
    try:
        return ord(column_name[0]) - ord("A")
    except ValueError:
        return None

def libreoffice_calc_get_last_used_row():
    cursor = sheet.createCursor()
    cursor.gotoEndOfUsedArea(False)
    return cursor.RangeAddress.EndRow

def libreoffice_calc_set_column_as_text(column_name):
    global ret
    try:
        # 获取列索引
        column_index = libreoffice_calc_get_column_index(column_name)
        if column_index is None:
            ret = f"Error: Invalid column name '{{column_name}}'"
            return False

        # 获取最后使用的行
        last_row = libreoffice_calc_get_last_used_row()
        if last_row == -1:
            ret = "Error: No data found in sheet"
            return False

        # 获取整列的范围
        cell_range = sheet.getCellRangeByPosition(column_index, 0, column_index, last_row)

        # 设置数字格式为文本格式
        # 使用 "@" 表示文本格式
        cell_range.NumberFormat = 0  # 重置格式

        # 获取格式对象并设置为文本
        formats = doc.NumberFormats
        locale = uno.createUnoStruct("com.sun.star.lang.Locale")
        locale.Language = "en"
        locale.Country = "US"

        # 创建文本格式
        text_format_key = formats.queryKey("@", locale, False)
        if text_format_key == -1:
            text_format_key = formats.addNew("@", locale)

        # 应用文本格式到整列
        cell_range.NumberFormat = text_format_key

        # 将现有数值转换为文本
        data_array = cell_range.getDataArray()
        for row_idx, row in enumerate(data_array):
            cell = sheet.getCellByPosition(column_index, row_idx)
            current_value = cell.getValue() if cell.getType().value == "VALUE" else cell.getString()
            if current_value != 0 or cell.getString() != "":
                # 将值设置为字符串
                cell.setString(str(current_value))

        ret = f"Successfully set column {{column_name}} as text format"
        return True

    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_set_column_as_text(column_name={column_name})
print(ret)
"""

    @agent_action
    def libreoffice_calc_set_column_as_text(self, column_name):

        return self.LIBREOFFICE_CALC_SET_COLUMN_AS_TEXT_CMD.format(column_name=repr(column_name))

    CODE_PERFORM_MERGE_CMD = """import json
import os
import subprocess
from pathlib import Path
ret = ""

def code_perform_merge(path1, path2, base, result):
    global ret
    try:
        subprocess.run(["code", "-m", path1, path2, base, result], check=True)
        ret = "Successfully performed merge"
    except subprocess.CalledProcessError as e:
        ret = f"Error performing merge: {{e}}"
    except Exception as e:
        ret = f"Unexpected error: {{e}}"

    return ret
code_perform_merge(path1={path1}, path2={path2}, base={base}, result={result})
print(ret)
"""

    @agent_action
    def code_perform_merge(self, path1, path2, base, result):

        return self.CODE_PERFORM_MERGE_CMD.format(path1=repr(path1), path2=repr(path2), base=repr(base),
                                                  result=repr(result))

    CODE_REMOVE_FOLDER_CMD = """import json
import os
import subprocess
from pathlib import Path
ret = ""

def code_remove_folder(folder):
    global ret
    try:
        subprocess.run(["code", "--remove", folder], check=True)
        ret = "Successfully removed folder"
    except subprocess.CalledProcessError as e:
        ret = f"Error removing folder: {{e}}"
    except Exception as e:
        ret = f"Unexpected error: {{e}}"

    return ret
code_remove_folder(folder={folder})
print(ret)
"""

    @agent_action
    def code_remove_folder(self, folder):

        return self.CODE_REMOVE_FOLDER_CMD.format(folder=repr(folder))

    CODE_INSTALL_EXTENSION_CMD = """import json
import os
import subprocess
from pathlib import Path
ret = ""

def code_install_extension(extension_id, pre_release=False):
    global ret
    try:
        command = ["code", "--install-extension", extension_id]
        if pre_release:
            command.append("--pre-release")
        subprocess.run(command, check=True)
        ret = "Successfully installed extension"
    except subprocess.CalledProcessError as e:
        ret = f"Error installing extension: {{e}}"
    except Exception as e:
        ret = f"Unexpected error: {{e}}"

    return ret
code_install_extension(extension_id={extension_id}, pre_release={pre_release})
print(ret)
"""

    @agent_action
    def code_install_extension(self, extension_id, pre_release):

        return self.CODE_INSTALL_EXTENSION_CMD.format(extension_id=repr(extension_id), pre_release=repr(pre_release))

    CODE_UNINSTALL_EXTENSION_CMD = """import json
import os
import subprocess
from pathlib import Path
ret = ""

def code_uninstall_extension(extension_id):
    global ret
    try:
        subprocess.run(["code", "--uninstall-extension", extension_id], check=True)
        ret = "Successfully uninstalled extension"
    except subprocess.CalledProcessError as e:
        ret = f"Error uninstalling extension: {{e}}"
    except Exception as e:
        ret = f"Unexpected error: {{e}}"

    return ret
code_uninstall_extension(extension_id={extension_id})
print(ret)
"""

    @agent_action
    def code_uninstall_extension(self, extension_id):

        return self.CODE_UNINSTALL_EXTENSION_CMD.format(extension_id=repr(extension_id))

    CODE_LIST_EXTENSIONS_CMD = """import json
import os
import subprocess
from pathlib import Path
ret = ""

def code_list_extensions(show_versions=False, category=None):
    global ret
    try:
        command = ["code", "--list-extensions"]
        if show_versions:
            command.append("--show-versions")
        if category:
            command.extend(["--category", category])
        ret = subprocess.run(command, check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError as e:
        ret = f"Error listing extensions: {{e}}"
    except Exception as e:
        ret = f"Unexpected error: {{e}}"

    return ret
code_list_extensions(show_versions={show_versions}, category={category})
print(ret)
"""

    @agent_action
    def code_list_extensions(self, show_versions, category):

        return self.CODE_LIST_EXTENSIONS_CMD.format(show_versions=repr(show_versions), category=repr(category))

    CODE_UPDATE_EXTENSIONS_CMD = """import json
import os
import subprocess
from pathlib import Path
ret = ""

def code_update_extensions():
    global ret
    try:
        subprocess.run(["code", "--update-extensions"], check=True)
        ret = "Successfully updated extensions"
    except subprocess.CalledProcessError as e:
        ret = f"Error updating extensions: {{e}}"
    except Exception as e:
        ret = f"Unexpected error: {{e}}"

    return ret
code_update_extensions()
print(ret)
"""

    @agent_action
    def code_update_extensions(self):

        return self.CODE_UPDATE_EXTENSIONS_CMD.format()

    CODE_DISABLE_EXTENSION_CMD = """import json
import os
import subprocess
from pathlib import Path
ret = ""

def code_disable_extension(extension_id):
    global ret
    try:
        subprocess.run(["code", "--disable-extension", extension_id], check=True)
        ret = "Successfully disabled extension"
    except subprocess.CalledProcessError as e:
        ret = f"Error disabling extension: {{e}}"
    except Exception as e:
        ret = f"Unexpected error: {{e}}"

    return ret
code_disable_extension(extension_id={extension_id})
print(ret)
"""

    @agent_action
    def code_disable_extension(self, extension_id):

        return self.CODE_DISABLE_EXTENSION_CMD.format(extension_id=repr(extension_id))

    CODE_TOGGLE_SYNC_CMD = """import json
import os
import subprocess
from pathlib import Path
ret = ""

def code_toggle_sync(state):
    global ret
    try:
        command = ["code", "--sync", state]
        subprocess.run(command, check=True)
        ret = "Successfully toggled sync"
    except subprocess.CalledProcessError as e:
        ret = f"Error toggling sync: {{e}}"
    except Exception as e:
        ret = f"Unexpected error: {{e}}"

    return ret
code_toggle_sync(state={state})
print(ret)
"""

    @agent_action
    def code_toggle_sync(self, state):

        return self.CODE_TOGGLE_SYNC_CMD.format(state=repr(state))

    LIBREOFFICE_IMPRESS_SAVE_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_save():
    global ret
    try:
        if doc.hasLocation():
            doc.store()
            ret = "Success"
        else:
            ret = "Error: Document has no save location"
        return True
    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_impress_save()
print(ret)
"""

    @agent_action
    def libreoffice_impress_save(self):

        return self.LIBREOFFICE_IMPRESS_SAVE_CMD.format()

    LIBREOFFICE_IMPRESS_GO_TO_SLIDE_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_go_to_slide(slide_index):
    global ret
    try:
        zero_based_index = slide_index - 1
        controller = doc.getCurrentController()
        if not controller:
            ret = "Error: Could not get document controller"
            return False
        pages = doc.getDrawPages()
        if zero_based_index < 0 or zero_based_index >= pages.getCount():
            ret = f"Error: Slide index {{slide_index}} is out of range. Valid range is 1-{{pages.getCount()}}"
            return False
        target_slide = pages.getByIndex(zero_based_index)
        controller.setCurrentPage(target_slide)
        ret = f"Successfully navigated to slide {{slide_index}}"
        return True
    except Exception as e:
        ret = f"Error navigating to slide: {{str(e)}}"
        return False
libreoffice_impress_go_to_slide(slide_index={slide_index})
print(ret)
"""

    @agent_action
    def libreoffice_impress_go_to_slide(self, slide_index):

        return self.LIBREOFFICE_IMPRESS_GO_TO_SLIDE_CMD.format(slide_index=repr(slide_index))

    LIBREOFFICE_IMPRESS_GET_SLIDE_COUNT_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_get_slide_count():
    global ret
    try:
        pages = doc.getDrawPages()
        count = pages.getCount()
        ret = count
        return count
    except Exception as e:
        ret = f"Error: {{str(e)}}"
        return 0
libreoffice_impress_get_slide_count()
print(ret)
"""

    @agent_action
    def libreoffice_impress_get_slide_count(self):

        return self.LIBREOFFICE_IMPRESS_GET_SLIDE_COUNT_CMD.format()

    LIBREOFFICE_IMPRESS_DUPLICATE_SLIDE_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_duplicate_slide(slide_index):
    global ret
    try:
        zero_based_index = slide_index - 1
        draw_pages = doc.getDrawPages()
        if zero_based_index < 0 or zero_based_index >= draw_pages.getCount():
            ret = f"Error: Invalid slide index {{slide_index}}. Valid range is 1 to {{draw_pages.getCount()}}"
            return False
        controller = doc.getCurrentController()
        controller.setCurrentPage(draw_pages.getByIndex(zero_based_index))
        dispatcher = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.DispatchHelper", ctx)
        frame = controller.getFrame()
        dispatcher.executeDispatch(frame, ".uno:DuplicatePage", "", 0, ())
        duplicated_slide_index = zero_based_index + 1
        slide_count = draw_pages.getCount()
        if duplicated_slide_index < slide_count - 1:
            controller.setCurrentPage(draw_pages.getByIndex(duplicated_slide_index))
            moves_needed = slide_count - duplicated_slide_index - 1
            for _ in range(moves_needed):
                dispatcher.executeDispatch(frame, ".uno:MovePageDown", "", 0, ())
        ret = f"Slide {{slide_index}} duplicated successfully and moved to the end"
        return True
    except Exception as e:
        ret = f"Error: {{str(e)}}"
        return False
libreoffice_impress_duplicate_slide(slide_index={slide_index})
print(ret)
"""

    @agent_action
    def libreoffice_impress_duplicate_slide(self, slide_index):

        return self.LIBREOFFICE_IMPRESS_DUPLICATE_SLIDE_CMD.format(slide_index=repr(slide_index))

    LIBREOFFICE_IMPRESS_SET_SLIDE_FONT_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_set_slide_font(slide_index, font_name):
    global ret
    try:
        zero_based_index = slide_index - 1
        slides = doc.getDrawPages()
        if zero_based_index < 0 or zero_based_index >= slides.getCount():
            ret = f"Error: Slide index {{slide_index}} is out of range. Valid range is 1 to {{slides.getCount()}}."
            return False
        slide = slides.getByIndex(zero_based_index)
        for i in range(slide.getCount()):
            shape = slide.getByIndex(i)
            if hasattr(shape, "getText"):
                text = shape.getText()
                if text:
                    cursor = text.createTextCursor()
                    cursor.gotoStart(False)
                    cursor.gotoEnd(True)
                    cursor.setPropertyValue("CharFontName", font_name)
        ret = f"Successfully set font to '{{font_name}}' for all text elements in slide {{slide_index}}."
        return True
    except Exception as e:
        ret = f"Error setting font: {{str(e)}}"
        return False
libreoffice_impress_set_slide_font(slide_index={slide_index}, font_name={font_name})
print(ret)
"""

    @agent_action
    def libreoffice_impress_set_slide_font(self, slide_index, font_name):

        return self.LIBREOFFICE_IMPRESS_SET_SLIDE_FONT_CMD.format(slide_index=repr(slide_index),
                                                                  font_name=repr(font_name))

    LIBREOFFICE_IMPRESS_WRITE_TEXT_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_write_text(content, page_index, box_index, bold=False, italic=False, size=None, append=False):
    global ret
    try:
        zero_based_page_index = page_index - 1
        pages = doc.getDrawPages()
        if zero_based_page_index < 0 or zero_based_page_index >= pages.getCount():
            ret = f"Error: Page index {{page_index}} is out of range"
            return False
        page = pages.getByIndex(zero_based_page_index)
        if box_index < 0 or box_index >= page.getCount():
            ret = f"Error: Box index {{box_index}} is out of range"
            return False
        shape = page.getByIndex(box_index)
        if not hasattr(shape, "String"):
            ret = f"Error: The shape at index {{box_index}} cannot contain text"
            return False
        if append:
            shape.String = shape.String + content
        else:
            shape.String = content
        if hasattr(shape, "getCharacterProperties"):
            char_props = shape.getCharacterProperties()
            if bold:
                char_props.CharWeight = BOLD
            else:
                char_props.CharWeight = NORMAL
            if italic:
                char_props.CharPosture = ITALIC
            else:
                char_props.CharPosture = NONE
            if size is not None:
                char_props.CharHeight = size

        ret = f"Text successfully written to page {{page_index}}, box {{box_index}}"
        return True
    except Exception as e:
        ret = f"Error: {{str(e)}}"
        return False
libreoffice_impress_write_text(content={content}, page_index={page_index}, box_index={box_index}, bold={bold}, italic={italic}, size={size}, append={append})
print(ret)
"""

    @agent_action
    def libreoffice_impress_write_text(self, content, page_index, box_index, bold, italic, size, append):

        return self.LIBREOFFICE_IMPRESS_WRITE_TEXT_CMD.format(content=repr(content), page_index=repr(page_index),
                                                              box_index=repr(box_index), bold=repr(bold),
                                                              italic=repr(italic), size=repr(size), append=repr(append))

    LIBREOFFICE_IMPRESS_SET_STYLE_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_set_style(slide_index, box_index, bold=None, italic=None, underline=None):
    global ret
    try:
        pages = doc.getDrawPages()
        if slide_index < 1 or slide_index > pages.getCount():
            ret = f"Error: Invalid slide index {{slide_index}}. Valid range is 1 to {{pages.getCount()}}"
            return False
        page = pages.getByIndex(slide_index - 1)
        if box_index < 0 or box_index >= page.getCount():
            ret = f"Error: Invalid box index {{box_index}}. Valid range is 0 to {{page.getCount() - 1}}"
            return False
        shape = page.getByIndex(box_index)
        if not hasattr(shape, "getText"):
            ret = "Error: The specified shape does not contain text"
            return False
        text = shape.getText()
        cursor = text.createTextCursor()
        cursor.gotoStart(False)
        cursor.gotoEnd(True)
        if bold is not None:
            cursor.setPropertyValue("CharWeight", BOLD if bold else NORMAL)
        if italic is not None:
            cursor.setPropertyValue("CharPosture", ITALIC if italic else NONE)
        if underline is not None:
            cursor.setPropertyValue("CharUnderline", 1 if underline else 0)
        ret = "Style applied successfully"
        return True
    except Exception as e:
        ret = f"Error: {{str(e)}}"
        return False
libreoffice_impress_set_style(slide_index={slide_index}, box_index={box_index}, bold={bold}, italic={italic}, underline={underline})
print(ret)
"""

    @agent_action
    def libreoffice_impress_set_style(self, slide_index, box_index, bold, italic, underline):

        return self.LIBREOFFICE_IMPRESS_SET_STYLE_CMD.format(slide_index=repr(slide_index), box_index=repr(box_index),
                                                             bold=repr(bold), italic=repr(italic),
                                                             underline=repr(underline))

    LIBREOFFICE_IMPRESS_CONFIGURE_AUTO_SAVE_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_configure_auto_save(enabled, interval_minutes):
    global ret
    try:
        if interval_minutes < 1:
            interval_minutes = 1
        config_provider = ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.configuration.ConfigurationProvider", ctx
        )
        prop = PropertyValue()
        prop.Name = "nodepath"
        prop.Value = "/org.openoffice.Office.Common/Save/Document"
        config_access = config_provider.createInstanceWithArguments(
            "com.sun.star.configuration.ConfigurationUpdateAccess", (prop,)
        )
        config_access.setPropertyValue("AutoSave", enabled)
        config_access.setPropertyValue("AutoSaveTimeIntervall", interval_minutes)
        config_access.commitChanges()
        ret = f"Auto-save {{'enabled' if enabled else 'disabled'}} with interval of {{interval_minutes}} minutes"
        return True
    except Exception as e:
        ret = f"Error configuring auto-save: {{str(e)}}"
        return False
libreoffice_impress_configure_auto_save(enabled={enabled}, interval_minutes={interval_minutes})
print(ret)
"""

    @agent_action
    def libreoffice_impress_configure_auto_save(self, enabled, interval_minutes):

        return self.LIBREOFFICE_IMPRESS_CONFIGURE_AUTO_SAVE_CMD.format(enabled=repr(enabled),
                                                                       interval_minutes=repr(interval_minutes))

    LIBREOFFICE_IMPRESS_SET_BACKGROUND_COLOR_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_set_background_color(slide_index, box_index, color):
    global ret
    try:
        zero_based_slide_index = slide_index - 1
        slides = doc.getDrawPages()
        if zero_based_slide_index < 0 or zero_based_slide_index >= slides.getCount():
            ret = f"Error: Slide index {{slide_index}} is out of range"
            return False
        slide = slides.getByIndex(zero_based_slide_index)
        if box_index < 0 or box_index >= slide.getCount():
            ret = f"Error: Box index {{box_index}} is out of range"
            return False
        shape = slide.getByIndex(box_index)
        color_int = 0
        color_map = {{
            "red": 16711680,
            "green": 65280,
            "blue": 255,
            "yellow": 16776960,
            "black": 0,
            "white": 16777215,
            "purple": 8388736,
            "orange": 16753920,
            "pink": 16761035,
            "gray": 8421504,
            "brown": 10824234,
            "cyan": 65535,
            "magenta": 16711935,
        }}
        if color.lower() in color_map:
            color_int = color_map[color.lower()]
        elif color.startswith("#") and len(color) == 7:
            color_int = int(color[1:], 16)
        else:
            ret = f"Error: Invalid color format: {{color}}"
            return False
        shape.FillStyle = uno.Enum("com.sun.star.drawing.FillStyle", "SOLID")
        shape.FillColor = color_int
        ret = f"Background color of textbox {{box_index}} on slide {{slide_index}} set to {{color}}"
        return True
    except Exception as e:
        ret = f"Error: {{str(e)}}"
        return False
libreoffice_impress_set_background_color(slide_index={slide_index}, box_index={box_index}, color={color})
print(ret)
"""

    @agent_action
    def libreoffice_impress_set_background_color(self, slide_index, box_index, color):

        return self.LIBREOFFICE_IMPRESS_SET_BACKGROUND_COLOR_CMD.format(slide_index=repr(slide_index),
                                                                        box_index=repr(box_index), color=repr(color))

    LIBREOFFICE_IMPRESS_SET_TEXT_COLOR_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_set_text_color(slide_index, box_index, color):
    global ret
    try:
        zero_based_slide_index = slide_index - 1
        slides = doc.getDrawPages()
        if zero_based_slide_index < 0 or zero_based_slide_index >= slides.getCount():
            ret = f"Error: Slide index {{slide_index}} is out of range"
            return False
        slide = slides.getByIndex(zero_based_slide_index)
        if box_index < 0 or box_index >= slide.getCount():
            ret = f"Error: Box index {{box_index}} is out of range"
            return False
        shape = slide.getByIndex(box_index)
        if not hasattr(shape, "getText"):
            ret = f"Error: Shape at index {{box_index}} does not contain text"
            return False
        color_int = 0
        if color.startswith("#"):
            color_int = int(color[1:], 16)
        else:
            color_map = {{
                "red": 16711680,
                "green": 43315,
                "blue": 255,
                "black": 0,
                "white": 16777215,
                "yellow": 16776960,
                "cyan": 65535,
                "magenta": 16711935,
                "gray": 8421504,
            }}
            if color.lower() in color_map:
                color_int = color_map[color.lower()]
            else:
                ret = f"Error: Unsupported color '{{color}}'"
                return False
        text = shape.getText()
        cursor = text.createTextCursor()
        cursor.gotoStart(False)
        cursor.gotoEnd(True)
        cursor.setPropertyValue("CharColor", color_int)
        ret = f"Successfully set text color to {{color}} for textbox {{box_index}} on slide {{slide_index}}"
        return True
    except Exception as e:
        ret = f"Error: {{str(e)}}"
        return False
libreoffice_impress_set_text_color(slide_index={slide_index}, box_index={box_index}, color={color})
print(ret)
"""

    @agent_action
    def libreoffice_impress_set_text_color(self, slide_index, box_index, color):

        return self.LIBREOFFICE_IMPRESS_SET_TEXT_COLOR_CMD.format(slide_index=repr(slide_index),
                                                                  box_index=repr(box_index), color=repr(color))

    LIBREOFFICE_IMPRESS_DELETE_CONTENT_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_delete_content(slide_index, box_index):
    global ret
    try:
        pages = doc.getDrawPages()
        zero_based_slide_index = slide_index - 1
        if zero_based_slide_index < 0 or zero_based_slide_index >= pages.getCount():
            ret = f"Error: Invalid slide index {{slide_index}}. Valid range is 1 to {{pages.getCount()}}"
            return False
        slide = pages.getByIndex(zero_based_slide_index)
        if box_index < 0 or box_index >= slide.getCount():
            ret = f"Error: Invalid box index {{box_index}}. Valid range is 0 to {{slide.getCount() - 1}}"
            return False
        shape = slide.getByIndex(box_index)
        slide.remove(shape)
        ret = f"Successfully deleted textbox {{box_index}} from slide {{slide_index}}"
        return True
    except Exception as e:
        ret = f"Error: {{str(e)}}"
        return False
libreoffice_impress_delete_content(slide_index={slide_index}, box_index={box_index})
print(ret)
"""

    @agent_action
    def libreoffice_impress_delete_content(self, slide_index, box_index):

        return self.LIBREOFFICE_IMPRESS_DELETE_CONTENT_CMD.format(slide_index=repr(slide_index),
                                                                  box_index=repr(box_index))

    LIBREOFFICE_IMPRESS_SET_SLIDE_ORIENTATION_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_set_slide_orientation(orientation):
    global ret
    try:
        draw_pages = doc.getDrawPages()
        first_page = draw_pages.getByIndex(0)
        current_width = first_page.Width
        current_height = first_page.Height
        if orientation == "portrait" and current_width > current_height:
            new_width, new_height = current_height, current_width
        elif orientation == "landscape" and current_width < current_height:
            new_width, new_height = current_height, current_width
        else:
            ret = f"Slides are already in {{orientation}} orientation"
            return True
        for i in range(draw_pages.getCount()):
            page = draw_pages.getByIndex(i)
            page.Width = new_width
            page.Height = new_height
        ret = f"Changed slide orientation to {{orientation}}"
        return True
    except Exception as e:
        ret = f"Error changing slide orientation: {{str(e)}}"
        return False
libreoffice_impress_set_slide_orientation(orientation={orientation})
print(ret)
"""

    @agent_action
    def libreoffice_impress_set_slide_orientation(self, orientation):

        return self.LIBREOFFICE_IMPRESS_SET_SLIDE_ORIENTATION_CMD.format(orientation=repr(orientation))

    LIBREOFFICE_IMPRESS_POSITION_BOX_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_position_box(slide_index, box_index, position):
    global ret
    try:
        pages = doc.getDrawPages()
        if slide_index < 1 or slide_index > pages.getCount():
            ret = f"Error: Invalid slide index {{slide_index}}"
            return False
        page = pages.getByIndex(slide_index - 1)
        if box_index < 0 or box_index >= page.getCount():
            ret = f"Error: Invalid box index {{box_index}}"
            return False
        shape = page.getByIndex(box_index)
        controller = doc.getCurrentController()
        slide_width = 28000
        slide_height = 21000
        shape_width = shape.Size.Width
        shape_height = shape.Size.Height
        margin = 500
        if position == "left":
            new_x = margin
            new_y = (slide_height - shape_height) / 2
        elif position == "right":
            new_x = slide_width - shape_width - margin
            new_y = (slide_height - shape_height) / 2
        elif position == "center":
            new_x = (slide_width - shape_width) / 2
            new_y = (slide_height - shape_height) / 2
        elif position == "top":
            new_x = (slide_width - shape_width) / 2
            new_y = margin
        elif position == "bottom":
            new_x = (slide_width - shape_width) / 2
            new_y = slide_height - shape_height - margin
        elif position == "top-left":
            new_x = margin
            new_y = margin
        elif position == "top-right":
            new_x = slide_width - shape_width - margin
            new_y = margin
        elif position == "bottom-left":
            new_x = margin
            new_y = slide_height - shape_height - margin
        elif position == "bottom-right":
            new_x = slide_width - shape_width - margin
            new_y = slide_height - shape_height - margin
        else:
            ret = f"Error: Invalid position '{{position}}'"
            return False
        try:
            shape.Position.X = int(new_x)
            shape.Position.Y = int(new_y)
        except:
            try:
                shape.setPropertyValue("PositionX", int(new_x))
                shape.setPropertyValue("PositionY", int(new_y))
            except:
                point = uno.createUnoStruct("com.sun.star.awt.Point", int(new_x), int(new_y))
                shape.setPosition(point)
        ret = f"Box positioned at {{position}} (X: {{new_x}}, Y: {{new_y}})"
        return True
    except Exception as e:
        ret = f"Error positioning box: {{str(e)}}"
        return False
libreoffice_impress_position_box(slide_index={slide_index}, box_index={box_index}, position={position})
print(ret)
"""

    @agent_action
    def libreoffice_impress_position_box(self, slide_index, box_index, position):

        return self.LIBREOFFICE_IMPRESS_POSITION_BOX_CMD.format(slide_index=repr(slide_index),
                                                                box_index=repr(box_index), position=repr(position))

    LIBREOFFICE_IMPRESS_INSERT_FILE_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_insert_file(file_path, slide_index=None, position=None, size=None, autoplay=False):
    global ret
    try:
        expanded_file_path = os.path.expanduser(file_path)
        if not os.path.exists(expanded_file_path):
            ret = f"Error: File not found: {{expanded_file_path}}"
            return False
        file_url = uno.systemPathToFileUrl(os.path.abspath(expanded_file_path))
        pages = doc.getDrawPages()
        if slide_index is not None:
            zero_based_index = slide_index - 1
            if zero_based_index < 0 or zero_based_index >= pages.getCount():
                ret = f"Error: Invalid slide index: {{slide_index}}"
                return False
            slide = pages.getByIndex(zero_based_index)
        else:
            controller = doc.getCurrentController()
            slide = controller.getCurrentPage()
        slide_width = 21000
        slide_height = 12750
        if position is None:
            position = {{"x": 10, "y": 10}}
        if size is None:
            size = {{"width": 80, "height": 60}}
        x = int(position["x"] * slide_width / 100)
        y = int(position["y"] * slide_height / 100)
        width = int(size["width"] * slide_width / 100)
        height = int(size["height"] * slide_height / 100)
        media_shape = doc.createInstance("com.sun.star.presentation.MediaShape")
        slide.add(media_shape)
        media_shape.setPosition(uno.createUnoStruct("com.sun.star.awt.Point", x, y))
        media_shape.setSize(uno.createUnoStruct("com.sun.star.awt.Size", width, height))
        media_shape.setPropertyValue("MediaURL", file_url)
        if autoplay:
            try:
                media_shape.setPropertyValue("MediaIsAutoPlay", True)
            except:
                pass
        ret = f"Video inserted successfully from {{expanded_file_path}}"
        return True
    except Exception as e:
        ret = f"Error inserting video: {{str(e)}}"
        return False
libreoffice_impress_insert_file(file_path={file_path}, slide_index={slide_index}, position={position}, size={size}, autoplay={autoplay})
print(ret)
"""

    @agent_action
    def libreoffice_impress_insert_file(self, file_path, slide_index, position, size, autoplay):

        return self.LIBREOFFICE_IMPRESS_INSERT_FILE_CMD.format(file_path=repr(file_path), slide_index=repr(slide_index),
                                                               position=repr(position), size=repr(size),
                                                               autoplay=repr(autoplay))

    LIBREOFFICE_IMPRESS_SET_SLIDE_BACKGROUND_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_set_slide_background(slide_index=None, color=None, image_path=None):
    global ret
    try:
        if not color and not image_path:
            ret = "Error: Either color or image_path must be provided"
            return False
        pages = doc.getDrawPages()
        page_count = pages.getCount()
        rgb_color = None
        if color:
            if color.startswith("#"):
                color = color.lstrip("#")
                rgb_color = int(color, 16)
            else:
                color_map = {{
                    "red": 16711680,
                    "green": 43315,
                    "blue": 255,
                    "black": 0,
                    "white": 16777215,
                    "yellow": 16776960,
                    "cyan": 65535,
                    "magenta": 16711935,
                    "gray": 8421504,
                }}
                rgb_color = color_map.get(color.lower(), 0)
        if slide_index is not None:
            slide_index = slide_index - 1
            if slide_index < 0 or slide_index >= page_count:
                ret = f"Error: Slide index {{slide_index + 1}} is out of range (1-{{page_count}})"
                return False
            slides_to_modify = [pages.getByIndex(slide_index)]
        else:
            slides_to_modify = [pages.getByIndex(i) for i in range(page_count)]
        for slide in slides_to_modify:
            fill_props = ctx.ServiceManager.createInstanceWithContext(
                "com.sun.star.drawing.FillProperties", ctx
            )
            if image_path and os.path.exists(image_path):
                abs_path = os.path.abspath(image_path)
                file_url = uno.systemPathToFileUrl(abs_path)
                fill_props.FillStyle = uno.Enum("com.sun.star.drawing.FillStyle", "BITMAP")
                fill_props.FillBitmapURL = file_url
                fill_props.FillBitmapMode = uno.Enum("com.sun.star.drawing.BitmapMode", "STRETCH")
            elif rgb_color is not None:
                fill_props.FillStyle = uno.Enum("com.sun.star.drawing.FillStyle", "SOLID")
                fill_props.FillColor = rgb_color
            slide.setPropertyValue("Background", fill_props)
        ret = "Background set successfully"
        return True
    except Exception as e:
        ret = f"Error setting background: {{str(e)}}"
        return False
libreoffice_impress_set_slide_background(slide_index={slide_index}, color={color}, image_path={image_path})
print(ret)
"""

    @agent_action
    def libreoffice_impress_set_slide_background(self, slide_index, color, image_path):

        return self.LIBREOFFICE_IMPRESS_SET_SLIDE_BACKGROUND_CMD.format(slide_index=repr(slide_index),
                                                                        color=repr(color), image_path=repr(image_path))

    LIBREOFFICE_IMPRESS_SAVE_AS_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_save_as(file_path, overwrite=False):
    global ret
    try:
        if os.path.exists(file_path) and not overwrite:
            ret = f"File already exists and overwrite is set to False: {{file_path}}"
            return False
        abs_path = os.path.abspath(file_path)
        if os.name == "nt":
            url = "file:///" + abs_path.replace("\\", "/")
        else:
            url = "file://" + abs_path
        properties = []
        overwrite_prop = PropertyValue()
        overwrite_prop.Name = "Overwrite"
        overwrite_prop.Value = overwrite
        properties.append(overwrite_prop)
        extension = os.path.splitext(file_path)[1].lower()
        if extension == ".odp":
            filter_name = "impress8"
        elif extension == ".ppt":
            filter_name = "MS PowerPoint 97"
        elif extension == ".pptx":
            filter_name = "Impress MS PowerPoint 2007 XML"
        elif extension == ".pdf":
            filter_name = "impress_pdf_Export"
        else:
            filter_name = "impress8"
        filter_prop = PropertyValue()
        filter_prop.Name = "FilterName"
        filter_prop.Value = filter_name
        properties.append(filter_prop)
        doc.storeAsURL(url, tuple(properties))
        ret = f"Document saved successfully to {{file_path}}"
        return True
    except Exception as e:
        ret = f"Error saving document: {{str(e)}}"
        return False
libreoffice_impress_save_as(file_path={file_path}, overwrite={overwrite})
print(ret)
"""

    @agent_action
    def libreoffice_impress_save_as(self, file_path, overwrite):

        return self.LIBREOFFICE_IMPRESS_SAVE_AS_CMD.format(file_path=repr(file_path), overwrite=repr(overwrite))

    LIBREOFFICE_IMPRESS_INSERT_IMAGE_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_insert_image(slide_index, image_path, width=None, height=None, position=None):
    global ret
    try:
        if not os.path.exists(image_path):
            ret = f"Error: Image file not found at {{image_path}}"
            return False
        zero_based_index = slide_index - 1
        slides = doc.getDrawPages()
        if zero_based_index < 0 or zero_based_index >= slides.getCount():
            ret = f"Error: Slide index {{slide_index}} is out of range. Valid range is 1 to {{slides.getCount()}}"
            return False
        slide = slides.getByIndex(zero_based_index)
        bitmap = doc.createInstance("com.sun.star.drawing.BitmapTable")
        image_url = uno.systemPathToFileUrl(os.path.abspath(image_path))
        shape = doc.createInstance("com.sun.star.drawing.GraphicObjectShape")
        shape.setPropertyValue("GraphicURL", image_url)
        slide.add(shape)
        x_pos = 0
        y_pos = 0
        slide_width = slide.Width
        slide_height = slide.Height
        if position:
            if "x" in position:
                x_pos = int(position["x"] / 100 * slide_width)
            if "y" in position:
                y_pos = int(position["y"] / 100 * slide_height)
        current_width = shape.Size.Width
        current_height = shape.Size.Height
        new_width = int(width * 1000) if width is not None else current_width
        new_height = int(height * 1000) if height is not None else current_height
        size = uno.createUnoStruct("com.sun.star.awt.Size")
        size.Width = new_width
        size.Height = new_height
        point = uno.createUnoStruct("com.sun.star.awt.Point")
        point.X = x_pos
        point.Y = y_pos
        shape.Size = size
        shape.Position = point
        ret = f"Image inserted successfully on slide {{slide_index}}"
        return True
    except Exception as e:
        ret = f"Error inserting image: {{str(e)}}"
        return False
libreoffice_impress_insert_image(slide_index={slide_index}, image_path={image_path}, width={width}, height={height}, position={position})
print(ret)
"""

    @agent_action
    def libreoffice_impress_insert_image(self, slide_index, image_path, width, height, position):

        return self.LIBREOFFICE_IMPRESS_INSERT_IMAGE_CMD.format(slide_index=repr(slide_index),
                                                                image_path=repr(image_path), width=repr(width),
                                                                height=repr(height), position=repr(position))

    LIBREOFFICE_IMPRESS_CONFIGURE_DISPLAY_SETTINGS_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_configure_display_settings(use_presenter_view=None, primary_monitor_only=None, monitor_for_presentation=None
    ):
    global ret
    try:
        controller = doc.getCurrentController()
        if not hasattr(controller, "getPropertyValue"):
            ret = "Error: Not an Impress presentation or controller not available"
            return False
        if use_presenter_view is not None:
            try:
                controller.setPropertyValue("IsPresentationViewEnabled", use_presenter_view)
            except Exception as e:
                ret = f"Warning: Could not set presenter view: {{str(e)}}"
        if primary_monitor_only is not None:
            try:
                controller.setPropertyValue("UsePrimaryMonitorOnly", primary_monitor_only)
            except Exception as e:
                ret = f"Warning: Could not set primary monitor usage: {{str(e)}}"
        if monitor_for_presentation is not None:
            try:
                controller.setPropertyValue("MonitorForPresentation", monitor_for_presentation - 1)
            except Exception as e:
                ret = f"Warning: Could not set presentation monitor: {{str(e)}}"
        ret = "Display settings configured successfully"
        return True
    except Exception as e:
        ret = f"Error configuring display settings: {{str(e)}}"
        return False
libreoffice_impress_configure_display_settings(use_presenter_view={use_presenter_view}, primary_monitor_only={primary_monitor_only}, monitor_for_presentation={monitor_for_presentation})
print(ret)
"""

    @agent_action
    def libreoffice_impress_configure_display_settings(self, use_presenter_view, primary_monitor_only,
                                                       monitor_for_presentation):

        return self.LIBREOFFICE_IMPRESS_CONFIGURE_DISPLAY_SETTINGS_CMD.format(
            use_presenter_view=repr(use_presenter_view), primary_monitor_only=repr(primary_monitor_only),
            monitor_for_presentation=repr(monitor_for_presentation))

    LIBREOFFICE_IMPRESS_SET_TEXT_STRIKETHROUGH_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_set_text_strikethrough(slide_index, box_index, line_numbers, apply):
    global ret
    try:
        slides = doc.getDrawPages()
        slide = slides.getByIndex(slide_index - 1)
        shape = slide.getByIndex(box_index)
        if not hasattr(shape, "getText"):
            ret = f"Error: Shape at index {{box_index}} does not contain text"
            return False
        text = shape.getText()
        cursor = text.createTextCursor()
        text_content = text.getString()
        lines = text_content.split("\n")
        for line_number in line_numbers:
            if 1 <= line_number <= len(lines):
                start_pos = 0
                for i in range(line_number - 1):
                    start_pos += len(lines[i]) + 1
                end_pos = start_pos + len(lines[line_number - 1])
                cursor.gotoStart(False)
                cursor.goRight(start_pos, False)
                cursor.goRight(len(lines[line_number - 1]), True)
                cursor.CharStrikeout = apply
        ret = f"Strike-through {{'applied' if apply else 'removed'}} successfully"
        return True
    except Exception as e:
        ret = f"Error: {{str(e)}}"
        return False
libreoffice_impress_set_text_strikethrough(slide_index={slide_index}, box_index={box_index}, line_numbers={line_numbers}, apply={apply})
print(ret)
"""

    @agent_action
    def libreoffice_impress_set_text_strikethrough(self, slide_index, box_index, line_numbers, apply):

        return self.LIBREOFFICE_IMPRESS_SET_TEXT_STRIKETHROUGH_CMD.format(slide_index=repr(slide_index),
                                                                          box_index=repr(box_index),
                                                                          line_numbers=repr(line_numbers),
                                                                          apply=repr(apply))

    LIBREOFFICE_IMPRESS_SET_TEXTBOX_ALIGNMENT_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_set_textbox_alignment(slide_index, box_index, alignment):
    global ret
    try:
        zero_based_slide_index = slide_index - 1
        slides = doc.getDrawPages()
        if zero_based_slide_index < 0 or zero_based_slide_index >= slides.getCount():
            ret = f"Error: Slide index {{slide_index}} out of range"
            return False
        slide = slides.getByIndex(zero_based_slide_index)
        if box_index < 0 or box_index >= slide.getCount():
            ret = f"Error: Box index {{box_index}} out of range"
            return False
        shape = slide.getByIndex(box_index)
        if not hasattr(shape, "getText"):
            ret = "Error: Selected shape does not support text"
            return False
        if alignment == "left":
            shape.TextHorizontalAdjust = LEFT
        elif alignment == "center":
            shape.TextHorizontalAdjust = CENTER
        elif alignment == "right":
            shape.TextHorizontalAdjust = RIGHT
        elif alignment == "justify":
            text = shape.getText()
            cursor = text.createTextCursor()
            cursor.gotoStart(False)
            cursor.gotoEnd(True)
            cursor.ParaAdjust = 3
        else:
            ret = f"Error: Invalid alignment value: {{alignment}}"
            return False
        ret = f"Successfully set text alignment to {{alignment}} for textbox {{box_index}} on slide {{slide_index}}"
        return True
    except Exception as e:
        ret = f"Error: {{str(e)}}"
        return False
libreoffice_impress_set_textbox_alignment(slide_index={slide_index}, box_index={box_index}, alignment={alignment})
print(ret)
"""

    @agent_action
    def libreoffice_impress_set_textbox_alignment(self, slide_index, box_index, alignment):

        return self.LIBREOFFICE_IMPRESS_SET_TEXTBOX_ALIGNMENT_CMD.format(slide_index=repr(slide_index),
                                                                         box_index=repr(box_index),
                                                                         alignment=repr(alignment))

    LIBREOFFICE_IMPRESS_SET_SLIDE_NUMBER_COLOR_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_set_slide_number_color(color):
    global ret
    try:
        color_map = {{
            "black": 0,
            "white": 16777215,
            "red": 16711680,
            "green": 65280,
            "blue": 255,
            "yellow": 16776960,
            "cyan": 65535,
            "magenta": 16711935,
            "gray": 8421504,
            "orange": 16753920,
            "purple": 8388736,
        }}
        if color.lower() in color_map:
            rgb_color = color_map[color.lower()]
        else:
            if color.startswith("#"):
                color = color[1:]
            try:
                if len(color) == 6:
                    rgb_color = int(color, 16)
                else:
                    rgb_color = 0
            except ValueError:
                rgb_color = 0
        found = False
        master_pages = doc.getMasterPages()
        for i in range(master_pages.getCount()):
            master_page = master_pages.getByIndex(i)
            for j in range(master_page.getCount()):
                shape = master_page.getByIndex(j)
                if hasattr(shape, "getText") and shape.getText() is not None:
                    text = shape.getText()
                    try:
                        enum = text.createEnumeration()
                        while enum.hasMoreElements():
                            para = enum.nextElement()
                            if hasattr(para, "createEnumeration"):
                                para_enum = para.createEnumeration()
                                while para_enum.hasMoreElements():
                                    portion = para_enum.nextElement()
                                    if (
                                        hasattr(portion, "TextPortionType")
                                        and portion.TextPortionType == "TextField"
                                    ):
                                        if hasattr(portion, "TextField") and portion.TextField is not None:
                                            field = portion.TextField
                                            if hasattr(field, "supportsService") and (
                                                field.supportsService(
                                                    "com.sun.star.presentation.TextField.PageNumber"
                                                )
                                                or field.supportsService("com.sun.star.text.TextField.PageNumber")
                                            ):
                                                portion.CharColor = rgb_color
                                                found = True
                    except Exception as e:
                        continue
        draw_pages = doc.getDrawPages()
        for i in range(draw_pages.getCount()):
            page = draw_pages.getByIndex(i)
            for j in range(page.getCount()):
                shape = page.getByIndex(j)
                if hasattr(shape, "getText") and shape.getText() is not None:
                    text = shape.getText()
                    try:
                        enum = text.createEnumeration()
                        while enum.hasMoreElements():
                            para = enum.nextElement()
                            if hasattr(para, "createEnumeration"):
                                para_enum = para.createEnumeration()
                                while para_enum.hasMoreElements():
                                    portion = para_enum.nextElement()
                                    if (
                                        hasattr(portion, "TextPortionType")
                                        and portion.TextPortionType == "TextField"
                                    ):
                                        if hasattr(portion, "TextField") and portion.TextField is not None:
                                            field = portion.TextField
                                            if hasattr(field, "supportsService") and (
                                                field.supportsService(
                                                    "com.sun.star.presentation.TextField.PageNumber"
                                                )
                                                or field.supportsService("com.sun.star.text.TextField.PageNumber")
                                            ):
                                                portion.CharColor = rgb_color
                                                found = True
                    except Exception as e:
                        continue
        for i in range(draw_pages.getCount()):
            page = draw_pages.getByIndex(i)
            for j in range(page.getCount()):
                shape = page.getByIndex(j)
                if hasattr(shape, "getText") and shape.getText() is not None:
                    text = shape.getText()
                    text_string = text.getString()
                    if text_string.isdigit() and len(text_string) <= 3:
                        try:
                            cursor = text.createTextCursor()
                            cursor.gotoStart(False)
                            cursor.gotoEnd(True)
                            cursor.CharColor = rgb_color
                            found = True
                        except Exception as e:
                            continue
        if found:
            ret = f"Slide number color set to {{color}}"
            return True
        else:
            ret = "Could not find slide numbers to change color"
            return False
    except Exception as e:
        ret = f"Error setting slide number color: {{str(e)}}"
        return False
libreoffice_impress_set_slide_number_color(color={color})
print(ret)
"""

    @agent_action
    def libreoffice_impress_set_slide_number_color(self, color):

        return self.LIBREOFFICE_IMPRESS_SET_SLIDE_NUMBER_COLOR_CMD.format(color=repr(color))

    LIBREOFFICE_IMPRESS_EXPORT_TO_IMAGE_CMD = """import json
import os
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.drawing.TextHorizontalAdjust import CENTER, LEFT, RIGHT
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_impress_export_to_image(file_path, format, slide_index=None):
    global ret
    try:
        format = format.lower()
        valid_formats = ["png", "jpeg", "jpg", "gif", "bmp", "tiff"]
        if format not in valid_formats:
            ret = f"Error: Invalid format '{{format}}'. Valid formats are: {{', '.join(valid_formats)}}"
            return False
        if format == "jpg":
            format = "jpeg"
        pages = doc.getDrawPages()
        page_count = pages.getCount()
        if slide_index is not None:
            slide_index = slide_index - 1
            if slide_index < 0 or slide_index >= page_count:
                ret = f"Error: Invalid slide index {{slide_index + 1}}. Valid range is 1 to {{page_count}}"
                return False
        controller = doc.getCurrentController()
        filter_name = f"draw_{{format}}_Export"
        filter_data = PropertyValue(Name="FilterData", Value=())
        if slide_index is not None:
            controller.setCurrentPage(pages.getByIndex(slide_index))
            props = PropertyValue(Name="FilterName", Value=filter_name), filter_data
            doc.storeToURL(uno.systemPathToFileUrl(file_path), props)
            ret = f"Successfully exported slide {{slide_index + 1}} to {{file_path}}"
            return True
        else:
            base_name, ext = os.path.splitext(file_path)
            for i in range(page_count):
                controller.setCurrentPage(pages.getByIndex(i))
                if page_count == 1:
                    current_file = f"{{base_name}}.{{format}}"
                else:
                    current_file = f"{{base_name}}_{{i + 1}}.{{format}}"
                props = PropertyValue(Name="FilterName", Value=filter_name), filter_data
                doc.storeToURL(uno.systemPathToFileUrl(current_file), props)

            if page_count == 1:
                ret = f"Successfully exported {{page_count}} slides to {{base_name}}.{{format}}"
            else:
                ret = f"Successfully exported {{page_count}} slides to {{base_name}}_[1-{{page_count}}].{{format}}"
            return True
    except Exception as e:
        ret = f"Error exporting to image: {{str(e)}}"
        return False
libreoffice_impress_export_to_image(file_path={file_path}, format={format}, slide_index={slide_index})
print(ret)
"""

    @agent_action
    def libreoffice_impress_export_to_image(self, file_path, format, slide_index):

        return self.LIBREOFFICE_IMPRESS_EXPORT_TO_IMAGE_CMD.format(file_path=repr(file_path), format=repr(format),
                                                                   slide_index=repr(slide_index))

    LIBREOFFICE_WRITER_SAVE_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_save():
    global ret
    try:
        if doc.hasLocation():
            doc.store()
        else:
            raise Exception("文档没有保存位置，请使用另存为功能")
        return True
    except Exception as e:
        return False
libreoffice_writer_save()
print(ret)
"""

    @agent_action
    def libreoffice_writer_save(self):

        return self.LIBREOFFICE_WRITER_SAVE_CMD.format()

    LIBREOFFICE_WRITER_WRITE_TEXT_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
global_text = doc.Text
cursor = global_text.createTextCursor()
ret = ""

def libreoffice_writer_write_text(text, bold=False, italic=False, size=None):
    global ret
    cursor.CharWeight = 150 if bold else 100
    cursor.CharPosture = ITALIC if italic else NONE
    if size:
        cursor.CharHeight = size
    global_text.insertString(cursor, text, False)
    ret = "Success"
libreoffice_writer_write_text(text={text}, bold={bold}, italic={italic}, size={size})
print(ret)
"""

    @agent_action
    def libreoffice_writer_write_text(self, text, bold, italic, size):

        return self.LIBREOFFICE_WRITER_WRITE_TEXT_CMD.format(text=repr(text), bold=repr(bold), italic=repr(italic),
                                                             size=repr(size))

    LIBREOFFICE_WRITER_SET_COLOR_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_set_color(pattern, color, paragraph_indices=None):
    global ret
    try:
        enum = doc.Text.createEnumeration()
        paragraphs = []
        while enum.hasMoreElements():
            paragraphs.append(enum.nextElement())
        if not paragraph_indices:
            paragraphs_to_process = range(len(paragraphs))
        else:
            paragraphs_to_process = paragraph_indices
        regex = re.compile(pattern)
        for idx in paragraphs_to_process:
            if idx < 0 or idx >= len(paragraphs):
                continue
            paragraph = paragraphs[idx]
            if not paragraph.supportsService("com.sun.star.text.Paragraph"):
                continue
            para_text = paragraph.getString()
            matches = regex.finditer(para_text)
            for match in matches:
                para_cursor = text.createTextCursorByRange(paragraph.getStart())
                para_cursor.goRight(match.start(), False)
                para_cursor.goRight(match.end() - match.start(), True)
                para_cursor.CharColor = color
        ret = "Success"
        return True
    except Exception as e:
        ret = f"Error: {{str(e)}}"
        return False
libreoffice_writer_set_color(pattern={pattern}, color={color}, paragraph_indices={paragraph_indices})
print(ret)
"""

    @agent_action
    def libreoffice_writer_set_color(self, pattern, color, paragraph_indices):

        return self.LIBREOFFICE_WRITER_SET_COLOR_CMD.format(pattern=repr(pattern), color=repr(color),
                                                            paragraph_indices=repr(paragraph_indices))

    LIBREOFFICE_WRITER_FIND_AND_REPLACE_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_find_and_replace(pattern, replacement, paragraph_indices=None):
    global ret
    try:
        enum = doc.Text.createEnumeration()
        paragraphs = []
        while enum.hasMoreElements():
            paragraphs.append(enum.nextElement())
        total_replacements = 0
        if not paragraph_indices:
            paragraphs_to_process = list(range(len(paragraphs)))
        else:
            paragraphs_to_process = [i for i in paragraph_indices if 0 <= i < len(paragraphs)]
        regex = re.compile(pattern)
        for idx in paragraphs_to_process:
            if idx >= len(paragraphs):
                continue
            paragraph = paragraphs[idx]
            if paragraph.supportsService("com.sun.star.text.Paragraph"):
                text_content = paragraph.getString()
                new_text, count = regex.subn(replacement, text_content)
                if count > 0:
                    paragraph.setString(new_text)
                    total_replacements += count
        ret = f"Successfully made {{total_replacements}} replacements"
        return ret
    except Exception as e:
        ret = f"Error during find and replace: {{str(e)}}"
        return ret
libreoffice_writer_find_and_replace(pattern={pattern}, replacement={replacement}, paragraph_indices={paragraph_indices})
print(ret)
"""

    @agent_action
    def libreoffice_writer_find_and_replace(self, pattern, replacement, paragraph_indices=None):

        return self.LIBREOFFICE_WRITER_FIND_AND_REPLACE_CMD.format(pattern=repr(pattern), replacement=repr(replacement),
                                                                   paragraph_indices=repr(paragraph_indices))

    LIBREOFFICE_WRITER_SET_FONT_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_set_font(font_name, paragraph_indices=None):
    global ret
    try:
        text = doc.getText()
        enum = text.createEnumeration()
        paragraphs = []
        while enum.hasMoreElements():
            paragraphs.append(enum.nextElement())
        if not paragraph_indices:
            paragraph_indices = range(len(paragraphs))
        for idx in paragraph_indices:
            if 0 <= idx < len(paragraphs):
                paragraph = paragraphs[idx]
                cursor = text.createTextCursorByRange(paragraph)
                cursor.CharFontName = font_name
        ret = "Success"
        return True
    except Exception as e:
        ret = f"Error: {{str(e)}}"
        return False
libreoffice_writer_set_font(font_name={font_name}, paragraph_indices={paragraph_indices})
print(ret)
"""

    # @agent_action
    # def libreoffice_writer_set_font(self, font_name, paragraph_indices):
    #
    #     return self.LIBREOFFICE_WRITER_SET_FONT_CMD.format(font_name=repr(font_name),
    #                                                        paragraph_indices=repr(paragraph_indices))
    @agent_action
    def libreoffice_writer_set_font(self, font_name, paragraph_indices=None):

        return self.LIBREOFFICE_WRITER_SET_FONT_CMD.format(font_name=repr(font_name),
                                                           paragraph_indices=repr(paragraph_indices))

    LIBREOFFICE_WRITER_SET_LINE_SPACING_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_set_line_spacing(spacing_value, paragraph_indices=None):
    global ret
    try:
        text = doc.getText()
        paragraph_enum = text.createEnumeration()
        line_spacing_value = int(spacing_value * 100)
        current_index = 0

        while paragraph_enum.hasMoreElements():
            paragraph = paragraph_enum.nextElement()

            if not paragraph_indices or current_index in paragraph_indices:
                line_spacing = uno.createUnoStruct("com.sun.star.style.LineSpacing")
                line_spacing.Mode = 0
                line_spacing.Height = line_spacing_value
                paragraph.ParaLineSpacing = line_spacing

            if paragraph.String.strip():
                current_index += 1

        ret = "Success"
        return True
    except Exception as e:
        ret = f"Error: {{str(e)}}"
        return False
libreoffice_writer_set_line_spacing(spacing_value={spacing_value}, paragraph_indices={paragraph_indices})
print(ret)
"""

    @agent_action
    def libreoffice_writer_set_line_spacing(self, spacing_value, paragraph_indices):

        return self.LIBREOFFICE_WRITER_SET_LINE_SPACING_CMD.format(spacing_value=repr(spacing_value),
                                                                   paragraph_indices=repr(paragraph_indices))

    LIBREOFFICE_WRITER_REMOVE_HIGHLIGHTING_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_remove_highlighting(paragraph_indices=None):
    global ret
    try:
        text = doc.getText()
        paragraphs = text.createEnumeration()
        target_indices = set(paragraph_indices) if paragraph_indices else None
        current_index = 0

        while paragraphs.hasMoreElements():
            paragraph = paragraphs.nextElement()
            if target_indices is None or current_index in target_indices:
                if paragraph.supportsService("com.sun.star.text.Paragraph"):
                    para_cursor = text.createTextCursorByRange(paragraph)
                    # Remove all highlighting by setting back color to -1
                    para_cursor.CharBackColor = -1

                    # Additional cleanup for individual text portions (optional)
                    text_portions = paragraph.createEnumeration()
                    while text_portions.hasMoreElements():
                        text_portion = text_portions.nextElement()
                        if hasattr(text_portion, "CharBackColor"):
                            portion_cursor = text.createTextCursorByRange(text_portion)
                            portion_cursor.CharBackColor = -1
            current_index += 1

        ret = "Successfully removed all highlighting"
        return ret
    except Exception as e:
        ret = f"Error removing highlighting: {{str(e)}}"
        return ret
libreoffice_writer_remove_highlighting(paragraph_indices={paragraph_indices})
print(ret)
"""

    @agent_action
    def libreoffice_writer_remove_highlighting(self, paragraph_indices):

        return self.LIBREOFFICE_WRITER_REMOVE_HIGHLIGHTING_CMD.format(paragraph_indices=repr(paragraph_indices))

    LIBREOFFICE_WRITER_FIND_HIGHLIGHTED_TEXT_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_find_highlighted_text(highlight_color):
    global ret
    color_map = {{
        "yellow": 16776960,
        "green": 65280,
        "blue": 255,
        "red": 16711680,
        "cyan": 65535,
        "magenta": 16711935,
        "black": 0,
        "white": 16777215,
        "gray": 8421504,
        "lightgray": 12632256,
    }}
    target_color = None
    if highlight_color.lower() in color_map:
        target_color = color_map[highlight_color.lower()]
    elif highlight_color.startswith("#") and len(highlight_color) == 7:
        try:
            hex_color = highlight_color[1:]
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            target_color = (r << 16) + (g << 8) + b
        except ValueError:
            ret = f"Invalid hex color format: {{highlight_color}}"
            return []
    else:
        ret = f"Unsupported color format: {{highlight_color}}"
        return []
    highlighted_text = []
    text = doc.getText()
    enum_paragraphs = text.createEnumeration()
    while enum_paragraphs.hasMoreElements():
        paragraph = enum_paragraphs.nextElement()
        if paragraph.supportsService("com.sun.star.text.Paragraph"):
            enum_portions = paragraph.createEnumeration()
            while enum_portions.hasMoreElements():
                text_portion = enum_portions.nextElement()
                if hasattr(text_portion, "CharBackColor") and text_portion.CharBackColor == target_color:
                    if text_portion.getString().strip():
                        highlighted_text.append(text_portion.getString())
    ret = f"Found {{len(highlighted_text)}} text segments with highlight color {{highlight_color}}"
    return highlighted_text
libreoffice_writer_find_highlighted_text(highlight_color={highlight_color})
print(ret)
"""

    @agent_action
    def libreoffice_writer_find_highlighted_text(self, highlight_color):

        return self.LIBREOFFICE_WRITER_FIND_HIGHLIGHTED_TEXT_CMD.format(highlight_color=repr(highlight_color))

    LIBREOFFICE_WRITER_INSERT_FORMULA_AT_CURSOR_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_insert_formula_at_cursor(formula):
    global ret
    try:
        embedded_obj = doc.createInstance("com.sun.star.text.TextEmbeddedObject")
        embedded_obj.setPropertyValue("CLSID", "078B7ABA-54FC-457F-8551-6147e776a997")
        embedded_obj.setPropertyValue("AnchorType", AS_CHARACTER)
        text.insertTextContent(cursor, embedded_obj, False)
        math_obj = embedded_obj.getEmbeddedObject()
        math_obj.Formula = formula
        ret = "Formula inserted successfully"
        return True
    except Exception as e:
        ret = f"Error inserting formula: {{str(e)}}"
        return False
libreoffice_writer_insert_formula_at_cursor(formula={formula})
print(ret)
"""

    @agent_action
    def libreoffice_writer_insert_formula_at_cursor(self, formula):

        return self.LIBREOFFICE_WRITER_INSERT_FORMULA_AT_CURSOR_CMD.format(formula=repr(formula))

    LIBREOFFICE_WRITER_INSERT_IMAGE_AT_CURSOR_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_insert_image_at_cursor(image_path, width=None, height=None):
    global ret
    try:
        if image_path.startswith("~"):
            image_path = os.path.expanduser(image_path)
        if not os.path.exists(image_path):
            ret = f"Error: Image file not found at {{image_path}}"
            return ret
        image_path = os.path.abspath(image_path)
        if os.name == "nt":
            file_url = "file:///" + image_path.replace("\\", "/")
        else:
            file_url = "file://" + image_path
        graphic = doc.createInstance("com.sun.star.text.GraphicObject")
        graphic.GraphicURL = file_url
        graphic.AnchorType = AS_CHARACTER
        if width is not None:
            graphic.Width = width * 100
        if height is not None:
            graphic.Height = height * 100
        text.insertTextContent(cursor, graphic, False)
        ret = "Success: Image inserted"
        return ret
    except Exception as e:
        ret = f"Error: {{str(e)}}"
        return ret
libreoffice_writer_insert_image_at_cursor(image_path={image_path}, width={width}, height={height})
print(ret)
"""

    @agent_action
    def libreoffice_writer_insert_image_at_cursor(self, image_path, width, height):

        return self.LIBREOFFICE_WRITER_INSERT_IMAGE_AT_CURSOR_CMD.format(image_path=repr(image_path), width=repr(width),
                                                                         height=repr(height))

    LIBREOFFICE_WRITER_SET_STRIKETHROUGH_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_set_strikethrough(pattern, paragraph_indices=None):
    global ret
    try:
        paragraphs = doc.getText().createEnumeration()
        para_index = 0
        found_matches = 0
        while paragraphs.hasMoreElements():
            paragraph = paragraphs.nextElement()
            if paragraph.supportsService("com.sun.star.text.Paragraph"):
                if paragraph_indices and para_index not in paragraph_indices:
                    para_index += 1
                    continue
                para_text = paragraph.getString()
                matches = list(re.finditer(pattern, para_text))
                for match in matches:
                    text_range = paragraph.getStart()
                    cursor = doc.getText().createTextCursorByRange(text_range)
                    cursor.goRight(match.start(), False)
                    cursor.goRight(match.end() - match.start(), True)
                    cursor.CharStrikeout = 1
                    found_matches += 1
                para_index += 1
        ret = f"Successfully applied strikethrough to {{found_matches}} matches of pattern: {{pattern}}"
        return ret
    except Exception as e:
        ret = f"Error applying strikethrough: {{str(e)}}"
        return ret
libreoffice_writer_set_strikethrough(pattern={pattern}, paragraph_indices={paragraph_indices})
print(ret)
"""

    @agent_action
    def libreoffice_writer_set_strikethrough(self, pattern, paragraph_indices):

        return self.LIBREOFFICE_WRITER_SET_STRIKETHROUGH_CMD.format(pattern=repr(pattern),
                                                                    paragraph_indices=repr(paragraph_indices))

    LIBREOFFICE_WRITER_SET_FONT_SIZE_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_set_font_size(font_size, pattern, paragraph_indices=None):
    global ret
    try:
        regex = re.compile(pattern)
        paragraphs = doc.getText().createEnumeration()
        current_index = 0
        while paragraphs.hasMoreElements():
            paragraph = paragraphs.nextElement()
            if paragraph_indices and current_index not in paragraph_indices:
                current_index += 1
                continue
            if paragraph.supportsService("com.sun.star.text.Paragraph"):
                para_cursor = text.createTextCursorByRange(paragraph)
                para_text = paragraph.getString()
                matches = list(regex.finditer(para_text))
                for match in reversed(matches):
                    start_pos = match.start()
                    end_pos = match.end()
                    para_cursor.gotoStart(False)
                    para_cursor.goRight(start_pos, False)
                    para_cursor.goRight(end_pos - start_pos, True)
                    para_cursor.CharHeight = font_size
            current_index += 1
        ret = f"Successfully changed font size to {{font_size}} for text matching '{{pattern}}'"
        return ret
    except Exception as e:
        ret = f"Error changing font size: {{str(e)}}"
        return ret
libreoffice_writer_set_font_size(font_size={font_size}, pattern={pattern}, paragraph_indices={paragraph_indices})
print(ret)
"""

    @agent_action
    def libreoffice_writer_set_font_size(self, font_size, pattern, paragraph_indices):

        return self.LIBREOFFICE_WRITER_SET_FONT_SIZE_CMD.format(font_size=repr(font_size), pattern=repr(pattern),
                                                                paragraph_indices=repr(paragraph_indices))

    LIBREOFFICE_WRITER_EXPORT_TO_PDF_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_export_to_pdf(output_path=None, output_filename=None, include_comments=False, quality="standard"):
    global ret
    try:
        doc_url = doc.getURL()
        if not doc_url and not output_path:
            return "Error: Document has not been saved and no output path provided"
        if doc_url:
            doc_path = uno.fileUrlToSystemPath(os.path.dirname(doc_url))
            doc_filename = os.path.basename(doc_url)
            doc_name = os.path.splitext(doc_filename)[0]
        else:
            doc_path = ""
            doc_name = "export"
        final_path = output_path if output_path else doc_path
        final_filename = output_filename if output_filename else f"{{doc_name}}.pdf"
        if not final_filename.lower().endswith(".pdf"):
            final_filename += ".pdf"
        full_output_path = os.path.join(final_path, final_filename)
        output_url = uno.systemPathToFileUrl(full_output_path)
        export_props = []
        if quality == "high":
            export_props.append(PropertyValue(Name="SelectPdfVersion", Value=1))
        elif quality == "print":
            export_props.append(PropertyValue(Name="SelectPdfVersion", Value=2))
        else:
            export_props.append(PropertyValue(Name="SelectPdfVersion", Value=0))
        export_props.append(PropertyValue(Name="ExportNotes", Value=include_comments))
        export_props.extend(
            [
                PropertyValue(Name="FilterName", Value="writer_pdf_Export"),
                PropertyValue(Name="Overwrite", Value=True),
            ]
        )
        doc.storeToURL(output_url, tuple(export_props))
        ret = f"PDF exported to: {{full_output_path}}"
        return full_output_path
    except Exception as e:
        ret = f"Error exporting to PDF: {{str(e)}}"
        return ret
libreoffice_writer_export_to_pdf(output_path={output_path}, output_filename={output_filename}, include_comments={include_comments}, quality={quality})
print(ret)
"""

    @agent_action
    def libreoffice_writer_export_to_pdf(self, output_path=None, output_filename=None, include_comments=False,
                                         quality="standard"):

        return self.LIBREOFFICE_WRITER_EXPORT_TO_PDF_CMD.format(output_path=repr(output_path),
                                                                    output_filename=repr(output_filename),
                                                                    include_comments=repr(include_comments),
                                                                    quality=repr(quality))
    # @agent_action
    # def libreoffice_writer_export_to_pdf(self, output_path, output_filename, include_comments, quality):
    #
    #     return self.LIBREOFFICE_WRITER_EXPORT_TO_PDF_CMD.format(output_path=repr(output_path),
    #                                                             output_filename=repr(output_filename),
    #                                                             include_comments=repr(include_comments),
    #                                                             quality=repr(quality))

    LIBREOFFICE_WRITER_SET_PARAGRAPH_ALIGNMENT_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_set_paragraph_alignment(alignment, paragraph_indices=None):
    global ret
    try:
        alignment_map = {{"left": LEFT, "center": CENTER, "right": RIGHT, "justify": 3}}
        if alignment.lower() not in alignment_map:
            ret = f"Error: Invalid alignment '{{alignment}}'. Use 'left', 'center', 'right', or 'justify'."
            return ret
        alignment_value = alignment_map[alignment.lower()]
        text = doc.getText()
        paragraph_enum = text.createEnumeration()
        paragraphs = []
        while paragraph_enum.hasMoreElements():
            paragraph = paragraph_enum.nextElement()
            if paragraph.supportsService("com.sun.star.text.Paragraph"):
                paragraphs.append(paragraph)
        if paragraph_indices:
            valid_indices = [i for i in paragraph_indices if 0 <= i < len(paragraphs)]
            if len(valid_indices) != len(paragraph_indices):
                ret = f"Warning: Some paragraph indices were out of range (0-{{len(paragraphs) - 1}})"
            for idx in valid_indices:
                paragraphs[idx].ParaAdjust = alignment_value
        else:
            for paragraph in paragraphs:
                paragraph.ParaAdjust = alignment_value
        ret = f"Successfully applied '{{alignment}}' alignment to paragraphs"
        return ret
    except Exception as e:
        ret = f"Error setting paragraph alignment: {{str(e)}}"
        return ret
libreoffice_writer_set_paragraph_alignment(alignment={alignment}, paragraph_indices={paragraph_indices})
print(ret)
"""

    @agent_action
    def libreoffice_writer_set_paragraph_alignment(self, alignment, paragraph_indices):

        return self.LIBREOFFICE_WRITER_SET_PARAGRAPH_ALIGNMENT_CMD.format(alignment=repr(alignment),
                                                                          paragraph_indices=repr(paragraph_indices))

    LIBREOFFICE_WRITER_CAPITALIZE_WORDS_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_capitalize_words(paragraph_indices=None):
    global ret
    try:
        text = doc.getText()
        enum = text.createEnumeration()
        paragraphs = []
        while enum.hasMoreElements():
            paragraph = enum.nextElement()
            if paragraph.supportsService("com.sun.star.text.Paragraph"):
                paragraphs.append(paragraph)
        if not paragraph_indices:
            target_paragraphs = list(range(len(paragraphs)))
        else:
            target_paragraphs = paragraph_indices
        valid_indices = [idx for idx in target_paragraphs if 0 <= idx < len(paragraphs)]
        for idx in valid_indices:
            paragraph = paragraphs[idx]
            text_content = paragraph.getString()
            if not text_content.strip():
                continue
            capitalized_text = " ".join(word.capitalize() if word else "" for word in text_content.split(" "))
            para_cursor = text.createTextCursorByRange(paragraph.getStart())
            para_cursor.gotoRange(paragraph.getEnd(), True)
            para_cursor.setString(capitalized_text)
        ret = f"Successfully capitalized words in {{len(valid_indices)}} paragraphs"
        return ret
    except Exception as e:
        ret = f"Error capitalizing words: {{str(e)}}"
        return ret
libreoffice_writer_capitalize_words(paragraph_indices={paragraph_indices})
print(ret)
"""

    @agent_action
    def libreoffice_writer_capitalize_words(self, paragraph_indices):

        return self.LIBREOFFICE_WRITER_CAPITALIZE_WORDS_CMD.format(paragraph_indices=repr(paragraph_indices))

    LIBREOFFICE_WRITER_SET_DEFAULT_FONT_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_set_default_font(font_name, font_size=None):
    global ret
    try:
        style_families = doc.getStyleFamilies()
        paragraph_styles = style_families.getByName("ParagraphStyles")
        default_style_names = ["Default", "Standard", "Normal"]
        standard_style = None
        for style_name in default_style_names:
            if paragraph_styles.hasByName(style_name):
                standard_style = paragraph_styles.getByName(style_name)
                break
        if standard_style is None:
            style_names = paragraph_styles.getElementNames()
            if style_names:
                standard_style = paragraph_styles.getByName(style_names[0])
            else:
                raise Exception("Could not find default paragraph style")
        standard_style.setPropertyValue("CharFontName", font_name)
        standard_style.setPropertyValue("CharFontNameAsian", font_name)
        standard_style.setPropertyValue("CharFontNameComplex", font_name)
        if font_size is not None:
            standard_style.setPropertyValue("CharHeight", float(font_size))
            standard_style.setPropertyValue("CharHeightAsian", float(font_size))
            standard_style.setPropertyValue("CharHeightComplex", float(font_size))
        cursor.setPropertyValue("CharFontName", font_name)
        cursor.setPropertyValue("CharFontNameAsian", font_name)
        cursor.setPropertyValue("CharFontNameComplex", font_name)
        if font_size is not None:
            cursor.setPropertyValue("CharHeight", float(font_size))
            cursor.setPropertyValue("CharHeightAsian", float(font_size))
            cursor.setPropertyValue("CharHeightComplex", float(font_size))
        ret = f"Default font set to '{{font_name}}'" + (f" with size {{font_size}}pt" if font_size else "")
        return ret
    except Exception as e:
        ret = f"Error setting default font: {{str(e)}}"
        return ret
libreoffice_writer_set_default_font(font_name={font_name}, font_size={font_size})
print(ret)
"""

    @agent_action
    def libreoffice_writer_set_default_font(self, font_name, font_size=None):

        return self.LIBREOFFICE_WRITER_SET_DEFAULT_FONT_CMD.format(font_name=repr(font_name), font_size=repr(font_size))

    # @agent_action
    # def libreoffice_writer_set_default_font(self, font_name, font_size):
    #
    #     return self.LIBREOFFICE_WRITER_SET_DEFAULT_FONT_CMD.format(font_name=repr(font_name), font_size=repr(font_size))

    LIBREOFFICE_WRITER_ADD_PAGE_NUMBERS_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_add_page_numbers(position, start_number=1, format=None):
    global ret
    try:
        page_styles = doc.StyleFamilies.getByName("PageStyles")
        default_style = page_styles.getByName("Standard")
        try:
            default_style.setPropertyValue("PageNumberOffset", start_number)
        except:
            pass
        if position.startswith("top"):
            default_style.HeaderIsOn = True
            target = default_style.HeaderText
        else:
            default_style.FooterIsOn = True
            target = default_style.FooterText
        cursor = target.createTextCursor()
        cursor.gotoStart(False)
        cursor.gotoEnd(True)
        cursor.setString("")
        cursor.gotoStart(False)
        if position.endswith("_left"):
            cursor.ParaAdjust = LEFT
        elif position.endswith("_center"):
            cursor.ParaAdjust = CENTER
        elif position.endswith("_right"):
            cursor.ParaAdjust = RIGHT
        if not format or format == "1":
            page_number = doc.createInstance("com.sun.star.text.TextField.PageNumber")
            page_number.NumberingType = 4
            target.insertTextContent(cursor, page_number, False)
        elif format == "Page 1" or "Page" in format and "of" not in format:
            target.insertString(cursor, "Page ", False)
            page_number = doc.createInstance("com.sun.star.text.TextField.PageNumber")
            page_number.NumberingType = 4
            target.insertTextContent(cursor, page_number, False)
        elif format == "1 of N" or format == "Page {{page}} of {{total}}" or "of" in format:
            if "Page" in format:
                target.insertString(cursor, "Page ", False)
            page_number = doc.createInstance("com.sun.star.text.TextField.PageNumber")
            page_number.NumberingType = 4
            target.insertTextContent(cursor, page_number, False)
            target.insertString(cursor, " of ", False)
            page_count = doc.createInstance("com.sun.star.text.TextField.PageCount")
            page_count.NumberingType = 4
            target.insertTextContent(cursor, page_count, False)
        else:
            page_number = doc.createInstance("com.sun.star.text.TextField.PageNumber")
            page_number.NumberingType = 4
            target.insertTextContent(cursor, page_number, False)
        ret = "Successfully added page numbers"
        return ret
    except Exception as e:
        ret = f"Error adding page numbers: {{str(e)}}"
        return ret
libreoffice_writer_add_page_numbers(position={position}, start_number={start_number}, format={format})
print(ret)
"""

    @agent_action
    def libreoffice_writer_add_page_numbers(self, position, start_number=1, format=None):
        return self.LIBREOFFICE_WRITER_ADD_PAGE_NUMBERS_CMD.format(position=repr(position),
                                                                   start_number=repr(start_number),
                                                                   format=repr(format))

    # @agent_action
    # def libreoffice_writer_add_page_numbers(self, position, start_number, format):
    #
    #     return self.LIBREOFFICE_WRITER_ADD_PAGE_NUMBERS_CMD.format(position=repr(position),
    #                                                                start_number=repr(start_number), format=repr(format))

    LIBREOFFICE_WRITER_INSERT_PAGE_BREAK_CMD = """import os
import re
import uno
from com.sun.star.awt.FontSlant import ITALIC, NONE, OBLIQUE
from com.sun.star.awt.FontWeight import BOLD, NORMAL
from com.sun.star.beans import PropertyValue
from com.sun.star.style.ParagraphAdjust import CENTER, LEFT, RIGHT
from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
text = doc.Text
cursor = text.createTextCursor()
ret = ""

def libreoffice_writer_insert_page_break(position="at_cursor"):
    global ret
    try:
        if position == "end_of_document":
            cursor.gotoEnd(False)
        text.insertControlCharacter(cursor, PARAGRAPH_BREAK, False)
        cursor.gotoStartOfParagraph(True)
        cursor.BreakType = uno.Enum("com.sun.star.style.BreakType", "PAGE_BEFORE")
        ret = "Page break inserted successfully"
        return True
    except Exception as e:
        ret = f"Error inserting page break: {{str(e)}}"
        return False
libreoffice_writer_insert_page_break(position={position})
print(ret)
"""

    @agent_action
    def libreoffice_writer_insert_page_break(self, position):

        return self.LIBREOFFICE_WRITER_INSERT_PAGE_BREAK_CMD.format(position=repr(position))

    LIBREOFFICE_CALC_SAVE_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_save():
    global ret
    try:
        # Just save the document
        doc.store()
        ret = "Success"
        return True
    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_save()
print(ret)
"""

    @agent_action
    def libreoffice_calc_save(self):

        return self.LIBREOFFICE_CALC_SAVE_CMD.format()

    LIBREOFFICE_CALC_GET_WORKBOOK_INFO_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_get_workbook_info():
    global ret
    try:
        info = {{
            "file_path": doc.getLocation(),
            "file_title": doc.getTitle(),
            "sheets": [],
            "active_sheet": sheet.Name,
        }}

        # Get sheets information
        sheets = doc.getSheets()
        info["sheet_count"] = sheets.getCount()

        # Get all sheet names and info
        for i in range(sheets.getCount()):
            sheet = sheets.getByIndex(i)
            cursor = sheet.createCursor()
            cursor.gotoEndOfUsedArea(False)
            end_col = cursor.getRangeAddress().EndColumn
            end_row = cursor.getRangeAddress().EndRow

            sheet_info = {{
                "name": sheet.getName(),
                "index": i,
                "visible": sheet.IsVisible,
                "row_count": end_row + 1,
                "column_count": end_col + 1,
            }}
            info["sheets"].append(sheet_info)

            # Check if this is the active sheet
            if sheet == sheet:
                info["active_sheet"] = sheet_info

        ret = json.dumps(info, ensure_ascii=False)
        return info

    except Exception as e:
        ret = f"Error: {{e}}"
libreoffice_calc_get_workbook_info()
print(ret)
"""

    @agent_action
    def libreoffice_calc_get_workbook_info(self):

        return self.LIBREOFFICE_CALC_GET_WORKBOOK_INFO_CMD.format()

    LIBREOFFICE_CALC_GET_COLUMN_DATA_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_get_column_index(column_name, sheet=None):

    try:
        return ord(column_name[0]) - ord("A")
    except ValueError:
        return None
def libreoffice_calc_get_last_used_row():

    cursor = sheet.createCursor()
    cursor.gotoEndOfUsedArea(False)
    return cursor.RangeAddress.EndRow

def libreoffice_calc_get_column_data(column_name):
    global ret
    column_index = libreoffice_calc_get_column_index(column_name)
    if column_index is None:
        return "Column not found"
    last_row = libreoffice_calc_get_last_used_row()
    _range = sheet.getCellRangeByPosition(column_index, 0, column_index, last_row)
    # 获取数据数组并展平
    ret = json.dumps([row[0] for row in _range.getDataArray()], ensure_ascii=False)
    return [row[0] for row in _range.getDataArray()]
libreoffice_calc_get_column_data(column_name={column_name})
print(ret)
"""

    @agent_action
    def libreoffice_calc_get_column_data(self, column_name):

        return self.LIBREOFFICE_CALC_GET_COLUMN_DATA_CMD.format(column_name=repr(column_name))

    LIBREOFFICE_CALC_SWITCH_ACTIVE_SHEET_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_switch_active_sheet(sheet_name):
    global ret
    try:
        # 获取所有工作表
        sheets = doc.getSheets()

        # 检查工作表是否存在
        if not sheets.hasByName(sheet_name):
            # 创建新工作表
            new_sheet = doc.createInstance("com.sun.star.sheet.Spreadsheet")
            sheets.insertByName(sheet_name, new_sheet)

        # 获取目标工作表
        sheet = sheets.getByName(sheet_name)

        # 切换到目标工作表
        doc.getCurrentController().setActiveSheet(sheet)

        # 更新当前工作表引用
        sheet = sheet
        ret = "Success"
        return True

    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_switch_active_sheet(sheet_name={sheet_name})
print(ret)
"""

    LIBREOFFICE_CALC_GET_ACTIVE_SHEET_DATA_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_get_last_used_row():
    cursor = sheet.createCursor()
    cursor.gotoEndOfUsedArea(False)
    return cursor.RangeAddress.EndRow

def libreoffice_calc_get_last_used_column():
    cursor = sheet.createCursor()
    cursor.gotoEndOfUsedArea(False)
    return cursor.RangeAddress.EndColumn

def libreoffice_calc_get_active_sheet_data():
    global ret
    try:
        # 获取使用范围的最后行和列
        last_row = libreoffice_calc_get_last_used_row()
        last_col = libreoffice_calc_get_last_used_column()

        # 如果没有数据，返回空结果
        if last_row == -1 or last_col == -1:
            ret = json.dumps({{"data": [], "rows": 0, "columns": 0}}, ensure_ascii=False)
            return {{"data": [], "rows": 0, "columns": 0}}

        # 获取整个使用范围的数据
        data_range = sheet.getCellRangeByPosition(0, 0, last_col, last_row)
        data_array = data_range.getDataArray()

        # 转换为带坐标信息的数据结构
        sheet_data = []
        for row_idx, row in enumerate(data_array):
            row_data = []
            for col_idx, cell in enumerate(row):
                # 计算Excel风格的列名 (A, B, C, ...)
                col_name = chr(ord('A') + col_idx) if col_idx < 26 else f"A{{chr(ord('A') + col_idx - 26)}}"
                cell_address = f"{{col_name}}{{row_idx + 1}}"

                # 处理不同类型的单元格值
                if isinstance(cell, (int, float)):
                    cell_value = cell
                elif isinstance(cell, str):
                    cell_value = cell
                else:
                    cell_value = str(cell)

                row_data.append({{
                    "address": cell_address,
                    "value": cell_value,
                    "row": row_idx + 1,
                    "col": col_idx + 1,
                    "col_name": col_name,
                    "is_empty": cell_value == "" or cell_value == "--"
                }})
            sheet_data.append(row_data)

        result = {{
            "data": sheet_data,
            "rows": last_row + 1,
            "columns": last_col + 1,
            "range": f"A1:{{chr(ord('A') + last_col)}}{{last_row + 1}}"
        }}

        ret = json.dumps(result, ensure_ascii=False)
        return result

    except Exception as e:
        ret = f"Error: {{e}}"
        return None
libreoffice_calc_get_active_sheet_data()
print(ret)
"""

    @agent_action
    def libreoffice_calc_get_active_sheet_data(self):
        return self.LIBREOFFICE_CALC_GET_ACTIVE_SHEET_DATA_CMD.format()

    @agent_action
    def libreoffice_calc_switch_active_sheet(self, sheet_name):

        return self.LIBREOFFICE_CALC_SWITCH_ACTIVE_SHEET_CMD.format(sheet_name=repr(sheet_name))

    LIBREOFFICE_CALC_SET_COLUMN_VALUES_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""
def libreoffice_calc_get_column_index(column_name, sheet=None):
    try:
        return ord(column_name[0]) - ord("A")
    except ValueError:
        return None

def libreoffice_calc_set_column_values(column_name, data, start_index=2):
    global ret
    column_index = libreoffice_calc_get_column_index(column_name)
    if column_index is None:
        ret = "Column not found"
        return False
    for i, value in enumerate(data):
        cell = sheet.getCellByPosition(column_index, i + start_index - 1)
        if isinstance(value, str) and value.startswith("="):
            cell.setFormula(value)  # ✅ 关键修复：公式用 setFormula
        elif isinstance(value, float) and value.is_integer():
            cell.setNumber(int(value))
        else:
            cell.setString(str(value))
    ret = "Success"
    return True

libreoffice_calc_set_column_values(column_name={column_name}, data={data}, start_index={start_index})
print(ret)
"""

    @agent_action
    def libreoffice_calc_set_column_values(self, column_name, data, start_index):

        return self.LIBREOFFICE_CALC_SET_COLUMN_VALUES_CMD.format(column_name=repr(column_name), data=repr(data),
                                                                  start_index=repr(start_index))

    LIBREOFFICE_CALC_HIGHLIGHT_RANGE_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_highlight_range(range_str, color=0xFF0000):
    global ret
    try:
        _range = sheet.getCellRangeByName(range_str)
        _range.CellBackColor = color
        ret = "Success"
        return True
    except:
        ret = "False"
        return False
libreoffice_calc_highlight_range(range_str={range_str}, color={color})
print(ret)
"""

    @agent_action
    def libreoffice_calc_highlight_range(self, range_str, color):
        """
    highlight the specified range with the specified color

Args:
    range_str (str): Range to highlight, in the format of "A1:B10"
    color (str): Color to highlight with, default is '0xFF0000' (red)

Returns:
    bool: True if successful, False otherwise
    """

        return self.LIBREOFFICE_CALC_HIGHLIGHT_RANGE_CMD.format(range_str=repr(range_str), color=repr(color))

    LIBREOFFICE_CALC_TRANSPOSE_RANGE_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_transpose_range(source_range, target_cell):
    global ret
    try:
        source = sheet.getCellRangeByName(source_range)
        target = sheet.getCellRangeByName(target_cell)

        data = source.getDataArray()
        # 转置数据
        transposed_data = list(map(list, zip(*data)))

        # 设置转置后的数据
        target_range = sheet.getCellRangeByPosition(
            target.CellAddress.Column,
            target.CellAddress.Row,
            target.CellAddress.Column + len(transposed_data[0]) - 1,
            target.CellAddress.Row + len(transposed_data) - 1,
        )
        target_range.setDataArray(transposed_data)
        ret = "Success"
        return True
    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_transpose_range(source_range={source_range}, target_cell={target_cell})
print(ret)
"""

    @agent_action
    def libreoffice_calc_transpose_range(self, source_range, target_cell):
        """
    Transpose the specified range and paste it to the target cell

Args:
    source_range (str): Range to transpose, in the format of "A1:B10"
    target_cell (str): Target cell to paste the transposed data, in the format of "A1"

Returns:
    bool: True if successful, False otherwise
    """

        return self.LIBREOFFICE_CALC_TRANSPOSE_RANGE_CMD.format(source_range=repr(source_range),
                                                                target_cell=repr(target_cell))

    LIBREOFFICE_CALC_EXPORT_TO_CSV_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_export_to_csv():
    global ret
    try:
        # 获取当前文档的URL
        doc_url = doc.getURL()
        if not doc_url:
            raise ValueError("Document must be saved first")

        # 构造CSV文件路径
        if doc_url.startswith("file://"):
            base_path = doc_url[7:]  # 移除 'file://' 前缀
        else:
            base_path = doc_url

        # 获取基本路径和文件名
        csv_path = os.path.splitext(base_path)[0] + ".csv"

        # 确保路径是绝对路径
        csv_path = os.path.abspath(csv_path)

        # 转换为 LibreOffice URL 格式
        csv_url = uno.systemPathToFileUrl(csv_path)

        # 设置CSV导出选项
        props = (
            PropertyValue(Name="FilterName", Value="Text - txt - csv (StarCalc)"),
            PropertyValue(
                Name="FilterOptions", Value="44,0,76,0"
            ),  # 44=comma, 34=quote, 76=UTF-8, 1=first row as header
        )

        # 导出文件
        doc.storeToURL(csv_url, props)
        ret = "Success"
        return True

    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_export_to_csv()
print(ret)
"""

    @agent_action
    def libreoffice_calc_export_to_csv(self):

        return self.LIBREOFFICE_CALC_EXPORT_TO_CSV_CMD.format()

    LIBREOFFICE_CALC_SORT_COLUMN_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""
def libreoffice_calc_get_column_index(column_name, sheet=None):

    try:
        return ord(column_name[0]) - ord("A")
    except ValueError:
        return None
def libreoffice_calc_get_last_used_row():

    cursor = sheet.createCursor()
    cursor.gotoEndOfUsedArea(False)
    return cursor.RangeAddress.EndRow

def libreoffice_calc_get_column_data(column_name):
    global ret
    column_index = libreoffice_calc_get_column_index(column_name)
    if column_index is None:
        return "Column not found"
    last_row = libreoffice_calc_get_last_used_row()
    _range = sheet.getCellRangeByPosition(column_index, 0, column_index, last_row)
    # 获取数据数组并展平
    ret = json.dumps([row[0] for row in _range.getDataArray()], ensure_ascii=False)
    return [row[0] for row in _range.getDataArray()]

def libreoffice_calc_get_column_index(column_name, sheet=None):

    try:
        return ord(column_name[0]) - ord("A")
    except ValueError:
        return None
def libreoffice_calc_set_column_values(column_name, data, start_index=2):
    global ret
    # 获取列的索引
    column_index = libreoffice_calc_get_column_index(column_name)
    if column_index is None:
        ret = "Column not found"
        return False
    for i, value in enumerate(data):
        cell = sheet.getCellByPosition(column_index, i + start_index - 1)
        if type(value) == float and value.is_integer():
            cell.setNumber(int(value))
        else:
            cell.setString(str(value))
    ret = "Success"
    return True

def libreoffice_calc_sort_column(column_name, ascending=True, start_index=2):
    global ret
    try:
        column_data = libreoffice_calc_get_column_data(column_name)[start_index - 1 :]
        column_data = sorted(column_data, key=lambda x: float(x), reverse=not ascending)
    except:
        ret = "Error: Invalid column name or data type"
        return False

    return libreoffice_calc_set_column_values(column_name, column_data, start_index)
libreoffice_calc_sort_column(column_name={column_name}, ascending={ascending}, start_index={start_index})
print(ret)
"""

    @agent_action
    def libreoffice_calc_sort_column(self, column_name, ascending, start_index):

        return self.LIBREOFFICE_CALC_SORT_COLUMN_CMD.format(column_name=repr(column_name), ascending=repr(ascending),
                                                            start_index=repr(start_index))

    LIBREOFFICE_CALC_SET_VALIDATION_LIST_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""
def libreoffice_calc_get_column_index(column_name, sheet=None):

    try:
        return ord(column_name[0]) - ord("A")
    except ValueError:
        return None
def libreoffice_calc_get_last_used_row():

    cursor = sheet.createCursor()
    cursor.gotoEndOfUsedArea(False)
    return cursor.RangeAddress.EndRow
def libreoffice_calc_set_validation_list(column_name, values):
    global ret
    try:
        column_index = libreoffice_calc_get_column_index(column_name)
        last_row = libreoffice_calc_get_last_used_row()
        cell_range = sheet.getCellRangeByPosition(column_index, 1, column_index, last_row)

        # 获取现有的验证对象
        validation = cell_range.getPropertyValue("Validation")

        # 设置基本验证类型
        validation.Type = uno.Enum("com.sun.star.sheet.ValidationType", "LIST")
        validation.Operator = uno.Enum("com.sun.star.sheet.ConditionOperator", "EQUAL")

        # 设置下拉列表
        validation.ShowList = True
        # 调试：打印实际的值
        print(f"Debug: Original values = {{{{values}}}}")
        # 用双引号包围每个值，这是 LibreOffice 的标准格式
        values_str = ";".join('"' + str(val) + '"' for val in values)
        print(f"Debug: values_str = '{{{{values_str}}}}'")
        validation.Formula1 = values_str

        # 应用验证设置回单元格范围
        cell_range.setPropertyValue("Validation", validation)

        ret = "Success"
        return True

    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_set_validation_list(column_name={column_name}, values={values})
print(ret)
"""

    @agent_action
    def libreoffice_calc_set_validation_list(self, column_name, values):

        return self.LIBREOFFICE_CALC_SET_VALIDATION_LIST_CMD.format(column_name=repr(column_name), values=repr(values))

    LIBREOFFICE_CALC_HIDE_ROW_DATA_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""
def libreoffice_calc_get_last_used_column():

    cursor = sheet.createCursor()
    cursor.gotoEndOfUsedArea(False)
    return cursor.RangeAddress.EndColumn

def libreoffice_calc_get_last_used_row():

    cursor = sheet.createCursor()
    cursor.gotoEndOfUsedArea(False)
    return cursor.RangeAddress.EndRow
def libreoffice_calc_hide_row_data(value="N/A"):
    global ret
    last_row = libreoffice_calc_get_last_used_row()
    last_col = libreoffice_calc_get_last_used_column()

    for row in range(1, last_row + 1):
        has_value = False
        for col in range(last_col + 1):
            cell = sheet.getCellByPosition(col, row)
            if cell.getString() == value:
                has_value = True
                break
        row_range = sheet.getRows().getByIndex(row)
        row_range.IsVisible = not has_value

    ret = "Success"
    return True
libreoffice_calc_hide_row_data(value={value})
print(ret)
"""

    @agent_action
    def libreoffice_calc_hide_row_data(self, value):

        return self.LIBREOFFICE_CALC_HIDE_ROW_DATA_CMD.format(value=repr(value))

    LIBREOFFICE_CALC_REORDER_COLUMNS_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""
def libreoffice_calc_get_column_index(column_name, sheet=None):

    try:
        return ord(column_name[0]) - ord("A")
    except ValueError:
        return None
def libreoffice_calc_reorder_columns(column_order):
    global ret
    try:
        # 获取新的列索引
        new_indices = [libreoffice_calc_get_column_index(col) for col in column_order]

        # 创建新的列顺序
        for new_index, old_index in enumerate(new_indices):
            if new_index != old_index:
                sheet.Columns.insertByIndex(new_index, 1)
                source = sheet.Columns[old_index + (old_index > new_index)]
                target = sheet.Columns[new_index]
                target.setDataArray(source.getDataArray())
                sheet.Columns.removeByIndex(old_index + (old_index > new_index), 1)
        ret = "Success"
        return True

    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_reorder_columns(column_order={column_order})
print(ret)
"""

    @agent_action
    def libreoffice_calc_reorder_columns(self, column_order):

        return self.LIBREOFFICE_CALC_REORDER_COLUMNS_CMD.format(column_order=repr(column_order))

    LIBREOFFICE_CALC_CREATE_PIVOT_TABLE_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""
def libreoffice_calc_get_column_index(column_name, sheet=None):

    try:
        return ord(column_name[0]) - ord("A")
    except ValueError:
        return None
def libreoffice_calc_create_pivot_table(source_sheet,
        table_name,
        row_fields=None,
        col_fields=None,
        value_fields=None,
        aggregation_function="sum",
        target_cell="A1",
    ):
    global ret
    try:
        source = doc.getSheets().getByName(source_sheet)

        # 获取数据范围
        cursor = source.createCursor()
        cursor.gotoEndOfUsedArea(False)
        end_col = cursor.getRangeAddress().EndColumn
        end_row = cursor.getRangeAddress().EndRow

        # 获取完整的数据范围
        source_range = source.getCellRangeByPosition(0, 0, end_col, end_row)

        # 获取数据透视表集合
        dp_tables = sheet.getDataPilotTables()

        # 创建数据透视表描述符
        dp_descriptor = dp_tables.createDataPilotDescriptor()

        # 设置数据源
        dp_descriptor.setSourceRange(source_range.getRangeAddress())

        # 设置行字段
        if row_fields:
            for field in row_fields:
                field_index = libreoffice_calc_get_column_index(field)
                dimension = dp_descriptor.getDataPilotFields().getByIndex(field_index)
                dimension.Orientation = uno.Enum("com.sun.star.sheet.DataPilotFieldOrientation", "ROW")

        # 设置列字段
        if col_fields:
            for field in col_fields:
                field_index = libreoffice_calc_get_column_index(field)
                dimension = dp_descriptor.getDataPilotFields().getByIndex(field_index)
                dimension.Orientation = uno.Enum("com.sun.star.sheet.DataPilotFieldOrientation", "COLUMN")

        # 设置数据字段
        for field in value_fields:
            field_index = libreoffice_calc_get_column_index(field)
            dimension = dp_descriptor.getDataPilotFields().getByIndex(field_index)
            dimension.Orientation = uno.Enum("com.sun.star.sheet.DataPilotFieldOrientation", "DATA")

            # 设置聚合函数
            function_map = {{"Count": "COUNT", "Sum": "SUM", "Average": "AVERAGE", "Min": "MIN", "Max": "MAX"}}

            if aggregation_function in function_map:
                dimension.Function = uno.Enum(
                    "com.sun.star.sheet.GeneralFunction", function_map[aggregation_function]
                )

        # 在当前工作表中创建数据透视表
        dp_tables.insertNewByName(
            table_name,  # 透视表名称
            sheet.getCellRangeByName(target_cell).CellAddress,  # 目标位置
            dp_descriptor,  # 描述符
        )

        ret = "Success"
        return True
    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_create_pivot_table(source_sheet={source_sheet}, table_name={table_name}, row_fields={row_fields}, col_fields={col_fields}, value_fields={value_fields}, aggregation_function={aggregation_function}, target_cell={target_cell})
print(ret)
"""

    @agent_action
    def libreoffice_calc_create_pivot_table(self, source_sheet, table_name, row_fields, col_fields, value_fields,
                                            aggregation_function, target_cell):

        return self.LIBREOFFICE_CALC_CREATE_PIVOT_TABLE_CMD.format(source_sheet=repr(source_sheet),
                                                                   table_name=repr(table_name),
                                                                   row_fields=repr(row_fields),
                                                                   col_fields=repr(col_fields),
                                                                   value_fields=repr(value_fields),
                                                                   aggregation_function=repr(aggregation_function),
                                                                   target_cell=repr(target_cell))

    LIBREOFFICE_CALC_MERGE_CELLS_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
ret = ""

def libreoffice_calc_merge_cells(sheet_name, range_str):
    global ret
    try:
        # 通过名称获取指定的工作表
        sheet = doc.getSheets().getByName(sheet_name)

        # 获取单元格范围
        cell_range = sheet.getCellRangeByName(range_str)

        # 检查单元格是否已经合并
        is_merged = cell_range.getIsMerged()

        # 如果单元格范围尚未合并，则进行合并
        if not is_merged:
            cell_range.merge(True)

        ret = "Success"
        return True
    except Exception as e:
        ret = f"Error: {{e}}"
        return False

# 调用函数时需要传入 sheet_name 和 range_str 两个参数
libreoffice_calc_merge_cells(sheet_name={sheet_name}, range_str={range_str})
print(ret)
"""

    @agent_action
    def libreoffice_calc_merge_cells(self, sheet_name, range_str):
        """
        Merges a specified range of cells within a specific worksheet.

        Args:
            sheet_name (str): The name of the worksheet, e.g., 'Sheet1'.
            range_str (str): The cell range to merge, e.g., 'A1:B10'.

        Returns:
            str: A formatted command string to be executed.
        """
        return self.LIBREOFFICE_CALC_MERGE_CELLS_CMD.format(
            sheet_name=repr(sheet_name),
            range_str=repr(range_str)
        )

    LIBREOFFICE_CALC_SET_CELL_VALUE_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_set_cell_value(cell, value):
    global ret
    try:
        # 获取单元格对象
        cell_obj = sheet.getCellRangeByName(cell)

        if isinstance(value, str) and value.startswith("="):
            # 设置公式
            cell_obj.Formula = value
            ret = "Success"
            return True

        # 尝试将值转换为数字
        try:
            # 尝试转换为整数
            int_value = int(value)
            cell_obj.Value = int_value
        except ValueError:
            try:
                # 尝试转换为浮点数
                float_value = float(value)
                cell_obj.Value = float_value
            except ValueError:
                # 如果不是数字，则设置为字符串
                cell_obj.String = value

        ret = "Success"
        return True
    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_set_cell_value(cell={cell}, value={value})
print(ret)
"""

    @agent_action
    def libreoffice_calc_set_cell_value(self, cell, value):

        return self.LIBREOFFICE_CALC_SET_CELL_VALUE_CMD.format(cell=repr(cell), value=repr(value))

    LIBREOFFICE_CALC_FORMAT_RANGE_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_format_range(range_str, background_color=None, font_color=None, bold=None, alignment=None):
    global ret
    try:
        # 获取指定范围
        cell_range = sheet.getCellRangeByName(range_str)

        # 设置背景颜色
        if background_color:
            # 将十六进制颜色转换为整数
            bg_color_int = int(background_color.replace("#", ""), 16)
            cell_range.CellBackColor = bg_color_int

        # 设置字体颜色
        if font_color:
            # 将十六进制颜色转换为整数
            font_color_int = int(font_color.replace("#", ""), 16)
            cell_range.CharColor = font_color_int

        # 设置粗体
        if bold is not None:
            cell_range.CharWeight = 150.0 if bold else 100.0  # 150.0 是粗体，100.0 是正常

        # 设置对齐方式
        if alignment:
            # 设置水平对齐方式
            struct = cell_range.getPropertyValue("HoriJustify")
            if alignment == "left":
                struct.value = "LEFT"
            elif alignment == "center":
                struct.value = "CENTER"
            elif alignment == "right":
                struct.value = "RIGHT"
            cell_range.setPropertyValue("HoriJustify", struct)

        ret = "Success"
        return True
    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_format_range(range_str={range_str}, background_color={background_color}, font_color={font_color}, bold={bold}, alignment={alignment})
print(ret)
"""

    @agent_action
    def libreoffice_calc_format_range(self, range_str, background_color, font_color, bold, alignment):

        return self.LIBREOFFICE_CALC_FORMAT_RANGE_CMD.format(range_str=repr(range_str),
                                                             background_color=repr(background_color),
                                                             font_color=repr(font_color), bold=repr(bold),
                                                             alignment=repr(alignment))

    LIBREOFFICE_CALC_INSERT_CHART_CMD = """import json
import os
import subprocess
import sys
import uno
import time
from com.sun.star.beans import PropertyValue
from com.sun.star.awt import Rectangle
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_insert_chart(
    chart_type="column",
    data_ranges=None,
    first_row_as_label=True,
    first_column_as_label=True,
    data_series_in_rows=False,
    title=None,
    subtitle=None,
    x_axis_title=None,
    y_axis_title=None,
    display_x_grid=False,
    display_y_grid=True,
    chart_name=None,
    chart_position=None,
    chart_size=None
):
    global ret

    try:
        # 生成唯一的图表名称
        if chart_name is None:
            import time
            timestamp = str(int(time.time() * 1000))  # 使用毫秒时间戳
            chart_name = f"Chart_{{timestamp}}"

        # 图表类型映射
        chart_type_map = {{
            "column": "com.sun.star.chart.ColumnDiagram",
            "line": "com.sun.star.chart.LineDiagram"
        }}

        if chart_type not in chart_type_map:
            ret = f"Error: Unsupported chart type '{{chart_type}}'. Supported: column, line"
            return False

        # 处理数据范围
        if isinstance(data_ranges, str):
            if "," in data_ranges:
                range_list = [r.strip() for r in data_ranges.split(",")]
            else:
                range_list = [data_ranges]
        elif isinstance(data_ranges, list):
            range_list = data_ranges
        else:
            ret = "Error: data_ranges must be string or list"
            return False

        # 转换数据范围为CellRangeAddress对象
        cell_ranges = []
        for range_str in range_list:
            try:
                cell_range = sheet.getCellRangeByName(range_str.replace("$", ""))
                cell_ranges.append(cell_range.getRangeAddress())
            except Exception as e:
                ret = f"Error processing range '{{range_str}}': {{e}}"
                return False

        # 设置图表位置和大小
        if chart_position and chart_size:
            rect = Rectangle(
                chart_position.get("x", 1000),
                chart_position.get("y", 1000), 
                chart_size.get("width", 10000),
                chart_size.get("height", 7000)
            )
        elif chart_position:
            rect = Rectangle(
                chart_position.get("x", 1000),
                chart_position.get("y", 1000),
                10000, 7000
            )
        else:
            rect = Rectangle(1000, 1000, 10000, 7000)

        # 创建图表
        charts = sheet.Charts
        charts.addNewByName(chart_name, rect, tuple(cell_ranges), first_row_as_label, first_column_as_label)

        # 获取图表对象
        chart_obj = charts.getByName(chart_name)
        chart_doc = chart_obj.EmbeddedObject

        # 创建并设置图表类型
        diagram = chart_doc.createInstance(chart_type_map[chart_type])
        chart_doc.setDiagram(diagram)

        # 设置数据系列排列方向
        try:
            if hasattr(chart_doc, 'setDataSourceLabelsInFirstRow'):
                chart_doc.setDataSourceLabelsInFirstRow(not data_series_in_rows)
            if hasattr(chart_doc, 'setDataSourceLabelsInFirstColumn'):  
                chart_doc.setDataSourceLabelsInFirstColumn(data_series_in_rows)
        except Exception as e:
            print(f"Warning: Failed to set data series orientation: {{e}}")

        # 设置图表标题
        if title:
            try:
                title_obj = chart_doc.getTitle()
                if not title_obj:
                    title_obj = chart_doc.createInstance("com.sun.star.chart.Title")
                    chart_doc.setTitleObject(title_obj)
                title_obj.String = title
            except Exception as e:
                print(f"Warning: Failed to set title: {{e}}")

        # 设置副标题
        if subtitle:
            try:
                subtitle_obj = chart_doc.getSubTitle()
                if not subtitle_obj:
                    subtitle_obj = chart_doc.createInstance("com.sun.star.chart.Title")
                    chart_doc.setSubTitleObject(subtitle_obj)
                subtitle_obj.String = subtitle
            except Exception as e:
                print(f"Warning: Failed to set subtitle: {{e}}")

        # 设置坐标轴标题
        if x_axis_title or y_axis_title:
            try:
                if hasattr(diagram, 'XAxisTitle') and x_axis_title:
                    diagram.HasXAxisTitle = True
                    x_title = diagram.XAxisTitle
                    x_title.String = x_axis_title

                if hasattr(diagram, 'YAxisTitle') and y_axis_title:
                    diagram.HasYAxisTitle = True
                    y_title = diagram.YAxisTitle
                    y_title.String = y_axis_title
            except Exception as e:
                print(f"Warning: Failed to set axis titles: {{e}}")

        # 设置网格线
        try:
            if hasattr(diagram, 'HasXAxisGrid'):
                diagram.HasXAxisGrid = display_x_grid
            if hasattr(diagram, 'HasYAxisGrid'):
                diagram.HasYAxisGrid = display_y_grid
        except Exception as e:
            print(f"Warning: Failed to set grid lines: {{e}}")

        ret = "Chart created successfully"
        return True

    except Exception as e:
        ret = f"Error creating chart: {{e}}"
        return False
libreoffice_calc_insert_chart(chart_type={chart_type}, data_ranges={data_ranges}, first_row_as_label={first_row_as_label}, first_column_as_label={first_column_as_label}, data_series_in_rows={data_series_in_rows}, title={title}, subtitle={subtitle}, x_axis_title={x_axis_title}, y_axis_title={y_axis_title}, display_x_grid={display_x_grid}, display_y_grid={display_y_grid}, chart_name={chart_name}, chart_position={chart_position}, chart_size={chart_size})
print(ret)"""

    @agent_action
    def libreoffice_calc_insert_chart(self, chart_type="column", data_ranges=None, first_row_as_label=True,
                                      first_column_as_label=True, data_series_in_rows=False, title=None,
                                      subtitle=None, x_axis_title=None, y_axis_title=None, display_x_grid=False,
                                      display_y_grid=True, chart_name=None, chart_position=None, chart_size=None):
        return self.LIBREOFFICE_CALC_INSERT_CHART_CMD.format(chart_type=repr(chart_type), data_ranges=repr(data_ranges),
                                                             first_row_as_label=repr(first_row_as_label),
                                                             first_column_as_label=repr(first_column_as_label),
                                                             data_series_in_rows=repr(data_series_in_rows),
                                                             title=repr(title), subtitle=repr(subtitle),
                                                             x_axis_title=repr(x_axis_title),
                                                             y_axis_title=repr(y_axis_title),
                                                             display_x_grid=repr(display_x_grid),
                                                             display_y_grid=repr(display_y_grid),
                                                             chart_name=repr(chart_name),
                                                             chart_position=repr(chart_position),
                                                             chart_size=repr(chart_size))

    LIBREOFFICE_CALC_FREEZE_PANES_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_freeze_panes(rows=0, columns=0):
    global ret
    try:
        # 获取当前视图
        view = doc.getCurrentController()

        # 设置冻结窗格
        view.freezeAtPosition(columns, rows)

        ret = "Success"
        return True
    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_freeze_panes(rows={rows}, columns={columns})
print(ret)
"""

    @agent_action
    def libreoffice_calc_freeze_panes(self, rows, columns):

        return self.LIBREOFFICE_CALC_FREEZE_PANES_CMD.format(rows=repr(rows), columns=repr(columns))

    LIBREOFFICE_CALC_RENAME_SHEET_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_rename_sheet(old_name, new_name):
    global ret
    try:
        # 获取所有工作表
        sheets = doc.getSheets()

        # 检查原工作表是否存在
        if not sheets.hasByName(old_name):
            return False

        # 检查新名称是否已存在
        if sheets.hasByName(new_name):
            return False

        # 获取要重命名的工作表
        sheet = sheets.getByName(old_name)

        # 重命名工作表
        sheet.setName(new_name)

        ret = "Success"
        return True

    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_rename_sheet(old_name={old_name}, new_name={new_name})
print(ret)
"""

    @agent_action
    def libreoffice_calc_rename_sheet(self, old_name, new_name):

        return self.LIBREOFFICE_CALC_RENAME_SHEET_CMD.format(old_name=repr(old_name), new_name=repr(new_name))

    LIBREOFFICE_CALC_COPY_SHEET_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_copy_sheet(source_sheet, new_sheet_name=None):
    global ret
    try:
        # 获取所有工作表
        sheets = doc.getSheets()

        # 检查源工作表是否存在
        if not sheets.hasByName(source_sheet):
            return None

        # 如果没有提供新名称，则生成一个
        if not new_sheet_name:
            # 生成类似 "Sheet1 (2)" 的名称
            base_name = source_sheet
            counter = 1
            new_sheet_name = f"{{base_name}} ({{counter}})"

            # 确保名称不重复
            while sheets.hasByName(new_sheet_name):
                counter += 1
                new_sheet_name = f"{{base_name}} ({{counter}})"

        # 检查新名称是否已存在
        if sheets.hasByName(new_sheet_name):
            return None  # 名称已存在，无法创建

        # 获取源工作表的索引
        source_index = -1
        for i in range(sheets.getCount()):
            if sheets.getByIndex(i).getName() == source_sheet:
                source_index = i
                break

        if source_index == -1:
            return None

        # 复制工作表
        sheets.copyByName(source_sheet, new_sheet_name, source_index + 1)

        ret = f"New sheet created: {{new_sheet_name}}"
        return new_sheet_name

    except Exception as e:
        ret = f"Error: {{e}}"
        return None
libreoffice_calc_copy_sheet(source_sheet={source_sheet}, new_sheet_name={new_sheet_name})
print(ret)
"""

    @agent_action
    def libreoffice_calc_copy_sheet(self, source_sheet, new_sheet_name):

        return self.LIBREOFFICE_CALC_COPY_SHEET_CMD.format(source_sheet=repr(source_sheet),
                                                           new_sheet_name=repr(new_sheet_name))

    LIBREOFFICE_CALC_REORDER_SHEETS_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_reorder_sheets(sheet_name, position):
    global ret
    try:
        # 获取所有工作表
        sheets = doc.getSheets()

        # 检查工作表是否存在
        if not sheets.hasByName(sheet_name):
            return False

        # 获取工作表总数
        sheet_count = sheets.getCount()

        # 检查位置是否有效
        if position < 0 or position >= sheet_count:
            return False

        # 获取要移动的工作表
        sheet = sheets.getByName(sheet_name)

        # 获取工作表当前索引
        current_index = -1
        for i in range(sheet_count):
            if sheets.getByIndex(i).Name == sheet_name:
                current_index = i
                break

        if current_index == -1:
            return False

        # 移动工作表到指定位置
        sheets.moveByName(sheet_name, position)

        ret = "Success"
        return True

    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_reorder_sheets(sheet_name={sheet_name}, position={position})
print(ret)
"""

    @agent_action
    def libreoffice_calc_reorder_sheets(self, sheet_name, position):

        return self.LIBREOFFICE_CALC_REORDER_SHEETS_CMD.format(sheet_name=repr(sheet_name), position=repr(position))

    LIBREOFFICE_CALC_SET_CHART_LEGEND_POSITION_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_set_chart_legend_position(position):
    global ret
    try:
        # 获取当前工作表中的所有图表
        charts = sheet.getCharts()
        if charts.getCount() == 0:
            return False

        # 获取第一个图表（假设我们要修改的是第一个图表）
        chart = charts.getByIndex(0)
        chart_obj = chart.getEmbeddedObject()

        # 获取图表的图例
        diagram = chart_obj.getDiagram()
        legend = chart_obj.getLegend()

        # 根据指定的位置设置图例位置
        if position == "none":
            # 如果选择"none"，则隐藏图例
            chart_obj.HasLegend = False
        else:
            # 确保图例可见
            chart_obj.HasLegend = True

            import inspect

            print(inspect.getmembers(legend))

            # 设置图例位置
            if position == "top":
                pos = uno.Enum("com.sun.star.chart.ChartLegendPosition", "TOP")
            elif position == "bottom":
                pos = uno.Enum("com.sun.star.chart.ChartLegendPosition", "BOTTOM")
            elif position == "left":
                pos = uno.Enum("com.sun.star.chart.ChartLegendPosition", "LEFT")
            elif position == "right":
                pos = uno.Enum("com.sun.star.chart.ChartLegendPosition", "RIGHT")

            legend.Alignment = pos

        ret = "Success"
        return True
    except Exception:
        ret = "Error"
        return False
libreoffice_calc_set_chart_legend_position(position={position})
print(ret)
"""

    @agent_action
    def libreoffice_calc_set_chart_legend_position(self, position):

        return self.LIBREOFFICE_CALC_SET_CHART_LEGEND_POSITION_CMD.format(position=repr(position))

    LIBREOFFICE_CALC_SET_NUMBER_FORMAT_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_set_number_format(range_str, format_type, decimal_places=None):
    global ret
    try:
        # 获取单元格范围
        cell_range = sheet.getCellRangeByName(range_str)

        # 获取数字格式化服务
        number_formats = doc.NumberFormats
        locale = doc.CharLocale

        # 根据格式类型设置格式字符串
        format_string = ""

        if format_type == "general":
            format_string = "General"
        elif format_type == "number":
            if decimal_places is not None:
                format_string = f"0{{('.' + '0' * decimal_places) if decimal_places > 0 else ''}}"
            else:
                format_string = "0"
        elif format_type == "currency":
            if decimal_places is not None:
                format_string = f"[$¥-804]#,##0{{('.' + '0' * decimal_places) if decimal_places > 0 else ''}}"
            else:
                format_string = "[$¥-804]#,##0.00"
        elif format_type == "accounting":
            if decimal_places is not None:
                format_string = f"_-[$¥-804]* #,##0{{('.' + '0' * decimal_places) if decimal_places > 0 else ''}}_-;-[$¥-804]* #,##0{{('.' + '0' * decimal_places) if decimal_places > 0 else ''}}_-;_-[$¥-804]* \"-\"_-;_-@_-"
            else:
                format_string = '_-[$¥-804]* #,##0.00_-;-[$¥-804]* #,##0.00_-;_-[$¥-804]* "-"??_-;_-@_-'
        elif format_type == "date":
            format_string = "YYYY/MM/DD"
        elif format_type == "time":
            format_string = "HH:MM:SS"
        elif format_type == "percentage":
            if decimal_places is not None:
                format_string = f"0{{('.' + '0' * decimal_places) if decimal_places > 0 else ''}}%"
            else:
                format_string = "0.00%"
        elif format_type == "fraction":
            format_string = "# ?/?"
        elif format_type == "scientific":
            if decimal_places is not None:
                format_string = f"0{{('.' + '0' * decimal_places) if decimal_places > 0 else ''}}E+00"
            else:
                format_string = "0.00E+00"
        elif format_type == "text":
            format_string = "@"

        # 获取格式键
        format_key = number_formats.queryKey(format_string, locale, True)

        # 如果格式不存在，则添加
        if format_key == -1:
            format_key = number_formats.addNew(format_string, locale)

        # 应用格式
        cell_range.NumberFormat = format_key

        ret = "Success"
        return True
    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_set_number_format(range_str={range_str}, format_type={format_type}, decimal_places={decimal_places})
print(ret)
"""

    @agent_action
    def libreoffice_calc_set_number_format(self, range_str, format_type, decimal_places):

        return self.LIBREOFFICE_CALC_SET_NUMBER_FORMAT_CMD.format(range_str=repr(range_str),
                                                                  format_type=repr(format_type),
                                                                  decimal_places=repr(decimal_places))

    LIBREOFFICE_CALC_ADJUST_COLUMN_WIDTH_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""
def libreoffice_calc_column_name_to_index(column_name):

    column_name = column_name.upper()
    result = 0
    for char in column_name:
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result - 1
def libreoffice_calc_adjust_column_width(columns, width=None, autofit=False):
    global ret
    try:
        # 解析列范围
        col_range = columns.split(":")
        start_col = libreoffice_calc_column_name_to_index(col_range[0])

        if len(col_range) > 1:
            end_col = libreoffice_calc_column_name_to_index(col_range[1])
        else:
            end_col = start_col

        # 获取列对象
        columns_obj = sheet.getColumns()

        # 遍历指定的列范围
        for col_idx in range(start_col, end_col + 1):
            column = columns_obj.getByIndex(col_idx)

            if autofit:
                # 自动调整列宽
                column.OptimalWidth = True
            elif width is not None:
                # 设置指定宽度（转换为1/100毫米）
                # 大约一个字符宽度为256 (1/100 mm)
                column.Width = int(width * 256)

        ret = "Success"
        return True

    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_adjust_column_width(columns={columns}, width={width}, autofit={autofit})
print(ret)
"""

    @agent_action
    def libreoffice_calc_adjust_column_width(self, columns, width, autofit):

        return self.LIBREOFFICE_CALC_ADJUST_COLUMN_WIDTH_CMD.format(columns=repr(columns), width=repr(width),
                                                                    autofit=repr(autofit))

    LIBREOFFICE_CALC_ADJUST_ROW_HEIGHT_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_adjust_row_height(rows, height=None, autofit=False):
    global ret
    try:
        # 解析行范围
        row_range = rows.split(":")
        start_row = int(row_range[0])
        end_row = int(row_range[1]) if len(row_range) > 1 else start_row

        # 获取行对象
        for row_index in range(start_row, end_row + 1):
            row = sheet.getRows().getByIndex(row_index - 1)  # 索引从0开始

            if autofit:
                # 自动调整行高以适应内容
                row.OptimalHeight = True
            elif height is not None:
                # 设置指定高度（将点转换为1/100毫米，LibreOffice使用的单位）
                # 1点 ≈ 35.28 1/100毫米
                row.Height = int(height * 35.28)
                row.OptimalHeight = False

        ret = "Success"
        return True
    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_adjust_row_height(rows={rows}, height={height}, autofit={autofit})
print(ret)
"""

    @agent_action
    def libreoffice_calc_adjust_row_height(self, rows, height, autofit):

        return self.LIBREOFFICE_CALC_ADJUST_ROW_HEIGHT_CMD.format(rows=repr(rows), height=repr(height),
                                                                  autofit=repr(autofit))

    LIBREOFFICE_CALC_EXPORT_TO_PDF_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_export_to_pdf(file_path=None, sheets=None, open_after_export=False):
    global ret
    try:
        # 如果未指定文件路径，则使用当前文档路径并更改扩展名为.pdf
        if not file_path:
            if doc.hasLocation():
                url = doc.getLocation()
                file_path = uno.fileUrlToSystemPath(url)
                file_path = os.path.splitext(file_path)[0] + ".pdf"
            else:
                # 如果文档尚未保存，则在用户桌面创建临时文件
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                file_path = os.path.join(desktop_path, "LibreOffice_Export.pdf")

        # 确保文件路径是系统路径，然后转换为URL
        pdf_url = uno.systemPathToFileUrl(os.path.abspath(file_path))

        # 创建导出属性
        export_props = []

        # 设置过滤器名称
        export_props.append(PropertyValue(Name="FilterName", Value="calc_pdf_Export"))

        # 如果指定了特定工作表，则只导出这些工作表
        if sheets and isinstance(sheets, list) and len(sheets) > 0:
            # 获取所有工作表
            all_sheets = doc.getSheets()
            selection = []

            # 查找指定的工作表
            for sheet_name in sheets:
                if all_sheets.hasByName(sheet_name):
                    sheet = all_sheets.getByName(sheet_name)
                    selection.append(sheet)

            # 如果找到了指定的工作表，则设置导出选择
            if selection:
                export_props.append(PropertyValue(Name="Selection", Value=tuple(selection)))

        # 导出PDF
        doc.storeToURL(pdf_url, tuple(export_props))

        # 如果需要，导出后打开PDF
        if open_after_export:
            if sys.platform.startswith("darwin"):  # macOS
                subprocess.call(("open", file_path))
            elif os.name == "nt":  # Windows
                os.startfile(file_path)
            elif os.name == "posix":  # Linux
                subprocess.call(("xdg-open", file_path))

        ret = "Success"
        return True

    except Exception as e:
        ret = f"Error: {{e}}"
        return False
libreoffice_calc_export_to_pdf(file_path={file_path}, sheets={sheets}, open_after_export={open_after_export})
print(ret)
"""

    @agent_action
    def libreoffice_calc_export_to_pdf(self, file_path, sheets, open_after_export):

        return self.LIBREOFFICE_CALC_EXPORT_TO_PDF_CMD.format(file_path=repr(file_path), sheets=repr(sheets),
                                                              open_after_export=repr(open_after_export))

    LIBREOFFICE_CALC_SET_ZOOM_LEVEL_CMD = """import json
import os
import subprocess
import sys
import uno
from com.sun.star.beans import PropertyValue
localContext = uno.getComponentContext()
resolver = localContext.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", localContext)
ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.getCurrentComponent()
sheet = doc.CurrentController.ActiveSheet
ret = ""

def libreoffice_calc_set_zoom_level(zoom_percentage):
    global ret
    try:
            # 获取当前控制器
            controller = doc.getCurrentController()

            # 设置缩放值
            # 确保缩放值在合理范围内
            if zoom_percentage < 10:
                zoom_percentage = 10
            elif zoom_percentage > 400:
                zoom_percentage = 400

            # 应用缩放值
            controller.ZoomValue = zoom_percentage
            ret = "Success"
            return True

        except Exception as e:
            ret = f"Error: {{e}}"
            return False

libreoffice_calc_set_zoom_level(zoom_percentage={zoom_percentage})
print(ret)
"""

    @agent_action
    def libreoffice_calc_set_zoom_level(self, zoom_percentage):

        return self.LIBREOFFICE_CALC_SET_ZOOM_LEVEL_CMD.format(zoom_percentage=repr(zoom_percentage))


# ACI that supports the worker-only mode: done() and fail() become task scoped instead
class OSWorldWorkerOnlyACI(OSWorldACI):
    @agent_action
    def done(
        self,
    ):
        """End the current task with a success. Use this when you believe the entire task has been fully completed."""
        return """DONE"""

    @agent_action
    def fail(self):
        """End the current task with a failure. Use this when you believe the entire task is impossible to complete."""
        return """FAIL"""
