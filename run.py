import argparse
import os

from scripts.utils import print_with_color

arg_desc = "AppAgent - deployment phase"
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=arg_desc)
parser.add_argument("--app")
parser.add_argument("--root_dir", default="./")
parser.add_argument("--platform", choices=["android", "web"], help="Platform to automate")
args = vars(parser.parse_args())

app = args["app"]
root_dir = args["root_dir"]
platform = args["platform"]

print_with_color("Welcome to the deployment phase of AppAgent!\nBefore giving me the task, you should first tell me "
                 "the platform, app/website name, and what documentation base you want me to use. I will "
                 "try my best to complete the task without your intervention.", "yellow")

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

if not app:
    if platform == "android":
        print_with_color("What is the name of the target app?", "blue")
    else:
        print_with_color("What is the name of the target website/web session?", "blue")
    app = input()
    app = app.replace(" ", "")

os.system(f"python scripts/task_executor.py --app {app} --root_dir {root_dir} --platform {platform}")
