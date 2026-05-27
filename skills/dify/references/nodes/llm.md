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
  name: Claude-4-Sonnet
  provider: langgenius/openai_api_compatible/openai_api_compatible
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
  - id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    role: system
    text: "You are a helpful assistant. Answer the user's question clearly.\n\nContext: {{#knowledge_node.result#}}"
  - id: 'b2c3d4e5-f6a7-8901-bcde-f12345678901'
    role: user
    text: "{{#start.user_question#}}"
```

**Field descriptions:**

- `id`: A unique UUIDv4 string per prompt entry. Required — Dify uses it to identify each prompt block in the editor.
- `role`: The message role. Valid values are `system`, `user`, or `assistant`.
  - `system`: Sets the model's behavior and persona. Usually the first entry.
  - `user`: Represents the human turn. Contains the actual request.
  - `assistant`: Used for few-shot examples — a prefilled assistant response that primes the model.
- `text`: The prompt content. Supports `{{#node_id.field#}}` variable injection anywhere in the string. Use `\n` for newlines within YAML strings.

Note: Real Dify exports do NOT include an `edition_type` field on prompt entries — omit it.

**Variable injection syntax:** `{{#node_id.field_name#}}`

- `node_id`: The `id` of the upstream node (the numeric string like `1732007415808`, or a named node id).
- `field_name`: The output field of that node (e.g., `text`, `result`, `user_input`).

**Multi-turn conversation:** Add multiple `user` and `assistant` entries to build few-shot examples or inject conversation history.

## Vision Configuration (for multimodal models)

Enable vision when the workflow passes image inputs to a multimodal model. Use cases include: OCR (text extraction from images), visual question answering, extracting structured data from screenshots or forms, reading charts and tables, analyzing diagrams, and parameter extraction from photos.

**Source: chatflow chat attachment (most common)**

In an advanced-chat app, images attached by the user to their message are available via `sys.files`:

```yaml
vision:
  enabled: true
  configs:
    detail: high
    variable_selector:
      - sys
      - files
```

**Source: start node file variable (workflow or form-based chatflow)**

If the image comes from a `file`-type variable defined in the start node:

```yaml
vision:
  enabled: true
  configs:
    detail: high
    variable_selector:
      - '[start_node_id]'   # the actual 13-digit ID of the start node
      - uploaded_image       # the variable name defined in the start node
```

- `detail: high` — reads at full resolution; required for OCR, small text, tables, and detailed diagrams
- `detail: low` — faster and cheaper; sufficient for simple scene description or color/layout questions where fine detail does not matter
- Only set `enabled: true` when the upstream path actually provides an image — leaving it true with no image input causes an empty vision context

**Ground-truth config reference:** `skills/dify/assets/chatflows/ocr-chatflow.yml` — shows a complete working LLM vision node with `sys.files`, `detail: high`, and the exact field ordering as exported from a real Dify instance.

## Context Configuration (for RAG workflows)

When using a Knowledge Retrieval node upstream, pass its results to the LLM via the context field.

```yaml
context:
  enabled: true
  variable_selector:
    - '[knowledge_retrieval_node_id]'   # actual 13-digit ID of the knowledge-retrieval node
    - result
```

- `enabled`: Set to `true` to inject retrieved document chunks into the prompt automatically.
- `variable_selector`: Points to the `result` output of a knowledge-retrieval node. The result is an array of objects — each object has `content`, `score`, `title`, and `url` fields.

When context is enabled, use `{{#context#}}` in the user prompt template to explicitly place the retrieved documents in the user turn:

```yaml
prompt_template:
  - edition_type: basic
    id: '[uuid]'
    role: system
    text: 'Answer only from the provided context. Cite your sources.'
  - edition_type: basic
    id: '[uuid]'
    role: user
    text: '{{#context#}}'
```

`{{#context#}}` expands to the retrieved document chunks at runtime. The user's actual question is carried separately via `memory.query_prompt_template` (set to `{{#sys.query#}}`). The model therefore sees both the retrieved evidence and the user's question.

**Ground-truth config reference:** `skills/dify/assets/chatflows/rag-chatflow.yml` — shows a complete working RAG LLM node with context enabled, `{{#context#}}` user prompt, and the correct memory template as exported from a real Dify instance.

## Structured Output

When you need the LLM to return a specific JSON structure instead of free text, enable structured output. The two fields are siblings at the top level of the node's `data` block — `structured_output_enabled` is the toggle and `structured_output` holds the JSON Schema.

**Disabled form — omit both fields entirely:**

When the LLM node does not use structured output, do not include `structured_output` or `structured_output_enabled` at all. Their absence is how Dify knows the feature is off. Writing `structured_output: {}` or `structured_output_enabled: false` is incorrect and may cause unexpected behavior.

**Enabled form:**

```yaml
structured_output:
  schema:
    additionalProperties: false
    type: object
    properties:
      summary:
        type: string
      sentiment:
        type: string
        enum:
          - positive
          - negative
          - neutral
      score:
        type: number
      is_valid:
        type: boolean
    required:
      - summary
      - sentiment
      - score
      - is_valid
structured_output_enabled: true
```

**Supported schema types:**

| Type | Example value | Notes |
|---|---|---|
| `string` | `"hello"` | Plain text field; add `enum` to restrict to fixed choices |
| `number` | `42`, `3.14` | Integer or float |
| `boolean` | `true`, `false` | Yes/no flag |
| `object` | `{"key": "value"}` | Nested object; define its own `properties`/`required` recursively |
| `array` of strings | `["a", "b"]` | Set `items: {type: string}` |
| `array` of numbers | `[1, 2, 3]` | Set `items: {type: number}` |
| `array` of objects | `[{...}, {...}]` | Set `items: {type: object, properties: {...}, required: [...], additionalProperties: false}` |

**Full nested schema example (complex real-world shape):**

```yaml
structured_output:
  schema:
    additionalProperties: false
    type: object
    properties:
      achievement_status:
        type: object
        properties:
          annual_target_rate:
            type: string
            description: "Achievement rate explained from Count, Amount, and Pipeline perspectives."
          process_kpis:
            type: array
            items:
              type: object
              properties:
                metric_name:
                  type: string
                current_value:
                  type: string
                target_value:
                  type: string
                calculation_details:
                  type: string
                is_achieved:
                  type: string
              required:
                - metric_name
                - current_value
                - target_value
                - calculation_details
                - is_achieved
              additionalProperties: false
        required:
          - annual_target_rate
          - process_kpis
        additionalProperties: false
      focus_areas:
        type: array
        items:
          type: object
          properties:
            company_name:
              type: string
            next_action:
              type: string
            reason_for_focus:
              type: string
          required:
            - company_name
            - next_action
            - reason_for_focus
          additionalProperties: false
    required:
      - achievement_status
      - focus_areas
structured_output_enabled: true
```

**Conventions:**
- Always set `additionalProperties: false` on every object (including nested ones) to prevent the LLM from hallucinating extra fields.
- Always list every field in `required` unless you explicitly want it to be optional.
- Use `description` on fields when the field name alone does not make the expected content obvious — the LLM reads these to know what to put there.
- All values should be typed as `string` unless you specifically need numeric operations downstream. Strings are more robust to formatting variation.

**Accessing structured output fields downstream:**

When `structured_output_enabled: true`, Dify parses the LLM's JSON response and makes the resulting object available as the `structured_output` field of the node. Map the whole `structured_output` object to a single template variable — the Jinja2 template then navigates the nested structure with dot notation.

In a **template-transform** node, map `structured_output` → one variable (conventionally named `data`):

```yaml
variables:
  - value_selector:
      - 'llm_node_id'
      - structured_output       # NOT "output" — this is the field the LLM node exposes
    value_type: object           # required
    variable: kpi_report         # user-chosen descriptive name; becomes {{ kpi_report.field }} in Jinja2
```

Then in the Jinja2 template, access the entire schema hierarchy through `data`:

```jinja2
{# Top-level field #}
{{ data.summary }}

{# Nested object #}
{{ data.achievement_status.annual_target_rate }}

{# Array of objects — iterate with for loop #}
{%- for kpi in data.achievement_status.process_kpis -%}
  {{ kpi.metric_name }}: {{ kpi.current_value }}
{%- endfor -%}

{# Array of strings — iterate directly #}
{%- for trend in data.analysis_results.deal_trends -%}
  - {{ trend }}
{%- endfor -%}
```

Map `structured_output` as a whole and access any fields you need via `data.field` in the template. You do not need to reference every field — use only what the current node requires.

**In a Code node downstream**, receive the same full dict and use only the keys relevant to that node's task:
```python
def main(data: dict) -> dict:
    kpis = data.get('achievement_status', {}).get('process_kpis', [])
    return {'kpi_count': len(kpis)}
```

The raw JSON string is also available as `{{#node_id.text#}}` if needed.

**When to use structured output vs parameter-extractor:**

| Situation | Use |
|---|---|
| Simple extraction of 1–5 flat fields | Parameter Extractor node |
| Complex nested objects or arrays of objects | Structured output on LLM node |
| The extracted data must be rendered by template-transform | Structured output (fields accessible individually) |
| Model does not support function calling | Parameter Extractor with prompt inference mode |
| You need reliable typing (numbers, booleans) | Structured output |

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

A minimal LLM node with RAG context enabled — matches real Dify export structure:

```yaml
- data:
    context:
      enabled: true
      variable_selector:
      - '1732007415800'
      - result
    memory:
      query_prompt_template: '{{#sys.query#}}'
      role_prefix:
        assistant: ''
        user: ''
      window:
        enabled: false
        size: 50
    model:
      completion_params:
        temperature: 0.3
      mode: chat
      name: Claude-4-Sonnet
      provider: langgenius/openai_api_compatible/openai_api_compatible
    prompt_template:
    - id: a1b2c3d4-0000-0000-0000-000000000001
      role: system
      text: 'You are a knowledgeable assistant. Use the provided context to answer
        the user''s question accurately and concisely. If the context does not contain
        relevant information, say so clearly.'
    - id: a1b2c3d4-0000-0000-0000-000000000002
      role: user
      text: '{{#context#}}'
    selected: false
    title: Generate Answer
    type: llm
    vision:
      enabled: false
  height: 90
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
  width: 243
```

**Required fields checklist** — every LLM node in a valid DSL must have all of these:

- `context` — always present, even when disabled (`enabled: false, variable_selector: []`)
- `memory` — include for chatflows where conversation history matters; omit for one-shot flows
- `model` — with `completion_params`, `mode`, `name`, `provider`
- `prompt_template` — each entry must have `id` (UUIDv4), `role`, `text`; no `edition_type` field
- `selected: false`
- `title`
- `type: llm`
- `vision` — always present, `enabled: false` unless image input is needed

**Optional fields** (only include when the feature is actually used):

- `structured_output` (with `schema:` nested inside) + `structured_output_enabled: true` — only when the node must return named JSON fields; omit BOTH fields entirely when not used (do not write `structured_output: {}`)
- `variables` — only needed for non-prompt variable injection patterns

## Common Mistakes

- **Wrong variable path**: Referencing a node_id that does not exist in the workflow, or misspelling the field name. Double-check that the `id` of the upstream node matches what you put in `{{#node_id.field#}}`.
- **Wrong model name string**: Using an approximate name like `claude-3.5-sonnet` instead of the exact identifier `claude-3-5-sonnet-20241022`. Check the provider's model list for the exact string.
- **Forgetting to enable vision**: Passing an image variable in the prompt but leaving `vision.enabled: false`. The image will not be processed.
- **Missing output format instructions**: When you expect structured output but have not enabled `structured_output_enabled`, add explicit formatting instructions in the system prompt (e.g., "Respond only with valid JSON matching this schema: ...").
- **Token overflow**: Setting `max_tokens` too low causes the response to be cut off (`finish_reason: length`). Set it generously for long-form outputs.
- **Memory in non-chatflow**: Enabling `memory` in a standard workflow app type has no effect and may cause errors. Only enable in chatflow.
- **Missing context enable**: Adding a Knowledge Retrieval node upstream but forgetting to set `context.enabled: true` in the LLM node means retrieved documents are silently ignored.
