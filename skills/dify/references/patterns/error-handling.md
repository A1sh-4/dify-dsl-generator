# Error Handling Pattern

## Overview

Dify provides four distinct error strategies for nodes that can fail at runtime: `abort`, `fail-branch`, `default-value`, and `retry`. Every HTTP node, LLM node, tool node, and knowledge-retrieval node should have an explicit error strategy. The default — if no strategy is set — is `abort`, which stops the entire workflow on any error and surfaces a raw error message to the user.

Production-grade DSL files never rely on the default. This document covers when to use each strategy and provides complete YAML patterns for the most common configurations.

---

## The 4 Error Strategies

### 1. `abort` (Default)

The workflow stops immediately when the node fails. The error is returned to the calling interface — the user sees an error message or the API caller receives an error response.

**Configured by:** not specifying an error strategy (implicit) or setting `error_strategy: abort`

**Use when:**
- The error is unrecoverable and there is no reasonable fallback
- The downstream pipeline cannot function without this node's output
- You want strict fail-fast behavior for debugging

**Avoid when:**
- The node calls an external API that has transient failures
- A fallback response is preferable to an error screen

---

### 2. `fail-branch`

When the node fails, execution diverges to an alternative path defined by an edge with `sourceHandle: error-handle`. The main path (the success path via `sourceHandle: source`) does not execute. The two paths reconverge at a `variable-aggregator` node.

**Error variables exposed in the fail branch:**

Both variables are available under the failing node's ID:
- `{{#node_id.error_message#}}` — a human-readable description of the error (e.g., "Connection timed out after 30 seconds")
- `{{#node_id.error_type#}}` — a machine-readable type string, e.g.:
  - `"REQUEST_TIMEOUT"`
  - `"RATE_LIMIT"`
  - `"CONNECTION_ERROR"`
  - `"INVALID_RESPONSE"`
  - `"AUTHENTICATION_ERROR"`

**Edge for fail-branch (critical):**

```yaml
- id: "HTTP_NODE_ID-error-handle-ERROR_HANDLER_NODE_ID-target"
  source: "HTTP_NODE_ID"
  sourceHandle: error-handle
  target: "ERROR_HANDLER_NODE_ID"
  targetHandle: target
  type: custom
  zIndex: 0
```

Note: `sourceHandle` is literally `error-handle` — this is the handle name, not a description.

**Use when:**
- You want graceful degradation instead of an error screen
- You want to log errors, notify via webhook, or generate a polite fallback message
- Downstream nodes need a result regardless of whether this node succeeded

---

### 3. `default-value`

The node pretends to succeed, returning a preset value as its output. Execution continues on the normal path as if the node completed successfully.

**Configured by:**

```yaml
error_strategy: default-value
default_value:
  - key: text         # for LLM nodes — the output field name
    value: "I'm sorry, I couldn't generate a response. Please try again."
  - key: result       # for knowledge-retrieval nodes
    value: ""
```

**Use when:**
- The node's output is optional or has a known safe default
- You want the pipeline to always complete, even if one step degrades gracefully
- Example: a sentiment classifier fails → default to "neutral"
- Example: knowledge retrieval fails → default to empty string (LLM will say it has no context)

**Avoid when:**
- The node's output is load-bearing and a wrong default would cause downstream nodes to produce incorrect results

---

### 4. `retry`

The node retries execution up to `max_retries` times before giving up. After exhausting retries, it falls back to either `abort` or `fail-branch` (configurable).

**Configuration:**

```yaml
error_strategy: retry
retry_config:
  max_retries: 3
  retry_interval: 1000    # milliseconds between retries
  stop_after_attempt: abort   # or: fail-branch
```

**Recommended settings:**

| Scenario | max_retries | retry_interval |
|----------|-------------|----------------|
| External REST API (transient failures) | 2–3 | 1000–2000ms |
| Rate-limited API (e.g., free tier) | 3–5 | 2000–5000ms |
| LLM call (occasional timeout) | 2 | 500ms |

**Use when:**
- Errors are likely transient: network blips, temporary rate limits, momentary service outages
- The node is idempotent (safe to call multiple times)

**Avoid when:**
- The error is deterministic (wrong credentials, malformed request) — retrying won't help
- The node has side effects (e.g., sends an email) — retrying would duplicate the action

---

## Node Support Matrix

| Node Type | abort | fail-branch | default-value | retry |
|-----------|:-----:|:-----------:|:-------------:|:-----:|
| HTTP | Yes | Yes | Yes | Yes |
| LLM | Yes | Yes | Yes | Yes |
| Tool | Yes | Yes | Yes | Yes |
| Code | Yes | Yes | Yes | No |
| Knowledge Retrieval | Yes | Yes | Yes | Yes |
| Agent | Yes | Yes | Yes | No |
| Iteration | Yes | Yes | No | No |

---

## Complete YAML — HTTP Node with Fail-Branch

### Node Graph

```
start → http → [success] → code (parse) → variable-aggregator → end
                ↓ error-handle
               llm (error msg) ──────────────────────────────────↗
```

All results — whether success or failure — flow into `variable-aggregator`, which merges the outputs and passes a single `result` variable to `end`.

### Node IDs

| Node | ID |
|------|-----|
| start | `"1747200000001"` |
| http | `"1747200000002"` |
| code (parse) | `"1747200000003"` |
| llm (error msg) | `"1747200000004"` |
| variable-aggregator | `"1747200000005"` |
| end | `"1747200000006"` |

### Positioning

| Node | x | y |
|------|---|---|
| start | 80 | 282 |
| http | 380 | 282 |
| code (success) | 680 | 132 |
| llm (fail) | 680 | 432 |
| variable-aggregator | 980 | 282 |
| end | 1280 | 282 |

```yaml
app:
  description: "HTTP call with fail-branch error handling and graceful degradation."
  icon: "\U0001F6E1"
  icon_background: "#FBE9E7"
  mode: workflow
  name: HTTP with Fail-Branch
dependencies: []
features: {}
kind: app
version: "0.1.0"
workflow:
  conversation_variables: []
  environment_variables:
    - name: API_KEY
      value: ""
      value_type: secret
  graph:
    edges:
      # start → http
      - data:
          isInIteration: false
          sourceType: start
          targetType: http-request
        id: "1747200000001-source-1747200000002-target"
        source: "1747200000001"
        sourceHandle: source
        target: "1747200000002"
        targetHandle: target
        type: custom
        zIndex: 0

      # http → code (success path)
      - data:
          isInIteration: false
          sourceType: http-request
          targetType: code
        id: "1747200000002-source-1747200000003-target"
        source: "1747200000002"
        sourceHandle: source
        target: "1747200000003"
        targetHandle: target
        type: custom
        zIndex: 0

      # http → llm (fail-branch path — sourceHandle is "error-handle")
      - data:
          isInIteration: false
          sourceType: http-request
          targetType: llm
        id: "1747200000002-error-handle-1747200000004-target"
        source: "1747200000002"
        sourceHandle: error-handle
        target: "1747200000004"
        targetHandle: target
        type: custom
        zIndex: 0

      # code → variable-aggregator (success path converges)
      - data:
          isInIteration: false
          sourceType: code
          targetType: variable-aggregator
        id: "1747200000003-source-1747200000005-target"
        source: "1747200000003"
        sourceHandle: source
        target: "1747200000005"
        targetHandle: target
        type: custom
        zIndex: 0

      # llm → variable-aggregator (fail path converges)
      - data:
          isInIteration: false
          sourceType: llm
          targetType: variable-aggregator
        id: "1747200000004-source-1747200000005-target"
        source: "1747200000004"
        sourceHandle: source
        target: "1747200000005"
        targetHandle: target
        type: custom
        zIndex: 0

      # variable-aggregator → end
      - data:
          isInIteration: false
          sourceType: variable-aggregator
          targetType: end
        id: "1747200000005-source-1747200000006-target"
        source: "1747200000005"
        sourceHandle: source
        target: "1747200000006"
        targetHandle: target
        type: custom
        zIndex: 0

    nodes:
      - data:
          desc: ""
          title: Start
          type: start
          variables:
            - label: User Query
              max_length: 500
              options: []
              required: true
              type: text-input
              variable: query
        height: 54
        id: "1747200000001"
        position:
          x: 80
          y: 282
        positionAbsolute:
          x: 80
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          authorization:
            config:
              header: Authorization
              type: bearer
              token: "{{#env.API_KEY#}}"
            type: api-key
          body:
            data: '{"query": "{{#1747200000001.query#}}"}'
            type: json
          desc: "Call the external API. Fail-branch handles errors."
          error_strategy: fail-branch
          headers: "Content-Type: application/json"
          method: POST
          timeout:
            connect: 10
            max_connect_time: 0
            read: 30
            write: 20
          title: External API Call
          type: http-request
          url: "https://api.example.com/v1/search"
          variables: []
        height: 134
        id: "1747200000002"
        position:
          x: 380
          y: 282
        positionAbsolute:
          x: 380
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          code: |
            import json

            def main(body: str) -> dict:
                data = json.loads(body)
                results = data.get("results", [])
                formatted = "\n".join([r.get("text", "") for r in results])
                return {"parsed_result": formatted}
          code_language: python3
          desc: "Parse the successful API response."
          outputs:
            - name: parsed_result
              type: string
          title: Parse Response
          type: code
          variables:
            - variable: body
              value_selector:
                - "1747200000002"
                - body
        height: 90
        id: "1747200000003"
        position:
          x: 680
          y: 132
        positionAbsolute:
          x: 680
          y: 132
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          desc: "Generate a polite error message from the failure details."
          model:
            completion_params:
              max_tokens: 256
              temperature: 0.3
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: error-system
              role: system
              text: |
                You are a helpful assistant. The external API call failed. Generate a polite, user-friendly error message.
                Do not expose technical details. Suggest the user try again or contact support.

                Error type: {{#1747200000002.error_type#}}
                Error message: {{#1747200000002.error_message#}}
            - id: error-user
              role: user
              text: "Generate a friendly error response for the user."
          title: Error Message LLM
          type: llm
          vision:
            enabled: false
        height: 98
        id: "1747200000004"
        position:
          x: 680
          y: 432
        positionAbsolute:
          x: 680
          y: 432
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          advanced_settings:
            group_enabled: false
          desc: "Merge success and failure paths into a single output."
          output_type: string
          title: Variable Aggregator
          type: variable-aggregator
          variables:
            - label: result
              variable_selector:
                - "1747200000003"
                - parsed_result
            - label: result
              variable_selector:
                - "1747200000004"
                - text
        height: 90
        id: "1747200000005"
        position:
          x: 980
          y: 282
        positionAbsolute:
          x: 980
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          desc: ""
          outputs:
            - label: Result
              name: result
              type: string
              value_selector:
                - "1747200000005"
                - output
          title: End
          type: end
        height: 54
        id: "1747200000006"
        position:
          x: 1280
          y: 282
        positionAbsolute:
          x: 1280
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
```

---

## LLM Node with Default-Value

When an LLM node fails (model timeout, context length exceeded, provider outage), `default-value` causes the node to return a preset string and continue execution:

```yaml
data:
  desc: "Classify the sentiment of the input."
  error_strategy: default-value
  default_value:
    - key: text
      value: "neutral"
  model:
    completion_params:
      max_tokens: 10
      temperature: 0.0
    mode: chat
    name: gpt-4o-mini
    provider: openai
  prompt_template:
    - id: classify-system
      role: system
      text: "Classify the sentiment of the following text as: positive, negative, or neutral. Output ONLY the single word."
    - id: classify-user
      role: user
      text: "{{#start.input_text#}}"
  title: Sentiment Classifier
  type: llm
```

If the LLM call fails for any reason, the node outputs `text: "neutral"` and the pipeline continues as if classification succeeded.

---

## Graceful Degradation Pattern

The recommended pattern for any flow that calls an external service:

```
HTTP call
  ├─ [retry 2x with 1500ms interval]
  ├─ [success] → Code (parse response) → Variable Aggregator
  └─ [fail-branch after retries] → LLM (polite fallback) → Variable Aggregator
                                                                      ↓
                                                                    Answer
```

YAML configuration for the HTTP node in this pattern:

```yaml
error_strategy: retry
retry_config:
  max_retries: 2
  retry_interval: 1500
  stop_after_attempt: fail-branch
```

This means: try 3 times total (initial attempt + 2 retries), then go to fail-branch if all attempts fail.

See also:
- `skills/dify/references/nodes/http-request.md` — full HTTP node field reference
- `skills/dify/references/nodes/variable-aggregator.md` — how to configure the merge node
- `skills/dify/references/patterns/parallel-execution.md` — combining error handling with parallel flows
- `skills/dify/references/schema/edge-types.md` — edge sourceHandle values for each branch type
