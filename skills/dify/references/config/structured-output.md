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

Structured output is configured directly on the LLM node in the DSL. Set `structured_output_enabled: true` and provide the schema under `structured_output_schema`. The schema follows the JSON Schema specification (draft-07 compatible).

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
      structured_output_enabled: true
      structured_output_schema:
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

When `structured_output_enabled: true`, the LLM node exposes its fields under `.output` rather than under `.text`. You must use the `.output.field_name` path to access individual fields.

**Reference syntax:**
```
{{#node_id.output.field_name#}}
```

**Examples using the article analysis schema above:**

```
Title:     {{#analyze_article.output.title#}}
Sentiment: {{#analyze_article.output.sentiment#}}
Score:     {{#analyze_article.output.score#}}
Tags:      {{#analyze_article.output.tags#}}
Language:  {{#analyze_article.output.metadata.language#}}
```

**Accessing nested object fields:** Use dot notation through the path.
```
{{#analyze_article.output.metadata.language#}}
{{#analyze_article.output.metadata.word_count#}}
```

**Important:** Do not use `{{#analyze_article.text#}}` on a structured output node — the `.text` field will contain the raw JSON string, not the parsed fields. Always access structured fields through `.output.field_name`.

**Condition node usage example:**

In an IF/ELSE node that branches on sentiment:
```yaml
conditions:
  - variable: "{{#analyze_article.output.sentiment#}}"
    operator: equals
    value: "negative"
```

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
| Output path | `.output.field_name` | `.field_name` directly |

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
