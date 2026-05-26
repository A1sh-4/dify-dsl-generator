# Dify Workflow DSL Schema Reference

## Overview

A **workflow** is a Dify application designed for single-run, non-conversational automation tasks. Unlike a chatflow (which runs on every message in an ongoing conversation), a workflow executes once per trigger, processes data through its node graph, and terminates — returning a structured result via an `end` node.

Key characteristics of a workflow:
- **Single-run execution**: Each invocation is independent. There is no conversation history or memory across invocations unless you explicitly build that into the flow.
- **End node required**: Workflows use an `end` node (not an `answer` node) to declare output variables that are returned to the caller.
- **No conversation variables**: The `conversation_variables` array is not supported in workflow mode and must remain empty or be omitted.
- **Trigger nodes available**: Workflows support specialized trigger entry points (`trigger-webhook`, `trigger-schedule`) that allow them to be invoked via HTTP webhook or on a cron schedule without a user interaction.
- **Structured output**: The `end` node explicitly declares which variables are returned, making workflows composable as building blocks in larger systems.

**File format**: YAML  
**Current version**: `0.1`  
**App mode string**: `workflow`

---

## Top-Level Structure

Every Dify workflow DSL file must contain exactly these top-level keys:

```yaml
app:
  description: 'A brief description of what this workflow does.'
  icon: '⚙️'                     # Any single emoji character
  icon_background: '#E0F2FE'     # Hex color for the icon background circle
  mode: workflow                 # MUST be workflow for all workflows — never 'advanced-chat'
  name: 'My Workflow'            # Display name shown in the Dify dashboard
  use_icon_as_answer_icon: false # Applies to chatflows only; set false here

kind: app                        # Always the literal string 'app'
version: '0.1'                  # DSL version — always quote this value

dependencies: []                 # Optional list of Dify marketplace plugins required at runtime
                                 # Leave as empty array [] if no plugins are needed

workflow:
  conversation_variables: []     # Must be empty [] — conversation variables are not supported in workflows
  environment_variables: []      # Secret or config values injected at runtime
  features: {}                   # UI feature toggles (see Features Block below)
  graph:
    edges: []                    # Connections between nodes
    nodes: []                    # Workflow node definitions
```

### Field-by-field notes

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `app.mode` | string | Yes | Must be `workflow`. Any other value causes import failure. |
| `app.icon` | string | Yes | Single emoji or empty string `''`. |
| `app.icon_background` | string | Yes | Must be a valid 7-char hex color including `#`. |
| `kind` | string | Yes | Always `app`. This is a file-type discriminator. |
| `version` | string | Yes | Always `'0.1'`. Must be quoted — bare `0.1` parses as float and fails. |
| `dependencies` | array | No | Omitting the key is fine; Dify treats missing as empty. |
| `workflow.conversation_variables` | array | No | Must be `[]` in workflows. Non-empty value causes validation error. |
| `workflow.features` | object | Yes | Can be an empty object `{}` — Dify applies defaults for all fields. |
| `workflow.graph` | object | Yes | Both `nodes` and `edges` arrays must be present, even if empty. |

---

## The `features` Block

The `features` block under `workflow` controls runtime capabilities. In workflow mode, many chat-specific features (like `opening_statement` and `suggested_questions`) have no effect but can be safely included with their defaults.

```yaml
features:
  file_upload:
    enabled: false               # Master switch for file upload capability
    image:
      enabled: false             # Allow image inputs (used with vision-enabled LLM nodes)
      number_limits: 3           # Max number of images per invocation (1–6)
      transfer_methods:          # One or both of the following values:
        - local_file             #   Upload from caller's device
        - remote_url             #   Pass an image URL as input

  opening_statement: ''          # Not displayed in workflow mode — include as empty string

  retriever_resource:
    enabled: true                # Show source citations when knowledge base nodes are used.
                                 # Set false to suppress citation output in API responses.

  sensitive_word_avoidance:
    enabled: false               # Enable Dify's built-in content moderation filter.

  speech_to_text:
    enabled: false               # Not applicable to workflows — include as false.

  suggested_questions: []        # Not applicable to workflows — include as empty array.

  suggested_questions_after_answer:
    enabled: false               # Not applicable to workflows — include as false.

  text_to_speech:
    enabled: false               # Not applicable to workflows — include as false.
    language: ''
    voice: ''
```

### Feature field types and defaults

| Field | Type | Default | Applicable in Workflow |
|-------|------|---------|------------------------|
| `file_upload.enabled` | boolean | `false` | Yes — enables file inputs |
| `file_upload.image.number_limits` | integer | `3` | Yes |
| `opening_statement` | string | `''` | No — ignored |
| `retriever_resource.enabled` | boolean | `true` | Yes — controls citation output |
| `sensitive_word_avoidance.enabled` | boolean | `false` | Yes |
| `speech_to_text.enabled` | boolean | `false` | No — ignored |
| `suggested_questions` | array[string] | `[]` | No — ignored |
| `suggested_questions_after_answer.enabled` | boolean | `false` | No — ignored |
| `text_to_speech.enabled` | boolean | `false` | No — ignored |

---

## The `graph` Block

The `graph` block defines every processing step and how data flows between them.

```yaml
graph:
  nodes: [...]    # Array of node objects, each representing one processing step
  edges: [...]    # Array of edge objects, each connecting one node's output to another's input
```

**Nodes** are processed in the order determined by edge connections, not by their array order. Every workflow graph must have exactly one `start` node and at least one `end` node. Workflows may have multiple `end` nodes if different branches produce different outputs (for example, a success path and a failure path).

**Edges** are directional — data flows from `source` to `target`. Special edge handles (`fail-branch`, `true`, `false`) route conditional and error flows to different branches.

---

## Node Structure (Generic Template)

All nodes share this outer envelope regardless of their type. The `data` object is type-specific.

```yaml
- data:
    desc: ''                     # Optional human-readable description shown in editor tooltip
    selected: false              # Editor UI state — always false in saved DSL
    title: 'Node Title'          # Display name shown on the node card in the editor
    type: start                  # Node type string — determines what fields appear in data
    # ... additional type-specific fields follow here (see node-type docs in skills/dify/references/nodes/)

  height: 54                     # Canvas height in pixels — set by Dify editor, not functional
  id: '1732007415808'            # Unique node identifier — use millisecond Unix timestamp as string
  position:
    x: 80                        # Horizontal canvas position (pixels from left edge)
    y: 282                       # Vertical canvas position (pixels from top edge)
  positionAbsolute:              # Mirror of position — must match position exactly
    x: 80
    y: 282
  selected: false                # Canvas selection state — always false in saved DSL
  sourcePosition: right          # Direction the output connector faces — always 'right'
  targetPosition: left           # Direction the input connector faces — always 'left'
  type: custom                   # React Flow node type — always the literal string 'custom'
  width: 244                     # Canvas width in pixels — standard is 244 for most nodes
```

### Node ID conventions

Node IDs must be unique within the file. The conventional format is a millisecond Unix timestamp as a string (e.g., `'1732007415808'`). When creating multiple nodes, increment by 1 or more milliseconds to guarantee uniqueness. Do not use UUIDs or sequential integers — Dify's editor produces timestamp IDs and validators may depend on this format.

### Positioning guidelines

Space nodes 300–400 pixels apart horizontally to avoid visual overlap in the editor canvas. Standard layout is left-to-right: the `start` node at approximately `x: 80`, the first processing node at `x: 380`, the next at `x: 730`, and the `end` node at the rightmost position.

### Node type strings available in workflows

| Type string | Description | Chatflow | Workflow |
|-------------|-------------|----------|----------|
| `start` | Entry point — receives inputs | Yes | Yes |
| `end` | Terminates flow, returns outputs | No | Yes |
| `answer` | Returns text to user in conversation | Yes | No |
| `llm` | Calls a language model | Yes | Yes |
| `code` | Executes a Python script | Yes | Yes |
| `http-request` | Makes an outbound HTTP call | Yes | Yes |
| `if-else` | Branches on a condition | Yes | Yes |
| `knowledge-retrieval` | Queries a Dify knowledge base | Yes | Yes |
| `parameter-extractor` | Extracts structured fields from text | Yes | Yes |
| `iteration` | Loops over an array | Yes | Yes |
| `template-transform` | Applies a Jinja2 template | Yes | Yes |
| `variable-assigner` | Writes a value to a variable | Yes | Yes |
| `tool` | Calls a Dify marketplace plugin tool | Yes | Yes |
| `trigger-webhook` | HTTP webhook entry point | No | Yes |
| `trigger-schedule` | Cron schedule entry point | No | Yes |

---

## Edge Structure

Each edge connects one node's output handle to another node's input handle.

```yaml
- data:
    isInIteration: false         # true only when this edge is inside an iteration node
    sourceType: start            # Type string of the source node
    targetType: llm              # Type string of the target node
  id: 'source_node_id-source-target_node_id-target'   # Composite ID: concatenate with hyphens
  source: 'source_node_id'      # id of the node sending data
  sourceHandle: source          # Output handle name on the source node:
                                #   'source'       — normal output
                                #   'fail-branch'  — error output (http-request, tool nodes)
                                #   'true'         — if-else true branch
                                #   'false'        — if-else false branch
  target: 'target_node_id'      # id of the node receiving data
  targetHandle: target          # Always 'target' for the receiving end
  type: custom                  # Always the literal string 'custom'
  zIndex: 0                     # Drawing order — always 0 for normal edges
```

### Edge ID format

The `id` field for an edge follows the pattern:  
`{source_node_id}-{sourceHandle}-{target_node_id}-{targetHandle}`

For a normal connection from node `1732007415808` to node `1732007415900`:  
`'1732007415808-source-1732007415900-target'`

For a fail-branch from an HTTP node `1732007416200` to an error handler node `1732007416300`:  
`'1732007416200-fail-branch-1732007416300-target'`

---

## The `end` Node — Output Variable Structure

The `end` node is the terminal node in a workflow. It does not return a conversational message — it declares which variables are included in the workflow's structured API response. This makes the `end` node configuration critical for any downstream system consuming the workflow output.

```yaml
- data:
    desc: 'Returns the processed result to the caller'
    outputs:
      - label: 'Summary'           # Human-readable label shown in the Dify editor
        value_selector:            # Path to the variable being output:
          - '1732007415900'        #   First element: the node id producing the value
          - 'text'                 #   Second element: the output field name on that node
        variable: 'summary'        # Key name in the workflow output JSON object
    selected: false
    title: 'End'
    type: end
  height: 119
  id: '1732007416000'
  position:
    x: 700
    y: 262
  positionAbsolute:
    x: 700
    y: 262
  selected: false
  sourcePosition: right
  targetPosition: left
  type: custom
  width: 244
```

### Output variable fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | Yes | Display label in the Dify editor — cosmetic only |
| `value_selector` | array[string] | Yes | Two-element path: `[node_id, output_field_name]` |
| `variable` | string | Yes | Key name in the API response JSON — must be a valid identifier |

### Common output field names by node type

| Node type | Output field | Description |
|-----------|-------------|-------------|
| `llm` | `text` | The generated text response |
| `code` | As declared in script | Python dict keys returned by the code |
| `http-request` | `body` | Raw response body string |
| `http-request` | `status_code` | HTTP status code integer |
| `knowledge-retrieval` | `result` | Array of retrieved document chunks |
| `parameter-extractor` | As declared | Extracted parameter names |
| `template-transform` | `output` | Rendered template string |

A workflow may have multiple output variables in a single `end` node:

```yaml
outputs:
  - label: 'Generated Summary'
    value_selector:
      - '1732007415900'
      - 'text'
    variable: 'summary'
  - label: 'HTTP Status'
    value_selector:
      - '1732007416100'
      - 'status_code'
    variable: 'api_status'
```

---

## Trigger Nodes (Workflow-Exclusive)

Trigger nodes replace the standard `start` node when a workflow needs to be invoked by an external event rather than a direct API call or manual run.

### Webhook Trigger

```yaml
- data:
    desc: 'Receives HTTP POST requests from external systems'
    selected: false
    title: 'Webhook Trigger'
    type: trigger-webhook
    variables: []                # The webhook payload is available as {{#sys.files#}} or body fields
  height: 54
  id: '1732007415808'
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
```

### Schedule Trigger

```yaml
- data:
    cron_expression: '0 9 * * 1'  # Cron expression — this example: every Monday at 9:00 AM UTC
    desc: 'Runs on a cron schedule'
    selected: false
    title: 'Schedule Trigger'
    type: trigger-schedule
  height: 54
  id: '1732007415808'
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
```

**Important**: Trigger nodes replace the `start` node — a workflow uses either a `start` node (manual/API invocation) or a trigger node, not both.

---

## `conversation_variables`

This section must be present but empty in workflow DSLs:

```yaml
conversation_variables: []
```

Conversation variables are not supported in workflow mode. Placing any entries here causes a Dify import validation error. All inter-node data sharing in workflows is done through variable references (`{{#node_id.field_name#}}`), and persistent state must be managed externally (e.g., a database node or HTTP call).

---

## `environment_variables`

Environment variables are configuration values set at the Dify instance level and injected into the workflow at runtime. They are ideal for API keys, endpoint URLs, and any value that differs between environments.

```yaml
environment_variables:
  - description: 'API key for the search service'
    id: 'env_var_001'            # Unique ID for this variable
    name: 'search_api_key'       # Name used in template references
    value_type: secret           # Use 'secret' for sensitive values — masked in logs
    value: ''                    # Leave empty in DSL — set in Dify dashboard at runtime

  - description: 'Target Notion database ID for output'
    id: 'env_var_002'
    name: 'notion_database_id'
    value_type: string
    value: ''
```

Reference environment variables in node fields using:  
`{{env.variable_name}}`

For example, in an HTTP node's Authorization header: `Bearer {{env.search_api_key}}`

### Value types

| Type | Use case |
|------|----------|
| `string` | Text configuration: URLs, IDs, labels |
| `number` | Numeric configuration: limits, thresholds |
| `secret` | Sensitive values — masked in logs and UI |

---

## Minimal Valid Workflow Example

The following is a complete, importable three-node workflow: `start → llm → end`. It includes every required field and is structured to import successfully into Dify without modification.

```yaml
app:
  description: 'A minimal workflow that processes user input through an LLM and returns the result.'
  icon: '⚙️'
  icon_background: '#E0F2FE'
  mode: workflow
  name: 'Minimal Workflow'
  use_icon_as_answer_icon: false

kind: app
version: '0.1'

dependencies: []

workflow:
  conversation_variables: []
  environment_variables: []

  features:
    file_upload:
      enabled: false
      image:
        enabled: false
        number_limits: 3
        transfer_methods:
          - local_file
          - remote_url
    opening_statement: ''
    retriever_resource:
      enabled: true
    sensitive_word_avoidance:
      enabled: false
    speech_to_text:
      enabled: false
    suggested_questions: []
    suggested_questions_after_answer:
      enabled: false
    text_to_speech:
      enabled: false
      language: ''
      voice: ''

  graph:
    nodes:

      - data:
          desc: 'Entry point — defines input variables for the workflow'
          selected: false
          title: 'Start'
          type: start
          variables:
            - label: 'User Input'       # Display label in the Dify editor
              max_length: 2000          # Maximum character length for this input
              options: []               # Dropdown options — empty unless type is 'select'
              required: true            # Whether the caller must provide this value
              type: paragraph           # Input type: text | paragraph | number | select | file | files
              variable: 'user_input'    # Variable name — referenced as {{#1732007415808.user_input#}}
        height: 116
        id: '1732007415808'
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
          context:
            enabled: false
            variable_selector: []
          desc: 'Processes the input using an LLM and generates a result'
          memory:
            query_prompt_template: '{{#sys.query#}}'
            role_prefix:
              assistant: ''
              user: ''
            window:
              enabled: false
              size: 10
          model:
            completion_params:
              temperature: 0.5
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: 'sys-prompt-001'
              role: system
              text: 'You are an assistant that processes text inputs and provides clear, structured results.'
            - id: 'user-prompt-001'
              role: user
              text: '{{#1732007415808.user_input#}}'
          selected: false
          title: 'LLM'
          type: llm
          variables: []
          vision:
            enabled: false
        height: 98
        id: '1732007415900'
        position:
          x: 400
          y: 262
        positionAbsolute:
          x: 400
          y: 262
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          desc: 'Returns the LLM result as the workflow output'
          outputs:
            - label: 'LLM Result'
              value_selector:
                - '1732007415900'      # Node ID of the LLM node
                - 'text'               # Output field name on the LLM node
              variable: 'result'       # Key name in the API response JSON
          selected: false
          title: 'End'
          type: end
        height: 119
        id: '1732007416000'
        position:
          x: 720
          y: 262
        positionAbsolute:
          x: 720
          y: 262
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

    edges:

      - data:
          isInIteration: false
          sourceType: start
          targetType: llm
        id: '1732007415808-source-1732007415900-target'
        source: '1732007415808'
        sourceHandle: source
        target: '1732007415900'
        targetHandle: target
        type: custom
        zIndex: 0

      - data:
          isInIteration: false
          sourceType: llm
          targetType: end
        id: '1732007415900-source-1732007416000-target'
        source: '1732007415900'
        sourceHandle: source
        target: '1732007416000'
        targetHandle: target
        type: custom
        zIndex: 0
```

---

## Key Rules for Workflows

1. **`mode` must be `workflow`**: Never use `advanced-chat`. Using `advanced-chat` imports the file as a chatflow, which requires an `answer` node and behaves differently at runtime.

2. **Must use `end` node, not `answer` node**: The `end` node is the correct terminal node for workflows. The `answer` node is a chatflow-only construct — using it in a workflow causes an import error or produces no output.

3. **`conversation_variables` must be empty `[]`**: Any entries in this array will cause a Dify validation error on import. Workflow state is managed through variable references, not persistent conversation variables.

4. **System variables `sys.conversation_id` and `sys.dialogue_count` are not available**: These are injected by the chatflow conversation runtime only. Referencing them in a workflow produces a blank value or a runtime error.

5. **The `end` node must explicitly declare outputs**: Unlike the `answer` node (which takes a single text string), the `end` node requires an `outputs` array where each entry specifies the source node, the source field, and the output variable name. A workflow with an `end` node that has no `outputs` returns an empty object.

6. **`version` must be quoted**: Write `version: '0.1'` not `version: 0.1`. YAML parses the bare value as a float and Dify's import parser expects a string.

7. **`start` node variables define the workflow's input contract**: For API-invoked workflows, the `variables` array on the `start` node defines what the caller must supply. Each variable's `variable` field becomes the key in the API request body.

---

## Key Differences: Workflow vs Chatflow

| Feature | Workflow (`mode: workflow`) | Chatflow (`mode: advanced-chat`) |
|---------|----------------------------|----------------------------------|
| **Terminal node** | `end` | `answer` |
| **Execution model** | Single run per invocation | Re-runs on every conversation message |
| **Conversation history** | Not available | Automatically threaded by Dify |
| **`conversation_variables`** | Not supported (must be `[]`) | Supported — persists across turns |
| **`sys.conversation_id`** | Not available | Available |
| **`sys.dialogue_count`** | Not available | Available |
| **Trigger nodes** | `trigger-webhook`, `trigger-schedule` | Not available |
| **Output structure** | Declared in `end` node `outputs` array | Text string in `answer` node |
| **Use case** | Batch processing, automation, API backends | Conversational assistants, chatbots |
| **`opening_statement`** | Ignored | Displayed before first message |
| **`suggested_questions`** | Ignored | Shown as clickable starter chips |

---

## Common Mistakes

1. **Using `mode: advanced-chat` instead of `mode: workflow`**: Workflows must use `workflow` as the mode string. This is the single most common import failure. Dify routes the file to a completely different runtime based on this field.

2. **Using an `answer` node instead of an `end` node**: The `answer` node is chatflow-exclusive. Using it in a workflow produces an import error or silently discards the output. Always use `end` in workflow mode.

3. **Leaving outputs empty in the `end` node**: A workflow with an `end` node that has no `outputs` array entries returns an empty JSON object `{}`. Any downstream system expecting output variables will receive nothing. Always declare at least one output variable.

4. **Referencing `sys.conversation_id` or `sys.dialogue_count`**: These system variables are injected by the chatflow conversation runtime. In a workflow, they resolve to empty strings. If you need a unique run identifier, use a code node to generate a UUID or use `sys.workflow_run_id` instead.

5. **Placing entries in `conversation_variables`**: Even with valid structure, non-empty `conversation_variables` in a workflow DSL triggers a validation error on import. The array must always be `[]` in workflow mode.
