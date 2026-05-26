# Agent Node

## Overview

The agent node runs an LLM in a tool-use loop where the model autonomously decides which tools to call, calls them, observes the results, and repeats until it has enough information to produce a final answer. Unlike a manual tool chain where the DSL specifies a fixed sequence of node calls, the agent node delegates that sequencing to the LLM at runtime — the model sees what it needs and decides what to call next.

The agent node exposes a single `text` output variable (the same interface as an LLM node), making it a drop-in replacement wherever you need tool-augmented generation.

## When to Use

Use the agent node when:

- The task is open-ended and the tools needed depend on the specific query
- The number of tool calls required is unpredictable (may need 1 call or 10)
- You want the LLM to adapt its research strategy based on intermediate results
- The use case is exploratory: web research, multi-source lookup, code debugging

Do NOT use the agent node when:

- You always call the same tools in the same order — use manual tool nodes instead (cheaper, faster, deterministic)
- Only one tool call is ever needed — a single `tool` node is sufficient and has no agent overhead
- The flow is compliance-critical and must be fully auditable — agent paths are non-deterministic
- Token cost is a primary constraint — each tool-call cycle incurs an additional LLM call

See `skills/dify/references/patterns/agentic-pattern.md` for a detailed comparison with manual tool chains.

## Node Type Reference

- **type**: `agent`
- **Execution Type**: EXECUTABLE
- **Required fields**: `type`, `title`, `model`, `prompt`, `tools`, `agent_config`
- **Output variable**: `text` (string — the agent's final synthesized response)

## agent_config

Controls the tool-use loop behavior.

```yaml
agent_config:
  max_iterations: 5
  strategy: function_call
```

### strategy

| Value | Description | When to Use |
|---|---|---|
| `function_call` | Uses the model's native function-calling API (OpenAI tool_use, Claude tool_use, etc.). The model outputs structured JSON per tool call. | Default — fastest and most reliable; works with all major function-calling models |
| `react` | ReAct loop: the model outputs `Thought:` → `Action:` → `Observation:` at each step. Intermediate reasoning is visible in the output. | When you need auditable step-by-step reasoning; complex multi-hop research |
| `cot` | Chain-of-thought: the model reasons through the full problem before choosing a tool. | Structured problem-solving tasks (math, code debugging, legal analysis) |

### max_iterations

Caps the number of tool-call cycles before the agent is forced to stop and return whatever it has.

| Task Type | Recommended Value |
|---|---|
| Simple lookup / single fact | 3–5 |
| Multi-hop research (cross-referencing sources) | 8–12 |
| Complex analysis (compare, evaluate, synthesize) | 15–20 |

Setting this too low causes the agent to return an incomplete answer. Setting it too high increases latency and cost for simple tasks. Start with 5 and tune based on observed behavior.

## model

Identical structure to the LLM node's `model` field. See `skills/dify/references/nodes/llm.md` for full field reference. For agent nodes, prefer:

- A model with strong function-calling support (GPT-4o, claude-3-5-sonnet, gemini-1.5-pro)
- Higher `max_tokens` than a typical LLM node — the agent generates multiple responses (one per iteration)
- Moderate temperature (0.3–0.5) — lower than creative tasks, higher than pure extraction

```yaml
model:
  completion_params:
    max_tokens: 4096
    temperature: 0.4
  mode: chat
  name: gpt-4o
  provider: openai
```

## prompt

The agent's system prompt. Uses the same structure as an LLM node but the field is named `prompt` (not `prompt_template`).

```yaml
prompt:
  - id: agent-system-unique-id
    role: system
    text: |
      You are a research assistant. Your goal: [specific, measurable goal].

      Available tools:
      - tool_name_1: [what it does]. Input: [expected input format].
      - tool_name_2: [what it does]. Input: [expected input format].

      Instructions:
      1. [Step-by-step strategy]
      2. [How to use results from one tool to inform the next call]
      3. [Stopping condition — when do you have enough?]

      Query: {{#start.user_query#}}
```

**System prompt rules for agent nodes:**

- Name each tool with its exact Dify tool identifier (the `tool_name` value from the tools array)
- Describe the input format each tool expects — the model uses this to form correct tool calls
- Give the model a clear stopping condition — "stop when you have enough information to answer confidently" prevents over-searching
- Do not mention tools that are not wired in the `tools` array — the model will attempt to call them and fail

Only `system` role is used in the prompt for agent nodes. Unlike LLM nodes, you do not add a separate `user` role entry — the current user message is automatically appended by Dify.

## tools

An array of tool configurations. Each entry wires one tool into the agent's available tool set.

```yaml
tools:
  - provider_id: langgenius/brave/brave
    provider_name: Brave Search
    provider_type: builtin
    tool_name: brave_search
    tool_parameters:
      count: 5
      query:
        type: mixed
        value: ""
    tool_label: Brave Search
```

### Tool field reference

| Field | Description |
|---|---|
| `provider_id` | Full provider path in the format `org/plugin-name/provider-name`. Find this in the plugin's manifest. |
| `provider_name` | Human-readable name of the plugin/provider. Used for display only. |
| `provider_type` | Always `builtin` for Dify marketplace plugins. Use `api` for custom API tools. |
| `tool_name` | The exact tool function name within the plugin. Must match what the plugin exposes. |
| `tool_parameters` | Key-value pairs of the tool's parameters. For parameters the agent should fill dynamically, use `type: mixed, value: ""`. For fixed parameters (e.g., `count: 5`), set them directly. |
| `tool_label` | Display label shown in the Dify canvas. Any string. |

### tool_parameters value types

| type | value | Meaning |
|---|---|---|
| `mixed` | `""` | Agent fills this parameter dynamically at runtime |
| `constant` | `"some value"` | Fixed value — always passed as-is, agent cannot override |

For the primary input parameter of a search or fetch tool (the query or URL), always set `type: mixed, value: ""` so the agent can supply the appropriate value per call.

### Common tools

| Tool | provider_id | tool_name | Primary parameter |
|---|---|---|---|
| Brave Search | `langgenius/brave/brave` | `brave_search` | `query` |
| Jina Reader (URL→text) | `langgenius/jina/jina` | `jina_reader` | `url` |
| Wikipedia | `langgenius/wikipedia/wikipedia` | `wikipedia_search` | `query` |
| DuckDuckGo | `langgenius/duckduckgo/duckduckgo` | `ddg_search` | `query` |
| GitHub | `langgenius/github/github` | `get_repository` | `repo` |

Check `skills/dify/references/features/plugins-marketplace.md` for the current full list and exact identifiers.

## Output Variables

| Variable | Type | Description |
|---|---|---|
| `{{#agent_node_id.text#}}` | string | The agent's final synthesized answer after all tool calls complete |

The `text` output is the agent's final response — the last message it generates after completing its tool-use loop. It does not include intermediate tool call results or reasoning steps (those are only visible in Dify's debug trace).

Replace `agent_node_id` with the actual `id` of the agent node.

## Memory (chatflow only)

Agent nodes in chatflows support conversation memory identically to LLM nodes. Add the same `memory` block:

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

Memory injects prior conversation turns into the agent's context before the tool-use loop begins.

## Complete YAML Example

A single-tool research agent in a chatflow:

```yaml
- data:
    agent_config:
      max_iterations: 8
      strategy: function_call
    desc: "Search the web to answer the user's question."
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
        max_tokens: 4096
        temperature: 0.4
      mode: chat
      name: gpt-4o
      provider: openai
    prompt:
      - id: research-agent-system
        role: system
        text: |
          You are a research assistant. Your goal: find accurate, up-to-date information
          to answer the user's question.

          Available tools:
          - brave_search: Search the web for current information. Input: a search query string.
          - jina_reader: Extract full text from a URL. Input: a URL string.

          Instructions:
          1. Start with a targeted search query based on the user's question
          2. If the top results look relevant, use jina_reader to get the full content from the best URL
          3. If the first search is insufficient, refine the query and search again
          4. Stop when you have enough information to give a confident, complete answer
          5. Synthesize findings into a clear, direct response

          User question: {{#start.sys.query#}}
    title: Research Agent
    tools:
      - provider_id: langgenius/brave/brave
        provider_name: Brave Search
        provider_type: builtin
        tool_name: brave_search
        tool_parameters:
          count: 5
          query:
            type: mixed
            value: ""
        tool_label: Brave Search
      - provider_id: langgenius/jina/jina
        provider_name: Jina Reader
        provider_type: builtin
        tool_name: jina_reader
        tool_parameters:
          url:
            type: mixed
            value: ""
        tool_label: Jina Reader
    type: agent
  height: 98
  id: '1748200000001'
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
```

## Dependencies

Any Dify marketplace plugin used in the `tools` array must be declared in the top-level `dependencies` block of the DSL file:

```yaml
dependencies:
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/brave:0.0.3/brave"
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/jina:0.0.2/jina"
```

The `marketplace_plugin_unique_identifier` format is `org/plugin:version/provider`. The version number is part of the identifier — check the plugin's current version in the Dify marketplace before generating.

If a plugin is wired in `tools` but missing from `dependencies`, Dify will fail to import the DSL.

## Common Mistakes

- **Using `prompt_template` instead of `prompt`.** Agent nodes use the key `prompt`, not `prompt_template`. Using the wrong key causes the system prompt to be silently ignored.
- **Missing plugin in `dependencies`.** Every plugin referenced in `tools` must have a matching entry in the top-level `dependencies` block. Validate this before writing the DSL.
- **Wrong `provider_id` format.** The format is `org/plugin-name/provider-name` (three parts, slash-separated). Do not use the marketplace identifier format (`org/plugin:version/provider`) in the `tools` array — that format belongs in `dependencies` only.
- **Not setting `type: mixed` on dynamic parameters.** If the agent's primary input parameter (`query`, `url`, etc.) is set to `type: constant`, the agent cannot change the value per call — it always passes the fixed `value`. Always use `type: mixed, value: ""` for parameters the agent should fill.
- **Setting `max_iterations` too low.** An agent that hits its iteration limit returns a partial answer without warning. For multi-hop research tasks, start with at least 8 iterations.
- **Choosing `react` strategy with a weak model.** The `react` strategy requires the model to reliably follow the Thought/Action/Observation format. Small or instruction-following-weak models often break the format. Use `function_call` for all but the strongest models.
- **Not declaring `memory` in chatflow agents.** In a chatflow, an agent node without `memory` configured treats every turn as a fresh start with no conversation history. Always include the `memory` block in chatflow agents, even if `enabled: false` is intentional.
