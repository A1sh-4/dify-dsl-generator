# Variable Assigner Node

## Overview

The variable-assigner node updates conversation variables in chatflows, enabling persistent state across multiple conversation turns. It writes values to variables that were declared in the workflow's conversation variable settings, allowing the chatflow to remember information from one turn and act on it in a later turn.

This node is exclusively available in chatflows — it has no function in single-run workflows. In a workflow (non-chat), there are no conversation turns, so persistent state is irrelevant. The variable-assigner is the mechanism that makes chatflows stateful.

## Chatflow Only

Variable-assigner is not available in regular (non-chat) workflows. If you are building a workflow triggered by a webhook, HTTP call, or schedule, use the start node's output variables and pass them through the graph directly instead.

In chatflows, conversation variables persist for the lifetime of the conversation session. They reset when the user starts a new conversation.

## Purpose

Without variable-assigner, every turn of a chatflow starts fresh — previous context exists only in the chat history, which the LLM may or may not use effectively. With variable-assigner, you can explicitly store and retrieve values that the workflow logic (not just the LLM) can act on:

- Remember the user's preferred language after they state it
- Track conversation state (e.g., which step of a multi-step process the user is on)
- Count interactions or accumulate data across turns
- Cache a retrieved value (e.g., user account ID) so you do not look it up on every turn
- Build forms that collect information across multiple messages

## Conversation Variable Types

The following types can be stored in conversation variables:

| Type | Description |
|------|-------------|
| `string` | Text value |
| `number` | Integer or float |
| `boolean` | True or false |
| `object` | JSON object / dictionary |
| `array` | List of values |
| `file` | File reference |

Variables must be declared in the chatflow's conversation variable settings before they can be assigned. The variable-assigner node cannot create new variables at runtime — it can only update variables that already exist.

## Multiple Assignments in One Node

A single variable-assigner node can update multiple conversation variables in one operation. You do not need a separate node per variable:

```yaml
assigned_variables:
  - variable_name: preferred_language
    assigned_variable_selector:
      - parameter_extractor
      - language
  - variable_name: user_name
    assigned_variable_selector:
      - parameter_extractor
      - name
  - variable_name: turn_count
    assigned_variable_selector:
      - increment_node
      - result
```

## Variable Lifecycle

Conversation variables are initialized to their default values (as configured in the chatflow settings) at the start of each new conversation. They persist and can be updated by variable-assigner nodes throughout the conversation. When the conversation session ends (user starts a new chat), all conversation variables reset to their defaults.

They do not persist across different users, different sessions, or different conversations. For cross-session persistence, you would need to store values in an external database via an HTTP node.

## Complete YAML Example

This example detects the user's preferred language from their first message and stores it, then uses it in all subsequent turns:

```yaml
nodes:
  - id: start
    type: start
    data:
      variables:
        - variable: user_message
          type: string

  - id: detect_language
    type: parameter-extractor
    data:
      title: Detect Language Preference
      query:
        variable_selector:
          - start
          - user_message
      model:
        provider: openai
        name: gpt-4o-mini
        mode: chat
      reasoning_mode: function_call
      parameters:
        - name: language
          type: string
          description: >
            The language the user is writing in, as an ISO 639-1 code
            (e.g., "en" for English, "fr" for French, "es" for Spanish).
          required: false
          default: en

  - id: store_language
    type: variable-assigner
    data:
      title: Store User Language
      assigned_variables:
        - variable_name: preferred_language
          assigned_variable_selector:
            - detect_language
            - language

  - id: respond
    type: llm
    data:
      title: Respond in User Language
      prompt_template:
        - role: system
          text: |
            You are a helpful assistant. Always respond in the language
            indicated by this language code: {{#conversation.preferred_language#}}
        - role: user
          text: "{{#start.user_message#}}"

  - id: answer
    type: answer
    data:
      answer: "{{#respond.text#}}"

edges:
  - source: start
    target: detect_language
  - source: detect_language
    target: store_language
  - source: store_language
    target: respond
  - source: respond
    target: answer
```

## Accessing Conversation Variables

After being set by variable-assigner, conversation variables are accessed using the `conversation` namespace:

```
{{#conversation.variable_name#}}
```

This reference works in any node that accepts variable references — LLM prompts, template-transform templates, if-else conditions, etc.

## Pattern: Track Conversation State

Use a conversation variable to implement a multi-step flow where the chatflow knows which step the user is on:

```yaml
- id: update_step
  type: variable-assigner
  data:
    assigned_variables:
      - variable_name: current_step
        assigned_variable_selector:
          - step_logic
          - next_step
```

Then use an if-else node at the start of each turn to check `{{#conversation.current_step#}}` and route to the appropriate handler.

## Pattern: Remember User Preferences

```yaml
- id: save_preferences
  type: variable-assigner
  data:
    assigned_variables:
      - variable_name: preferred_language
        assigned_variable_selector:
          - extract_prefs
          - language
      - variable_name: response_format
        assigned_variable_selector:
          - extract_prefs
          - format
```

## Common Mistakes

1. **Using variable-assigner in a workflow instead of a chatflow.** This node does nothing in a non-chat workflow — there are no conversation variables to update. If you need to pass values between nodes in a workflow, use direct variable references.

2. **Trying to assign a variable that was not declared in settings.** The variable-assigner can only update variables declared in the chatflow's conversation variable configuration. You cannot dynamically create new variables at runtime.

3. **Confusing conversation variables with node output variables.** Conversation variables are accessed as `{{#conversation.var_name#}}`. Node outputs are accessed as `{{#node_id.field#}}`. These are separate namespaces.

4. **Expecting conversation variables to persist across sessions.** Variables reset at the start of each new conversation. Do not use them as a long-term user profile store. For persistence, write to an external database.

5. **Assigning the wrong type.** If a conversation variable is declared as `number` but you assign a string to it, behavior depends on Dify's type coercion — it may error or silently fail. Always match the assigned value type to the declared variable type.
