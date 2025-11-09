import re
import time
from abc import abstractmethod
from typing import List
from http import HTTPStatus

import requests
import ollama

from config import load_config
from utils import print_with_color, encode_image, SystemMonitor


class BaseModel:
    def __init__(self):
        pass

    @abstractmethod
    def get_model_response(self, prompt: str, images: List[str]) -> (bool, str):
        pass


class OpenAIModel(BaseModel):
    """
    OpenAI Model using base64 encoding for images.
    """
    def __init__(self, base_url: str, api_key: str, model: str, temperature: float, max_tokens: int):
        super().__init__()
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        print_with_color(f"✓ OpenAI Model initialized: {model} (using base64 encoding)", "green")

    def get_model_response(self, prompt: str, images: List[str]) -> (bool, str):
        """
        Get model response using base64 encoding for images.

        Args:
            prompt: Text prompt
            images: List of file paths

        Returns:
            (success, response_text)
        """
        # Start system monitoring
        monitor = SystemMonitor()
        monitor.start()
        start_time = time.time()

        content = [
            {
                "type": "text",
                "text": prompt
            }
        ]

        # Encode images to base64
        for img in images:
            base64_img = encode_image(img)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_img}"
                }
            })
            print_with_color(f"Image encoded to base64: {img}", "cyan")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=120).json()
        except requests.exceptions.Timeout:
            return False, "Request timeout after 120 seconds"
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"
        except Exception as e:
            return False, f"Failed to parse response: {str(e)}"

        # Calculate response time
        response_time = time.time() - start_time

        # Check for errors in response
        if "error" in response:
            return False, response["error"]["message"]

        # Check if response has expected structure
        if "choices" not in response or not response["choices"]:
            print_with_color("ERROR: No 'choices' in model response", "red")
            print_with_color(f"Response: {response}", "red")
            return False, "Invalid response format: missing 'choices'"

        # Extract content
        message = response["choices"][0]["message"]
        content = message.get("content", "")

        # Check if content is empty but reasoning exists (some models like Qwen use reasoning field)
        if not content or len(content.strip()) == 0:
            # Try to use reasoning field if available
            if "reasoning" in message and message["reasoning"]:
                print_with_color("INFO: Using reasoning field as model returned empty content", "yellow")
                content = message["reasoning"]
            else:
                print_with_color("WARNING: Model returned empty content", "yellow")
                print_with_color(f"Full response: {response}", "yellow")
                return False, "Model returned empty response"

        # Print usage info if available
        if "usage" in response:
            usage = response["usage"]
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            print_with_color(f"Request cost is "
                             f"${'{0:.2f}'.format(prompt_tokens / 1000 * 0.01 + completion_tokens / 1000 * 0.03)}",
                             "yellow")

        # Stop monitoring and print summary
        print_with_color(f"Response time: {response_time:.2f}s", "yellow")
        monitor.stop()
        monitor.print_summary()

        return True, content


class OllamaModel(BaseModel):
    """
    Ollama Model using native Ollama SDK for optimal performance.
    Uses file paths directly instead of base64 encoding.
    """
    def __init__(self, model: str, temperature: float, max_tokens: int):
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        print_with_color(f"✓ Ollama Model initialized: {model}", "green")

    def get_model_response(self, prompt: str, images: List[str]) -> (bool, str):
        """
        Get model response using Ollama SDK with file paths.

        Args:
            prompt: Text prompt
            images: List of file paths (NOT base64!)

        Returns:
            (success, response_text)
        """
        # Start monitoring
        monitor = SystemMonitor()
        monitor.start()
        start_time = time.time()

        try:
            # Ollama SDK accepts file paths directly!
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': images  # File paths as-is
                }],
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens
                }
            )

            # Calculate response time
            response_time = time.time() - start_time

            # Extract content
            content = response['message']['content']

            if not content or len(content.strip()) == 0:
                print_with_color("WARNING: Model returned empty content", "yellow")
                return False, "Model returned empty response"

            # Print summary
            print_with_color(f"Response time: {response_time:.2f}s", "yellow")
            print_with_color(f"Images sent: {len(images)} file paths (no base64 encoding)", "cyan")

            monitor.stop()
            monitor.print_summary()

            return True, content

        except Exception as e:
            response_time = time.time() - start_time
            print_with_color(f"ERROR: Ollama request failed after {response_time:.2f}s: {e}", "red")
            monitor.stop()
            return False, f"Ollama request failed: {str(e)}"


def parse_explore_rsp(rsp):
    try:
        observation = re.findall(r"Observation: (.*?)$", rsp, re.MULTILINE)[0].strip()
        think = re.findall(r"Thought: (.*?)$", rsp, re.MULTILINE)[0].strip()
        act = re.findall(r"Action: (.*?)$", rsp, re.MULTILINE)[0].strip()
        # Handle cases where Summary is missing (common with local models)
        summary_matches = re.findall(r"Summary: (.*?)$", rsp, re.MULTILINE)
        last_act = summary_matches[0].strip() if summary_matches else "No summary available"
        print_with_color("Observation:", "yellow")
        print_with_color(observation, "magenta")
        print_with_color("Thought:", "yellow")
        print_with_color(think, "magenta")
        print_with_color("Action:", "yellow")
        print_with_color(act, "magenta")
        print_with_color("Summary:", "yellow")
        print_with_color(last_act, "magenta")
        if "FINISH" in act:
            return ["FINISH", observation, think, act, last_act]
        act_name = act.split("(")[0].strip()
        if act_name == "tap":
            area = int(re.findall(r"tap\((.*?)\)", act)[0])
            return [act_name, area, last_act, observation, think, act]
        elif act_name == "text":
            input_str = re.findall(r"text\((.*?)\)", act)[0][1:-1]
            return [act_name, input_str, last_act, observation, think, act]
        elif act_name == "long_press":
            area = int(re.findall(r"long_press\((.*?)\)", act)[0])
            return [act_name, area, last_act, observation, think, act]
        elif act_name == "swipe":
            params = re.findall(r"swipe\((.*?)\)", act)[0]
            area, swipe_dir, dist = params.split(",")
            area = int(area)
            swipe_dir = swipe_dir.strip()[1:-1]
            dist = dist.strip()[1:-1]
            return [act_name, area, swipe_dir, dist, last_act, observation, think, act]
        elif act_name == "grid":
            return [act_name, observation, think, act, last_act]
        else:
            print_with_color(f"ERROR: Undefined act {act_name}!", "red")
            return ["ERROR"]
    except Exception as e:
        print_with_color(f"ERROR: an exception occurs while parsing the model response: {e}", "red")
        print_with_color(rsp, "red")
        return ["ERROR"]


def parse_grid_rsp(rsp):
    try:
        observation = re.findall(r"Observation: (.*?)$", rsp, re.MULTILINE)[0].strip()
        think = re.findall(r"Thought: (.*?)$", rsp, re.MULTILINE)[0].strip()
        act = re.findall(r"Action: (.*?)$", rsp, re.MULTILINE)[0].strip()
        # Handle cases where Summary is missing (common with local models)
        summary_matches = re.findall(r"Summary: (.*?)$", rsp, re.MULTILINE)
        last_act = summary_matches[0].strip() if summary_matches else "No summary available"
        print_with_color("Observation:", "yellow")
        print_with_color(observation, "magenta")
        print_with_color("Thought:", "yellow")
        print_with_color(think, "magenta")
        print_with_color("Action:", "yellow")
        print_with_color(act, "magenta")
        print_with_color("Summary:", "yellow")
        print_with_color(last_act, "magenta")
        if "FINISH" in act:
            return ["FINISH", observation, think, act, last_act]
        act_name = act.split("(")[0].strip()
        if act_name == "tap":
            params = re.findall(r"tap\((.*?)\)", act)[0].split(",")
            area = int(params[0].strip())
            subarea = params[1].strip()[1:-1]
            return [act_name + "_grid", area, subarea, last_act, observation, think, act]
        elif act_name == "long_press":
            params = re.findall(r"long_press\((.*?)\)", act)[0].split(",")
            area = int(params[0].strip())
            subarea = params[1].strip()[1:-1]
            return [act_name + "_grid", area, subarea, last_act, observation, think, act]
        elif act_name == "swipe":
            params = re.findall(r"swipe\((.*?)\)", act)[0].split(",")
            start_area = int(params[0].strip())
            start_subarea = params[1].strip()[1:-1]
            end_area = int(params[2].strip())
            end_subarea = params[3].strip()[1:-1]
            return [act_name + "_grid", start_area, start_subarea, end_area, end_subarea, last_act, observation, think, act]
        elif act_name == "grid":
            return [act_name, observation, think, act, last_act]
        else:
            print_with_color(f"ERROR: Undefined act {act_name}!", "red")
            return ["ERROR"]
    except Exception as e:
        print_with_color(f"ERROR: an exception occurs while parsing the model response: {e}", "red")
        print_with_color(rsp, "red")
        return ["ERROR"]


def parse_reflect_rsp(rsp):
    try:
        # Check if response is empty or too short
        if not rsp or len(rsp.strip()) < 10:
            print_with_color("ERROR: Model response is empty or too short", "red")
            print_with_color(f"Response: '{rsp}'", "red")
            return ["ERROR"]

        # Handle cases where Decision or Thought is missing
        decision_matches = re.findall(r"Decision: (.*?)$", rsp, re.MULTILINE)
        think_matches = re.findall(r"Thought: (.*?)$", rsp, re.MULTILINE)

        if not decision_matches:
            print_with_color("ERROR: No 'Decision:' found in model response", "red")
            print_with_color(rsp, "red")
            return ["ERROR"]

        if not think_matches:
            print_with_color("ERROR: No 'Thought:' found in model response", "red")
            print_with_color(rsp, "red")
            return ["ERROR"]

        decision = decision_matches[0].strip()
        think = think_matches[0].strip()

        print_with_color("Decision:", "yellow")
        print_with_color(decision, "magenta")
        print_with_color("Thought:", "yellow")
        print_with_color(think, "magenta")

        if decision == "INEFFECTIVE":
            return [decision, think, None]  # Return None for doc to maintain consistent structure
        elif decision == "BACK" or decision == "CONTINUE" or decision == "SUCCESS":
            doc_matches = re.findall(r"Documentation: (.*?)$", rsp, re.MULTILINE)
            if not doc_matches:
                print_with_color("WARNING: No 'Documentation:' found, using placeholder", "yellow")
                doc = "No documentation available"
            else:
                doc = doc_matches[0].strip()
            print_with_color("Documentation:", "yellow")
            print_with_color(doc, "magenta")
            return [decision, think, doc]
        else:
            print_with_color(f"ERROR: Undefined decision {decision}!", "red")
            return ["ERROR"]
    except Exception as e:
        print_with_color(f"ERROR: an exception occurs while parsing the model response: {e}", "red")
        print_with_color(rsp, "red")
        return ["ERROR"]
