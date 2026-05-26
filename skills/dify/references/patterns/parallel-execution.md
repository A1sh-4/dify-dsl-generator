# Parallel Execution Pattern

## Overview

Dify can execute multiple nodes simultaneously when they have no data dependency on each other. Understanding when Dify runs nodes in parallel — and how to design flows that take advantage of this — is critical for building high-performance pipelines that minimize end-to-end latency.

---

## When Dify Runs Nodes in Parallel

Dify's execution engine analyzes the graph and runs nodes in parallel automatically when both conditions are met:

1. **Multiple nodes are ready to execute** — their input dependencies are all satisfied
2. **Those nodes do not depend on each other's output**

This happens most commonly in the **fan-out / fan-in pattern**: a single upstream node completes, and its output edge triggers multiple independent downstream nodes simultaneously.

### What Is NOT Parallel

- **If-else branches** are conditional, not parallel. When an `if-else` node evaluates, only one branch executes — either `true` or `false`. Both branches never run at the same time.
- **Sequential chains** where node B uses output from node A are always sequential by definition.
- **Retry attempts** run sequentially, not in parallel.

---

## Parallel Iteration

The `iteration` node has a `parallel_num` field that enables parallel processing of items in an array.

```yaml
data:
  type: iteration
  iterator_selector:
    - "start_node_id"
    - items_list
  output_selector:
    - "inner_llm_node_id"
    - text
  parallel_mode: true
  parallel_num: 5     # process up to 5 items simultaneously (max: 10)
```

**Use parallel iteration when:**

- Processing a list of files, URLs, or records with the same pipeline
- Running LLM calls over multiple items (e.g., translate 20 product descriptions)
- Making batch API requests where each item is independent

**Warning:** Parallel iteration with `parallel_num: 10` on a 100-item list runs 10 simultaneous LLM calls per batch. This can cause rate-limit errors on model providers with strict per-minute token limits. Set `parallel_num` conservatively (3–5) unless you have verified your model provider's rate limits.

---

## Fan-Out / Fan-In Pattern

This is the primary pattern for parallelism in Dify:

```text
         ┌── Node A (branch 1) ──┐
Source ──┤                       ├── Convergence Node ── Downstream
         └── Node B (branch 2) ──┘
```

**Fan-out:** A single source node has multiple outgoing edges, each targeting a different node. Both target nodes start executing simultaneously as soon as the source completes.

**Fan-in (convergence):** Any node with multiple incoming edges automatically waits for ALL of those upstream nodes to complete before executing. This is Dify's built-in synchronization — no special configuration is required. The convergence node choice depends on what the branches produce:

| Branches produce | Convergence node | Why |
| --- | --- | --- |
| The **same type of data** to be merged into one combined value (e.g., two search results concatenated into one string) | `variable-aggregator` | Merges multiple values of the same type into a single output variable |
| **Different named outputs**, each rendered as its own section (e.g., action items, decisions, risks from parallel LLM extractions) | `template-transform` directly (no aggregator) | The template already binds each branch output as a separate named variable — no merging needed |

**The most common mistake:** inserting a `variable-aggregator` between focused parallel LLM nodes and a `template-transform`. When each LLM produces a distinct output (action_items, decisions, risks), the template-transform binds them as separate named variables and renders each independently. A variable-aggregator would try to merge them into one value, which is wrong and wasteful.

---

## Example: Parallel Web Search + Scrape

### Node Graph

```text
start ──┬── brave_search (Tool) ──┐
        │                         ├── variable-aggregator ── llm ── end
        └── jina_reader  (Tool) ──┘
```

Both the search and scrape tools execute simultaneously after `start`. The aggregator waits for both, then the LLM synthesizes the combined output.

### Positioning

| Node | x | y | Notes |
|------|---|---|-------|
| start | 80 | 282 | Center |
| brave_search | 380 | 132 | y = 282 - 150 (upper branch) |
| jina_reader | 380 | 432 | y = 282 + 150 (lower branch) |
| variable-aggregator | 680 | 282 | Back to center y |
| llm | 980 | 282 | Continue center |
| end | 1280 | 282 | Continue center |

### Complete YAML — Parallel Search + Scrape Workflow

```yaml
app:
  description: "Runs web search and URL scraping in parallel, then synthesizes results."
  icon: "\U000026A1"
  icon_background: "#E3F2FD"
  mode: workflow
  name: Parallel Search and Scrape
dependencies:
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/brave:0.0.3/brave"
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/jina:0.0.2/jina"
features: {}
kind: app
version: "0.1.0"
workflow:
  conversation_variables: []
  environment_variables: []
  graph:
    edges:
      # start → brave_search (upper branch)
      - data:
          isInIteration: false
          sourceType: start
          targetType: tool
        id: "1747300000001-source-1747300000002-target"
        source: "1747300000001"
        sourceHandle: source
        target: "1747300000002"
        targetHandle: target
        type: custom
        zIndex: 0

      # start → jina_reader (lower branch — same sourceHandle "source")
      - data:
          isInIteration: false
          sourceType: start
          targetType: tool
        id: "1747300000001-source-1747300000003-target"
        source: "1747300000001"
        sourceHandle: source
        target: "1747300000003"
        targetHandle: target
        type: custom
        zIndex: 0

      # brave_search → variable-aggregator (fan-in)
      - data:
          isInIteration: false
          sourceType: tool
          targetType: variable-aggregator
        id: "1747300000002-source-1747300000004-target"
        source: "1747300000002"
        sourceHandle: source
        target: "1747300000004"
        targetHandle: target
        type: custom
        zIndex: 0

      # jina_reader → variable-aggregator (fan-in)
      - data:
          isInIteration: false
          sourceType: tool
          targetType: variable-aggregator
        id: "1747300000003-source-1747300000004-target"
        source: "1747300000003"
        sourceHandle: source
        target: "1747300000004"
        targetHandle: target
        type: custom
        zIndex: 0

      # variable-aggregator → llm
      - data:
          isInIteration: false
          sourceType: variable-aggregator
          targetType: llm
        id: "1747300000004-source-1747300000005-target"
        source: "1747300000004"
        sourceHandle: source
        target: "1747300000005"
        targetHandle: target
        type: custom
        zIndex: 0

      # llm → end
      - data:
          isInIteration: false
          sourceType: llm
          targetType: end
        id: "1747300000005-source-1747300000006-target"
        source: "1747300000005"
        sourceHandle: source
        target: "1747300000006"
        targetHandle: target
        type: custom
        zIndex: 0

    nodes:
      - data:
          desc: ""
          title: Start
          type: start
          variables:
            - label: Search Query
              max_length: 500
              options: []
              required: true
              type: text-input
              variable: search_query
            - label: URL to Scrape
              max_length: 2048
              options: []
              required: true
              type: text-input
              variable: url
        height: 90
        id: "1747300000001"
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

      # Upper branch: web search
      - data:
          desc: "Search the web for current information."
          provider_id: langgenius/brave/brave
          provider_name: Brave Search
          provider_type: builtin
          title: Web Search
          tool_configurations:
            count: 5
          tool_name: brave_search
          tool_parameters:
            query:
              type: mixed
              value: "{{#1747300000001.search_query#}}"
          type: tool
        height: 90
        id: "1747300000002"
        position:
          x: 380
          y: 132
        positionAbsolute:
          x: 380
          y: 132
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      # Lower branch: URL scraping
      - data:
          desc: "Extract full text content from a URL."
          provider_id: langgenius/jina/jina
          provider_name: Jina Reader
          provider_type: builtin
          title: Web Scraper
          tool_configurations: {}
          tool_name: jina_reader
          tool_parameters:
            url:
              type: mixed
              value: "{{#1747300000001.url#}}"
          type: tool
        height: 90
        id: "1747300000003"
        position:
          x: 380
          y: 432
        positionAbsolute:
          x: 380
          y: 432
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      # Fan-in: aggregate both parallel outputs
      - data:
          advanced_settings:
            group_enabled: false
          desc: "Collect outputs from both parallel branches."
          output_type: string
          title: Combine Results
          type: variable-aggregator
          variables:
            - label: search_results
              variable_selector:
                - "1747300000002"
                - text
            - label: scraped_content
              variable_selector:
                - "1747300000003"
                - text
        height: 90
        id: "1747300000004"
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
          desc: "Synthesize search results and scraped content into a final answer."
          model:
            completion_params:
              max_tokens: 2048
              temperature: 0.3
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: synth-system
              role: system
              text: |
                You are a research analyst. You have two sources of information:

                ## Web Search Results
                {{#1747300000002.text#}}

                ## Scraped Web Page Content
                {{#1747300000003.text#}}

                Synthesize both sources into a comprehensive, accurate answer. Note any contradictions between sources. Cite where information came from.
            - id: synth-user
              role: user
              text: "Synthesize the information for: {{#1747300000001.search_query#}}"
          title: Synthesis LLM
          type: llm
          vision:
            enabled: false
        height: 98
        id: "1747300000005"
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
            - label: Synthesis
              name: synthesis
              type: string
              value_selector:
                - "1747300000005"
                - text
          title: End
          type: end
        height: 54
        id: "1747300000006"
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

## Shared Variable Limitation

Parallel branches cannot write to the same conversation variable simultaneously. Dify does not have a locking mechanism for concurrent writes. If two branches both try to append to the same conversation variable, the result is undefined (one write will be lost).

**Safe pattern:** Each parallel branch writes to its own output variable. The `variable-aggregator` merges them after all branches complete.

**Unsafe pattern (do not do this):** Both parallel branches update `conversation_variable.shared_log` — only the last one to complete will persist.

---

## When NOT to Use Parallel Execution

- **Sequential dependency:** Branch B requires output from Branch A. Dify cannot start B until A completes — there is no real parallelism here, just a sequential chain. Do not fan out if branches are dependent.
- **Shared external state:** If both branches write to the same external resource (same database row, same file), you will have a race condition. Add a synchronization step (code node or variable-aggregator) before accessing shared state.
- **Rate-limited tools:** If both branches call the same API with a strict rate limit, parallel execution may cause `429 Too Many Requests` errors. Add error-handling retry logic or serialize the calls.

---

## Edge Note: Fan-Out Edges

Both fan-out edges from `start` use `sourceHandle: source`. This is correct — the same `source` handle can have multiple outgoing edges. Dify interprets multiple edges from the same source handle (when the source is not an if-else node) as parallel fan-out.

```yaml
# Both edges from the same source node, same sourceHandle — valid fan-out
- source: "1747300000001"
  sourceHandle: source
  target: "1747300000002"
  ...
- source: "1747300000001"
  sourceHandle: source
  target: "1747300000003"
  ...
```

---

## Pattern: Parallel Multi-Section Extraction (No Variable-Aggregator)

This is the most common real-world parallel pattern and the one most often implemented incorrectly as a single sequential LLM.

**Use case:** The user wants to extract or analyze multiple independent sections from one input document — meeting notes, a customer review, a research paper, a support ticket. Each section (action items, decisions, risks, sentiment, topics, etc.) is logically independent of the others. They all read from the same source and none depends on another's output.

**Wrong design (slow, serial):**

```text
start → llm (extracts everything in one prompt) → template-transform → answer
```

This forces the LLM to do all work in one call, produces a larger, harder-to-control prompt, and takes as long as all the work combined.

**Correct design (fast, parallel):**

```text
start ──┬── llm (section A) ──┐
        ├── llm (section B) ──┤
        ├── llm (section C) ──┼── template-transform → answer
        └── llm (section D) ──┘
```

All four LLMs run simultaneously. The template-transform waits for all four, then renders the combined dashboard. No `variable-aggregator` is needed — the template binds each LLM's output as a separate named variable.

### Node count formula

For N independent sections: `1 (start) + N (parallel LLMs) + 1 (template-transform) + 1 (answer) = N + 3 nodes`

A 4-section dashboard needs 7 nodes total. A 3-section report needs 6 nodes.

### Canvas positioning for parallel LLMs

Source (start) and convergence (template-transform) nodes stay at y=282. Parallel LLM nodes are distributed vertically:

| N | y values for parallel LLM nodes |
| --- | --- |
| 2 | 97, 467 |
| 3 | 97, 282, 467 |
| 4 | 80, 260, 440, 620 |

x increments +300 per column as usual.

### Variable wiring in template-transform

Each parallel LLM uses `structured_output_enabled: true` with a focused schema for its one section. The template-transform binds each LLM's `output` field as a separately named variable:

```yaml
variables:
  - value_selector: ['llm_section_a_id', 'output']
    variable: section_a
  - value_selector: ['llm_section_b_id', 'output']
    variable: section_b
  - value_selector: ['llm_section_c_id', 'output']
    variable: section_c
  - value_selector: ['llm_section_d_id', 'output']
    variable: section_d
```

The Jinja2 template then renders each section independently:

```jinja2
{% if section_a.items and section_a.items|length > 0 %}
<div class="section-a">...</div>
{% endif %}

{% if section_b.results and section_b.results|length > 0 %}
<div class="section-b">...</div>
{% endif %}
```

### Prompt design for focused parallel LLMs

Each LLM's system prompt must be tightly scoped. The prompt for section A should say explicitly: "Extract ONLY [section A content]. Do not extract [section B], [section C], or [section D] — those are handled separately." This prevents the model from bleeding content across categories and keeps each output clean and focused.

### When to use this pattern

Use parallel multi-section extraction whenever the requirements describe ANY of these:

- "Extract X, Y, Z from the same document"
- "Analyze [topic] from multiple angles"
- "Generate a report with sections A, B, C"
- "Produce a dashboard showing [thing 1], [thing 2], [thing 3]"
- "Check for [issue type A] and [issue type B] separately"

The word "and" in a list of output sections is almost always a signal that those sections should be parallel branches, not sequential LLM calls.

---

See also:

- `skills/dify/references/nodes/variable-aggregator.md` — fan-in node reference
- `skills/dify/references/nodes/iteration.md` — parallel iteration configuration
- `skills/dify/references/patterns/error-handling.md` — handling failures in parallel branches
- `skills/dify/references/schema/edge-types.md` — edge sourceHandle reference
