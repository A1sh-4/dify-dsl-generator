# LLM Node

## Overview

The LLM node sends a prompt to a language model and returns the response. It is the core processing node of most Dify workflows. Nearly every workflow that needs to reason, generate text, or make decisions will contain at least one LLM node. The node supports system prompts, multi-turn conversation history, vision inputs, RAG context injection, and structured output schemas.

## When to Use

Use the LLM node for any task where an AI language model is the right tool:

- Generating text responses to user questions
- Answering questions based on retrieved knowledge (RAG)
- Summarizing long documents or conversation threads
- Translating between languages
- Classifying content into categories
- Extracting structured data from unstructured text
- Coding assistance and code generation
- Rewriting, improving, or formatting text
- Multi-step reasoning and planning tasks

If the task is deterministic computation (math, string manipulation, JSON parsing), use a Code node instead. If the task involves routing based on topic, consider a Question Classifier node.

## Node Type Reference

From the Dify node type reference:

- **type**: `llm`
- **Execution Type**: EXECUTABLE
- **Required fields**: `type`, `title`, `model`, `prompt_template`
- **Variable references**: `{{#node_id.field_name#}}`

## Model Configuration

The `model` sub-object controls which model is called and how it behaves.

```yaml
model:
  completion_params:
    frequency_penalty: 0
    max_tokens: 2000
    presence_penalty: 0
    stop: []
    temperature: 0.7
    top_p: 1
  mode: chat
  name: claude-3-5-sonnet-20241022
  provider: anthropic
```

**Field descriptions:**

- `mode`: Always `chat` for conversational models. Use `completion` only for legacy base models.
- `provider`: The model provider identifier. Common values: `anthropic`, `openai`, `google`, `azure_openai`, `cohere`.
- `name`: The exact model identifier string as defined by the provider. Examples:
  - Anthropic: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, `claude-3-haiku-20240307`
  - OpenAI: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`
  - Google: `gemini-1.5-pro`, `gemini-1.5-flash`
- `temperature`: Controls randomness. Range 0.0–1.0. Lower = more deterministic; higher = more creative.
- `max_tokens`: Maximum tokens in the response. Set based on expected output length.
- `frequency_penalty`: Reduces repetition of the same words (0 = off).
- `presence_penalty`: Encourages introducing new topics (0 = off).
- `stop`: Array of strings that stop generation when encountered. Usually empty `[]`.
- `top_p`: Nucleus sampling. Keep at `1` unless you have a specific reason to change it.

## Prompt Configuration

Prompts are defined as an ordered array of message objects. This mirrors the chat completions format.

```yaml
prompt_template:
  - id: 'system-prompt-id'
    role: system
    text: "You are a helpful assistant. Answer the user's question clearly.\n\nContext: {{#knowledge_node.result#}}"
  - id: 'user-prompt-id'
    role: user
    text: "{{#start.user_question#}}"
```

**Field descriptions:**

- `id`: A unique string identifier for this message. Can be any unique string.
- `role`: The message role. Valid values are `system`, `user`, or `assistant`.
  - `system`: Sets the model's behavior and persona. Usually the first entry.
  - `user`: Represents the human turn. Contains the actual request.
  - `assistant`: Used for few-shot examples — a prefilled assistant response that primes the model.
- `text`: The prompt content. Supports `{{#node_id.field#}}` variable injection anywhere in the string. Use `\n` for newlines within YAML strings.

**Variable injection syntax:** `{{#node_id.field_name#}}`

- `node_id`: The `id` of the upstream node (the numeric string like `1732007415808`, or a named node id).
- `field_name`: The output field of that node (e.g., `text`, `result`, `user_input`).

**Multi-turn conversation:** Add multiple `user` and `assistant` entries to build few-shot examples or inject conversation history.

## Vision Configuration (for multimodal models)

Enable vision when the workflow passes image inputs to a multimodal model.

```yaml
vision:
  enabled: true
  configs:
    detail: high   # or low
    variable_selector:
      - start
      - uploaded_image
```

- `enabled`: Set to `true` to activate image input processing.
- `detail`: Image analysis depth. `high` uses more tokens for detailed analysis; `low` is faster and cheaper.
- `variable_selector`: Array path `[node_id, field_name]` pointing to the image variable.

Only enable vision when the upstream node actually provides an image. Most models require a specific variant (e.g., `claude-3-5-sonnet-20241022` supports vision natively).

## Context Configuration (for RAG workflows)

When using a Knowledge Retrieval node upstream, pass its results to the LLM via the context field.

```yaml
context:
  enabled: true
  variable_selector:
    - knowledge_node
    - result
```

- `enabled`: Set to `true` to inject knowledge retrieval results as context.
- `variable_selector`: Array path pointing to the retrieval result variable.

This is the standard pattern for Retrieval-Augmented Generation (RAG). The retrieved documents are injected into the prompt automatically in a structured format.

## Structured Output

When you need the LLM to return a specific JSON structure instead of free text, enable structured output.

```yaml
structured_output_enabled: true
structured_output_schema:
  type: object
  properties:
    summary:
      type: string
    sentiment:
      type: string
      enum: [positive, negative, neutral]
    score:
      type: number
  required:
    - summary
    - sentiment
```

- `structured_output_enabled`: Set to `true` to enforce JSON output matching the schema.
- `structured_output_schema`: A JSON Schema object defining the expected shape.
- The LLM will return a JSON object conforming to this schema. Access fields via `{{#llm_node_id.text#}}` and parse with a downstream Code node, or use Parameter Extractor for simpler cases.

## Memory Configuration (chatflow only)

In chatflow mode, enable memory to automatically inject conversation history into each request.

```yaml
memory:
  enabled: true
  role_prefix:
    assistant: ''
    user: ''
  window:
    enabled: true
    size: 10
```

- `enabled`: Set to `true` to activate memory.
- `role_prefix`: Optional string prefixes added before each role's messages in the history. Usually left empty.
- `window.enabled`: Whether to limit the history window. Recommended `true` to avoid token overflows.
- `window.size`: Number of prior conversation turns to include. `10` means the last 10 user+assistant pairs.

Memory is only relevant in **chatflow** app type. In standard workflow apps, memory is not applicable.

## Output Variables

After the LLM node executes, the following variables are available to downstream nodes:

| Variable | Type | Description |
|---|---|---|
| `{{#llm_node_id.text#}}` | string | The full generated text response |
| `{{#llm_node_id.usage#}}` | object | Token usage: `prompt_tokens`, `completion_tokens`, `total_tokens` |
| `{{#llm_node_id.finish_reason#}}` | string | Why generation stopped: `stop`, `length`, or `tool_calls` |

Replace `llm_node_id` with the actual `id` of your LLM node (the numeric string set in the node's `id` field).

## Complete YAML Example

A full LLM node with model, system + user prompts, and RAG context enabled:

```yaml
- data:
    context:
      enabled: true
      variable_selector:
        - knowledge_retrieval_node
        - result
    desc: ''
    model:
      completion_params:
        frequency_penalty: 0
        max_tokens: 2000
        presence_penalty: 0
        stop: []
        temperature: 0.7
        top_p: 1
      mode: chat
      name: claude-3-5-sonnet-20241022
      provider: anthropic
    prompt_template:
      - id: system-prompt-001
        role: system
        text: "You are a knowledgeable assistant. Use the provided context to answer the user's question accurately and concisely. If the context does not contain relevant information, say so.\n\nContext:\n{{#knowledge_retrieval_node.result#}}"
      - id: user-prompt-001
        role: user
        text: "{{#start.user_question#}}"
    selected: false
    title: Generate Answer
    type: llm
    vision:
      enabled: false
  height: 98
  id: '1732007415808'
  position:
    x: 680
    y: 282
  positionAbsolute:
    x: 680
    y: 282
  selected: false
  sourcePosition: right
  targetPosition: left
  type: custom
  width: 244
```

## Common Mistakes

- **Wrong variable path**: Referencing a node_id that does not exist in the workflow, or misspelling the field name. Double-check that the `id` of the upstream node matches what you put in `{{#node_id.field#}}`.
- **Wrong model name string**: Using an approximate name like `claude-3.5-sonnet` instead of the exact identifier `claude-3-5-sonnet-20241022`. Check the provider's model list for the exact string.
- **Forgetting to enable vision**: Passing an image variable in the prompt but leaving `vision.enabled: false`. The image will not be processed.
- **Missing output format instructions**: When you expect structured output but have not enabled `structured_output_enabled`, add explicit formatting instructions in the system prompt (e.g., "Respond only with valid JSON matching this schema: ...").
- **Token overflow**: Setting `max_tokens` too low causes the response to be cut off (`finish_reason: length`). Set it generously for long-form outputs.
- **Memory in non-chatflow**: Enabling `memory` in a standard workflow app type has no effect and may cause errors. Only enable in chatflow.
- **Missing context enable**: Adding a Knowledge Retrieval node upstream but forgetting to set `context.enabled: true` in the LLM node means retrieved documents are silently ignored.
