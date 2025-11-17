import re
import time
from abc import abstractmethod
from typing import List
from http import HTTPStatus

import requests
import ollama

try:
    from litellm import completion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from config import load_config
from utils import print_with_color, encode_image, optimize_image


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
        start_time = time.time()

        # Optimize images before encoding
        optimized_images = []
        for img_path in images:
            optimized_path = optimize_image(img_path)
            optimized_images.append(optimized_path)

        content = [
            {
                "type": "text",
                "text": prompt
            }
        ]

        # Encode images to base64
        for img in optimized_images:
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

        # Print response time
        print_with_color(f"Response time: {response_time:.2f}s", "yellow")

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
        start_time = time.time()

        # Optimize images before sending to model
        optimized_images = []
        for img_path in images:
            optimized_path = optimize_image(img_path)
            optimized_images.append(optimized_path)

        # Debug logging
        print_with_color(f"[DEBUG] Prompt length: {len(prompt)} chars", "cyan")
        print_with_color(f"[DEBUG] Images: {len(optimized_images)} files", "cyan")
        print_with_color(f"[DEBUG] Max tokens: {self.max_tokens}", "cyan")
        for i, img_path in enumerate(optimized_images):
            import os
            if os.path.exists(img_path):
                size_kb = os.path.getsize(img_path) / 1024
                print_with_color(f"[DEBUG] Image {i+1}: {size_kb:.1f}KB - {img_path}", "cyan")
            else:
                print_with_color(f"[DEBUG] Image {i+1}: NOT FOUND - {img_path}", "red")

        try:
            # Ollama SDK accepts file paths directly!
            print_with_color(f"[DEBUG] Calling ollama.chat with model={self.model}", "cyan")
            # Add system message to prevent thinking mode
            messages = [
                {
                    'role': 'system',
                    'content': 'You are a helpful assistant. Provide direct, concise responses without showing your reasoning process.'
                },
                {
                    'role': 'user',
                    'content': prompt,
                    'images': optimized_images  # Use optimized images
                }
            ]

            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens,
                    'num_ctx': 8192,  # Set context window explicitly
                    'top_p': 0.9,  # Reduce randomness
                    'repeat_penalty': 1.5  # Prevent infinite loops in thinking mode
                }
            )
            print_with_color(f"[DEBUG] ollama.chat completed", "cyan")

            # Calculate response time
            response_time = time.time() - start_time

            # Debug: Print response structure (ChatResponse object, not dict)
            print_with_color(f"[DEBUG] Response type: {type(response)}", "cyan")
            print_with_color(f"[DEBUG] Response model: {response.model}", "cyan")

            # Extract content from ChatResponse object
            content = response.message.content

            # If content is empty, try to use thinking field (qwen3-vl:4b sometimes uses this)
            if not content or len(content.strip()) == 0:
                if hasattr(response.message, 'thinking') and response.message.thinking:
                    print_with_color("WARNING: Content empty, using thinking field", "yellow")
                    # Thinking field might be too verbose, skip it
                    print_with_color(f"[DEBUG] Thinking length: {len(response.message.thinking)} chars", "yellow")
                    return False, "Model returned empty content (only thinking field available)"
                else:
                    print_with_color("WARNING: Model returned empty content", "yellow")
                    print_with_color(f"[DEBUG] Full message: {response.message}", "red")
                    return False, "Model returned empty response"

            # Print summary
            print_with_color(f"Response time: {response_time:.2f}s", "yellow")
            print_with_color(f"Response length: {len(content)} chars", "yellow")
            print_with_color(f"Images sent: {len(images)} file paths (no base64 encoding)", "cyan")

            return True, content

        except Exception as e:
            response_time = time.time() - start_time
            print_with_color(f"ERROR: Ollama request failed after {response_time:.2f}s: {e}", "red")
            return False, f"Ollama request failed: {str(e)}"


class UnifiedModel(BaseModel):
    """
    Unified Model using LiteLLM for 100+ LLM providers.

    Supports all modern model APIs including:
    - OpenRouter (openrouter/...)
    - Anthropic Claude (claude-...)
    - xAI Grok (xai/grok-...)
    - OpenAI (gpt-...)
    - Google Gemini (gemini/...)
    - Azure OpenAI (azure/...)
    - Cohere (command-...)
    - Mistral (mistral/...)
    - And 100+ more providers

    The unified interface normalizes all responses to a consistent format.
    """
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int, base_url: str = None):
        super().__init__()
        if not LITELLM_AVAILABLE:
            raise ImportError("LiteLLM is not installed. Install it with: pip install litellm")

        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url

        # Detect provider from model name
        self.provider = self._detect_provider(model)
        print_with_color(f"✓ Unified Model initialized: {model} (Provider: {self.provider}, via LiteLLM)", "green")

    def _detect_provider(self, model: str) -> str:
        """Detect the provider from the model name."""
        if model.startswith("openrouter/"):
            return "OpenRouter"
        elif model.startswith("claude-"):
            return "Anthropic"
        elif model.startswith("xai/") or model.startswith("grok"):
            return "xAI (Grok)"
        elif model.startswith("gpt-"):
            return "OpenAI"
        elif model.startswith("gemini/"):
            return "Google Gemini"
        elif model.startswith("azure/"):
            return "Azure OpenAI"
        elif model.startswith("command-") or model.startswith("cohere/"):
            return "Cohere"
        elif model.startswith("mistral/"):
            return "Mistral"
        elif model.startswith("together_ai/"):
            return "Together AI"
        elif model.startswith("perplexity/"):
            return "Perplexity"
        elif model.startswith("deepseek/"):
            return "DeepSeek"
        else:
            return "Unknown"

    def get_model_response(self, prompt: str, images: List[str]) -> (bool, str):
        """
        Get model response using LiteLLM unified interface.

        Args:
            prompt: Text prompt
            images: List of file paths

        Returns:
            (success, response_text)
        """
        start_time = time.time()

        # Optimize images before encoding
        optimized_images = []
        for img_path in images:
            optimized_path = optimize_image(img_path)
            optimized_images.append(optimized_path)

        # Build content array
        content = [{"type": "text", "text": prompt}]

        # Add images (LiteLLM handles base64 encoding internally)
        for img in optimized_images:
            base64_img = encode_image(img)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_img}"
                }
            })
            print_with_color(f"Image encoded: {img}", "cyan")

        try:
            # Prepare completion parameters
            completion_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": content}],
                "api_key": self.api_key,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "timeout": 120
            }

            # Add base_url if provided (for custom endpoints like OpenRouter)
            if self.base_url:
                completion_params["api_base"] = self.base_url
                print_with_color(f"Using custom base URL: {self.base_url}", "cyan")

            # LiteLLM automatically handles different provider formats
            print_with_color(f"Sending request to {self.provider}...", "cyan")
            response = completion(**completion_params)

            # Calculate response time
            response_time = time.time() - start_time

            # LiteLLM normalizes all responses to OpenAI format
            response_content = response.choices[0].message.content

            if not response_content or len(response_content.strip()) == 0:
                print_with_color("WARNING: Model returned empty content", "yellow")
                return False, "Model returned empty response"

            # Print usage info if available
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                prompt_tokens = getattr(usage, 'prompt_tokens', 0)
                completion_tokens = getattr(usage, 'completion_tokens', 0)
                total_tokens = getattr(usage, 'total_tokens', prompt_tokens + completion_tokens)
                print_with_color(
                    f"Tokens - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}",
                    "yellow"
                )

            # Print response time
            print_with_color(f"✓ {self.provider} response received in {response_time:.2f}s", "green")

            return True, response_content

        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)

            # Provide helpful error messages for common issues
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                print_with_color(f"ERROR: Authentication failed for {self.provider}. Check your API key.", "red")
            elif "rate_limit" in error_msg.lower() or "quota" in error_msg.lower():
                print_with_color(f"ERROR: Rate limit or quota exceeded for {self.provider}.", "red")
            elif "not found" in error_msg.lower() or "404" in error_msg:
                print_with_color(f"ERROR: Model '{self.model}' not found. Check the model name.", "red")
            else:
                print_with_color(f"ERROR: {self.provider} request failed after {response_time:.2f}s: {error_msg}", "red")

            return False, f"{self.provider} request failed: {error_msg}"


class AnthropicModel(BaseModel):
    """
    Anthropic Claude Model using official Anthropic SDK.
    Optimized for Claude Sonnet, Opus, and Haiku models.
    """
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int):
        super().__init__()
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic SDK is not installed. Install it with: pip install anthropic")

        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        print_with_color(f"✓ Anthropic Model initialized: {model}", "green")

    def get_model_response(self, prompt: str, images: List[str]) -> (bool, str):
        """
        Get model response using official Anthropic SDK.

        Args:
            prompt: Text prompt
            images: List of file paths

        Returns:
            (success, response_text)
        """
        start_time = time.time()

        # Optimize images before encoding
        optimized_images = []
        for img_path in images:
            optimized_path = optimize_image(img_path)
            optimized_images.append(optimized_path)

        # Build content array (Anthropic format)
        content = []

        # Add images first (Anthropic prefers images before text)
        for img in optimized_images:
            base64_img = encode_image(img)
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64_img
                }
            })
            print_with_color(f"Image encoded: {img}", "cyan")

        # Add text prompt
        content.append({"type": "text", "text": prompt})

        try:
            # Use official Anthropic SDK
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": content}]
            )

            # Calculate response time
            response_time = time.time() - start_time

            # Extract text from content blocks
            # Anthropic returns content as a list of content blocks
            text_content = []
            for block in message.content:
                if block.type == "text":
                    text_content.append(block.text)
                elif block.type == "thinking":
                    # Some models include thinking blocks, we can optionally log this
                    print_with_color(f"[Thinking block detected, length: {len(block.text)} chars]", "cyan")

            response_text = "".join(text_content)

            if not response_text or len(response_text.strip()) == 0:
                print_with_color("WARNING: Model returned empty content", "yellow")
                return False, "Model returned empty response"

            # Print usage info
            if hasattr(message, 'usage') and message.usage:
                print_with_color(f"Tokens - Input: {message.usage.input_tokens}, Output: {message.usage.output_tokens}", "yellow")

            # Print response time
            print_with_color(f"Response time: {response_time:.2f}s", "yellow")

            return True, response_text

        except Exception as e:
            response_time = time.time() - start_time
            print_with_color(f"ERROR: Anthropic request failed after {response_time:.2f}s: {e}", "red")
            return False, f"Anthropic request failed: {str(e)}"


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
