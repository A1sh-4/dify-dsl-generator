# Structured Output Configuration

## Overview

Structured output is a capability that forces an LLM to return a response that conforms to a specific JSON schema you define. Instead of parsing free-form text with regex or a second LLM pass, structured output gives you guaranteed, type-safe fields you can access directly in downstream nodes. When properly configured, the model's response will be a valid JSON object matching your schema — every time.

This document covers when to use structured output, how to configure the schema in Dify DSL, how to access the output fields in downstream nodes, and which models support it natively.

---

## When to Use Structured Output

**Use structured output when:**

- You need to extract specific, named fields from text or from a model's analysis
- Downstream nodes require typed data (numbers, booleans, enums) rather than raw string text
- You want to guarantee JSON format without adding a code node to parse free-form output
- Your workflow branches on the value of a specific field (e.g., `sentiment == "negative"` triggers an escalation path)
- You are building an extraction pipeline where consistent field presence matters for reliability

**Do not use structured output when:**

- The model needs to produce prose, narrative, or freeform explanation as its primary output
- You only need a single string value — use a regular LLM node and access `.text`
- The model you are using does not support it (see Model Support Matrix below) — use parameter-extractor instead

---

## JSON Schema Configuration

Structured output is configured directly on the LLM node in the DSL. Set `structured_output_enabled: true` and provide the schema nested under `structured_output.schema`. The schema follows the JSON Schema specification (draft-07 compatible).

**Full example — article analysis:**

```yaml
nodes:
  - id: analyze_article
    type: llm
    data:
      model:
        provider: openai
        name: gpt-4o
        mode: chat
      prompts:
        - role: system
          text: |
            Analyze the provided article. Return a structured assessment
            covering the title, sentiment, quality score, relevant tags,
            and document metadata.
      structured_output:
        schema:
          additionalProperties: false
          type: object
          properties:
            title:
              type: string
              description: "Article title extracted from the content, maximum 100 characters"
            sentiment:
              type: string
              enum:
                - positive
                - negative
                - neutral
              description: "Overall sentiment of the article"
            score:
              type: number
              minimum: 0
              maximum: 10
              description: "Quality score from 0 (lowest) to 10 (highest)"
            tags:
              type: array
              items:
                type: string
              description: "List of relevant topic tags, maximum 5"
            metadata:
              additionalProperties: false
              type: object
              properties:
                language:
                  type: string
                  description: "ISO 639-1 language code (e.g., en, fr, de)"
                word_count:
                  type: number
                  description: "Approximate word count of the article"
                has_citations:
                  type: boolean
                  description: "Whether the article includes citations or references"
              required:
                - language
                - word_count
          required:
            - title
            - sentiment
            - score
      structured_output_enabled: true
```

---

## Schema Property Configuration

### Primitive Types

```yaml
# String with no constraints
name:
  type: string
  description: "Person's full name"

# String with enum constraint — model must pick one of these values
status:
  type: string
  enum:
    - active
    - inactive
    - pending
    - archived

# Number with range constraint
confidence:
  type: number
  minimum: 0.0
  maximum: 1.0

# Integer only
priority:
  type: integer
  minimum: 1
  maximum: 5

# Boolean
is_spam:
  type: boolean
```

### Arrays

```yaml
# Array of strings
keywords:
  type: array
  items:
    type: string

# Array of objects
line_items:
  type: array
  items:
    type: object
    properties:
      product_name:
        type: string
      quantity:
        type: integer
      unit_price:
        type: number
    required:
      - product_name
      - quantity
```

### Nullable Fields

When a field may not be present in the input, mark it as nullable so the model can return `null` rather than fabricating a value:

```yaml
phone_number:
  type:
    - string
    - "null"
  description: "Phone number if found in the text, otherwise null"
```

### required Array

Always specify the `required` array at each object level. Fields listed in `required` will always be present in the output. Fields not listed may be omitted by the model if it cannot determine their value.

```yaml
type: object
properties:
  title:
    type: string
  subtitle:
    type: string    # optional
required:
  - title           # always present; subtitle may be absent
```

---

## Accessing Structured Output Fields in Downstream Nodes

When `structured_output_enabled: true`, the LLM node exposes the parsed JSON object as the `structured_output` field — not `output`. The field is a typed `object` value that downstream nodes receive by mapping it to a named variable.

**In a template-transform node**, map the whole object to one descriptive variable, then access fields in Jinja2:

```yaml
variables:
  - value_selector:
      - 'analyze_article'       # the LLM node's id
      - structured_output       # always "structured_output" — not "output"
    value_type: object          # required
    variable: article_result    # user-chosen descriptive name
```

Then in the Jinja2 template:

```jinja2
Title:     {{ article_result.title }}
Sentiment: {{ article_result.sentiment }}
Score:     {{ article_result.score }}
Language:  {{ article_result.metadata.language }}
```

**In a code node**, same wiring — `structured_output` as the field, `object` as `value_type`, and a parameter name that matches the Python function signature:

```yaml
variables:
  - value_selector:
      - 'analyze_article'
      - structured_output
    value_type: object
    variable: article_result    # must match the Python function parameter name
```

```python
def main(article_result: dict) -> dict:
    return {"sentiment": article_result.get("sentiment", "unknown")}
```

**Variable naming rule:** The `variable:` name is yours to define — it is not fixed by Dify. Use a descriptive name that says what the data is (`article_result`, `kpi_report`, `pipeline_summary`) rather than a generic name like `data`. For code nodes, this name must match the Python function parameter exactly.

**Important:** Do not use `.text` to access structured fields — `.text` gives the raw JSON string. Use the `structured_output` field selector and navigate fields through your named variable in Jinja2 or Python.

**If-else branching on a structured field:** To branch on a specific field value, route it through a template-transform or code node that outputs the scalar field you need, then branch on that scalar in an IF/ELSE node downstream.

---

## Supported JSON Schema Types

| Type | Description | Example Value |
|---|---|---|
| `string` | Unicode text | `"hello world"` |
| `number` | Floating point number | `3.14` |
| `integer` | Whole number | `42` |
| `boolean` | True or false | `true` |
| `array` | Ordered list of items | `["a", "b", "c"]` |
| `object` | Key-value pairs (nested) | `{"key": "value"}` |
| `null` | Explicit null / missing value | `null` |

Use `type: ["string", "null"]` syntax to allow a field to be either a value or null.

---

## Model Support Matrix

Not all models support structured output natively. For unsupported models, use the parameter-extractor node or add a code node to parse the LLM's text output.

| Model | Native Structured Output | Implementation | Notes |
|---|---|---|---|
| gpt-4o | Yes | JSON mode + response_format | Best reliability; recommended default |
| gpt-4o-mini | Yes | JSON mode + response_format | Cost-efficient; good reliability |
| gpt-4-turbo | Partial | JSON mode only | No schema enforcement; less reliable |
| gpt-3.5-turbo | No | None | Use parameter-extractor instead |
| o1-preview, o1-mini | No | Not supported | Reasoning models don't support this |
| claude-3-5-sonnet-20241022 | Yes | Via tool calling | Reliable; schema enforced |
| claude-3-5-haiku-20241022 | Yes | Via tool calling | Good reliability |
| claude-3-opus | Yes | Via tool calling | Works well |
| claude-3-haiku | Partial | Via tool calling | Less reliable on complex schemas |
| gemini-1.5-pro | Yes | response_schema | Good reliability |
| gemini-1.5-flash | Yes | response_schema | Good reliability |
| gemini-2.0-flash | Yes | response_schema | Strong performance |
| Ollama models | Varies | Depends on model | llama3.2 and mistral have basic support |

---

## Structured Output vs Parameter-Extractor

These two Dify features solve related but distinct problems. Understanding the distinction prevents misuse of each.

| Dimension | Structured Output (LLM node) | Parameter-Extractor Node |
|---|---|---|
| Primary input | Any text the LLM generates or analyzes | User's natural language message |
| When applied | At the LLM generation step | Post-LLM, on existing text |
| Schema control | Full JSON Schema (types, enums, nested) | Simpler parameter list |
| Best for | Extracting fields from documents, analysis tasks | Pulling intent/parameters from user queries |
| Requires | Model with native structured output support | Any model |
| Output path | `structured_output` field → named variable → Jinja2/Python | `.field_name` directly |

**Decision rule:**
- If you are analyzing a document or generating a structured response: use **structured output on an LLM node**
- If you are extracting parameters from what the user typed in their message: use a **parameter-extractor node**

---

## Practical Tips

**Write descriptions for every field.** The `description` property in your schema is sent to the model as an instruction about what to extract. A descriptive field description is as important as the field name itself.

**Use enums aggressively for categorical fields.** Instead of asking the model to write a category, constrain it with an enum. This eliminates casing issues, spelling variations, and hallucinated categories.

**Keep schemas flat when possible.** Deeply nested schemas (more than 2 levels) increase the probability of schema violations on less capable models. Flatten where practical.

**Test with edge cases.** Run your workflow with inputs that are missing expected data. Verify that nullable fields return `null` rather than fabricated values. Verify that required fields are always present.

**Use the `required` array at every object level.** Omitting required fields in a schema will result in the model treating all fields as optional, leading to missing data in outputs.
