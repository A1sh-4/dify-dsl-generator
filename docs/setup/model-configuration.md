# Model Provider Configuration

Dify requires at least one LLM provider to run any workflow or chatflow. This guide covers how to add model providers, which credentials each requires, and how model names appear in DSL YAML files.

---

## How to Add a Model Provider

The process is the same for all providers:

1. Open your Dify instance and go to **Settings → Model Provider**
2. Click the provider you want to add (e.g., Anthropic, OpenAI)
3. Enter the required credentials (API key, endpoint URL, etc.)
4. Click **Save**
5. Click **Test** to verify the credentials work

Once a provider is active, its models are available in all LLM nodes across all apps in your workspace.

---

## Provider 1: Anthropic (Claude)

**Where to get credentials:** [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key

**Fields in Dify:**
| Field | Value |
|---|---|
| `api_key` | Your Anthropic API key (starts with `sk-ant-`) |

**Available models:**
- `claude-opus-4-7` — most capable, best for complex reasoning and long documents
- `claude-sonnet-4-6` — strong balance of capability and speed (recommended default)
- `claude-haiku-4-5-20251001` — fastest and most cost-efficient, good for classification and simple tasks

**Capabilities:** Text generation, vision (image input), extended thinking (claude-3.7+), tool use

**DSL YAML reference:**
```yaml
model:
  provider: anthropic
  name: claude-sonnet-4-6
  mode: chat
  completion_params:
    temperature: 0.7
    max_tokens: 4096
```

**Notes:** Extended thinking is enabled per-node via `enable_thinking: true` in `completion_params`. Claude models support vision input when the node receives an image variable.

---

## Provider 2: OpenAI

**Where to get credentials:** [platform.openai.com](https://platform.openai.com) → API Keys → Create new secret key

**Fields in Dify:**
| Field | Value |
|---|---|
| `api_key` | Your OpenAI API key (starts with `sk-`) |
| `organization` | (Optional) Your OpenAI organization ID |

**Available models:**
- `gpt-4o` — flagship multimodal model, vision + text + function calling
- `gpt-4o-mini` — fast and cost-efficient, good for high-volume tasks
- `gpt-4-turbo` — previous generation flagship, 128K context
- `gpt-3.5-turbo` — legacy model, cheapest option

**Capabilities:** Text generation, vision (gpt-4o), function calling, structured output (JSON mode), streaming

**DSL YAML reference:**
```yaml
model:
  provider: openai
  name: gpt-4o
  mode: chat
  completion_params:
    temperature: 0.5
    max_tokens: 2048
```

**Notes:** For structured JSON output, set `response_format: json_object` in `completion_params`. OpenAI's organization ID is only required if your API key belongs to multiple organizations.

---

## Provider 3: Google (Gemini)

**Where to get credentials:** [aistudio.google.com](https://aistudio.google.com) → Get API Key

**Fields in Dify:**
| Field | Value |
|---|---|
| `api_key` | Your Google AI Studio API key |

**Available models:**
- `gemini-2.0-flash` — fast, multimodal, good for high-throughput use cases
- `gemini-1.5-pro` — large context window (1 million tokens), strong reasoning
- `gemini-1.5-flash` — cost-efficient version of 1.5 Pro

**Capabilities:** Text generation, vision, audio input (Gemini 1.5+), very long context windows, code generation

**DSL YAML reference:**
```yaml
model:
  provider: google
  name: gemini-2.0-flash
  mode: chat
  completion_params:
    temperature: 0.7
    max_tokens: 8192
```

**Notes:** Gemini 1.5 Pro's 1M token context window makes it well-suited for workflows that process entire documents or long conversation histories. Ensure your Dify version supports the Gemini provider (added in Dify 0.6.x).

---

## Provider 4: Ollama (Local Models)

Ollama lets you run open-source models locally, with no API key and no per-token cost. Ideal for development, privacy-sensitive workflows, or teams with their own GPU hardware.

**Where to get Ollama:** [ollama.ai](https://ollama.ai) — download and install for your OS

**Pull a model before adding the provider:**
```bash
ollama pull llama3
ollama pull mistral
ollama pull qwen2
```

**Fields in Dify:**
| Field | Value |
|---|---|
| `base_url` | Ollama server URL (default: `http://localhost:11434`) |

No API key is required. If Dify is running in Docker and Ollama is on the host, use `http://host.docker.internal:11434` instead of `localhost`.

**Available models:** Whatever you have pulled locally. Common choices:
- `llama3` / `llama3:70b` — Meta's Llama 3 family
- `mistral` / `mixtral` — Mistral AI models
- `qwen2` — Alibaba's Qwen 2 series
- `phi3` — Microsoft's small-but-capable Phi-3

**DSL YAML reference:**
```yaml
model:
  provider: ollama
  name: llama3
  mode: chat
  completion_params:
    temperature: 0.7
    max_tokens: 2048
```

**Notes:** Ollama models run on your machine's CPU or GPU. Response speed depends on your hardware. Not recommended for production workflows serving many concurrent users.

---

## Provider 5: Azure OpenAI

Azure OpenAI gives you access to OpenAI models hosted in Microsoft Azure, which is required for some enterprise compliance scenarios.

**Where to get credentials:** Azure Portal → Azure OpenAI resource → Keys and Endpoint

**Fields in Dify:**
| Field | Value |
|---|---|
| `api_key` | Azure OpenAI key (from Keys and Endpoint) |
| `api_base` | Your Azure endpoint URL (e.g., `https://your-resource.openai.azure.com/`) |
| `api_version` | API version string (e.g., `2024-08-01-preview`) |

**Model naming:** In Azure OpenAI, you deploy models under custom deployment names. The model name in Dify must match your **deployment name**, not the underlying model name.

**DSL YAML reference:**
```yaml
model:
  provider: azure_openai
  name: my-gpt4o-deployment
  mode: chat
  completion_params:
    temperature: 0.7
    max_tokens: 4096
```

**Notes:** Create deployments in Azure AI Studio before adding credentials to Dify. Each deployment can have a different model version and capacity quota.

---

## Setting the System Model

Dify uses a "system model" for built-in tasks that don't have an explicit model configured — such as automatic question classification and intent detection.

**Go to:** Settings → Model Provider → System Model Settings

| Setting | Purpose |
|---|---|
| Text generation model | Default LLM for nodes without an explicit model, and for Dify's internal classification |
| Embedding model | Used for knowledge base indexing and semantic retrieval |
| Reranking model | Used when reranking is enabled in knowledge retrieval nodes |
| Speech-to-text model | Used for voice input features |

The embedding model set here must match the embedding model used when a knowledge base was indexed. If you change the system embedding model after indexing documents, you must re-index those documents.

---

## Load Balancing Across Multiple API Keys

To distribute load across multiple API keys (for higher rate limits or fault tolerance):

1. Go to Settings → Model Provider → [Provider]
2. Click **Add Credential** to add a second set of credentials
3. Dify will round-robin requests across all active credentials

This is useful for OpenAI where rate limits are per-key, and for teams where individuals have separate API accounts.

---

## Testing a Model After Adding

After saving credentials:

1. Go to Settings → Model Provider → [Provider]
2. Click the **Test** button next to the provider
3. A test completion request is sent — green means the credentials work, red means there is a credential or connectivity error

Always test before using a new provider in a production workflow.

---

## Model Name Strings in DSL YAML

The `dsl-generator` agent uses these exact provider and model name strings when building DSL files. Reference this table when reviewing or editing generated YAML manually:

| Provider display name | DSL `provider` string | Example `name` string |
|---|---|---|
| Anthropic | `anthropic` | `claude-sonnet-4-6` |
| OpenAI | `openai` | `gpt-4o` |
| Google | `google` | `gemini-2.0-flash` |
| Ollama | `ollama` | `llama3` |
| Azure OpenAI | `azure_openai` | your deployment name |
| Mistral | `mistral` | `mistral-large-latest` |
| Cohere | `cohere` | `command-r-plus` |

The full LLM node model configuration block follows this structure:

```yaml
model:
  provider: anthropic
  name: claude-sonnet-4-6
  mode: chat
  completion_params:
    temperature: 0.7
    max_tokens: 4096
    top_p: 1
    frequency_penalty: 0
    presence_penalty: 0
```

The `completion_params` fields available depend on the provider. Not all providers support all parameters. Unsupported parameters are silently ignored by most providers, but it is good practice to only include parameters the provider documents.
