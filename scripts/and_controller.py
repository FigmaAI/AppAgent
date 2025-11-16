import os
import subprocess
import xml.etree.ElementTree as ET
import cv2
import shutil

from config import load_config
from utils import print_with_color


configs = load_config()


def get_android_sdk_path():
    """
    Get Android SDK path from config.

    Priority:
    1. configs['ANDROID_SDK_PATH'] (set by SetupWizard or Settings, passed via Electron env var)
    2. Empty string (will trigger common_paths fallback in find_sdk_tool)

    Returns:
        str: Android SDK path or empty string
    """
    # Get from config (already loaded at module level, passed from Electron)
    return configs.get('ANDROID_SDK_PATH', '')


def find_sdk_tool(tool_name, subfolder='platform-tools'):
    """
    Find Android SDK tool (adb, emulator, etc.) using SDK path or common paths.

    Args:
        tool_name: Tool executable name (e.g., 'adb', 'emulator')
        subfolder: SDK subfolder containing the tool (e.g., 'platform-tools', 'emulator')

    Returns:
        str: Full path to the tool or None if not found
    """
    # First, check if tool is in PATH
    tool_path = shutil.which(tool_name)
    if tool_path:
        return tool_path

    # Get SDK path from config/env
    sdk_path = get_android_sdk_path()

    # If SDK path is specified, check there first
    if sdk_path:
        candidate_path = os.path.join(sdk_path, subfolder, tool_name)
        if os.path.exists(candidate_path):
            return candidate_path

    # Fallback to common paths (platform-specific)
    common_paths = []
    if tool_name == 'emulator':
        common_paths = [
            os.path.expanduser("~/Library/Android/sdk/emulator/emulator"),      # macOS
            os.path.expanduser("~/Android/Sdk/emulator/emulator"),               # Linux
            "C:\\Users\\%USERNAME%\\AppData\\Local\\Android\\Sdk\\emulator\\emulator.exe",  # Windows
            "/opt/android-sdk/emulator/emulator"                                 # Linux (alternative)
        ]
    elif tool_name == 'adb':
        common_paths = [
            os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),     # macOS
            os.path.expanduser("~/Android/Sdk/platform-tools/adb"),              # Linux
            "C:\\Users\\%USERNAME%\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe",  # Windows
            "/opt/android-sdk/platform-tools/adb"                                # Linux (alternative)
        ]

    # Check common paths
    for path in common_paths:
        expanded_path = os.path.expandvars(path)  # Expand %USERNAME% on Windows
        if os.path.exists(expanded_path):
            return expanded_path

    return None


class AndroidElement:
    def __init__(self, uid, bbox, attrib):
        self.uid = uid
        self.bbox = bbox
        self.attrib = attrib


def get_adb_path():
    """Get adb executable path using find_sdk_tool helper"""
    return find_sdk_tool('adb', 'platform-tools')


def execute_adb(adb_command):
    """
    Execute adb command using full path to adb executable

    Args:
        adb_command: Command string (e.g., "adb devices" or just "devices")

    Returns:
        Command output or "ERROR"
    """
    # Get adb path
    adb_path = get_adb_path()
    if not adb_path:
        print_with_color("ERROR: adb command not found", "red")
        print_with_color("Please configure Android SDK path in Settings", "yellow")
        sdk_path = get_android_sdk_path()
        if sdk_path:
            print_with_color(f"Current ANDROID_SDK_PATH: {sdk_path}", "yellow")
        else:
            print_with_color("ANDROID_SDK_PATH not set - configure in Settings", "yellow")
        return "ERROR"

    # Replace 'adb' with full path in command
    # Handle both "adb devices" and "devices" formats
    if adb_command.startswith('adb '):
        adb_command = adb_command.replace('adb ', f'{adb_path} ', 1)
    else:
        adb_command = f'{adb_path} {adb_command}'

    result = subprocess.run(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    print_with_color(f"Command execution failed: {adb_command}", "red")
    print_with_color(result.stderr, "red")
    return "ERROR"


def list_all_devices():
    """List all connected Android devices"""
    adb_path = get_adb_path()
    if not adb_path:
        print_with_color("ERROR: adb not found. Please configure Android SDK path in Settings", "red")
        return []

    device_list = []
    result = execute_adb("devices")
    if result != "ERROR":
        devices = result.split("\n")[1:]
        for d in devices:
            if d.strip():  # Skip empty lines
                device_list.append(d.split()[0])

    return device_list


def list_available_emulators():
    """List all available Android emulators (AVDs)"""

    # Find emulator using new helper function
    emulator_path = find_sdk_tool('emulator', 'emulator')

    if not emulator_path:
        print_with_color("ERROR: emulator command not found. Please install Android SDK.", "red")
        print_with_color("Set ANDROID_SDK_PATH in Settings or ensure emulator is in PATH", "yellow")
        return []

    # List AVDs
    result = subprocess.run([emulator_path, '-list-avds'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          text=True)

    if result.returncode == 0:
        avds = [avd.strip() for avd in result.stdout.strip().split('\n') if avd.strip()]
        return avds
    return []


def start_emulator(avd_name=None, wait_for_boot=True):
    """
    Start an Android emulator

    Args:
        avd_name: Name of AVD to start (if None, uses first available)
        wait_for_boot: Wait for emulator to fully boot

    Returns:
        True if successful, False otherwise
    """
    import time

    # Get emulator path using new helper function
    emulator_path = find_sdk_tool('emulator', 'emulator')

    if not emulator_path:
        print_with_color("ERROR: emulator command not found", "red")
        print_with_color("Please configure Android SDK path in Settings", "yellow")
        sdk_path = get_android_sdk_path()
        if sdk_path:
            print_with_color(f"Current ANDROID_SDK_PATH: {sdk_path}", "yellow")
        else:
            print_with_color("ANDROID_SDK_PATH not set - configure in Settings", "yellow")
        return False

    # Get AVD list
    avds = list_available_emulators()
    if not avds:
        print_with_color("ERROR: No Android emulators (AVDs) found", "red")
        print_with_color("Create an AVD using Android Studio or avdmanager", "yellow")
        return False

    # Select AVD
    if avd_name is None:
        avd_name = avds[0]
        print_with_color(f"Using first available emulator: {avd_name}", "yellow")
    elif avd_name not in avds:
        print_with_color(f"ERROR: AVD '{avd_name}' not found", "red")
        print_with_color(f"Available AVDs: {', '.join(avds)}", "yellow")
        return False

    # Start emulator in background with cold boot
    print_with_color(f"Starting emulator: {avd_name} (cold boot)...", "green")
    subprocess.Popen([emulator_path, '-avd', avd_name, '-no-snapshot-load'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)

    if wait_for_boot:
        return wait_for_device()

    return True


def wait_for_device(timeout=120):
    """
    Wait for Android device to be ready

    Args:
        timeout: Maximum seconds to wait

    Returns:
        True if device is ready, False if timeout
    """
    import time

    print_with_color(f"Waiting for device to be ready (timeout: {timeout}s)...", "yellow")

    # Wait for device to be detected
    start_time = time.time()
    while time.time() - start_time < timeout:
        devices = list_all_devices()
        if devices:
            print_with_color(f"Device detected: {devices[0]}", "green")
            break
        time.sleep(2)
    else:
        print_with_color("ERROR: Timeout waiting for device", "red")
        return False

    # Wait for device to boot completely
    print_with_color("Waiting for device to boot completely...", "yellow")
    adb_command = "adb wait-for-device shell getprop sys.boot_completed"

    start_time = time.time()
    while time.time() - start_time < timeout:
        result = execute_adb(adb_command)
        if result == "1":
            print_with_color("✓ Device is ready!", "green")
            time.sleep(2)  # Extra wait for stability
            return True
        time.sleep(3)

    print_with_color("ERROR: Device did not boot in time", "red")
    return False


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
                    parent_prefix = get_id_from_element(path[-2])
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

class AndroidController:
    def __init__(self, device):
        self.device = device
        self.screenshot_dir = configs["ANDROID_SCREENSHOT_DIR"]
        self.xml_dir = configs["ANDROID_XML_DIR"]
        self.width, self.height = self.get_device_size()
        self.backslash = "\\"

    def get_device_size(self):
        adb_command = f"adb -s {self.device} shell wm size"
        result = execute_adb(adb_command)
        if result != "ERROR":
            return map(int, result.split(": ")[1].split("x"))
        return 0, 0

    def get_screenshot(self, prefix, save_dir):
        cap_command = f"adb -s {self.device} shell screencap -p " \
                      f"{os.path.join(self.screenshot_dir, prefix + '.png').replace(self.backslash, '/')}"
        pull_command = f"adb -s {self.device} pull " \
                       f"{os.path.join(self.screenshot_dir, prefix + '.png').replace(self.backslash, '/')} " \
                       f"{os.path.join(save_dir, prefix + '.png')}"
        result = execute_adb(cap_command)
        if result != "ERROR":
            result = execute_adb(pull_command)
            if result != "ERROR":
                return os.path.join(save_dir, prefix + ".png")
            return result
        return result

    def get_xml(self, prefix, save_dir):
        dump_command = f"adb -s {self.device} shell uiautomator dump " \
                       f"{os.path.join(self.xml_dir, prefix + '.xml').replace(self.backslash, '/')}"
        pull_command = f"adb -s {self.device} pull " \
                       f"{os.path.join(self.xml_dir, prefix + '.xml').replace(self.backslash, '/')} " \
                       f"{os.path.join(save_dir, prefix + '.xml')}"
        result = execute_adb(dump_command)
        if result != "ERROR":
            result = execute_adb(pull_command)
            if result != "ERROR":
                return os.path.join(save_dir, prefix + ".xml")
            return result
        return result

    def back(self):
        adb_command = f"adb -s {self.device} shell input keyevent KEYCODE_BACK"
        ret = execute_adb(adb_command)
        return ret

    def tap(self, x, y):
        adb_command = f"adb -s {self.device} shell input tap {x} {y}"
        ret = execute_adb(adb_command)
        return ret

    def text(self, input_str):
        input_str = input_str.replace(" ", "%s")
        input_str = input_str.replace("'", "")
        adb_command = f"adb -s {self.device} shell input text {input_str}"
        ret = execute_adb(adb_command)
        return ret

    def long_press(self, x, y, duration=1000):
        adb_command = f"adb -s {self.device} shell input swipe {x} {y} {x} {y} {duration}"
        ret = execute_adb(adb_command)
        return ret

    def swipe(self, x, y, direction, dist="medium", quick=False):
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
            return "ERROR"
        duration = 100 if quick else 400
        adb_command = f"adb -s {self.device} shell input swipe {x} {y} {x+offset[0]} {y+offset[1]} {duration}"
        ret = execute_adb(adb_command)
        return ret

    def swipe_precise(self, start, end, duration=400):
        start_x, start_y = start
        end_x, end_y = end
        adb_command = f"adb -s {self.device} shell input swipe {start_x} {start_x} {end_x} {end_y} {duration}"
        ret = execute_adb(adb_command)
        return ret

    def get_screenshot_with_bbox(self, screenshot_before, save_dir, tl, br):
        # Copy the screenshot_before image
        img_path = save_dir
        shutil.copy(screenshot_before, img_path)

        # Load the copied image
        img = cv2.imread(img_path)

        # Draw the bounding box on the image
        cv2.rectangle(img, (int(tl[0]), int(tl[1])), (int(br[0]), int(br[1])), (0, 255, 0), 2)

        # Save the image with the bounding box
        cv2.imwrite(img_path, img)

        return img_path

    def draw_circle(self, x, y, img_path, r=10, thickness=2):
        img = cv2.imread(img_path)
        cv2.circle(img, (int(x), int(y)), r, (0, 0, 255), thickness)
        cv2.imwrite(img_path, img)

    def draw_arrow(self, x, y, direction, dist, image_path, arrow_color=(0, 255, 0), thickness=2):
        img = cv2.imread(image_path)

        # Calculate the arrow length based on the screen width and dist
        screen_width = img.shape[1]
        unit_dist = int(screen_width / 10)
        if dist == "long":
            arrow_length = 3 * unit_dist
        elif dist == "medium":
            arrow_length = 2 * unit_dist
        else:
            arrow_length = unit_dist

        # Define the arrow directions
        if direction == "up":
            end_point = (x, y - arrow_length)
        elif direction == "down":
            end_point = (x, y + arrow_length)
        elif direction == "left":
            end_point = (x - arrow_length, y)
        elif direction == "right":
            end_point = (x + arrow_length, y)
        else:
            raise ValueError(f"Invalid direction: {direction}")

        # Draw the arrow
        cv2.arrowedLine(img, (x, y), end_point, arrow_color, thickness)

        # Save the modified image
        cv2.imwrite(image_path, img)
