# Modern Model API Providers Guide

This guide shows you how to use AppAgent with various modern AI model providers including **OpenRouter, Anthropic Claude, xAI Grok, OpenAI, Google Gemini**, and many more.

## Table of Contents
- [Quick Start](#quick-start)
- [Supported Providers](#supported-providers)
- [Configuration Guide](#configuration-guide)
- [Provider-Specific Setup](#provider-specific-setup)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Choose Your Provider
AppAgent supports **100+ model providers** through two methods:

**Method 1: Unified Mode (Recommended)**
- Use `MODEL: "unified"` in `config.yaml`
- Works with **OpenRouter, Claude, Grok, Gemini, GPT-4, and 100+ more**
- Single interface, normalized responses

**Method 2: Direct SDK**
- Use `MODEL: "anthropic"` for Anthropic Claude (uses official SDK)
- Optimized for Claude-specific features

### 3. Configure Your API Key
Edit `config.yaml`:
```yaml
MODEL: "unified"
UNIFIED_API_KEY: "your-api-key-here"
UNIFIED_MODEL: "claude-sonnet-4-5-20250929"
```

---

## Supported Providers

| Provider | Model Examples | Prefix | Vision Support |
|----------|---------------|--------|----------------|
| **OpenRouter** | Claude, GPT-4, Gemini, Grok, etc. | `openrouter/` | ✅ |
| **Anthropic** | Claude Sonnet 4.5, Opus 4, Haiku | `claude-` | ✅ |
| **xAI** | Grok Beta, Grok Vision | `xai/` | ✅ |
| **OpenAI** | GPT-4o, GPT-4 Turbo, GPT-4o Mini | `gpt-` | ✅ |
| **Google** | Gemini 2.0 Flash, Gemini Pro Vision | `gemini/` | ✅ |
| **Mistral** | Mistral Large, Pixtral | `mistral/` | ✅ |
| **DeepSeek** | DeepSeek Chat, DeepSeek Reasoner | `deepseek/` | ❌ |
| **Together AI** | Various open models | `together_ai/` | Varies |
| **Perplexity** | Sonar models | `perplexity/` | ❌ |
| **Cohere** | Command R+, Command R | `command-` | ❌ |

And 90+ more providers supported by [LiteLLM](https://docs.litellm.ai/docs/providers)!

---

## Configuration Guide

### Unified Mode Configuration
Edit `config.yaml`:

```yaml
MODEL: "unified"  # Use LiteLLM for all modern APIs

# Required fields
UNIFIED_API_KEY: "your-api-key"
UNIFIED_MODEL: "model-name"

# Optional: Custom base URL (for OpenRouter, custom endpoints, etc.)
UNIFIED_BASE_URL: ""  # Leave empty for default endpoints

# Common settings
TEMPERATURE: 0.0
MAX_TOKENS: 4096
```

### Command Line Override
You can override settings via CLI:
```bash
python scripts/self_explorer.py \
  --model unified \
  --model_name "claude-sonnet-4-5-20250929" \
  --app YourApp
```

---

## Provider-Specific Setup

### 🌐 OpenRouter (Recommended for Multi-Model Access)

**Why OpenRouter?**
- Access 100+ models through one API
- No need to manage multiple API keys
- Competitive pricing
- Unified billing

**Setup:**
```yaml
MODEL: "unified"
UNIFIED_API_KEY: "sk-or-v1-..."  # Get from https://openrouter.ai/keys
UNIFIED_BASE_URL: "https://openrouter.ai/api/v1"
UNIFIED_MODEL: "openrouter/anthropic/claude-sonnet-4"
```

**Popular Models via OpenRouter:**
```yaml
# Claude Sonnet 4
UNIFIED_MODEL: "openrouter/anthropic/claude-sonnet-4"

# GPT-4o
UNIFIED_MODEL: "openrouter/openai/gpt-4o"

# Gemini 2.0 Flash
UNIFIED_MODEL: "openrouter/google/gemini-2.0-flash-exp"

# Grok 2 Vision
UNIFIED_MODEL: "openrouter/x-ai/grok-2-vision-1212"

# DeepSeek Chat
UNIFIED_MODEL: "openrouter/deepseek/deepseek-chat"
```

---

### 🤖 Anthropic Claude (Direct API)

**Setup via Unified Mode:**
```yaml
MODEL: "unified"
UNIFIED_API_KEY: "sk-ant-..."  # Get from https://console.anthropic.com/
UNIFIED_MODEL: "claude-sonnet-4-5-20250929"
```

**Setup via Anthropic SDK (Alternative):**
```yaml
MODEL: "anthropic"
ANTHROPIC_API_KEY: "sk-ant-..."
ANTHROPIC_MODEL: "claude-sonnet-4-5-20250929"
```

**Available Claude Models:**
```yaml
# Latest Sonnet 4.5 (Best for most tasks)
UNIFIED_MODEL: "claude-sonnet-4-5-20250929"

# Opus 4 (Most capable)
UNIFIED_MODEL: "claude-opus-4-20250514"

# Sonnet 3.5 (Previous generation)
UNIFIED_MODEL: "claude-3-5-sonnet-20241022"

# Haiku 3.5 (Fast and affordable)
UNIFIED_MODEL: "claude-3-5-haiku-20241022"
```

---

### 🚀 xAI Grok

**Setup:**
```yaml
MODEL: "unified"
UNIFIED_API_KEY: "xai-..."  # Get from https://console.x.ai/
UNIFIED_MODEL: "xai/grok-beta"
```

**Available Grok Models:**
```yaml
# Grok Beta
UNIFIED_MODEL: "xai/grok-beta"

# Grok Vision Beta (with image understanding)
UNIFIED_MODEL: "xai/grok-vision-beta"
```

---

### 🔵 OpenAI

**Setup:**
```yaml
MODEL: "unified"
UNIFIED_API_KEY: "sk-..."  # Get from https://platform.openai.com/api-keys
UNIFIED_MODEL: "gpt-4o"
```

**Available Models:**
```yaml
# GPT-4 Omni (Latest, multimodal)
UNIFIED_MODEL: "gpt-4o"

# GPT-4 Omni Mini (Faster, cheaper)
UNIFIED_MODEL: "gpt-4o-mini"

# GPT-4 Turbo
UNIFIED_MODEL: "gpt-4-turbo"

# GPT-4 Vision
UNIFIED_MODEL: "gpt-4-vision-preview"
```

---

### 🔮 Google Gemini

**Setup:**
```yaml
MODEL: "unified"
UNIFIED_API_KEY: "..."  # Get from https://aistudio.google.com/app/apikey
UNIFIED_MODEL: "gemini/gemini-2.0-flash-exp"
```

**Available Models:**
```yaml
# Gemini 2.0 Flash (Latest, fast)
UNIFIED_MODEL: "gemini/gemini-2.0-flash-exp"

# Gemini Pro Vision
UNIFIED_MODEL: "gemini/gemini-pro-vision"

# Gemini Pro
UNIFIED_MODEL: "gemini/gemini-pro"
```

---

### 🌟 Mistral AI

**Setup:**
```yaml
MODEL: "unified"
UNIFIED_API_KEY: "..."  # Get from https://console.mistral.ai/
UNIFIED_MODEL: "mistral/mistral-large-latest"
```

**Available Models:**
```yaml
# Mistral Large (Most capable)
UNIFIED_MODEL: "mistral/mistral-large-latest"

# Pixtral (Vision model)
UNIFIED_MODEL: "mistral/pixtral-12b-2409"

# Mistral Medium
UNIFIED_MODEL: "mistral/mistral-medium-latest"
```

---

### 🔍 DeepSeek

**Setup:**
```yaml
MODEL: "unified"
UNIFIED_API_KEY: "..."  # Get from https://platform.deepseek.com/
UNIFIED_MODEL: "deepseek/deepseek-chat"
```

**Available Models:**
```yaml
# DeepSeek Chat
UNIFIED_MODEL: "deepseek/deepseek-chat"

# DeepSeek Reasoner
UNIFIED_MODEL: "deepseek/deepseek-reasoner"

# DeepSeek Coder
UNIFIED_MODEL: "deepseek/deepseek-coder"
```

---

## Troubleshooting

### Authentication Errors
```
ERROR: Authentication failed for [Provider]. Check your API key.
```
**Solution:**
- Verify your API key is correct in `config.yaml`
- Ensure the key has proper permissions
- Check if your account has credits/quota

### Model Not Found
```
ERROR: Model 'xxx' not found. Check the model name.
```
**Solution:**
- Verify model name is spelled correctly
- Check if model requires specific access/waitlist
- Refer to provider documentation for available models

### Rate Limit Errors
```
ERROR: Rate limit or quota exceeded for [Provider].
```
**Solution:**
- Wait a few minutes and try again
- Check your account's rate limits
- Consider upgrading your plan or using a different model

### Empty Response
```
WARNING: Model returned empty content
```
**Solution:**
- Some models may timeout on complex images
- Try reducing `IMAGE_MAX_WIDTH` and `IMAGE_MAX_HEIGHT` in config.yaml
- Increase `MAX_TOKENS` if the response is being cut off

### Provider-Specific Issues

**OpenRouter:**
- Ensure you're using the correct model format: `openrouter/provider/model-name`
- Check [OpenRouter Models](https://openrouter.ai/models) for available models
- Set `UNIFIED_BASE_URL: "https://openrouter.ai/api/v1"`

**Anthropic:**
- Ensure API key starts with `sk-ant-`
- Claude models require `max_tokens` parameter (already set in config)

**xAI Grok:**
- Grok is currently in beta - you may need waitlist access
- Ensure API key format is correct

---

## Best Practices

### 1. Choose the Right Model
- **For complex reasoning:** Claude Opus 4, GPT-4o
- **For speed:** Claude Sonnet 4.5, GPT-4o-mini, Gemini 2.0 Flash
- **For cost:** GPT-4o-mini, Claude Haiku, Gemini Flash
- **For vision tasks:** All models listed support vision

### 2. Optimize Performance
```yaml
# Faster responses
TEMPERATURE: 0.0  # More deterministic
MAX_TOKENS: 2048  # Shorter responses

# Better quality
TEMPERATURE: 0.3  # More creative
MAX_TOKENS: 4096  # Longer responses

# Image optimization (reduces cost & latency)
IMAGE_MAX_WIDTH: 512
IMAGE_MAX_HEIGHT: 512
OPTIMIZE_IMAGES: true
```

### 3. Monitor Costs
- Start with cheaper models (GPT-4o-mini, Claude Haiku) for testing
- Use OpenRouter to compare pricing across models
- Enable image optimization to reduce token usage
- Set reasonable `MAX_TOKENS` limits

### 4. Handle Errors Gracefully
- Implement retry logic for transient errors
- Have fallback models configured
- Monitor rate limits

---

## Additional Resources

- **LiteLLM Documentation:** https://docs.litellm.ai/
- **OpenRouter:** https://openrouter.ai/
- **Anthropic Claude:** https://console.anthropic.com/
- **OpenAI Platform:** https://platform.openai.com/
- **Google AI Studio:** https://aistudio.google.com/
- **xAI Console:** https://console.x.ai/

---

## Support

For issues specific to AppAgent's model integration:
1. Check this documentation first
2. Verify your configuration in `config.yaml`
3. Test with a simple model (e.g., `gpt-4o-mini`) to isolate issues
4. Report issues with clear error messages and configuration details

For provider-specific API issues, contact the respective provider's support.
