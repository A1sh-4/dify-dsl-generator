# Variables Reference

> **Scope of this doc vs. `schema/variable-syntax.md`:** This file is the authority on the **five variable *types*** (input / node-output / environment / conversation / system) — how to *declare* them in node config, supported type strings, naming rules, and the type-compatibility matrix. For the **reference syntax mechanics** — how to *write* a `{{#node_id.field#}}` reference, scope rules, nested/array access, the DSL-vs-Jinja2 distinction, and common reference mistakes — see `skills/dify/references/schema/variable-syntax.md`. The two are complementary; the duplicated system-variables table is kept in both for convenience, but `variable-syntax.md` is canonical for syntax and this doc is canonical for types and declaration.

## Overview

Dify DSL workflows use five distinct variable types to pass data between nodes, carry user input, persist state, reference secrets, and access system-provided context. Each type has its own syntax, lifecycle, and appropriate use cases. Understanding all five — and when to use each — is fundamental to building robust Dify workflows.

This document is the complete reference for all variable types: Input Variables, Node Output Variables, Environment Variables, Conversation Variables, and System Variables.

---

## 1. Input Variables (Start Node)

Input variables are defined in the workflow or chatflow's start node. They represent the data that comes into the workflow from the outside — either typed by a user in the chat interface, submitted via the Dify web form, or passed programmatically via the Dify API.

**Reference syntax:**
```
{{#start.variable_name#}}
```

The prefix is always `start`, matching the start node's fixed ID, followed by the variable's `name` field as defined in the start node's `variables` array.

**DSL definition (start node):**
```yaml
nodes:
  - id: start
    type: start
    data:
      variables:
        - label: User Query
          name: user_query
          required: true
          type: text-input
          max_length: 1000

        - label: Document
          name: uploaded_doc
          required: false
          type: single-file
          allowed_file_types:
            - .pdf
            - .txt
            - .docx
          allowed_file_upload_methods:
            - local_file

        - label: Response Language
          name: language
          required: false
          type: select
          options:
            - label: English
              value: en
            - label: French
              value: fr
            - label: Spanish
              value: es
          default: en

        - label: Max Results
          name: max_results
          required: false
          type: number
          default: 5
```

**Supported input variable types:**

| Type | Description | Use For |
|---|---|---|
| `text-input` | Single-line text, up to max_length chars | Short queries, names, IDs |
| `paragraph` | Multi-line text area | Long-form input, documents, messages |
| `select` | Dropdown with predefined options | Language, category, mode selection |
| `number` | Numeric value | Count, threshold, page number |
| `single-file` | One file upload | Document, image, audio |
| `file-list` | Multiple file uploads | Batch document processing |

**Usage in prompts:**
```
Analyze the following user query and provide a response in {{#start.language#}}:
{{#start.user_query#}}
```

---

## 2. Node Output Variables

Every node in a Dify workflow produces output variables when it executes. These outputs are accessible to any downstream node that is connected by an edge in the workflow graph. Downstream nodes reference these outputs using the producing node's ID and the specific output field name.

**Reference syntax:**
```
{{#node_id.output_field#}}
```

The `node_id` is the `id` property of the upstream node. The `output_field` is the specific field produced by that node type.

**Output variables by node type:**

| Node Type | Output Field | Type | Description |
|---|---|---|---|
| LLM | `.text` | string | Full generated text response |
| LLM (structured output) | `.output.field_name` | varies | Individual schema fields |
| LLM | `.usage.prompt_tokens` | integer | Tokens used for input |
| LLM | `.usage.completion_tokens` | integer | Tokens generated |
| Code | any field in `return` dict | varies | Whatever the code node returns |
| HTTP Request | `.body` | string | Full response body |
| HTTP Request | `.status_code` | integer | HTTP status code |
| HTTP Request | `.headers` | object | Response headers |
| Knowledge Retrieval | `.result` | string | Retrieved and formatted passages |
| Parameter Extractor | `.field_name` | varies | Each extracted parameter |
| Iteration | `.output` | array | Array of results from each iteration |
| Template Transform | `.output` | string | Rendered template string |
| Question Classifier | `.class_name` | string | Predicted class label |

**Code node example — returning multiple fields:**
```python
# Code node with id: parse_response
def main(inputs):
    data = json.loads(inputs["raw_json"])
    return {
        "customer_id": data["id"],
        "order_count": len(data["orders"]),
        "is_vip": data.get("tier") == "gold"
    }
```

Reference in downstream nodes:
```
{{#parse_response.customer_id#}}
{{#parse_response.order_count#}}
{{#parse_response.is_vip#}}
```

---

## 3. Environment Variables

Environment variables are workspace-level values configured in Dify's admin settings. They are not part of the workflow DSL itself — they are external to any individual workflow and shared across all workflows in the workspace. This makes them the correct place to store API keys, credentials, URLs, and configuration values that should not be embedded directly in workflow files.

**Reference syntax:**
```
{{#env.variable_name#}}
```

**Variable types:**

| Type | Displayed in UI | Use For |
|---|---|---|
| `string` | Visible in plain text | Non-sensitive config (company name, region, model name) |
| `secret` | Masked / hidden | API keys, passwords, tokens, private URLs |

**Where to configure:** Dify Workspace Settings → Environment Variables

**Critical rule: Never hardcode credentials in DSL files.** If your workflow needs an API key for an external service (a CRM, a payment gateway, an analytics API), store that key as a secret environment variable and reference it in your workflow. This keeps credentials out of version control and allows key rotation without modifying the workflow.

**Common uses in DSL nodes:**

In an HTTP node's authorization header:
```yaml
headers:
  Authorization: "Bearer {{#env.crm_api_key#}}"
  X-Company-ID: "{{#env.company_id#}}"
```

In a code node's inputs:
```yaml
inputs:
  api_endpoint:
    type: string
    value: "{{#env.external_api_base_url#}}"
```

In an LLM node's system prompt:
```
You are a support agent for {{#env.company_name#}}.
Always direct users to {{#env.support_portal_url#}} for account issues.
```

---

## 4. Conversation Variables (Chatflow Only)

Conversation variables persist specific named values across multiple turns within a single conversation. They are defined at the workflow level, initialized with default values, and updated during the conversation by variable-assigner nodes. When the conversation ends, they reset to their defaults.

Conversation variables are the right tool when you need to track application state that evolves over the course of a conversation — the user's detected language, their selected topic, an accumulated list of items, or any value you explicitly extract and want to reliably recall later.

**Reference syntax:**
```
{{#conversation.variable_name#}}
```

**DSL definition (workflow level):**
```yaml
conversation_variables:
  - id: 'cvar_001'
    name: language_preference
    value_type: string
    value: 'english'
    description: 'User preferred response language, updated on detection'

  - id: 'cvar_002'
    name: topics_discussed
    value_type: array
    value: []
    description: 'Topics the user has asked about during this session'

  - id: 'cvar_003'
    name: escalation_requested
    value_type: boolean
    value: false
    description: 'Whether the user has asked to speak with a human agent'

  - id: 'cvar_004'
    name: current_order_id
    value_type: string
    value: ''
    description: 'Order ID extracted from the current support session'

  - id: 'cvar_005'
    name: cart_total
    value_type: number
    value: 0
    description: 'Running total of items added to cart this session'
```

**Updating conversation variables — variable-assigner node:**
```yaml
- id: update_language
  type: variable-assigner
  data:
    variables:
      - variable: language_preference
        set_type: string
        value: "{{#lang_detector.output.detected_language#}}"
```

**Supported value types:**

| Type | Default Example | Use For |
|---|---|---|
| `string` | `''` | Text values, codes, labels |
| `number` | `0` | Counts, totals, numeric state |
| `boolean` | `false` | Flags, switches, yes/no state |
| `object` | `{}` | Structured data (user profile, session context) |
| `array` | `[]` | Lists of items accumulated over turns |
| `file` | — | File references within a session |

**Usage in LLM prompt:**
```
System: Always respond in {{#conversation.language_preference#}}.
{% if conversation.escalation_requested %}
The user has requested human support. Acknowledge this and provide the support queue URL.
{% endif %}
```

---

## 5. System Variables

System variables are built-in variables automatically provided by the Dify platform. No configuration is required — they are always available. They provide metadata about the current execution context: who the user is, what workflow is running, when it is running, and conversation-specific identifiers.

**Reference syntax:**
```
{{#sys.variable_name#}}
```

**Complete system variables table:**

| Variable | Availability | Type | Description |
|---|---|---|---|
| `sys.query` | Chatflow only | string | The current user's message text |
| `sys.files` | Chatflow only | array | Files uploaded with the current message |
| `sys.user_id` | Both | string | Unique identifier of the current end user |
| `sys.app_id` | Both | string | Unique identifier of the Dify app |
| `sys.workflow_id` | Both | string | Unique identifier of this workflow definition |
| `sys.workflow_run_id` | Both | string | Unique identifier of this specific execution run |
| `sys.timestamp` | Both | integer | Unix timestamp of the current request (seconds) |
| `sys.conversation_id` | Chatflow only | string | Unique identifier of the current conversation session |
| `sys.dialogue_count` | Chatflow only | integer | Number of turns completed in this conversation so far |

**Common uses:**

Personalizing responses using user ID for a logged-in user lookup:
```
Customer ID: {{#sys.user_id#}}
```

Logging the run ID for traceability:
```yaml
# HTTP node — sending run metadata to a logging endpoint
body:
  run_id: "{{#sys.workflow_run_id#}}"
  app_id: "{{#sys.app_id#}}"
  timestamp: "{{#sys.timestamp#}}"
  user_id: "{{#sys.user_id#}}"
```

Using `sys.dialogue_count` to offer escalation after enough turns:
```yaml
# Condition: offer human agent after 5 turns
conditions:
  - variable: "{{#sys.dialogue_count#}}"
    operator: greater_than
    value: 5
```

---

## Variable Naming Rules

All variable names across all types (input variables, conversation variables, environment variables) must follow these rules:

- Use lowercase letters (`a–z`), digits (`0–9`), and underscores (`_`) only
- No spaces — use underscores as separators
- No hyphens (`-`), dots (`.`), or any other special characters
- Cannot begin with a digit (e.g., `3rd_item` is invalid; use `item_3` instead)
- Must be unique within their scope:
  - Input variables: unique within the start node's `variables` array
  - Conversation variables: unique within the `conversation_variables` array
  - Environment variables: unique within the workspace

**Valid names:** `user_query`, `order_id`, `max_results`, `language_preference`, `is_vip`  
**Invalid names:** `user-query`, `order.id`, `3rd_result`, `Max Results`, `API_KEY` (uppercase is technically accepted but not recommended — use lowercase for consistency)

---

## Variable Type Compatibility

Not all node input fields accept all variable types. This table shows which variable types are compatible with the key input field categories across node types.

| Input Field Type | Accepts string | Accepts number | Accepts boolean | Accepts array | Accepts object | Accepts file |
|---|---|---|---|---|---|---|
| LLM prompt text | Yes | Yes (coerced) | Yes (coerced) | No | No | No |
| Code node input | Yes | Yes | Yes | Yes | Yes | Yes |
| HTTP node header/param | Yes | Yes (coerced) | No | No | No | No |
| HTTP node body (JSON) | Yes | Yes | Yes | Yes | Yes | No |
| Condition node operand | Yes | Yes | Yes | No | No | No |
| Variable assigner value | Yes | Yes | Yes | Yes | Yes | Yes |
| Template transform input | Yes | Yes | Yes | Yes | Yes | No |
| Iteration input | No | No | No | Yes (required) | No | No |

**Notes on type coercion:**
- When a number or boolean is injected into a text prompt via `{{#...#}}`, it is automatically converted to its string representation
- Arrays and objects cannot be directly injected into LLM prompt text — pass them to a code node or template-transform first to format them as a string
- The iteration node requires its input to be an array type; other types will cause a runtime error

**Passing an array to a prompt — use a code node intermediary:**
```python
# Code node: format_tags_for_prompt
def main(inputs):
    tags = inputs["tags"]  # array from upstream node
    return {
        "tags_string": ", ".join(tags)
    }
```

Then reference `{{#format_tags_for_prompt.tags_string#}}` in the LLM prompt.
