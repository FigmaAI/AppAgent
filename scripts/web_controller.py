import os
import time
from typing import List, Tuple
from playwright.sync_api import sync_playwright, Page, Browser
import cv2
from bs4 import BeautifulSoup

from config import load_config
from utils import print_with_color


configs = load_config()


class WebElement:
    """Web element similar to AndroidElement for consistency"""
    def __init__(self, uid, bbox, attrib):
        self.uid = uid
        self.bbox = bbox
        self.attrib = attrib


def extract_interactive_elements(page: Page, html_content: str = None) -> List[WebElement]:
    """
    Extract interactive elements from HTML using Playwright's accessibility tree
    and DOM analysis. Returns list of WebElement objects.

    Interactive elements include:
    - Links (<a>)
    - Buttons (<button>, <input type="button/submit">)
    - Input fields (<input>, <textarea>, <select>)
    - Clickable elements (role="button", onclick handlers)
    """
    elem_list = []

    if html_content is None:
        html_content = page.content()

    # Use Playwright's built-in locator to find interactive elements
    # This is more reliable than pure HTML parsing
    selectors = [
        'a[href]',  # Links
        'button',  # Buttons
        'input:not([type="hidden"])',  # Input fields (excluding hidden)
        'textarea',  # Text areas
        'select',  # Dropdowns
        '[role="button"]',  # ARIA buttons
        '[onclick]',  # Elements with click handlers
        '[role="link"]',  # ARIA links
        '[role="textbox"]',  # ARIA textboxes
        '[contenteditable="true"]',  # Editable content
    ]

    seen_positions = set()
    min_dist = configs.get("MIN_DIST", 30)

    for selector in selectors:
        try:
            elements = page.locator(selector).all()
            for elem in elements:
                try:
                    # Check if element is visible
                    if not elem.is_visible():
                        continue

                    # Get bounding box
                    bbox_dict = elem.bounding_box()
                    if not bbox_dict:
                        continue

                    x = bbox_dict['x']
                    y = bbox_dict['y']
                    width = bbox_dict['width']
                    height = bbox_dict['height']

                    # Skip tiny elements (likely not interactive)
                    if width < 5 or height < 5:
                        continue

                    # Calculate center
                    center_x = int(x + width / 2)
                    center_y = int(y + height / 2)

                    # Check if too close to existing element
                    too_close = False
                    for seen_pos in seen_positions:
                        dist = ((center_x - seen_pos[0]) ** 2 + (center_y - seen_pos[1]) ** 2) ** 0.5
                        if dist < min_dist:
                            too_close = True
                            break

                    if too_close:
                        continue

                    seen_positions.add((center_x, center_y))

                    # Get element attributes
                    tag_name = elem.evaluate("el => el.tagName.toLowerCase()")
                    elem_id = elem.get_attribute("id") or ""
                    elem_class = elem.get_attribute("class") or ""
                    elem_type = elem.get_attribute("type") or ""
                    elem_role = elem.get_attribute("role") or ""
                    elem_text = elem.inner_text()[:50] if elem.inner_text() else ""
                    elem_placeholder = elem.get_attribute("placeholder") or ""

                    # Create unique identifier
                    uid = f"{tag_name}"
                    if elem_id:
                        uid += f"#{elem_id}"
                    elif elem_class:
                        class_name = elem_class.split()[0] if elem_class else ""
                        uid += f".{class_name}"
                    if elem_type:
                        uid += f"[type={elem_type}]"
                    if elem_text:
                        safe_text = elem_text.replace(" ", "_").replace("/", "_")[:20]
                        uid += f"_{safe_text}"

                    # Store attributes
                    attrib = {
                        "tag": tag_name,
                        "id": elem_id,
                        "class": elem_class,
                        "type": elem_type,
                        "role": elem_role,
                        "text": elem_text,
                        "placeholder": elem_placeholder,
                        "selector": selector,
                        "center": (center_x, center_y)
                    }

                    # Create WebElement
                    bbox = ((int(x), int(y)), (int(x + width), int(y + height)))
                    web_elem = WebElement(uid, bbox, attrib)
                    elem_list.append(web_elem)

                except Exception as e:
                    # Skip elements that cause errors
                    continue

        except Exception as e:
            # Skip selectors that cause errors
            continue

    print_with_color(f"Found {len(elem_list)} interactive elements on the page", "yellow")
    return elem_list


class WebController:
    """Web controller using Playwright, similar interface to AndroidController"""

    def __init__(self, browser_type="chromium", headless=False, url=None):
        """
        Initialize Playwright browser

        Args:
            browser_type: "chromium", "firefox", or "webkit"
            headless: Run browser in headless mode
            url: Initial URL to navigate to
        """
        self.playwright = sync_playwright().start()

        # Launch browser
        if browser_type == "chromium":
            self.browser = self.playwright.chromium.launch(headless=headless)
        elif browser_type == "firefox":
            self.browser = self.playwright.firefox.launch(headless=headless)
        elif browser_type == "webkit":
            self.browser = self.playwright.webkit.launch(headless=headless)
        else:
            raise ValueError(f"Invalid browser_type: {browser_type}")

        # Create context and page
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.page = self.context.new_page()

        # Get viewport size
        viewport = self.page.viewport_size
        self.width = viewport["width"]
        self.height = viewport["height"]

        print_with_color(f"WebController initialized: {browser_type}, {self.width}x{self.height}", "green")

        # Navigate to initial URL if provided
        if url:
            self.page.goto(url, wait_until="networkidle")
            print_with_color(f"Navigated to: {url}", "yellow")

    def navigate(self, url: str):
        """Navigate to URL"""
        self.page.goto(url, wait_until="networkidle")
        time.sleep(1)  # Extra wait for dynamic content
        return self.page.url

    def get_screenshot(self, prefix: str, save_dir: str) -> str:
        """
        Capture screenshot and save to file

        Args:
            prefix: Filename prefix (e.g., "step_1")
            save_dir: Directory to save screenshot

        Returns:
            Path to saved screenshot
        """
        os.makedirs(save_dir, exist_ok=True)
        screenshot_path = os.path.join(save_dir, f"{prefix}.png")
        self.page.screenshot(path=screenshot_path, full_page=False)
        return screenshot_path

    def get_html(self, prefix: str, save_dir: str) -> str:
        """
        Get HTML content and save to file (similar to get_xml for Android)

        Args:
            prefix: Filename prefix
            save_dir: Directory to save HTML

        Returns:
            Path to saved HTML file
        """
        os.makedirs(save_dir, exist_ok=True)
        html_path = os.path.join(save_dir, f"{prefix}.html")
        html_content = self.page.content()

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_path

    def get_interactive_elements(self) -> List[WebElement]:
        """Get list of interactive elements on current page"""
        return extract_interactive_elements(self.page)

    def back(self):
        """Go back to previous page"""
        self.page.go_back(wait_until="networkidle")
        return "SUCCESS"

    def tap(self, x: int, y: int):
        """
        Click at coordinates (x, y)

        Args:
            x: X coordinate
            y: Y coordinate
        """
        try:
            self.page.mouse.click(x, y)
            time.sleep(0.5)  # Wait for click to register
            return "SUCCESS"
        except Exception as e:
            print_with_color(f"Click failed: {e}", "red")
            return "ERROR"

    def click_element(self, element: WebElement):
        """Click on a WebElement"""
        center = element.attrib.get("center")
        if center:
            return self.tap(center[0], center[1])
        return "ERROR"

    def text(self, input_str: str):
        """
        Type text into focused element

        Args:
            input_str: Text to type
        """
        try:
            self.page.keyboard.type(input_str)
            time.sleep(0.3)
            return "SUCCESS"
        except Exception as e:
            print_with_color(f"Text input failed: {e}", "red")
            return "ERROR"

    def text_to_element(self, element: WebElement, input_str: str):
        """Type text into specific element"""
        try:
            # Click element first to focus
            self.click_element(element)
            time.sleep(0.2)

            # Clear existing text if input field
            if element.attrib.get("tag") in ["input", "textarea"]:
                self.page.keyboard.press("Control+A")
                self.page.keyboard.press("Backspace")

            # Type text
            return self.text(input_str)
        except Exception as e:
            print_with_color(f"Text to element failed: {e}", "red")
            return "ERROR"

    def scroll(self, direction: str, amount: int = None):
        """
        Scroll the page

        Args:
            direction: "up", "down", "left", "right"
            amount: Scroll amount in pixels (default: 1/3 of viewport)
        """
        if amount is None:
            amount = self.height // 3 if direction in ["up", "down"] else self.width // 3

        try:
            if direction == "down":
                self.page.mouse.wheel(0, amount)
            elif direction == "up":
                self.page.mouse.wheel(0, -amount)
            elif direction == "right":
                self.page.mouse.wheel(amount, 0)
            elif direction == "left":
                self.page.mouse.wheel(-amount, 0)
            else:
                return "ERROR"

            time.sleep(0.5)  # Wait for scroll to complete
            return "SUCCESS"
        except Exception as e:
            print_with_color(f"Scroll failed: {e}", "red")
            return "ERROR"

    def swipe(self, x: int, y: int, direction: str, dist: str = "medium", quick: bool = False):
        """
        Swipe gesture (implemented as scroll for web)
        Kept for compatibility with Android controller interface
        """
        return self.scroll(direction)

    def get_current_url(self) -> str:
        """Get current page URL"""
        return self.page.url

    def get_page_title(self) -> str:
        """Get current page title"""
        return self.page.title()

    def close(self):
        """Close browser and cleanup"""
        self.page.close()
        self.context.close()
        self.browser.close()
        self.playwright.stop()
        print_with_color("WebController closed", "yellow")
