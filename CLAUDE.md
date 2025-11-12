# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AppAgent is an LLM-based multimodal agent framework that operates smartphone applications and web browsers through human-like interactions (tapping, swiping, typing). The agent learns through autonomous exploration or human demonstration, building a knowledge base for executing complex tasks.

This is a fork enhanced for Figma automation via the [KleverDesktop](https://github.com/FigmaAI/KleverDesktop) wrapper application.

## Commands

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
Edit `config.yaml` to configure:
- Model selection: `MODEL: "api"` (OpenAI/OpenRouter) or `MODEL: "local"` (Ollama)
- API settings: `API_BASE_URL`, `API_KEY`, `API_MODEL`
- Local model: `LOCAL_MODEL` (e.g., `qwen3-vl:4b` for 16GB RAM)
- Image optimization: `OPTIMIZE_IMAGES`, `IMAGE_MAX_WIDTH`, `IMAGE_MAX_HEIGHT`
- Android paths: `ANDROID_SCREENSHOT_DIR`, `ANDROID_XML_DIR`
- Web browser: `WEB_BROWSER_TYPE`, `WEB_HEADLESS`, viewport dimensions

### Exploration Phase (Learning)
```bash
# Interactive mode - prompts for platform (Android/Web) and mode (autonomous/demo)
python learn.py

# Command-line mode
python learn.py --app <app_name> --platform android
python learn.py --app <session_name> --platform web
```

Generates documentation in `apps/<app_name>/auto_docs/` or `apps/<app_name>/demo_docs/`

### Deployment Phase (Execution)
```bash
# Interactive mode
python run.py

# Command-line mode
python run.py --app <app_name> --platform android
python run.py --app <app_name> --platform web
```

Task logs and screenshots saved to `tasks/task_<app>_<timestamp>/`

### Android Prerequisites
- Install [Android Debug Bridge (adb)](https://developer.android.com/tools/adb)
- Enable USB debugging on Android device
- Connect device via USB or use Android Studio emulator

### Web Prerequisites
```bash
# Install Playwright browsers
playwright install chromium
```

## Architecture

### Two-Phase Design

**Exploration Phase** (`learn.py` → `self_explorer.py` or `step_recorder.py` + `document_generation.py`):
- **Autonomous Exploration**: Agent explores app/website independently, attempting given task and generating UI element documentation
- **Human Demonstration**: User demonstrates task; agent observes and documents interacted elements
- Creates knowledge base: element descriptions, locations, functions

**Deployment Phase** (`run.py` → `task_executor.py`):
- Uses pre-generated documentation to complete user-specified tasks
- Agent makes decisions based on current screen state and documentation
- Automatically retries with grid overlay if element detection fails

### Controller Abstraction

Two platform controllers with unified interface:

**AndroidController** (`scripts/and_controller.py`):
- Communicates with Android devices via ADB commands
- Operations: `get_screenshot()`, `get_xml()`, `tap()`, `text()`, `swipe()`, `long_press()`, `back()`
- Parses UI hierarchy from XML dumps (`traverse_tree()`)
- Element labeling with bounding boxes
- Emulator management: `list_available_emulators()`, `start_emulator()`, `wait_for_device()`

**WebController** (`scripts/web_controller.py`):
- Browser automation via Playwright
- Operations: mirror AndroidController methods (`tap()`, `text()`, `scroll()`)
- HTML parsing for interactive elements (`get_interactive_elements()`)
- Additional methods: `navigate()`, `get_html()`, `get_current_url()`, `close()`
- URL normalization handles missing protocols

### Model Integration

**BaseModel** abstract class with two implementations (`scripts/model.py`):

**OpenAIModel**: OpenAI-compatible APIs (OpenAI, OpenRouter, etc.)
- Uses base64 image encoding
- Configurable via `API_BASE_URL`, `API_KEY`, `API_MODEL`
- Automatic image optimization before encoding

**OllamaModel**: Local inference via Ollama
- Native Ollama SDK with direct file paths (no base64)
- Optimized for vision models like `qwen3-vl:4b`
- Automatic image optimization before sending
- System prompts suppress thinking mode for concise responses

**Response Parsers**:
- `parse_explore_rsp()`: Extracts Observation, Thought, Action, Summary from exploration responses
- `parse_reflect_rsp()`: Extracts Decision, Thought, Documentation from reflection responses
- `parse_grid_rsp()`: Handles grid-based action responses for precise coordinate targeting

### Prompting System

**prompts.py**: Contains all prompt templates for different agent modes:
- Exploration prompts with/without documentation
- Reflection prompts for action evaluation
- Deployment prompts for task execution
- Grid-based interaction prompts

### Image Optimization

**Image Processing** (`scripts/utils.py` - `optimize_image()`):
- Resizes images to configurable max dimensions (default 512x512)
- Maintains aspect ratio
- JPEG compression (quality: 85)
- Reduces token usage by 50-70% for vision models
- Temporary optimized files saved to `./temp_optimized/`

### Documentation Generation

**Element Documentation**:
- Each explored/demonstrated element gets JSON documentation
- Stored with unique IDs based on resource-id, class, dimensions
- Format: `{"text": "...", "resource-id": "...", "function": "..."}`
- Documentation refined through reflection (`DOC_REFINE` config option)

### Visual Feedback

**Element Labeling** (`scripts/utils.py`):
- `draw_bbox_multi()`: Labels interactive elements with numeric tags on screenshots
- `draw_grid()`: Overlays grid for precise coordinate-based actions
- Supports dark mode (`DARK_MODE` config)
- Minimum distance between labels (`MIN_DIST` config)

**Report Generation**:
- Markdown logs with professional table formatting
- Images displayed in tables: `| Before | After |`
- `append_images_as_table()` handles multi-image rows

### Configuration Management

**config.py**: Loads `config.yaml` and merges with environment variables
- Single source of truth for all settings
- Accessed via `load_config()` throughout codebase

### Grid Overlay System

When element detection fails, agent switches to grid-based interaction:
- `calculate_grid_coordinates()` in `self_explorer.py`
- Divides screen into uniform grid (120-180px cells)
- Allows targeting specific subareas: center, corners, edges
- More robust for unlabeled UI elements

## Project Structure

```
AppAgent/
├── learn.py              # Exploration phase entry point
├── run.py                # Deployment phase entry point
├── config.yaml           # Configuration file
├── requirements.txt      # Python dependencies
├── scripts/
│   ├── config.py         # Config loader
│   ├── model.py          # Model abstractions (OpenAI/Ollama)
│   ├── and_controller.py # Android automation via ADB
│   ├── web_controller.py # Web automation via Playwright
│   ├── self_explorer.py  # Autonomous exploration logic
│   ├── step_recorder.py  # Human demonstration recorder
│   ├── document_generation.py  # Element documentation generator
│   ├── task_executor.py  # Deployment phase executor
│   ├── prompts.py        # Prompt templates
│   └── utils.py          # Helper functions (logging, image processing)
├── apps/                 # Generated documentation per app
│   └── <app_name>/
│       ├── auto_docs/    # Autonomous exploration docs
│       └── demo_docs/    # Human demonstration docs
└── tasks/                # Execution logs and screenshots
    └── task_<app>_<timestamp>/
```

## Model Configuration

### Recommended Models

| Use Case | Model | Configuration |
|----------|-------|---------------|
| Local development (16GB RAM) | `qwen3-vl:4b` via Ollama | `MODEL: "local"` |
| Production (cost-effective) | `gpt-4o-mini` via API | `MODEL: "api"` |
| Production (best quality) | `gpt-4o` via API | `MODEL: "api"` |

### Token Optimization

1. Enable image optimization: `OPTIMIZE_IMAGES: true`
2. Use smaller models: `gpt-4o-mini` is 60% cheaper than `gpt-4o`
3. Local models: Free inference via Ollama (slower on CPU)
4. Adjust max tokens: Lower `MAX_TOKENS` for shorter responses

## KleverDesktop Integration

This fork is designed as a submodule for KleverDesktop Figma automation:

```bash
# In KleverDesktop project
git submodule add https://github.com/FigmaAI/AppAgent.git AppAgent
git submodule update --init --recursive
cd AppAgent
pip install -r requirements.txt
```

Configure `config.yaml` for your use case (local or API), then run exploration or deployment phases.

## Common Development Tasks

### Adding a New Model Provider

1. Create new model class in `scripts/model.py` inheriting from `BaseModel`
2. Implement `get_model_response(prompt: str, images: List[str]) -> (bool, str)`
3. Add new model type to config.yaml
4. Update model initialization in entry point scripts (`learn.py`, `run.py`, `self_explorer.py`, `task_executor.py`)

### Adding a New Platform

1. Create new controller class in `scripts/` (e.g., `ios_controller.py`)
2. Implement methods matching AndroidController interface
3. Add platform choice to `learn.py` and `run.py`
4. Update `self_explorer.py`, `step_recorder.py`, `task_executor.py` to support new platform

### Modifying Prompts

Edit `scripts/prompts.py` - all agent prompts are centralized here. Follow existing format for action space definitions.

### Testing Without Devices

Use Android Studio emulator:
- Agent automatically attempts to start emulator if no devices found
- `start_emulator()` handles AVD detection and boot waiting
- For web: No prerequisites needed beyond Playwright installation