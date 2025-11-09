import argparse
import datetime
import os
import time

from scripts.utils import print_with_color

arg_desc = "AppAgent - exploration phase"
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=arg_desc)
parser.add_argument("--app")
parser.add_argument("--root_dir", default="./")
parser.add_argument("--platform", choices=["android", "web"], help="Platform to automate")
args = vars(parser.parse_args())

app = args["app"]
root_dir = args["root_dir"]
platform = args["platform"]


print_with_color("Welcome to the exploration phase of AppAgent!\nThe exploration phase aims at generating "
                 "documentations for UI elements through either autonomous exploration or human demonstration. "
                 "Both options are task-oriented, which means you need to give a task description. During "
                 "autonomous exploration, the agent will try to complete the task by interacting with possible "
                 "elements on the UI within limited rounds. Documentations will be generated during the process of "
                 "interacting with the correct elements to proceed with the task. Human demonstration relies on "
                 "the user to show the agent how to complete the given task, and the agent will generate "
                 "documentations for the elements interacted during the human demo.", "yellow")

# Platform selection
if not platform:
    print_with_color("\nChoose platform:\n1. Android\n2. Web\nType 1 or 2.", "blue")
    platform_input = ""
    while platform_input not in ["1", "2"]:
        platform_input = input()
    platform = "android" if platform_input == "1" else "web"

if platform == "android":
    print_with_color("Please enter the main interface of the app on your Android device.", "yellow")
else:
    print_with_color("Web automation mode selected. You will be prompted for URL during execution.", "yellow")

# Mode selection
print_with_color("\nChoose from the following modes:\n1. autonomous exploration\n2. human demonstration\n"
                 "Type 1 or 2.", "blue")
user_input = ""
while user_input != "1" and user_input != "2":
    user_input = input()

if not app:
    if platform == "android":
        print_with_color("What is the name of the target app?", "blue")
    else:
        print_with_color("What name would you like to give to this web exploration session?", "blue")
    app = input()
    app = app.replace(" ", "")

if user_input == "1":
    os.system(f"python scripts/self_explorer.py --app {app} --root_dir {root_dir} --platform {platform}")
else:
    demo_timestamp = int(time.time())
    demo_name = datetime.datetime.fromtimestamp(demo_timestamp).strftime(f"demo_{app}_%Y-%m-%d_%H-%M-%S")
    os.system(f"python scripts/step_recorder.py --app {app} --demo {demo_name} --root_dir {root_dir} --platform {platform}")
    os.system(f"python scripts/document_generation.py --app {app} --demo {demo_name} --root_dir {root_dir} --platform {platform}")
