# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import subprocess
import time
import re
import traceback
from time import sleep
from typing import Optional, Tuple, List
import base64

import xml.etree.ElementTree as ET
import os

from aworld.logs.util import logger, color_log, Color
from aworld.utils import import_package

configs = {"MIN_DIST": 30}


class AndroidElement:
    def __init__(self, uid, bbox, attrib):
        self.uid = uid
        self.bbox = bbox
        self.attrib = attrib
        import_package('cv2', install_name='opencv-python')
        import_package('pyshine')

def get_id_from_element(elem):
    bounds = elem.attrib["bounds"][1:-1].split("][")
    x1, y1 = map(int, bounds[0].split(","))
    x2, y2 = map(int, bounds[1].split(","))
    elem_w, elem_h = x2 - x1, y2 - y1
    if "resource-id" in elem.attrib and elem.attrib["resource-id"]:
        elem_id = elem.attrib["resource-id"].replace(":", ".").replace("/", "_")
    else:
        elem_id = f"{elem.attrib['class']}_{elem_w}_{elem_h}"
    if "content-desc" in elem.attrib and elem.attrib["content-desc"] and len(elem.attrib["content-desc"]) < 20:
        content_desc = elem.attrib['content-desc'].replace("/", "_").replace(" ", "").replace(":", "_")
        elem_id += f"_{content_desc}"
    return elem_id


def traverse_tree(xml_path, elem_list, attrib, add_index=False):
    path = []
    for event, elem in ET.iterparse(xml_path, ['start', 'end']):
        if event == 'start':
            path.append(elem)
            if attrib in elem.attrib and elem.attrib[attrib] == "true":
                parent_prefix = ""
                if len(path) > 1:
                    parent_elem = path[-2]
                    # Checks if the parent element has the required attributes
                    has_bounds = "bounds" in parent_elem.attrib
                    has_rid_or_class = "resource-id" in parent_elem.attrib or "class" in parent_elem.attrib
                    if has_bounds and has_rid_or_class:
                        parent_prefix = get_id_from_element(parent_elem)
                bounds = elem.attrib["bounds"][1:-1].split("][")
                x1, y1 = map(int, bounds[0].split(","))
                x2, y2 = map(int, bounds[1].split(","))
                center = (x1 + x2) // 2, (y1 + y2) // 2
                elem_id = get_id_from_element(elem)
                if parent_prefix:
                    elem_id = parent_prefix + "_" + elem_id
                if add_index:
                    elem_id += f"_{elem.attrib['index']}"
                close = False
                for e in elem_list:
                    bbox = e.bbox
                    center_ = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
                    dist = (abs(center[0] - center_[0]) ** 2 + abs(center[1] - center_[1]) ** 2) ** 0.5
                    if dist <= configs["MIN_DIST"]:
                        close = True
                        break
                if not close:
                    elem_list.append(AndroidElement(elem_id, ((x1, y1), (x2, y2)), attrib))

        if event == 'end':
            path.pop()


def create_directory_for_file(file_path):
    # Extract the directory from the file path
    directory = os.path.dirname(file_path)

    # Check if the directory exists
    if not os.path.exists(directory):
        # Create the directory
        os.makedirs(directory)
        # Print the absolute path of the directory
        absolute_directory_path = os.path.abspath(directory)
        logger.info(f"Directory absolute path: {absolute_directory_path}")


def draw_bbox_multi(img_path, output_path, elem_list):
    import cv2
    import pyshine as ps

    imgcv = cv2.imread(img_path)
    count = 1
    for elem in elem_list:
        try:
            top_left = elem.bbox[0]
            bottom_right = elem.bbox[1]
            left, top = top_left[0], top_left[1]
            right, bottom = bottom_right[0], bottom_right[1]

            # draw rectangle
            cv2.rectangle(imgcv,
                          (left, top),
                          (right, bottom),
                          (0, 0, 221),
                          3)

            label = str(count)
            imgcv = ps.putBText(imgcv, label, text_offset_x=(left + right) // 2 + 10,
                                text_offset_y=(top + bottom) // 2 + 10,
                                vspace=10, hspace=10, font_scale=1, thickness=2, background_RGB=(221, 0, 0),
                                text_RGB=(255, 255, 255), alpha=0.0)

        except Exception as e:
            color_log(f"ERROR: An exception occurs while labeling the image\n{e}", Color.red)
            logger.info(traceback.print_exc())
        count += 1
    cv2.imwrite(output_path, imgcv)
    return imgcv


def draw_grid(img_path, output_path):
    import cv2

    def get_unit_len(n):
        for i in range(1, n + 1):
            if n % i == 0 and 120 <= i <= 180:
                return i
        return -1

    image = cv2.imread(img_path)
    height, width, _ = image.shape
    color = (255, 116, 113)
    unit_height = get_unit_len(height)
    if unit_height < 0:
        unit_height = 120
    unit_width = get_unit_len(width)
    if unit_width < 0:
        unit_width = 120
    thick = int(unit_width // 50)
    rows = height // unit_height
    cols = width // unit_width
    for i in range(rows):
        for j in range(cols):
            label = i * cols + j + 1
            left = int(j * unit_width)
            top = int(i * unit_height)
            right = int((j + 1) * unit_width)
            bottom = int((i + 1) * unit_height)
            cv2.rectangle(image, (left, top), (right, bottom), color, thick // 2)
            cv2.putText(image, str(label), (left + int(unit_width * 0.05) + 3, top + int(unit_height * 0.3) + 3), 0,
                        int(0.01 * unit_width), (0, 0, 0), thick)
            cv2.putText(image, str(label), (left + int(unit_width * 0.05), top + int(unit_height * 0.3)), 0,
                        int(0.01 * unit_width), color, thick)
    cv2.imwrite(output_path, image)
    return rows, cols


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


class ADBController:
    def __init__(self, avd_name: str = None,
                 adb_path: str = os.path.expanduser('~') + "/Library/Android/sdk/platform-tools/adb",
                 emulator_path: str = os.path.expanduser('~') + "/Library/Android/sdk/emulator/emulator",
                 timeout: int = 30):
        self.avd_name = avd_name
        self.adb_path = adb_path
        self.emulator_path = emulator_path
        self.timeout = timeout
        self.emulator_process = None
        self.device_serial = "emulator-5554"  # default
        self.current_elem_list = []
        self.width, self.height = 0, 0

    def start_emulator(self, avd_name: str = None, headless: bool = False,
                       max_retry: int = 2) -> bool:
        avd = avd_name or self.avd_name
        if not avd:
            raise ValueError("AVD name must be specified")

        for attempt in range(max_retry + 1):
            if self._start_emulator_process(avd, headless):
                if self._wait_for_device():
                    logger.info(f"start success，attempt count：{attempt + 1}")
                    self.width, self.height = self.get_screen_size()
                    return True
                self.stop_emulator()
        return False

    def _start_emulator_process(self, avd: str, headless: bool) -> bool:
        try:
            cmd = [
                self.emulator_path,
                f"@{avd}",
                "-no-snapshot",
                "-no-audio",
                "-gpu", "swiftshader",
                "-wipe-data"
            ]
            if headless:
                cmd.append("-no-window")

            self.emulator_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT
            )
            return True
        except Exception as e:
            logger.warning(f"adb start fail: {str(e)}")
            return False

    def stop_emulator(self) -> bool:
        try:
            result = subprocess.run(
                [self.adb_path, "-s", self.device_serial, "emu", "kill"],
                timeout=self.timeout,
                capture_output=True,
                text=True
            )
            return "OK" in result.stdout
        except subprocess.TimeoutExpired:
            return False
        finally:
            if self.emulator_process:
                self.emulator_process.terminate()

    def execute_adb(self, command: list, device_serial: str = None) -> Tuple[bool, str]:
        """execute adb command"""
        device = device_serial or self.device_serial
        full_cmd = [self.adb_path, "-s", device] + command

        try:
            result = subprocess.run(
                full_cmd,
                timeout=self.timeout,
                check=True,
                capture_output=True,
                text=True
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, f"Command failed: {e.stderr}"
        except Exception as e:
            return False, str(e)

    def execute_adb_with_stdout(self, command: List[str]) -> Tuple[bool, Optional[str]]:
        try:
            result = subprocess.run(
                ["adb", "-s", self.device_serial] + command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, None
        except subprocess.TimeoutExpired:
            return False, None
        except Exception as e:
            return False, None

    # ---------- device operate ----------

    def screenshot(self, save_path: str) -> bool:
        timestamp = int(time.time())
        remote_path = f"/sdcard/screenshot_{timestamp}.png"

        success, _ = self.execute_adb(["shell", "screencap", "-p", remote_path])
        if not success:
            return False

        return self._pull_file(remote_path, save_path)

    def dump_ui_xml(self, save_path: str) -> Optional[str]:
        remote_path = "/sdcard/ui_dump.xml"
        success, _ = self.execute_adb(["shell", "uiautomator", "dump", remote_path])
        if not success:
            logger.info("dump ui xml fail")
            return None
        success = self._pull_file(remote_path, save_path)
        if not success:
            logger.info("pull ui xml fail")
            return None

        with open(save_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        return xml_content

    def tap(self, element: int):
        x, y = self.__get_element_center(element)
        self.__tap_coordinate(x, y)

    def text(self, text: str):
        """
        Input text, automatically replacing spaces with %s for proper ADB text input.

        Parameters:
            text: The text to input
        """
        # Replace spaces with %s for proper handling in ADB
        formatted_text = text.replace(" ", "%s")
        success, _ = self.execute_adb(["shell", "input", "text", formatted_text])
        return success

    def long_press(self, element: int):
        x, y = self.__get_element_center(element)
        self.__swipe_coordinate(x, y, x, y, 2000)

    def swipe(self, element: int, direction: str, dist: str = "medium"):
        """
        Perform swipe operations based on screen element labels

        Parameters：
        element_tag: digital label displayed on the interface (1-based)
        direction: swipe direction ["up", "down", "left", "right"]
        dist: swipe distance ["short", "medium", "long"]
        """

        # 获取元素坐标
        x, y = self.__get_element_center(element)

        unit_dist = int(self.width / 10)
        if dist == "long":
            unit_dist *= 3
        elif dist == "medium":
            unit_dist *= 2
        if direction == "up":
            offset = 0, -2 * unit_dist
        elif direction == "down":
            offset = 0, 2 * unit_dist
        elif direction == "left":
            offset = -1 * unit_dist, 0
        elif direction == "right":
            offset = unit_dist, 0
        else:
            return False

        self.__swipe_coordinate(x, y, x + offset[0], y + offset[1])

    def screenshot_and_annotate(self, name_prefix=None, return_base64=True):
        import cv2

        """Collect screen information and mark interactive elements, and return data containing Base64 images"""
        sleep(3)
        if name_prefix is None:
            name_prefix = str(time.time())
        tmp_files_dir = os.path.join(os.path.dirname(__file__), "tmp_files")
        os.makedirs(tmp_files_dir, exist_ok=True)
        screenshot_path = os.path.join(tmp_files_dir, f"{name_prefix}_origin.png")
        screenshot_res = self.screenshot(screenshot_path)
        xml_path = os.path.join(tmp_files_dir, f"{name_prefix}.xml")
        xml_res = self.dump_ui_xml(xml_path)
        if screenshot_res == "ERROR" or xml_res is None:
            logger.warning(f"Failed to take screenshot or read XML")
            return None, None

        # Parsing interactive elements
        clickable_list = []
        focusable_list = []
        traverse_tree(xml_path, clickable_list, "clickable", True)
        traverse_tree(xml_path, focusable_list, "focusable", True)

        # Merge a list of duplicate elements
        elem_list = clickable_list.copy()
        for elem in focusable_list:
            bbox = elem.bbox
            center = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
            if not any(
                    ((center[0] - ((e.bbox[0][0] + e.bbox[1][0]) // 2)) ** 2 +
                     (center[1] - ((e.bbox[0][1] + e.bbox[1][1]) // 2)) ** 2) ** 0.5 <= configs["MIN_DIST"]
                    for e in clickable_list
            ):
                elem_list.append(elem)

        # Generate annotated images
        labeled_path = os.path.join(tmp_files_dir, f"{name_prefix}_labeled.png")
        labeled_img = draw_bbox_multi(screenshot_path, labeled_path, elem_list)

        # Show Image Window
        # cv2.imshow("image", labeled_img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        # Base64 encoding
        base64_str = None
        if return_base64:
            # Convert color space BGR->RGB
            rgb_image = cv2.cvtColor(labeled_img, cv2.COLOR_BGR2RGB)
            # Compress to JPEG format (with adjustable quality parameters)
            success, buffer = cv2.imencode(".jpg", rgb_image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if success:
                base64_str = base64.b64encode(buffer).decode("utf-8")

        self.current_elem_list = elem_list.copy()
        logger.info(f"Current elem size{len(self.current_elem_list)}")
        return xml_res, base64_str

    def setup_connection(self) -> bool:
        """Intelligent initialization device connection"""
        # Prioritize physical equipment testing
        if self.__connect_physical_device():
            return True

        # Try connecting to the simulator
        if self.avd_name and self.start_emulator():
            return True

        raise ConnectionError("No available device found, please connect your phone or configure the simulator")

    # ---------- Helper Methods ----------
    def __connect_physical_device(self) -> bool:
        """Connect an authorized USB device"""
        devices = self.__get_authorized_devices()
        if not devices:
            return False

        self.device = devices[0]
        logger.info(f"Connected physical device: {self.device}")
        self.device_serial = self.device
        self.width, self.height = self.get_screen_size()
        return True

    def __get_authorized_devices(self) -> list:
        """Get a list of authorized devices"""
        success, output = self.execute_adb(["devices"])
        if not success:
            return []

        return [
            line.split("\t")[0]
            for line in output.splitlines()
            if "\tdevice" in line and "emulator" not in line
        ]

    def __tap_coordinate(self, x: int, y: int) -> bool:
        """Click screen coordinates"""
        success, _ = self.execute_adb(["shell", "input", "tap", str(x), str(y)])
        return success

    def __get_element_center(self, elem_idx: int) -> tuple:
        """Calculate the coordinates of the center of the element"""
        tl, br = self.current_elem_list[int(elem_idx) - 1].bbox
        return (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2

    def __swipe_coordinate(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        """Slide Operation"""
        success, _ = self.execute_adb([
            "shell", "input", "swipe",
            str(x1), str(y1), str(x2), str(y2),
            str(duration)
        ])
        return success

    def _wait_for_device(self, timeout: int = 300) -> bool:
        """Three-level waiting detection strategy"""
        start_time = time.time()
        stages = {
            "adb_connected": False,
            "boot_completed": False,
            "services_ready": False
        }

        while time.time() - start_time < timeout:
            # Step 1: Detect adb connection
            if not stages["adb_connected"]:
                _, devices = self.execute_adb(["devices"])
                if self.device_serial in devices:
                    stages["adb_connected"] = True

            # Step 2: Detection system boot completed
            if stages["adb_connected"] and not stages["boot_completed"]:
                _, output = self.execute_adb([
                    "shell", "getprop", "sys.boot_completed"
                ])
                if output.strip() == "1":
                    stages["boot_completed"] = True

            # Step 3: Detecting Graphics Service Readiness
            if stages["boot_completed"] and not stages["services_ready"]:
                _, output = self.execute_adb([
                    "shell", "service check SurfaceFlinger"
                ])
                if "found" in output.lower():
                    return True

        return False

    def _pull_file(self, remote: str, local: str) -> bool:
        """Pull device files to local"""
        create_directory_for_file(local)
        success, _ = self.execute_adb(["pull", remote, local])
        if success:
            self.execute_adb(["shell", "rm", remote])  # 清理临时文件
        return success

    def get_screen_size(self) -> Optional[Tuple[int, int]]:
        """Get screen resolution"""
        success, output = self.execute_adb(["shell", "wm", "size"])
        if not success:
            return None

        match = re.search(r"(\d+)x(\d+)", output)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None


if __name__ == "__main__":
    # Examples
    controller = ADBController(avd_name="Medium_Phone_API_35")

    # controller.stop_emulator()
    if controller.setup_connection():
        logger.info("Simulator started successfully")
        width, height = controller.get_screen_size()
        logger.info(f"Get the screen size{width},{height}")

        # Take screenshots and annotate them
        controller.screenshot_and_annotate()
        controller.swipe(6, "up")

        # controller.screenshot_and_annotate()
        # controller.tap(6)
        xml_txt, base64_txt = controller.screenshot_and_annotate()
        logger.info(xml_txt)

        # controller.stop_emulator()
        logger.info("Close the simulator")
