import base64
import os
import cv2
import pyshine as ps

from colorama import Fore, Style


def print_with_color(text: str, color="", log_file=None, heading_level=None):
    if color == "red":
        print(Fore.RED + text)
    elif color == "green":
        print(Fore.GREEN + text)
    elif color == "yellow":
        print(Fore.YELLOW + text)
    elif color == "blue":
        print(Fore.BLUE + text)
    elif color == "magenta":
        print(Fore.MAGENTA + text)
    elif color == "cyan":
        print(Fore.CYAN + text)
    elif color == "white":
        print(Fore.WHITE + text)
    elif color == "black":
        print(Fore.BLACK + text)
    else:
        print(text)
    print(Style.RESET_ALL)

    # If a log file is specified, append the message to the file
    if log_file is not None:
        # If a heading level is specified, prepend the message with the appropriate number of '#'
        if heading_level is not None:
            text = '#' * heading_level + ' ' + text
        with open(log_file, "a") as f:
            f.write(text + "\n")


def append_to_log(text: str, log_file: str, break_line: bool = True):
    with open(log_file, "a") as f:
        f.write(text + ("\n" if break_line else ""))


def append_images_as_table(images: list, log_file: str):
    """
    Append multiple images as a markdown table.

    Args:
        images: List of tuples (alt_text, image_path)
                e.g., [("Before action", "./1_before.png"), ("After action", "./1_after.png")]
        log_file: Path to the log file
    """
    if not images:
        return

    with open(log_file, "a") as f:
        # Header row with alt texts
        f.write("| " + " | ".join([alt for alt, _ in images]) + " |\n")
        # Separator row
        f.write("|" + "|".join(["------" for _ in images]) + "|\n")
        # Image row
        f.write("| " + " | ".join([f"![{alt}]({path})" for alt, path in images]) + " |\n\n")


def draw_bbox_multi(img_path, output_path, elem_list, record_mode=False, dark_mode=False):
    imgcv = cv2.imread(img_path)
    count = 1
    for elem in elem_list:
        try:
            top_left = elem.bbox[0]
            bottom_right = elem.bbox[1]
            left, top = top_left[0], top_left[1]
            right, bottom = bottom_right[0], bottom_right[1]
            label = str(count)
            if record_mode:
                if elem.attrib == "clickable":
                    color = (250, 0, 0)
                elif elem.attrib == "focusable":
                    color = (0, 0, 250)
                else:
                    color = (0, 250, 0)
                imgcv = ps.putBText(imgcv, label, text_offset_x=(left + right) // 2 + 10, text_offset_y=(top + bottom) // 2 + 10,
                                    vspace=10, hspace=10, font_scale=1, thickness=2, background_RGB=color,
                                    text_RGB=(255, 250, 250), alpha=0.5)
            else:
                text_color = (10, 10, 10) if dark_mode else (255, 250, 250)
                bg_color = (255, 250, 250) if dark_mode else (10, 10, 10)
                imgcv = ps.putBText(imgcv, label, text_offset_x=(left + right) // 2 + 10, text_offset_y=(top + bottom) // 2 + 10,
                                    vspace=10, hspace=10, font_scale=1, thickness=2, background_RGB=bg_color,
                                    text_RGB=text_color, alpha=0.5)
        except Exception as e:
            print_with_color(f"ERROR: An exception occurs while labeling the image\n{e}", "red")
        count += 1
    cv2.imwrite(output_path, imgcv)
    return imgcv


def draw_grid(img_path, output_path):
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
    """Encode image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def optimize_image(image_path, max_size=512, quality=85, output_path=None):
    """
    Resize image to reduce token usage for vision models.
    Maintains aspect ratio and resizes so the longest side is max_size.

    Args:
        image_path: Path to input image
        max_size: Maximum width or height in pixels (default: 512)
        quality: JPEG quality 1-100 (default: 85)
        output_path: Path to save optimized image (if None, overwrites input)

    Returns:
        Path to optimized image
    """
    from config import load_config

    configs = load_config()

    # Check if optimization is enabled
    if not configs.get("OPTIMIZE_IMAGES", True):
        return image_path

    # Use config values if available
    max_size = configs.get("IMAGE_MAX_WIDTH", max_size)
    max_height = configs.get("IMAGE_MAX_HEIGHT", max_size)
    max_size = min(max_size, max_height)  # Use the smaller value
    quality = configs.get("IMAGE_QUALITY", quality)

    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print_with_color(f"WARNING: Failed to read image: {image_path}", "yellow")
        return image_path

    # Get current dimensions
    height, width = img.shape[:2]
    original_size = os.path.getsize(image_path) / 1024  # KB

    # Calculate new dimensions (maintain aspect ratio)
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))

        # Resize image
        img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)

        # Save optimized image
        if output_path is None:
            output_path = image_path

        cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, quality])

        new_size = os.path.getsize(output_path) / 1024  # KB
        print_with_color(
            f"Image optimized: {width}x{height} → {new_width}x{new_height}, "
            f"{original_size:.1f}KB → {new_size:.1f}KB ({new_size/original_size*100:.0f}%)",
            "cyan"
        )
    else:
        print_with_color(f"Image already optimal: {width}x{height} ({original_size:.1f}KB)", "cyan")

    return output_path if output_path else image_path
