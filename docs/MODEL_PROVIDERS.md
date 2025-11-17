# Modern Model API Support

AppAgent now supports **100+ model providers** through a unified interface, powered by LiteLLM. You can use OpenAI, Anthropic Claude, xAI Grok, Google Gemini, OpenRouter, and many more providers using the same simple configuration.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Your Model

Edit `config.yaml`:
```yaml
MODEL: "api"  # Use "api" for all cloud models, "local" for Ollama
API_KEY: "your-api-key"
API_MODEL: "gpt-4o"  # Or any other supported model
```

That's it! The system automatically detects the provider from the model name.

---

## Supported Providers

AppAgent automatically supports all these providers through LiteLLM:

| Provider | Models | Get API Key |
|----------|--------|-------------|
| **OpenAI** | GPT-4o, GPT-4 Turbo, GPT-4o-mini | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| **Anthropic** | Claude Sonnet 4.5, Opus 4, Haiku | [console.anthropic.com](https://console.anthropic.com/) |
| **xAI** | Grok Beta, Grok Vision | [console.x.ai](https://console.x.ai/) |
| **Google** | Gemini 2.0 Flash, Gemini Pro Vision | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| **OpenRouter** | 100+ models from all providers | [openrouter.ai/keys](https://openrouter.ai/keys) |
| **Mistral** | Mistral Large, Pixtral | [console.mistral.ai](https://console.mistral.ai/) |
| **DeepSeek** | DeepSeek Chat, Reasoner | [platform.deepseek.com](https://platform.deepseek.com/) |
| **+ 90 more** | See [LiteLLM docs](https://docs.litellm.ai/docs/providers) | Various |

---

## Configuration Examples

### OpenAI GPT-4o
```yaml
MODEL: "api"
API_KEY: "sk-..."
API_MODEL: "gpt-4o"
```

### Anthropic Claude Sonnet 4.5
```yaml
MODEL: "api"
API_KEY: "sk-ant-..."
API_MODEL: "claude-sonnet-4-5-20250929"
```

### xAI Grok Vision
```yaml
MODEL: "api"
API_KEY: "xai-..."
API_MODEL: "grok-vision-beta"
```

### Google Gemini 2.0 Flash
```yaml
MODEL: "api"
API_KEY: "..."
API_MODEL: "gemini/gemini-2.0-flash-exp"
```

### OpenRouter (Access All Models)
```yaml
MODEL: "api"
API_KEY: "sk-or-v1-..."
API_BASE_URL: "https://openrouter.ai/api/v1"
API_MODEL: "openrouter/anthropic/claude-sonnet-4"
```

You can also use:
- `openrouter/google/gemini-2.0-flash-exp`
- `openrouter/x-ai/grok-2-vision-1212`
- `openrouter/openai/gpt-4o`
- And 100+ more!

### Mistral Pixtral (Vision)
```yaml
MODEL: "api"
API_KEY: "..."
API_MODEL: "mistral/pixtral-12b-2409"
```

### DeepSeek Chat
```yaml
MODEL: "api"
API_KEY: "..."
API_MODEL: "deepseek/deepseek-chat"
```

---

## Command Line Usage

Override model settings from the command line:

```bash
# Use Claude Sonnet 4.5
python scripts/self_explorer.py \
  --model api \
  --model_name "claude-sonnet-4-5-20250929" \
  --app YourApp

# Use Grok via OpenRouter
python scripts/task_executor.py \
  --model api \
  --model_name "openrouter/x-ai/grok-2-vision-1212" \
  --app YourApp \
  --task_desc "Your task here"

# Use Gemini 2.0 Flash
python scripts/self_explorer.py \
  --model api \
  --model_name "gemini/gemini-2.0-flash-exp" \
  --app YourApp
```

---

## How It Works

### Automatic Provider Detection

The system automatically detects the provider from your model name:

- `gpt-*` → OpenAI
- `claude-*` → Anthropic
- `grok*` or `xai/*` → xAI
- `gemini/*` → Google
- `openrouter/*` → OpenRouter
- `mistral/*` → Mistral
- `deepseek/*` → DeepSeek
- And more...

No need to configure the provider separately!

### LiteLLM Integration

Under the hood, AppAgent uses [LiteLLM](https://docs.litellm.ai/) to:
- Normalize API responses across all providers
- Handle authentication automatically
- Provide helpful error messages
- Support 100+ providers with a single interface

### Fallback Mode

If LiteLLM is not installed, AppAgent falls back to basic OpenAI-compatible mode using the `requests` library. Install LiteLLM for full provider support:

```bash
pip install litellm
```

---

## Features

### ✅ What's Supported

- **100+ model providers** through LiteLLM
- **Vision models** from all major providers
- **Automatic format conversion** (all responses normalized)
- **Custom base URLs** (for OpenRouter, proxies, etc.)
- **Token usage tracking** across all providers
- **Helpful error messages** for common issues
- **Backward compatibility** with existing configurations

### 🎯 Best Practices

1. **Start with cheaper models** for testing:
   - `gpt-4o-mini` (OpenAI)
   - `claude-3-5-haiku-20241022` (Anthropic)
   - `gemini/gemini-2.0-flash-exp` (Google)

2. **Use OpenRouter** for easy access to multiple providers:
   - Single API key
   - Unified billing
   - Access 100+ models

3. **Optimize costs**:
   - Enable image optimization in `config.yaml`
   - Set appropriate `MAX_TOKENS` limits
   - Use fast models for simple tasks

4. **Monitor usage**:
   - Check token counts in console output
   - Track API costs through provider dashboards

---

## Troubleshooting

### Authentication Errors
```
ERROR: Authentication failed for [Provider]. Check your API key.
```

**Solution:** Verify your API key is correct and has proper permissions.

### Model Not Found
```
ERROR: Model 'xxx' not found. Check the model name.
```

**Solution:** Check the model name spelling. Refer to provider documentation for available models.

### Rate Limits
```
ERROR: Rate limit or quota exceeded for [Provider].
```

**Solution:** Wait a few minutes or upgrade your plan.

### Empty Response
```
WARNING: Model returned empty content
```

**Solution:**
- Try reducing `IMAGE_MAX_WIDTH` and `IMAGE_MAX_HEIGHT` in `config.yaml`
- Increase `MAX_TOKENS` if responses are being cut off

---

## Advanced Configuration

### Custom Base URLs

For providers like OpenRouter or custom proxies:

```yaml
API_BASE_URL: "https://openrouter.ai/api/v1"
API_KEY: "sk-or-v1-..."
API_MODEL: "openrouter/anthropic/claude-sonnet-4"
```

### Image Optimization

Reduce costs and latency by optimizing images:

```yaml
IMAGE_MAX_WIDTH: 512
IMAGE_MAX_HEIGHT: 512
IMAGE_QUALITY: 85
OPTIMIZE_IMAGES: true
```

### Model Settings

Adjust model behavior:

```yaml
TEMPERATURE: 0.0      # More deterministic (0-1)
MAX_TOKENS: 4096      # Maximum response length
REQUEST_INTERVAL: 10  # Seconds between requests
```

---

## Migration Guide

### From Previous Versions

If you were using `unified` or `anthropic` modes:

**Old Configuration:**
```yaml
MODEL: "unified"
UNIFIED_API_KEY: "sk-ant-..."
UNIFIED_MODEL: "claude-sonnet-4-5-20250929"
```

**New Configuration:**
```yaml
MODEL: "api"
API_KEY: "sk-ant-..."
API_MODEL: "claude-sonnet-4-5-20250929"
```

The new simplified approach works the same way but with less configuration!

---

## Additional Resources

- **LiteLLM Documentation:** [docs.litellm.ai](https://docs.litellm.ai/)
- **Supported Providers:** [docs.litellm.ai/docs/providers](https://docs.litellm.ai/docs/providers)
- **OpenRouter Models:** [openrouter.ai/models](https://openrouter.ai/models)
- **AppAgent Documentation:** See main README.md

---

## Support

For issues with AppAgent's model integration:
1. Check `config.yaml` configuration
2. Verify API key and model name
3. Test with `gpt-4o-mini` to isolate issues
4. Check provider documentation for model availability

For provider-specific API issues, contact the respective provider's support.
