# Pattern: Stateful Chatflows with Conversation Variables

## Overview

A stateful chatflow remembers information across multiple conversation turns — not just by giving the LLM access to prior messages (that is the `memory` window), but by explicitly storing named values that your workflow logic can read and branch on. Conversation variables are the mechanism for this: they are typed, named slots that persist for the lifetime of a conversation session and can be read by any node.

This pattern is **chatflow-only**. Regular workflows process one run at a time with no conversation concept, so conversation variables do not exist in them.

---

## Memory vs Conversation Variables

These two features are complementary, not alternatives. Understanding the difference prevents misuse.

| Dimension | LLM Memory Window | Conversation Variables |
|---|---|---|
| What it stores | Raw text of prior messages | Specific named values you define |
| How it's accessed | Auto-injected into LLM context | `{{#conversation.var_name#}}` in any node |
| How it's updated | Automatically after each turn | Explicitly via a `variable-assigner` node |
| Your workflow can branch on it | No — LLM sees it, not the graph | Yes — `if-else` conditions can read it |
| Token cost | Grows with window size | Fixed — only the stored values |
| Best for | Conversational continuity, tone, context | State tracking, preferences, accumulated data |

Use memory for natural conversation flow. Use conversation variables for extracted facts your graph needs to act on.

See `skills/dify/references/config/memory.md` for the LLM memory window configuration reference.

---

## How Conversation Variables Work

### 1. Declaration in the DSL

Conversation variables must be declared at the `workflow` level before they can be used. Each variable needs a unique `id` (UUIDv4), a `name`, a `value_type`, and a default `value`.

```yaml
workflow:
  conversation_variables:
    - description: 'The language the user prefers for responses'
      id: 'cv-0001-0000-0000-000000000001'
      name: preferred_language
      value_type: string
      value: 'en'
    - description: 'Which step of onboarding the user is on'
      id: 'cv-0001-0000-0000-000000000002'
      name: onboarding_step
      value_type: string
      value: 'start'
    - description: 'Whether the user has accepted terms'
      id: 'cv-0001-0000-0000-000000000003'
      name: terms_accepted
      value_type: boolean
      value: false
    - description: 'Count of messages in this session'
      id: 'cv-0001-0000-0000-000000000004'
      name: message_count
      value_type: number
      value: 0
  environment_variables: []
```

### Supported value_type values

| value_type | Description | Default value format |
|---|---|---|
| `string` | Text | `''` or a default string |
| `number` | Integer or float | `0` |
| `boolean` | True/false | `false` |
| `object` | JSON dictionary | `{}` |
| `array[string]` | List of strings | `[]` |
| `array[number]` | List of numbers | `[]` |
| `array[object]` | List of objects | `[]` |
| `file` | File reference | `null` |

### 2. Reading conversation variables

In any node that accepts variable references, use the `conversation` namespace:

```
{{#conversation.preferred_language#}}
{{#conversation.onboarding_step#}}
{{#conversation.terms_accepted#}}
```

This works in LLM prompt templates, template-transform Jinja2, if-else conditions, and HTTP node body templates.

### 3. Writing conversation variables

Use a `variable-assigner` node to update one or more conversation variables in a single step:

```yaml
- data:
    assigned_variables:
      - variable_name: preferred_language
        assigned_variable_selector:
          - extract_prefs_node_id
          - language
      - variable_name: onboarding_step
        assigned_variable_selector:
          - logic_node_id
          - next_step
    title: Save User State
    type: variable-assigner
  id: '1748300000010'
  ...
```

The `variable_name` must match a name declared in `conversation_variables`. The `assigned_variable_selector` is an array path `[node_id, output_field]` pointing to the value to store.

---

## Pattern 1 — User Preference Detection and Persistence

**Use case:** User states a preference early in the conversation (language, format, tone). Store it explicitly so later turns can apply it reliably — rather than relying on the LLM to remember it from history.

### Node graph

```
start → parameter-extractor (detect prefs) → variable-assigner (save prefs) → llm (respond) → answer
```

### How it works

1. Every turn: `parameter-extractor` reads `sys.query` and attempts to extract a `language` preference. If none detected, it returns a default (e.g., `"en"`).
2. `variable-assigner` writes `language` to `conversation.preferred_language`.
3. `llm` reads `{{#conversation.preferred_language#}}` in its system prompt and responds in the detected language.

### Key nodes

**parameter-extractor** — extracts the preference:
```yaml
- data:
    desc: "Detect language and format preferences from user message."
    model:
      completion_params:
        temperature: 0.0
      mode: chat
      name: gpt-4o-mini
      provider: openai
    parameters:
      - default: en
        description: >
          ISO 639-1 language code the user is writing in.
          Examples: en, fr, es, ja, zh. Default to en if not detectable.
        name: language
        required: false
        type: string
      - default: paragraph
        description: >
          Preferred response format. One of: paragraph, bullet_list, numbered_list.
        name: format
        required: false
        type: string
    query:
      variable_selector:
        - '1748300000001'
        - sys.query
    reasoning_mode: function_call
    title: Detect Preferences
    type: parameter-extractor
  id: '1748300000002'
  ...
```

**variable-assigner** — persists both values:
```yaml
- data:
    assigned_variables:
      - variable_name: preferred_language
        assigned_variable_selector:
          - '1748300000002'
          - language
      - variable_name: preferred_format
        assigned_variable_selector:
          - '1748300000002'
          - format
    title: Save Preferences
    type: variable-assigner
  id: '1748300000003'
  ...
```

**llm** — uses the stored values:
```yaml
prompt_template:
  - id: pref-system
    role: system
    text: |
      You are a helpful assistant.
      Always respond in this language: {{#conversation.preferred_language#}}
      Always format responses as: {{#conversation.preferred_format#}}
  - id: pref-user
    role: user
    text: "{{#1748300000001.sys.query#}}"
```

---

## Pattern 2 — Multi-Step Form Collection

**Use case:** Collect several pieces of information across multiple turns (e.g., name, email, and company for a lead capture bot) without requiring the user to fill in a single long form.

### Node graph

```
start
  → if-else (check step)
      → [step == "collect_name"]  → llm (ask for name)   → answer
      → [step == "collect_email"] → llm (ask for email)  → answer
      → [step == "collect_company"] → llm (ask for company) → answer
      → [step == "complete"]       → llm (confirm + submit) → answer

Every non-first turn also runs: parameter-extractor → variable-assigner (update step + store value)
```

**Note:** In chatflows, you cannot have a single if-else that routes AND then also feeds back in. The standard implementation uses an if-else at the start of each turn that routes based on `conversation.current_step`.

### Conversation variables declared

```yaml
conversation_variables:
  - id: 'cv-form-0001'
    name: current_step
    value_type: string
    value: 'collect_name'
  - id: 'cv-form-0002'
    name: user_name
    value_type: string
    value: ''
  - id: 'cv-form-0003'
    name: user_email
    value_type: string
    value: ''
  - id: 'cv-form-0004'
    name: user_company
    value_type: string
    value: ''
```

### if-else node routing on step

```yaml
- data:
    conditions:
      - comparison_operator: ==
        id: cond-name
        value: collect_name
        variable_selector:
          - conversation
          - current_step
      - comparison_operator: ==
        id: cond-email
        value: collect_email
        variable_selector:
          - conversation
          - current_step
    logical_operator: or
    title: Route by Step
    type: if-else
  id: '1748300000020'
  ...
```

Each branch leads to an LLM that either asks for the next value or (in the final step) confirms and triggers the submission logic.

### variable-assigner updates both the stored value and advances the step

```yaml
- data:
    assigned_variables:
      - variable_name: user_name
        assigned_variable_selector:
          - '1748300000025'   # parameter-extractor node
          - name
      - variable_name: current_step
        assigned_variable_selector:
          - '1748300000026'   # code node that returns "collect_email"
          - next_step
    title: Save Name and Advance
    type: variable-assigner
  id: '1748300000027'
  ...
```

---

## Pattern 3 — Conversation State Machine

**Use case:** A chatflow that has multiple modes or phases (e.g., `onboarding` → `active` → `escalated`). State transitions are triggered by workflow logic, not by the LLM guessing what mode it's in.

### Conversation variable

```yaml
conversation_variables:
  - id: 'cv-state-0001'
    name: conversation_state
    value_type: string
    value: 'onboarding'
```

### Turn structure

```
start
  → if-else (state == onboarding)
      → [true]  → onboarding-llm → answer
      → [false] → if-else (state == escalated)
                    → [true]  → escalation-llm → answer
                    → [false] → main-llm → answer

Parallel branch: parameter-extractor (detect escalation trigger) → if-else (triggered?) → variable-assigner (set state = escalated)
```

In Dify chatflows, the state check runs at the start of each turn. After generating a response, if conditions warrant a state change, a `variable-assigner` updates the state so the next turn starts in the new state.

### LLM system prompt reads the state for awareness

```yaml
prompt_template:
  - id: state-system
    role: system
    text: |
      Current conversation state: {{#conversation.conversation_state#}}

      If state is "onboarding": guide the user through the setup steps.
      If state is "active": answer questions using the knowledge base.
      If state is "escalated": inform the user a human agent will follow up and collect their contact details.
```

---

## Pattern 4 — Turn Counter and Rate Limiting

**Use case:** Track how many messages a user has sent in a session and change behavior after a threshold (e.g., offer a human handoff after 10 unanswered questions).

### Conversation variable

```yaml
conversation_variables:
  - id: 'cv-count-0001'
    name: turn_count
    value_type: number
    value: 0
```

### Code node increments the counter

```yaml
- data:
    code: |
      def main(turn_count: int) -> dict:
          return {"new_count": turn_count + 1}
    code_language: python3
    inputs:
      - name: turn_count
        type: number
        variable_selector:
          - conversation
          - turn_count
    outputs:
      - name: new_count
        type: number
    title: Increment Turn Count
    type: code
  id: '1748300000040'
  ...
```

### variable-assigner writes the new count

```yaml
- data:
    assigned_variables:
      - variable_name: turn_count
        assigned_variable_selector:
          - '1748300000040'
          - new_count
    title: Update Turn Count
    type: variable-assigner
  id: '1748300000041'
  ...
```

### if-else gates on threshold

```yaml
- data:
    conditions:
      - comparison_operator: '>'
        id: threshold-check
        value: '10'
        variable_selector:
          - conversation
          - turn_count
    logical_operator: and
    title: Check Turn Limit
    type: if-else
  id: '1748300000042'
  ...
```

---

## Complete YAML — Language Preference Chatflow

A minimal but complete chatflow implementing Pattern 1:

```yaml
app:
  description: "Chatbot that detects and remembers the user's language preference."
  icon: "\U0001F310"
  icon_background: "#EEF4FF"
  mode: advanced-chat
  name: Language-Aware Chatbot
dependencies: []
features:
  file_upload:
    enabled: false
  opening_statement: "Hello! You can write to me in any language."
  speech_to_text:
    enabled: false
  suggested_questions: []
  suggested_questions_after_answer:
    enabled: false
  text_to_speech:
    enabled: false
kind: app
version: "0.1.0"
workflow:
  conversation_variables:
    - description: 'ISO 639-1 language code detected from user messages'
      id: 'cv-lang-0001-0000-000000000001'
      name: preferred_language
      value_type: string
      value: 'en'
  environment_variables: []
  graph:
    edges:
      - data:
          isInIteration: false
          sourceType: start
          targetType: parameter-extractor
        id: "1748300000001-source-1748300000002-target"
        source: "1748300000001"
        sourceHandle: source
        target: "1748300000002"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: parameter-extractor
          targetType: variable-assigner
        id: "1748300000002-source-1748300000003-target"
        source: "1748300000002"
        sourceHandle: source
        target: "1748300000003"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: variable-assigner
          targetType: llm
        id: "1748300000003-source-1748300000004-target"
        source: "1748300000003"
        sourceHandle: source
        target: "1748300000004"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: llm
          targetType: answer
        id: "1748300000004-source-1748300000005-target"
        source: "1748300000004"
        sourceHandle: source
        target: "1748300000005"
        targetHandle: target
        type: custom
        zIndex: 0
    nodes:
      - data:
          desc: ""
          title: Start
          type: start
          variables: []
        height: 54
        id: "1748300000001"
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
          desc: "Detect the language the user is writing in."
          model:
            completion_params:
              temperature: 0.0
            mode: chat
            name: gpt-4o-mini
            provider: openai
          parameters:
            - default: en
              description: >
                ISO 639-1 code for the language the user is writing in.
                Examples: en, fr, es, de, ja, zh. Default to en if unclear.
              name: language
              required: false
              type: string
          query:
            variable_selector:
              - "1748300000001"
              - sys.query
          reasoning_mode: function_call
          title: Detect Language
          type: parameter-extractor
        height: 90
        id: "1748300000002"
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
          assigned_variables:
            - variable_name: preferred_language
              assigned_variable_selector:
                - "1748300000002"
                - language
          desc: "Persist the detected language for this conversation."
          title: Save Language
          type: variable-assigner
        height: 54
        id: "1748300000003"
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

      - data:
          context:
            enabled: false
            variable_selector: []
          desc: "Respond in the user's preferred language."
          memory:
            enabled: true
            role_prefix:
              assistant: ''
              user: ''
            window:
              enabled: true
              size: 10
          model:
            completion_params:
              temperature: 0.7
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: lang-system-prompt
              role: system
              text: |
                You are a helpful assistant. Always respond in this language: {{#conversation.preferred_language#}}

                If the language code is "en", respond in English.
                If "fr", respond in French. If "es", respond in Spanish. Apply the same logic for all other codes.
            - id: lang-user-prompt
              role: user
              text: "{{#1748300000001.sys.query#}}"
          selected: false
          title: Respond
          type: llm
          vision:
            enabled: false
        height: 98
        id: "1748300000004"
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
          answer: "{{#1748300000004.text#}}"
          desc: ""
          title: Answer
          type: answer
        height: 54
        id: "1748300000005"
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

## Conversation Variable Lifecycle Summary

| Event | Effect on conversation variables |
|---|---|
| New conversation starts | All variables reset to declared `value` defaults |
| `variable-assigner` node executes | Updates the named variable(s) with the assigned values |
| Turn completes | Variables retain their current values for the next turn |
| User starts a new conversation | Variables reset again |
| Different user | Separate conversation_id — variables are fully isolated |

---

## Common Mistakes

1. **Forgetting to declare variables in `conversation_variables`.** The `variable-assigner` node cannot create variables at runtime. Every variable it writes must be declared in the `workflow.conversation_variables` array with a matching `name`.

2. **Using node output variable syntax for conversation variables.** Conversation variables use `{{#conversation.var_name#}}`. Node outputs use `{{#node_id.field#}}`. These are separate namespaces.

3. **Expecting variables to persist across conversations.** When a user starts a new conversation, all conversation variables reset to their defaults. For cross-session persistence, store values in an external database via an HTTP node.

4. **Using conversation variables in workflows (non-chat).** Conversation variables and the `variable-assigner` node are chatflow-only. In a standard workflow, pass values between nodes using direct variable references.

5. **Type mismatch on assignment.** If a variable is declared as `number` but the `variable-assigner` writes a `string` value, behavior depends on Dify's coercion — it may error silently. Match the assigned value type to the declared `value_type`.

6. **Relying only on LLM memory for state the graph needs to branch on.** Memory gives the LLM access to prior messages, but `if-else` and `code` nodes cannot read LLM memory — they can only read conversation variables and node outputs. If your graph needs to branch based on something extracted from an earlier turn, store it in a conversation variable.

See also:
- `skills/dify/references/nodes/variable-assigner.md` — full variable-assigner node reference
- `skills/dify/references/nodes/parameter-extractor.md` — extracting structured values from user messages
- `skills/dify/references/config/memory.md` — LLM conversation memory window configuration
- `skills/dify/references/nodes/if-else.md` — branching on conversation variable values
