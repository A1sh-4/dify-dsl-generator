# Dify Chatflow DSL Schema Reference

## Overview

A **chatflow** is a Dify application designed for multi-turn, conversational interactions. Unlike a workflow (which runs once and terminates), a chatflow maintains a running conversation context — every user message triggers the graph again, and the conversation history is automatically threaded across turns.

Key characteristics of a chatflow:
- **Multi-turn**: The same flow executes for every message in the conversation. Dify injects `sys.conversation_id`, `sys.dialogue_count`, and `sys.query` automatically.
- **Answer node required**: Chatflows must use an `answer` node (not an `end` node) to return text back to the user within a conversation turn.
- **Conversation variables**: A special variable type (`conversation_variables`) persists across turns within a single conversation session — use these to track state such as detected language, user preferences, or slot-filled entities.
- **System variables exclusive to chatflows**: `sys.conversation_id`, `sys.dialogue_count`, and `sys.user_id` are only available in chatflow mode.

**File format**: YAML  
**Current version**: `0.1`  
**App mode string**: `advanced-chat`

---

## Top-Level Structure

Every Dify chatflow DSL file must contain exactly these top-level keys:

```yaml
app:
  description: 'A brief description of what this chatflow does.'
  icon: '🤖'                     # Any single emoji character
  icon_background: '#FFEAD5'     # Hex color for the icon background circle
  mode: advanced-chat            # MUST be advanced-chat for all chatflows — never 'workflow'
  name: 'My Chatflow'            # Display name shown in the Dify dashboard
  use_icon_as_answer_icon: false # If true, the app icon replaces the default bot avatar

kind: app                        # Always the literal string 'app'
version: '0.1'                  # DSL version — always quote this value

dependencies: []                 # Optional list of Dify marketplace plugins required at runtime
                                 # Leave as empty array [] if no plugins are needed

workflow:
  conversation_variables: []     # Variables that persist across turns in one conversation
  environment_variables: []      # Secret or config values injected at runtime
  features: {}                   # UI feature toggles (see Features Block below)
  graph:
    edges: []                    # Connections between nodes
    nodes: []                    # Workflow node definitions
```

### Field-by-field notes

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `app.mode` | string | Yes | Must be `advanced-chat`. Any other value causes import failure. |
| `app.icon` | string | Yes | Single emoji or empty string `''`. |
| `app.icon_background` | string | Yes | Must be a valid 7-char hex color including `#`. |
| `kind` | string | Yes | Always `app`. This is a file-type discriminator. |
| `version` | string | Yes | Always `'0.1'`. Must be quoted — bare `0.1` parses as float and fails. |
| `dependencies` | array | No | Omitting the key is fine; Dify treats missing as empty. |
| `workflow.features` | object | Yes | Can be an empty object `{}` — Dify applies defaults for all fields. |
| `workflow.graph` | object | Yes | Both `nodes` and `edges` arrays must be present, even if empty. |

---

## The `features` Block

The `features` block under `workflow` controls UI capabilities shown to end users in the Dify chat interface. All fields are optional — omitting a field uses the Dify default.

```yaml
features:
  file_upload:
    enabled: false               # Master switch for file upload capability
    image:
      enabled: false             # Allow image uploads specifically
      number_limits: 3           # Max number of images per message (1–6)
      transfer_methods:          # One or both of the following values:
        - local_file             #   Upload from user's device
        - remote_url             #   Paste an image URL

  opening_statement: ''          # Welcome message shown before first user message.
                                 # Supports Markdown. Empty string shows nothing.

  retriever_resource:
    enabled: true                # Show source citations when knowledge base nodes
                                 # are used. Set false to hide citation cards.

  sensitive_word_avoidance:
    enabled: false               # Enable Dify's built-in content moderation filter.

  speech_to_text:
    enabled: false               # Show microphone button for voice input.

  suggested_questions: []        # List of pre-written opening question strings shown
                                 # as clickable chips before the first user turn.
                                 # Example: ['What can you help me with?', 'Show me an example']

  suggested_questions_after_answer:
    enabled: false               # If true, Dify generates follow-up question suggestions
                                 # after each answer node response.

  text_to_speech:
    enabled: false               # Enable text-to-speech for answer node output.
    language: ''                 # BCP-47 language code, e.g. 'en-US', 'zh-CN'. Empty = auto-detect.
    voice: ''                    # Provider-specific voice ID. Empty = provider default.
```

### Feature field types and defaults

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `file_upload.enabled` | boolean | `false` | Master file upload toggle |
| `file_upload.image.number_limits` | integer | `3` | Max images; capped at 6 by Dify |
| `opening_statement` | string | `''` | Markdown welcome message |
| `retriever_resource.enabled` | boolean | `true` | Show knowledge base citations |
| `sensitive_word_avoidance.enabled` | boolean | `false` | Content moderation filter |
| `speech_to_text.enabled` | boolean | `false` | Voice input button |
| `suggested_questions` | array[string] | `[]` | Starter question chips |
| `suggested_questions_after_answer.enabled` | boolean | `false` | Auto follow-up suggestions |
| `text_to_speech.enabled` | boolean | `false` | Read-aloud toggle |

---

## The `graph` Block

The `graph` block is the heart of the DSL — it defines every processing step and how they connect.

```yaml
graph:
  nodes: [...]    # Array of node objects, each representing one processing step
  edges: [...]    # Array of edge objects, each connecting one node's output to another's input
```

**Nodes** are processed in the order determined by edge connections, not by their array order. The array order only affects canvas rendering in the Dify editor. Every graph must have exactly one `start` node and at least one `answer` node.

**Edges** are directional — data flows from `source` to `target`. Each edge references nodes by their `id` values. An edge can carry normal flow (`source` handle), error flow (`fail-branch` handle), or conditional flow (`true`/`false` handles from if-else nodes).

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

Space nodes 300–400 pixels apart horizontally to avoid visual overlap in the editor canvas. The standard layout is left-to-right: the `start` node sits at approximately `x: 80`, the first processing node at `x: 380`, the next at `x: 730`, and so on.

### Node type strings

| Type string | Description |
|-------------|-------------|
| `start` | Entry point — receives user input |
| `answer` | Returns text to user (chatflow only — replaces `end`) |
| `llm` | Calls a language model |
| `code` | Executes a Python script |
| `http-request` | Makes an outbound HTTP call |
| `if-else` | Branches on a condition |
| `knowledge-retrieval` | Queries a Dify knowledge base |
| `parameter-extractor` | Extracts structured fields from text |
| `iteration` | Loops over an array |
| `template-transform` | Applies a Jinja2 template |
| `variable-assigner` | Writes a value to a conversation variable |
| `tool` | Calls a Dify marketplace plugin tool |

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

For a true-branch connection from an if-else node `1732007416000` to node `1732007416100`:  
`'1732007416000-true-1732007416100-target'`

---

## `conversation_variables`

Conversation variables are exclusive to chatflow mode. They persist for the lifetime of a single conversation session — they are reset when a new conversation starts. Use them to track state across multiple turns: which language the user prefers, how many times they have asked about a topic, slot-filled values from earlier turns, etc.

```yaml
conversation_variables:
  - description: 'The language the user is communicating in'   # Human-readable explanation
    id: 'conv_var_001'           # Unique ID for this variable — any string, kept stable
    name: 'language'             # Variable name used in references: {{#conv_var_001.language#}}
                                 # Actually referenced as: {{#conversation.language#}}
    value_type: string           # Data type: string | number | object | array-object | secret
    value: ''                    # Initial/default value at conversation start

  - description: 'Count of unresolved issues reported this session'
    id: 'conv_var_002'
    name: 'issue_count'
    value_type: number
    value: 0
```

### Referencing conversation variables in nodes

In LLM prompts and other node fields, reference conversation variables using:  
`{{#conversation.variable_name#}}`

To write a new value into a conversation variable, use a `variable-assigner` node.

### Value types

| Type | Use case |
|------|----------|
| `string` | Text values: language codes, user names, last intent |
| `number` | Counters, scores, numeric thresholds |
| `object` | Structured data (JSON object) |
| `array-object` | List of structured items |
| `secret` | Sensitive values — masked in logs |

---

## `environment_variables`

Environment variables are configuration values set at the Dify instance level and injected into the workflow at runtime. They are ideal for API keys, endpoint URLs, and other values that differ between environments (development vs. production) but must not be hardcoded in the DSL.

```yaml
environment_variables:
  - description: 'API key for external service authentication'
    id: 'env_var_001'            # Unique ID for this variable
    name: 'api_key'              # Name used in template references
    value_type: secret           # Always use 'secret' for sensitive values
    value: ''                    # Leave empty in DSL — set in Dify dashboard at runtime

  - description: 'Base URL for the internal API'
    id: 'env_var_002'
    name: 'api_base_url'
    value_type: string
    value: 'https://api.example.com'
```

Reference environment variables in node fields using:  
`{{env.variable_name}}`  

For example, in an HTTP node's URL field: `{{env.api_base_url}}/v1/search`

---

## Minimal Valid Chatflow Example

The following is a complete, importable three-node chatflow: `start → llm → answer`. It includes every required field and is structured to import successfully into Dify without modification.

```yaml
app:
  description: 'A minimal chatflow that echoes the user query through an LLM.'
  icon: '🤖'
  icon_background: '#FFEAD5'
  mode: advanced-chat
  name: 'Minimal Chatflow'
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
    opening_statement: 'Hello! How can I help you today?'
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
          desc: 'Entry point — receives the user message'
          selected: false
          title: 'Start'
          type: start
          variables: []          # No additional input variables beyond sys.query
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

      - data:
          context:
            enabled: false
            variable_selector: []
          desc: 'Generates a response using the LLM'
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
              temperature: 0.7
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: 'sys-prompt-001'
              role: system
              text: 'You are a helpful assistant. Answer the user clearly and concisely.'
            - id: 'user-prompt-001'
              role: user
              text: '{{#sys.query#}}'
          selected: false
          title: 'LLM'
          type: llm
          variables: []
          vision:
            enabled: false
        height: 98
        id: '1732007415900'
        position:
          x: 380
          y: 262
        positionAbsolute:
          x: 380
          y: 262
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          answer: '{{#1732007415900.text#}}'   # References the LLM node output by its id
          desc: 'Returns the LLM response to the user'
          selected: false
          title: 'Answer'
          type: answer
          variables: []
        height: 107
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
          targetType: answer
        id: '1732007415900-source-1732007416000-target'
        source: '1732007415900'
        sourceHandle: source
        target: '1732007416000'
        targetHandle: target
        type: custom
        zIndex: 0
```

---

## Key Rules for Chatflows

1. **`mode` must be `advanced-chat`**: Never use `workflow`. Dify routes the DSL to the wrong runtime if mode is wrong, causing import to silently produce a non-conversational app or fail entirely.

2. **Must have at least one `answer` node**: Chatflows cannot use an `end` node. The `answer` node is the mechanism that sends text back to the user. Without it, the conversation produces no output.

3. **`conversation_variables` are chatflow-exclusive**: These variables appear only in chatflow DSLs. Placing them in a workflow DSL causes a validation error on import.

4. **System variables `sys.conversation_id` and `sys.dialogue_count` are chatflow-only**: These are injected by Dify's conversation runtime and do not exist in workflow mode. Do not reference them in workflow DSLs.

5. **`version` must be quoted**: Write `version: '0.1'` not `version: 0.1`. YAML parses the bare value as a float and Dify's import parser expects a string.

6. **Node IDs must be unique timestamp strings**: Use millisecond Unix timestamps as strings. IDs like `'1'`, `'node_a'`, or UUIDs are not forbidden by the YAML spec but differ from Dify's convention and may cause issues with edge ID construction.

7. **`positionAbsolute` must mirror `position`**: Both fields must contain identical `x` and `y` values. Dify writes both when exporting but only uses `positionAbsolute` for canvas rendering.

---

## Common Mistakes

1. **Using `mode: workflow` instead of `mode: advanced-chat`**: This is the single most common import failure. Chatflows always use `advanced-chat`. The word "advanced" is part of the string — `chat` alone is not valid.

2. **Using an `end` node instead of an `answer` node**: Developers familiar with Dify workflows often use `end` nodes. In a chatflow, the `end` node is not recognized as the conversation response mechanism — it produces no output visible to the user.

3. **Forgetting to quote `version: '0.1'`**: YAML silently parses `0.1` as a float. Dify's import layer expects a string and will either fail or produce unexpected behavior.

4. **Hardcoding LLM provider and model names**: The `model.provider` and `model.name` fields must match exactly what is configured in the Dify instance. A chatflow referencing `openai/gpt-4o` will fail on an instance that has `azure_openai` configured instead. Keep these fields as variables or document the dependency explicitly.

5. **Variable references using the wrong node ID**: When an `answer` node references LLM output with `{{#1732007415900.text#}}`, the ID `1732007415900` must exactly match the `id` field of the LLM node. A mismatch produces a blank answer at runtime with no error shown to the user — it silently passes an empty string.
