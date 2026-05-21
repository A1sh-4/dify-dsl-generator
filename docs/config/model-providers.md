# Model Providers Configuration

## Overview

Dify supports multiple LLM providers through a unified interface. Each provider has its own API credentials, model naming conventions, supported features, and behavioral characteristics. This document covers how providers are configured in the Dify DSL, how to set up credentials, which models are available, and how to choose the right provider and model for your use case.

---

## The provider + name Fields in DSL

Every LLM node in a Dify workflow specifies a `model` block that identifies the provider, the specific model name, and the interaction mode:

```yaml
model:
  provider: anthropic
  name: claude-3-5-sonnet-20241022
  mode: chat
  completion_params:
    temperature: 0.5
    max_tokens: 2000
```

**Field breakdown:**

- `provider`: The lowercase string identifier for the model provider (see per-provider sections below). This must exactly match Dify's registered provider key.
- `name`: The model's API identifier as defined by the provider. Use the exact string the provider's API expects — copy it from the provider's documentation to avoid errors.
- `mode`: Either `chat` (for instruction-following conversational models — the vast majority) or `completion` (for older base/completion models). Almost all modern workflows use `chat`.
- `completion_params`: Optional block for sampling parameters. If omitted, Dify uses defaults. See `llm-settings.md` for the full parameter reference.

---

## Supported Providers Reference

### Anthropic

Anthropic's Claude family is known for strong instruction-following, nuanced reasoning, and a long context window across all Claude 3+ models.

- **Provider string:** `anthropic`
- **Credentials required:** `ANTHROPIC_API_KEY`
- **Available models:**
  - `claude-3-5-sonnet-20241022` — Best balance of capability and speed; recommended default
  - `claude-3-5-haiku-20241022` — Fastest Claude 3.5; cost-efficient for high-volume tasks
  - `claude-3-opus-20240229` — Highest capability for complex reasoning; slower and more expensive
  - `claude-3-sonnet-20240229` — Mid-tier Claude 3; generally superseded by claude-3-5-sonnet
  - `claude-3-haiku-20240307` — Fastest Claude 3; budget option for simple tasks

**Supported features:**
- Vision (image understanding): all Claude 3 and 3.5 models
- Tool / function calling: all Claude 3 and 3.5 models
- Structured output via tool calling: all Claude 3 and 3.5 models
- System prompts: fully supported

**DSL example:**
```yaml
model:
  provider: anthropic
  name: claude-3-5-sonnet-20241022
  mode: chat
  completion_params:
    temperature: 0.5
    max_tokens: 2000
```

---

### OpenAI

OpenAI offers the broadest range of models from commodity classification models to frontier reasoning systems. The widest ecosystem of tooling and fine-tuned variants.

- **Provider string:** `openai`
- **Credentials required:** `OPENAI_API_KEY`; optionally `OPENAI_ORGANIZATION` for organization-scoped billing
- **Available models:**
  - `gpt-4o` — Flagship multimodal model; strong across all tasks
  - `gpt-4o-mini` — Cost-efficient; excellent for RAG, classification, and light reasoning
  - `gpt-4-turbo` — Previous flagship; generally superseded by gpt-4o
  - `gpt-3.5-turbo` — Legacy; cheap but less capable; use gpt-4o-mini instead for new projects
  - `o1-preview` — Reasoning model; best for complex math and code; no system prompt support
  - `o1-mini` — Faster reasoning model; cost-optimized
  - `o3-mini` — Latest reasoning model; strong performance-to-cost ratio

**Supported features:**
- Vision: gpt-4o and gpt-4o-mini
- Function calling: all gpt-4 series
- Structured output (JSON mode + response_format): gpt-4o and gpt-4o-mini
- System prompts: not supported on o1/o3 models

**DSL example:**
```yaml
model:
  provider: openai
  name: gpt-4o-mini
  mode: chat
  completion_params:
    temperature: 0.3
    max_tokens: 1500
```

---

### Google

Google's Gemini family offers extremely long context windows and strong multimodal capabilities. Gemini 1.5 Pro's 2 million token context is unmatched for document-heavy workflows.

- **Provider string:** `google`
- **Credentials required:** `GOOGLE_API_KEY` (from Google AI Studio or Vertex AI)
- **Available models:**
  - `gemini-2.0-flash` — Latest flash model; fast and cost-efficient
  - `gemini-2.0-pro` — Latest pro model; strong general capability
  - `gemini-1.5-flash` — Highly optimized for speed and volume
  - `gemini-1.5-pro` — Up to 2 million token context; ideal for very long documents

**Supported features:**
- Vision: all Gemini models
- Very long context window: up to 2M tokens (gemini-1.5-pro)
- Function calling: all models
- top_k sampling parameter: natively supported

**DSL example:**
```yaml
model:
  provider: google
  name: gemini-1.5-pro
  mode: chat
  completion_params:
    temperature: 0.4
    top_p: 0.95
    max_tokens: 4000
```

---

### Azure OpenAI

Azure OpenAI provides the same OpenAI models hosted in Microsoft Azure infrastructure. Required for organizations with Azure enterprise agreements, data residency requirements, or compliance constraints.

- **Provider string:** `azure_openai`
- **Credentials required:**
  - Azure endpoint URL (e.g., `https://your-resource.openai.azure.com/`)
  - Azure API key
  - Deployment name (the name you gave your deployment in Azure, not the model name)
- **Available models:** Equivalent to OpenAI models, but referenced by your deployment name
- **Key difference:** The `name` field in DSL should be your Azure deployment name, not the OpenAI model string

**DSL example:**
```yaml
model:
  provider: azure_openai
  name: my-gpt4o-deployment    # Azure deployment name, not "gpt-4o"
  mode: chat
  completion_params:
    temperature: 0.5
    max_tokens: 2000
```

**Setup note:** In Dify workspace settings, you configure the endpoint URL and API key. Multiple deployments (e.g., gpt-4o + gpt-4o-mini) require separate provider entries or using Dify's multi-deployment support.

---

### Ollama (Local Models)

Ollama enables running open-source models locally on your own hardware. No API costs, no data leaving your network — ideal for privacy-sensitive applications or development without cloud spend.

- **Provider string:** `ollama`
- **Credentials required:** Server URL (default: `http://localhost:11434`). No API key by default.
- **Available models (must be pulled to your Ollama server first):**
  - `llama3.2` — Meta's latest general-purpose open model
  - `mistral` — Strong reasoning and instruction-following
  - `phi3` — Microsoft's compact model; excellent performance-to-size ratio
  - `gemma2` — Google's open model family
  - `qwen2.5` — Alibaba's multilingual model; strong for non-English tasks
  - Any other model available via `ollama pull`

**Supported features:**
- No cost per token
- Full data privacy (no external API calls)
- top_k and most sampling parameters supported
- Tool calling: supported on newer llama and mistral variants

**Tradeoffs:**
- Slower inference than cloud APIs unless you have a capable GPU
- Model quality below frontier models for complex reasoning
- No SLA or reliability guarantees

**DSL example:**
```yaml
model:
  provider: ollama
  name: llama3.2
  mode: chat
  completion_params:
    temperature: 0.6
    max_tokens: 2000
```

---

### OpenRouter

OpenRouter is a unified API gateway that provides access to hundreds of models from multiple providers through a single API key. Useful for model routing, fallback strategies, and access to models not directly integrated into Dify.

- **Provider string:** `openrouter`
- **Credentials required:** `OPENROUTER_API_KEY`
- **Available models:** Hundreds, including models from Anthropic, OpenAI, Google, Meta, Mistral, Cohere, and many others. See openrouter.ai for the full catalog.
- **Model naming:** Use OpenRouter's model identifiers, e.g., `anthropic/claude-3-5-sonnet`, `openai/gpt-4o`, `meta-llama/llama-3.2-90b-vision-instruct`

**DSL example:**
```yaml
model:
  provider: openrouter
  name: anthropic/claude-3-5-sonnet
  mode: chat
  completion_params:
    temperature: 0.5
    max_tokens: 2000
```

---

## Load Balancing

Dify supports load balancing across multiple API keys for the same provider. This is useful for:

- **Avoiding rate limits:** Distributing requests across keys avoids hitting per-key RPM/TPM limits
- **Distributing costs:** Spreading usage across billing accounts
- **Redundancy:** If one key is revoked or hits its limit, others continue serving requests

Load balancing uses a round-robin strategy by default. Configuration is done in the Dify UI:

1. Navigate to **Workspace Settings → Model Providers**
2. Select the provider you want to configure
3. Add multiple API keys under the same provider entry
4. Enable load balancing in the provider settings

This is a workspace-level setting — it applies to all workflows using that provider, not to individual nodes.

---

## Choosing a Model for Your Use Case

| Use Case | Recommended Model | Reason |
|---|---|---|
| RAG / Q&A | claude-3-5-sonnet, gpt-4o-mini | Strong instruction-following; good context use |
| Code generation | claude-3-5-sonnet, gpt-4o | High reasoning; best code accuracy |
| Long document processing | gemini-1.5-pro | 2M token context; handles entire documents |
| Fast / cheap / high volume | claude-3-5-haiku, gpt-4o-mini, gemini-2.0-flash | Low cost per token; good enough quality |
| Classification | claude-3-haiku, gpt-4o-mini | Simple task; no need for frontier capability |
| Complex reasoning / math | o3-mini, o1-preview, claude-3-opus | Reasoning models excel here |
| Local / private deployment | ollama with llama3.2 or mistral | No data leaves your infrastructure |
| Multilingual tasks | qwen2.5 (via Ollama), gemini-1.5-pro | Strong non-English support |
| Structured output | gpt-4o, claude-3-5-sonnet, gemini-1.5+ | Native structured output support |

---

## Provider-Level Error Handling

When configuring providers, keep the following in mind:

- **API key rotation:** Store keys in environment variables, not hardcoded in DSL. Rotate keys without changing workflow configuration.
- **Rate limit errors (429):** Enable load balancing with multiple keys, or add retry logic in your workflow via error branches.
- **Model deprecation:** Provider model names can be deprecated. Pin to specific dated versions (e.g., `claude-3-5-sonnet-20241022`) rather than floating aliases where possible to avoid unexpected behavior changes.
- **Regional availability:** Some Azure OpenAI deployments are region-specific. Ensure your chosen model is available in your configured Azure region.
