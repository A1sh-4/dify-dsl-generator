# Agent Node

## Overview

The agent node runs an LLM in a tool-use loop where the model autonomously decides which tools to call, calls them, observes the results, and repeats until it has enough information to produce a final answer. Unlike a manual tool chain where the DSL specifies a fixed sequence of node calls, the agent node delegates that sequencing to the LLM at runtime — the model sees what it needs and decides what to call next.

The agent node exposes a single `text` output variable (the same interface as an LLM node), making it a drop-in replacement wherever you need tool-augmented generation.

Requires Dify **1.7.0 or later**. The agent node is itself a marketplace plugin (`langgenius/agent`) — it must be installed before the DSL can be imported.

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

## Node Type Reference

- **type**: `agent`
- **Minimum Dify version**: 1.7.0
- **Required fields**: `agent_parameters`, `agent_strategy_name`, `agent_strategy_provider_name`, `plugin_unique_identifier`, `tool_node_version`
- **Output variable**: `text` (string — the agent's final synthesized response)

## agent_parameters

All agent configuration lives inside the `agent_parameters` object. Every field uses a typed wrapper: `{type: constant, value: ...}` for fixed values or `{type: variable, value: [node_id, field]}` for values wired from upstream nodes.

### context (fully optional — omit entirely when not needed)

Wires the output of a knowledge-retrieval node into the agent's context window. **Only include this field when a knowledge-retrieval node is present in the flow and feeding the agent.** If the agent does not use a knowledge base, do not include the `context` key at all — not even as `null` or an empty block. Omitting it entirely is correct and has no side effects.

```yaml
context:
  type: variable
  value:
  - '[knowledge_retrieval_node_id]'
  - result
```

### instruction

The agent's system prompt. This is what the doc at `skills/dify/references/nodes/llm.md` calls `prompt_template[role=system]`, but for agent nodes it is a single string under `instruction`.

```yaml
instruction:
  type: constant
  value: |
    You are an expert research agent. When given a question:
    1. Search for relevant, up-to-date information using your tools
    2. Cross-reference multiple sources where possible
    3. Synthesize findings into a clear, structured answer
    4. Use markdown headings and bullet points for readability
    5. Be honest if information is uncertain or unavailable

    Always search before answering — do not rely solely on prior knowledge.
```

### maximum_iterations

Caps the number of tool-call cycles before the agent is forced to stop.

```yaml
maximum_iterations:
  type: constant
  value: 5
```

| Task Type | Recommended Value |
| --- | --- |
| Simple lookup / single fact | 3–5 |
| Multi-hop research | 8–12 |
| Complex analysis (compare, evaluate, synthesize) | 15–20 |

### model

```yaml
model:
  type: constant
  value:
    completion_params: {}
    mode: chat
    model: Claude-4-Sonnet
    model_type: llm
    provider: langgenius/openai_api_compatible/openai_api_compatible
    type: model-selector
```

Prefer models with strong function-calling support. Set `completion_params: {}` to use the model's defaults — the agent generates multiple responses per session (one per iteration) so letting the model manage its own parameters is usually correct.

### query

The user's input fed to the agent each turn. In chatflows always use the system query variable:

```yaml
query:
  type: constant
  value: '{{#sys.query#}}'
```

### tools

A list of tool configurations. Each tool must be `enabled: true`. The `parameters` block lists only the parameters that should be filled dynamically by the agent (set `auto: 1, value: null`). Fixed parameters go in `settings`.

The `schemas` array describes each parameter in detail (name, type, label, description, options). Dify populates this automatically when you add a tool in the UI — copy it verbatim from a real export rather than hand-crafting it.

```yaml
tools:
  type: constant
  value:
  - enabled: true
    extra:
      description: A tool for performing a Wikipedia search.
    parameters:
      query:
        auto: 1
        value: null
    provider_name: langgenius/wikipedia/wikipedia
    provider_show_name: langgenius/wikipedia/wikipedia
    schemas: [...]       # copy from a real Dify export — do not hand-craft
    settings: {}
    tool_description: A tool for performing a Wikipedia search and extracting snippets and webpages.
    tool_label: WikipediaSearch
    tool_name: wikipedia_search
    type: builtin
```

**Built-in tools** (no plugin install needed): `webscraper`, `time` (current_time)

**Plugin tools** (require marketplace install): `langgenius/wikipedia/wikipedia`, `langgenius/brave/brave`, `langgenius/duckduckgo/duckduckgo`

## Strategy

Controls the tool-use loop behavior.

```yaml
agent_strategy_label: FunctionCalling
agent_strategy_name: function_calling
agent_strategy_provider_name: langgenius/agent/agent
```

| agent_strategy_name | agent_strategy_label | Description |
| --- | --- | --- |
| `function_calling` | `FunctionCalling` | Uses the model's native function-calling API. Default — fastest and most reliable. |
| `react` | `ReAct` | Thought → Action → Observation loop. Use when step-by-step reasoning must be visible. |

## Memory (chatflow only)

```yaml
memory:
  query_prompt_template: '{{#sys.query#}}

    {{#sys.files#}}'
  window:
    enabled: false
    size: 50
```

Enable `window.enabled` to inject prior conversation turns into the agent's context. The `query_prompt_template` controls how the current user message is formatted for each iteration. The `{{#sys.files#}}` reference passes any uploaded files to the agent.

Best practice: enable memory (`window.enabled: true`) but do not set a specific window size — let Dify manage the context window automatically.

## Plugin Identifier

The agent node itself is a Dify marketplace plugin. The `plugin_unique_identifier` field pins the exact plugin version used:

```yaml
plugin_unique_identifier: langgenius/agent:0.0.37@a5dcc6ea00bca23439b49ff7d65704f3f5dd6ce2ca353205e62278e2148d84b6
```

This identifier is set automatically by Dify when you export a DSL. Copy it verbatim from a real export — do not construct it by hand.

```yaml
meta:
  minimum_dify_version: 1.7.0
  version: 0.0.2
output_schema: {}
tool_node_version: '2'
```

## Output Variables

| Variable | Type | Description |
| --- | --- | --- |
| `{{#agent_node_id.text#}}` | string | The agent's final synthesized answer after all tool calls complete |

Replace `agent_node_id` with the actual `id` of the agent node.

The `text` output is the agent's final response — the last message it generates after completing its tool-use loop. It does not include intermediate tool call results or reasoning steps (those are only visible in Dify's debug trace).

## Complete YAML Example

A research agent chatflow with knowledge retrieval context and three built-in tools. This matches the verified export at `skills/dify/assets/chatflows/agent-chatflow.yml`.

```yaml
- data:
    agent_parameters:
      context:
        type: variable
        value:
        - '[knowledge_retrieval_node_id]'
        - result
      instruction:
        type: constant
        value: 'You are an expert research agent. When given a question:
          1. Search for relevant, up-to-date information using your tools
          2. Cross-reference multiple sources where possible
          3. Synthesize findings into a clear, structured answer
          4. Use markdown headings and bullet points for readability
          5. Be honest if information is uncertain or unavailable

          Always search before answering — do not rely solely on prior knowledge.'
      maximum_iterations:
        type: constant
        value: 5
      model:
        type: constant
        value:
          completion_params: {}
          mode: chat
          model: Claude-4-Sonnet
          model_type: llm
          provider: langgenius/openai_api_compatible/openai_api_compatible
          type: model-selector
      query:
        type: constant
        value: '{{#sys.query#}}'
      tools:
        type: constant
        value:
        - enabled: true
          extra:
            description: A tool for scraping webpages.
          parameters:
            url:
              auto: 1
              value: null
          provider_name: webscraper
          provider_show_name: webscraper
          schemas: [...]   # copy from real export
          settings:
            generate_summary:
              value:
                type: constant
                value: 'false'
          tool_description: A tool for scraping webpages.
          tool_label: Web Scraper
          tool_name: webscraper
          type: builtin
        - enabled: true
          extra:
            description: A tool for performing a Wikipedia search.
          parameters:
            language:
              auto: 1
              value: null
            query:
              auto: 1
              value: null
          provider_name: langgenius/wikipedia/wikipedia
          provider_show_name: langgenius/wikipedia/wikipedia
          schemas: [...]   # copy from real export
          settings: {}
          tool_description: A tool for performing a Wikipedia search and extracting snippets and webpages.
          tool_label: WikipediaSearch
          tool_name: wikipedia_search
          type: builtin
    agent_strategy_label: FunctionCalling
    agent_strategy_name: function_calling
    agent_strategy_provider_name: langgenius/agent/agent
    memory:
      query_prompt_template: '{{#sys.query#}}


        {{#sys.files#}}'
      window:
        enabled: false
        size: 50
    meta:
      minimum_dify_version: 1.7.0
      version: 0.0.2
    output_schema: {}
    plugin_unique_identifier: langgenius/agent:0.0.37@a5dcc6ea00bca23439b49ff7d65704f3f5dd6ce2ca353205e62278e2148d84b6
    selected: false
    title: Agent
    tool_node_version: '2'
    type: agent
  height: 190
  id: '[13-digit-id]'
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

The downstream `answer` node references `{{#agent_node_id.text#}}` — not `.output` (that is the template-transform field). Agent nodes output via `.text`.

## Dependencies

If the flow uses plugin-based tools (e.g., Wikipedia, Brave), each plugin must appear in the top-level `dependencies` block:

```yaml
dependencies:
- current_identifier: null
  type: marketplace
  value:
    marketplace_plugin_unique_identifier: langgenius/wikipedia:0.0.5@[hash]
    version: null
```

The `marketplace_plugin_unique_identifier` format is `org/plugin:version@hash`. Copy this verbatim from a real Dify export — the hash is content-addressed and must be exact.

Built-in tools (`webscraper`, `time`) and the agent plugin itself (`langgenius/agent`) do not need a `dependencies` entry.

## Common Mistakes

- **Using the old field structure** (`agent_config`, `prompt`, `tools` at `data` top level). The current Dify agent node (v1.7+) wraps all config inside `agent_parameters`. The old structure will silently fail to load.
- **Hand-crafting the `schemas` array.** Each tool's `schemas` array describes its parameter signatures in full. These are complex and plugin-specific — always copy them from a real Dify export rather than writing them manually.
- **Including an empty `context` block when no knowledge retrieval is used.** If the flow has no knowledge-retrieval node, omit the `context` key entirely from `agent_parameters`. Do not set it to `null`, `{}`, or an empty value — just leave the key out.
- **Missing `plugin_unique_identifier`.** The agent node itself is a plugin. Without the correct `plugin_unique_identifier`, Dify cannot instantiate the node.
- **Referencing `.output` instead of `.text` in the downstream node.** Agent nodes output via `text`, not `output` (that field belongs to template-transform nodes).
- **Setting `window.enabled: true` with a fixed `size`.** Best practice is to enable memory without specifying a window size — let Dify manage context automatically.
- **Skipping the template-transform node.** Because the agent node already produces markdown-formatted prose via its instruction prompt, a template-transform node is optional for simple agent chatflows. The agent outputs directly to the `answer` node. Add a template-transform only if you need to apply additional HTML layout to the agent's response.
