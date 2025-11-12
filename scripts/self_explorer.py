import argparse
import ast
import datetime
import json
import os
import re
import shutil
import sys
import time

import cv2
import prompts
from config import load_config
from and_controller import list_all_devices, AndroidController, traverse_tree, start_emulator, list_available_emulators
from web_controller import WebController
from model import parse_explore_rsp, parse_reflect_rsp, parse_grid_rsp, OpenAIModel, OllamaModel
from utils import print_with_color, draw_bbox_multi, append_to_log, append_images_as_table, draw_grid

def calculate_grid_coordinates(area, subarea, screen_width, screen_height, rows, cols):
    """
    Calculate x, y coordinates from grid area number and subarea position.

    Args:
        area: Grid area number (1-indexed)
        subarea: Subarea position ("center", "top-left", "top", "top-right", "left", "right", "bottom-left", "bottom", "bottom-right")
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        rows: Number of grid rows
        cols: Number of grid columns

    Returns:
        (x, y) coordinates
    """
    # Calculate unit sizes (matching draw_grid logic)
    def get_unit_len(n):
        for i in range(1, n + 1):
            if n % i == 0 and 120 <= i <= 180:
                return i
        return -1

    unit_height = get_unit_len(screen_height)
    if unit_height < 0:
        unit_height = 120
    unit_width = get_unit_len(screen_width)
    if unit_width < 0:
        unit_width = 120

    # Convert area number to row and column (area is 1-indexed)
    area_index = area - 1
    row = area_index // cols
    col = area_index % cols

    # Calculate cell boundaries
    left = int(col * unit_width)
    top = int(row * unit_height)
    right = int((col + 1) * unit_width)
    bottom = int((row + 1) * unit_height)

    # Calculate coordinates based on subarea
    subarea_offsets = {
        "center": (0.5, 0.5),
        "top-left": (0.2, 0.2),
        "top": (0.5, 0.2),
        "top-right": (0.8, 0.2),
        "left": (0.2, 0.5),
        "right": (0.8, 0.5),
        "bottom-left": (0.2, 0.8),
        "bottom": (0.5, 0.8),
        "bottom-right": (0.8, 0.8)
    }

    offset_x, offset_y = subarea_offsets.get(subarea, (0.5, 0.5))  # Default to center
    x = int(left + (right - left) * offset_x)
    y = int(top + (bottom - top) * offset_y)

    return x, y


arg_desc = "AppAgent - Autonomous Exploration"
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=arg_desc)
parser.add_argument("--app")
parser.add_argument("--root_dir", default="./")
parser.add_argument("--platform", choices=["android", "web"], default="android", help="Platform to automate")
args = vars(parser.parse_args())

configs = load_config()

if configs["MODEL"] == "api":
    # OpenAI API: Uses base64 encoding
    mllm = OpenAIModel(base_url=configs["API_BASE_URL"],
                       api_key=configs["API_KEY"],
                       model=configs["API_MODEL"],
                       temperature=configs["TEMPERATURE"],
                       max_tokens=configs["MAX_TOKENS"])
elif configs["MODEL"] == "local":
    # Ollama: Uses native SDK with file paths directly
    mllm = OllamaModel(model=configs["LOCAL_MODEL"],
                       temperature=configs["TEMPERATURE"],
                       max_tokens=configs["MAX_TOKENS"])
else:
    print_with_color(f"ERROR: Unsupported model type {configs['MODEL']}! Use 'api' or 'local'.", "red")
    sys.exit()

app = args["app"]
root_dir = args["root_dir"]
platform = args["platform"]

if not app:
    if platform == "android":
        print_with_color("What is the name of the target app?", "blue")
    else:
        print_with_color("What name would you like to give to this web exploration session?", "blue")
    app = input()
    app = app.replace(" ", "")

work_dir = os.path.join(root_dir, "apps")
if not os.path.exists(work_dir):
    os.mkdir(work_dir)
work_dir = os.path.join(work_dir, app)
if not os.path.exists(work_dir):
    os.mkdir(work_dir)
demo_dir = os.path.join(work_dir, "demos")
if not os.path.exists(demo_dir):
    os.mkdir(demo_dir)
demo_timestamp = int(time.time())
task_name = datetime.datetime.fromtimestamp(demo_timestamp).strftime("self_explore_%Y-%m-%d_%H-%M-%S")
task_dir = os.path.join(demo_dir, task_name)
os.mkdir(task_dir)
docs_dir = os.path.join(work_dir, "auto_docs")
if not os.path.exists(docs_dir):
    os.mkdir(docs_dir)
explore_log_path = os.path.join(task_dir, f"log_explore_{task_name}.txt")
reflect_log_path = os.path.join(task_dir, f"log_reflect_{task_name}.txt")
report_log_path = os.path.join(task_dir, f"log_report_{task_name}.md")

# Initialize controller based on platform
if platform == "android":
    device_list = list_all_devices()
    if not device_list:
        print_with_color("No Android device found.", "yellow")
        print_with_color("Attempting to start emulator...", "green")

        # Try to start emulator
        if start_emulator():
            # Refresh device list after emulator starts
            device_list = list_all_devices()
            if not device_list:
                print_with_color("ERROR: Emulator started but device not detected!", "red")
                sys.exit()
        else:
            print_with_color("ERROR: Failed to start emulator!", "red")
            print_with_color("Please start an Android device or emulator manually and try again.", "yellow")

            # Show available emulators
            avds = list_available_emulators()
            if avds:
                print_with_color(f"Available emulators: {', '.join(avds)}", "cyan")
                print_with_color("You can start one manually with: emulator -avd <name>", "cyan")

            sys.exit()

    print_with_color(f"List of devices attached:\n{str(device_list)}", "yellow")
    if len(device_list) == 1:
        device = device_list[0]
        print_with_color(f"Device selected: {device}", "yellow")
    else:
        print_with_color("Please choose the Android device to start demo by entering its ID:", "blue")
        device = input()
    controller = AndroidController(device)
    width, height = controller.get_device_size()
    if not width and not height:
        print_with_color("ERROR: Invalid device size!", "red")
        sys.exit()
    print_with_color(f"Screen resolution of {device}: {width}x{height}", "yellow")
else:  # web
    print_with_color("Please enter the URL you want to explore:", "blue")
    url = input()
    controller = WebController(
        browser_type=configs.get("WEB_BROWSER_TYPE", "chromium"),
        headless=configs.get("WEB_HEADLESS", False),
        url=url
    )
    width = controller.width
    height = controller.height
    print_with_color(f"Browser resolution: {width}x{height}", "yellow")

print_with_color("Please enter the description of the task you want me to complete in a few sentences:", "blue")
task_desc = input()

round_count = 0
doc_count = 0
useless_list = set()
last_act = "None"
task_complete = False

# Write the report markdown file
append_to_log(f"# User Testing Report for {app}", report_log_path)
append_to_log(task_name, report_log_path)
append_to_log(f"## Task Description", report_log_path)
append_to_log(task_desc, report_log_path)

while round_count < configs["MAX_ROUNDS"]:
    round_count += 1
    print_with_color(f"Round {round_count}", "yellow", log_file=report_log_path, heading_level=2)
    screenshot_before = controller.get_screenshot(f"{round_count}_before", task_dir)

    # Get interactive elements based on platform
    if platform == "android":
        xml_path = controller.get_xml(f"{round_count}", task_dir)
        if screenshot_before == "ERROR" or xml_path == "ERROR":
            break
        clickable_list = []
        focusable_list = []
        traverse_tree(xml_path, clickable_list, "clickable", True)
        traverse_tree(xml_path, focusable_list, "focusable", True)
    else:  # web
        if screenshot_before == "ERROR":
            break
        # Save HTML for reference
        html_path = controller.get_html(f"{round_count}", task_dir)
        # Get interactive elements from page
        clickable_list = controller.get_interactive_elements()
        focusable_list = []  # Web uses same list for both
    elem_list = []
    for elem in clickable_list:
        if elem.uid in useless_list:
            continue
        elem_list.append(elem)
    for elem in focusable_list:
        if elem.uid in useless_list:
            continue
        bbox = elem.bbox
        center = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
        close = False
        for e in clickable_list:
            bbox = e.bbox
            center_ = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
            dist = (abs(center[0] - center_[0]) ** 2 + abs(center[1] - center_[1]) ** 2) ** 0.5
            if dist <= configs["MIN_DIST"]:
                close = True
                break
        if not close:
            elem_list.append(elem)
    draw_bbox_multi(screenshot_before, os.path.join(task_dir, f"{round_count}_before_labeled.png"), elem_list,
                    dark_mode=configs["DARK_MODE"])

    # Add the screenshots as a table to the report markdown file
    append_images_as_table(
        [
            ("Before action", f"./{round_count}_before.png"),
            ("Before action labeled", f"./{round_count}_before_labeled.png")
        ],
        report_log_path
    )

    prompt = re.sub(r"<task_description>", task_desc, prompts.self_explore_task_template)
    prompt = re.sub(r"<last_act>", last_act, prompt)
    base64_img_before = os.path.join(task_dir, f"{round_count}_before_labeled.png")
    print_with_color("Thinking about what to do in the next step...", "yellow")
    status, rsp = mllm.get_model_response(prompt, [base64_img_before])

    if status:
        with open(explore_log_path, "a") as logfile:
            log_item = {"step": round_count, "prompt": prompt, "image": f"{round_count}_before_labeled.png",
                        "response": rsp}
            logfile.write(json.dumps(log_item) + "\n")
        res = parse_explore_rsp(rsp)
        act_name = res[0]

        # Extract reasoning information based on action type
        if act_name == "FINISH":
            observation, think, act, last_act = res[1], res[2], res[3], res[4]
            # Write reasoning to report
            append_to_log(f"\n**Observation:** {observation}\n", report_log_path)
            append_to_log(f"**Thought:** {think}\n", report_log_path)
            append_to_log(f"**Action:** {act}\n", report_log_path)
            append_to_log(f"**Summary:** {last_act}\n", report_log_path)
            task_complete = True
            break
        elif act_name == "grid":
            observation, think, act, last_act = res[1], res[2], res[3], res[4]
        elif act_name in ["tap", "long_press"]:
            last_act = res[2]
            observation, think, act = res[3], res[4], res[5]
        elif act_name == "text":
            last_act = res[2]
            observation, think, act = res[3], res[4], res[5]
        elif act_name == "swipe":
            last_act = res[4]
            observation, think, act = res[5], res[6], res[7]
        else:
            observation = think = act = last_act = "Unknown"

        # Write reasoning to report
        append_to_log(f"\n**Observation:** {observation}\n", report_log_path)
        append_to_log(f"**Thought:** {think}\n", report_log_path)
        append_to_log(f"**Action:** {act}\n", report_log_path)
        append_to_log(f"**Summary:** {last_act}\n", report_log_path)
        if act_name == "tap":
            _, area, _, _, _, _ = res
            tl, br = elem_list[area - 1].bbox
            x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2

            # Draw a bounding box on the canvas image and save it
            screenshot_before_actioned = os.path.join(task_dir, f"{round_count}_before_labeled_action.png")
            controller.get_screenshot_with_bbox(screenshot_before, screenshot_before_actioned, tl, br)
            controller.draw_circle(x, y, screenshot_before_actioned)

            ret = controller.tap(x, y)
            if ret == "ERROR":
                print_with_color("ERROR: tap execution failed", "red")
                break
        elif act_name == "text":
            _, input_str, _, _, _, _ = res

            # Draw a bounding box on the canvas image and save it
            screenshot_before_actioned = os.path.join(task_dir, f"{round_count}_before_labeled_action.png")
            controller.get_screenshot_with_bbox(screenshot_before, screenshot_before_actioned, tl, br)

            ret = controller.text(input_str)
            if ret == "ERROR":
                print_with_color("ERROR: text execution failed", "red")
                break
        elif act_name == "long_press":
            _, area, _, _, _, _ = res
            tl, br = elem_list[area - 1].bbox
            x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2

            # Draw a bounding box on the canvas image and save it
            screenshot_before_actioned = os.path.join(task_dir, f"{round_count}_before_labeled_action.png")
            controller.get_screenshot_with_bbox(screenshot_before, screenshot_before_actioned, tl, br)
            controller.draw_circle(x, y, screenshot_before_actioned)

            ret = controller.long_press(x, y)
            if ret == "ERROR":
                print_with_color("ERROR: long press execution failed", "red")
                break
        elif act_name == "swipe":
            _, area, swipe_dir, dist, _, _, _, _ = res
            tl, br = elem_list[area - 1].bbox
            x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2

            # Draw a bounding box on the canvas image and save it
            screenshot_before_actioned = os.path.join(task_dir, f"{round_count}_before_labeled_action.png")
            controller.get_screenshot_with_bbox(screenshot_before, screenshot_before_actioned, tl, br)
            controller.draw_arrow(x, y, swipe_dir, dist, screenshot_before_actioned)

            ret = controller.swipe(x, y, swipe_dir, dist)
            if ret == "ERROR":
                print_with_color("ERROR: swipe execution failed", "red")
                break
        elif act_name == "grid":
            # Grid mode - re-label the screen with grid overlay
            grid_screenshot = os.path.join(task_dir, f"{round_count}_grid.png")
            rows, cols = draw_grid(screenshot_before, grid_screenshot)
            print_with_color("Grid mode activated. Waiting for grid-based action...", "yellow")

            # Add grid screenshot to report
            append_to_log(
                f"![Grid overlay](./{round_count}_grid.png)",
                report_log_path,
            )

            # Ask model for grid-based action
            prompt = re.sub(r"<task_description>", task_desc, prompts.task_template_grid)
            prompt = re.sub(r"<last_act>", last_act, prompt)

            status, grid_rsp = mllm.get_model_response(prompt, [grid_screenshot])
            if not status:
                print_with_color(f"ERROR: {grid_rsp}", "red")
                break

            grid_res = parse_grid_rsp(grid_rsp)
            grid_act_name = grid_res[0]

            if grid_act_name == "FINISH":
                observation, think, act, last_act = grid_res[1], grid_res[2], grid_res[3], grid_res[4]
                # Write reasoning to report
                append_to_log(f"\n**Observation:** {observation}\n", report_log_path)
                append_to_log(f"**Thought:** {think}\n", report_log_path)
                append_to_log(f"**Action:** {act}\n", report_log_path)
                append_to_log(f"**Summary:** {last_act}\n", report_log_path)
                task_complete = True
                break
            elif grid_act_name == "tap_grid":
                _, area, subarea, last_act, observation, think, act = grid_res
                # Write reasoning to report
                append_to_log(f"\n**Observation:** {observation}\n", report_log_path)
                append_to_log(f"**Thought:** {think}\n", report_log_path)
                append_to_log(f"**Action:** {act}\n", report_log_path)
                append_to_log(f"**Summary:** {last_act}\n", report_log_path)
                x, y = calculate_grid_coordinates(area, subarea, width, height, rows, cols)
                print_with_color(f"Grid tap: area {area}, subarea {subarea} -> ({x}, {y})", "yellow")

                # Draw circle on the grid screenshot and save
                screenshot_grid_actioned = os.path.join(task_dir, f"{round_count}_grid_action.png")
                controller.get_screenshot_with_bbox(grid_screenshot, screenshot_grid_actioned, (x-5, y-5), (x+5, y+5))
                controller.draw_circle(x, y, screenshot_grid_actioned)

                ret = controller.tap(x, y)
                if ret == "ERROR":
                    print_with_color("ERROR: grid tap execution failed", "red")
                    break

                # Add actioned image to report
                append_to_log(
                    f"![Grid action](./{round_count}_grid_action.png)",
                    report_log_path,
                )
            elif grid_act_name == "long_press_grid":
                _, area, subarea, last_act, observation, think, act = grid_res
                # Write reasoning to report
                append_to_log(f"\n**Observation:** {observation}\n", report_log_path)
                append_to_log(f"**Thought:** {think}\n", report_log_path)
                append_to_log(f"**Action:** {act}\n", report_log_path)
                append_to_log(f"**Summary:** {last_act}\n", report_log_path)
                x, y = calculate_grid_coordinates(area, subarea, width, height, rows, cols)
                print_with_color(f"Grid long press: area {area}, subarea {subarea} -> ({x}, {y})", "yellow")

                # Draw circle on the grid screenshot and save
                screenshot_grid_actioned = os.path.join(task_dir, f"{round_count}_grid_action.png")
                controller.get_screenshot_with_bbox(grid_screenshot, screenshot_grid_actioned, (x-5, y-5), (x+5, y+5))
                controller.draw_circle(x, y, screenshot_grid_actioned)

                ret = controller.long_press(x, y)
                if ret == "ERROR":
                    print_with_color("ERROR: grid long press execution failed", "red")
                    break

                # Add actioned image to report
                append_to_log(
                    f"![Grid action](./{round_count}_grid_action.png)",
                    report_log_path,
                )
            elif grid_act_name == "swipe_grid":
                _, start_area, start_subarea, end_area, end_subarea, last_act, observation, think, act = grid_res
                # Write reasoning to report
                append_to_log(f"\n**Observation:** {observation}\n", report_log_path)
                append_to_log(f"**Thought:** {think}\n", report_log_path)
                append_to_log(f"**Action:** {act}\n", report_log_path)
                append_to_log(f"**Summary:** {last_act}\n", report_log_path)
                start_x, start_y = calculate_grid_coordinates(start_area, start_subarea, width, height, rows, cols)
                end_x, end_y = calculate_grid_coordinates(end_area, end_subarea, width, height, rows, cols)
                print_with_color(f"Grid swipe: from area {start_area}/{start_subarea} ({start_x},{start_y}) to area {end_area}/{end_subarea} ({end_x},{end_y})", "yellow")

                # Draw arrow on the grid screenshot and save
                screenshot_grid_actioned = os.path.join(task_dir, f"{round_count}_grid_action.png")
                shutil.copy(grid_screenshot, screenshot_grid_actioned)
                img = cv2.imread(screenshot_grid_actioned)
                cv2.arrowedLine(img, (start_x, start_y), (end_x, end_y), (0, 0, 255), 3, tipLength=0.3)
                cv2.imwrite(screenshot_grid_actioned, img)

                # For web, use scroll; for Android, calculate direction
                if platform == "web":
                    # Determine scroll direction from coordinates
                    if abs(end_y - start_y) > abs(end_x - start_x):
                        direction = "down" if end_y > start_y else "up"
                    else:
                        direction = "right" if end_x > start_x else "left"
                    ret = controller.scroll(direction)
                else:
                    # For Android, use swipe with calculated direction
                    dx = end_x - start_x
                    dy = end_y - start_y
                    if abs(dy) > abs(dx):
                        direction = "down" if dy > 0 else "up"
                    else:
                        direction = "right" if dx > 0 else "left"
                    dist = "long"  # Grid swipes are typically longer
                    ret = controller.swipe(start_x, start_y, direction, dist)

                if ret == "ERROR":
                    print_with_color("ERROR: grid swipe execution failed", "red")
                    break

                # Add actioned image to report
                append_to_log(
                    f"![Grid action](./{round_count}_grid_action.png)",
                    report_log_path,
                )
            else:
                print_with_color(f"ERROR: Undefined grid action {grid_act_name}!", "red")
                break
        else:
            break
        time.sleep(configs["REQUEST_INTERVAL"])

        # Add the actioned image to the report markdown file
        append_to_log(
            f"![Before action labeled action](./{round_count}_before_labeled_action.png)",
            report_log_path,
        )
    else:
        print_with_color(rsp, "red")
        break

    screenshot_after = controller.get_screenshot(f"{round_count}_after", task_dir)
    if screenshot_after == "ERROR":
        break
    draw_bbox_multi(screenshot_after, os.path.join(task_dir, f"{round_count}_after_labeled.png"), elem_list,
                    dark_mode=configs["DARK_MODE"])
    base64_img_after = os.path.join(task_dir, f"{round_count}_after_labeled.png")

    if act_name == "tap":
        prompt = re.sub(r"<action>", "tapping", prompts.self_explore_reflect_template)
    elif act_name == "text":
        continue
    elif act_name == "long_press":
        prompt = re.sub(r"<action>", "long pressing", prompts.self_explore_reflect_template)
    elif act_name == "swipe":
        swipe_dir = res[2]
        if swipe_dir == "up" or swipe_dir == "down":
            act_name = "v_swipe"
        elif swipe_dir == "left" or swipe_dir == "right":
            act_name = "h_swipe"
        prompt = re.sub(r"<action>", "swiping", prompts.self_explore_reflect_template)
    else:
        print_with_color("ERROR: Undefined act!", "red")
        break
    prompt = re.sub(r"<ui_element>", str(area), prompt)
    prompt = re.sub(r"<task_desc>", task_desc, prompt)
    prompt = re.sub(r"<last_act>", last_act, prompt)

    print_with_color("Reflecting on my previous action...", "yellow")
    status, rsp = mllm.get_model_response(prompt, [base64_img_before, base64_img_after])
    if status:
        resource_id = elem_list[int(area) - 1].uid
        with open(reflect_log_path, "a") as logfile:
            log_item = {"step": round_count, "prompt": prompt, "image_before": f"{round_count}_before_labeled.png",
                        "image_after": f"{round_count}_after.png", "response": rsp}
            logfile.write(json.dumps(log_item) + "\n")
        res = parse_reflect_rsp(rsp)
        decision = res[0]
        reflect_think = res[1]
        reflect_doc = res[2]

        # Write reflection results to report
        append_to_log(f"\n### Reflection\n", report_log_path)
        append_to_log(f"**Decision:** {decision}\n", report_log_path)
        append_to_log(f"**Thought:** {reflect_think}\n", report_log_path)
        if reflect_doc:
            append_to_log(f"**Documentation:** {reflect_doc}\n", report_log_path)
        if decision == "ERROR":
            break
        if decision == "INEFFECTIVE":
            useless_list.add(resource_id)
            last_act = "None"
        elif decision == "BACK" or decision == "CONTINUE" or decision == "SUCCESS":
            if decision == "BACK" or decision == "CONTINUE":
                useless_list.add(resource_id)
                last_act = "None"
                if decision == "BACK":
                    ret = controller.back()
                    if ret == "ERROR":
                        print_with_color("ERROR: back execution failed", "red")
                        break
            doc = res[-1]
            doc_name = resource_id + ".txt"
            doc_path = os.path.join(docs_dir, doc_name)
            if os.path.exists(doc_path):
                doc_content = ast.literal_eval(open(doc_path).read())
                if doc_content[act_name]:
                    print_with_color(f"Documentation for the element {resource_id} already exists.", "yellow")
                    continue
            else:
                doc_content = {
                    "tap": "",
                    "text": "",
                    "v_swipe": "",
                    "h_swipe": "",
                    "long_press": ""
                }
            doc_content[act_name] = doc
            with open(doc_path, "w") as outfile:
                outfile.write(str(doc_content))
            doc_count += 1
            print_with_color(f"Documentation generated and saved to {doc_path}", "yellow")
        else:
            print_with_color(f"ERROR: Undefined decision! {decision}", "red")
            break
    else:
        print_with_color(f"ERROR: {rsp}", "red")
        break
    time.sleep(configs["REQUEST_INTERVAL"])

if task_complete:
    print_with_color(f"Autonomous exploration completed successfully. {doc_count} docs generated.", "yellow")
elif round_count == configs["MAX_ROUNDS"]:
    print_with_color(f"Autonomous exploration finished due to reaching max rounds. {doc_count} docs generated.",
                     "yellow")
else:
    print_with_color(f"Autonomous exploration finished unexpectedly. {doc_count} docs generated.", "red")
