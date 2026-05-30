# Loop Node

## Overview

The loop node repeats a contained sub-workflow until a termination condition becomes true or the maximum cycle count is reached. Unlike the iteration node, the loop is **stateful** — variables declared in `loop_variables` persist from one cycle to the next, allowing each cycle to build on the previous result. This makes the loop node the right choice for refinement, optimization, and quality-checking patterns where the number of cycles is not known in advance.

The loop node is always sequential. Every cycle completes before the next one begins. This is intentional: each cycle's output influences the next cycle's input through the persisted loop variables.

---

## When to Use

**Use loop when:**
- The result of cycle N feeds into cycle N+1 — stateful refinement (write output back to a loop variable)
- You do not have an array to iterate over; the loop continues until a condition is met
- You are implementing a quality gate: generate → evaluate → refine until score exceeds a threshold
- You want iterative RAG: retrieve → check if context is sufficient → loop again with a refined query if not

**Do NOT use loop when:**
- You have a fixed array of items to process — use `iteration` instead
- Each item is processed independently with no state carried between items — use `iteration`
- You need parallel processing — loop is always sequential; iteration supports parallelism

---

## Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ✅ | Always `loop` |
| `start_node_id` | string | ✅ | ID of the `loop-start` node inside the container (format: `{loop_node_id}start`) |
| `loop_count` | integer | ✅ | Maximum number of cycles before the loop exits regardless of break conditions. Default: 10. Upper limit controlled by the `LOOP_NODE_MAX_COUNT` environment variable on the Dify server. |
| `loop_variables` | array | ✅ | Variables that persist across cycles. Each cycle can read and update them. Accessible both inside the loop and after it completes. |
| `break_conditions` | array | ✅ | One or more conditions that trigger early exit. The loop exits as soon as any condition evaluates true (or all conditions if `logical_operator: and`). |
| `logical_operator` | string | ✅ | `and` — all break conditions must be true to exit. `or` — any single condition triggers exit. |
| `error_handle_mode` | string | — | How to handle node failures inside the loop: `terminated` (stop the workflow), `continue` (skip the failed node), or `remove_abnormal_output` |

### `loop_variables` Item Schema

```yaml
# Constant initial value (most common):
loop_variables:
  - id: "uuid-string"          # Unique ID for this variable
    label: "variable_name"     # Name used to reference it: {loop_node_id}.variable_name
    var_type: number            # Type: number | string | array[string] | array[object]
    value_type: constant        # "constant" — use a literal initial value
    value: "0"                  # Initial value (always a string, even for numbers)

# Initialized from an upstream node's output:
loop_variables:
  - id: "uuid-string"
    label: "search_word"
    var_type: string
    value_type: variable        # "variable" — initialize from a node output
    value:                      # value is a selector list when value_type is variable
      - "{upstream_node_id}"
      - output_field_name
```

`break_conditions: []` (empty array) is valid — the loop simply runs `loop_count` times with no early exit.

### `break_conditions` Item Schema

```yaml
break_conditions:
  - id: "uuid-string"
    varType: string             # Type of the variable being tested
    variable_selector:          # Which variable to test
      - "{loop_node_id}"        # Reference the loop node's ID
      - variable_name           # Name of the loop variable
    comparison_operator: "is"   # See operator table below
    value: "yes"                # Value to compare against
```

**Comparison operators for break conditions:**

| Operator | Meaning | Works With |
|----------|---------|------------|
| `=` | Equal (numeric) | number |
| `≠` | Not equal (numeric) | number |
| `>` | Greater than | number |
| `<` | Less than | number |
| `≥` | Greater than or equal | number |
| `≤` | Less than or equal | number |
| `is` | Exact match | string |
| `is not` | Does not match | string |
| `contains` | Substring match | string |
| `not contains` | No substring match | string |
| `empty` | Variable is empty | string, array |
| `not empty` | Variable is not empty | string, array |

---

## Loop Variables: Read and Write

Loop variables are declared in `loop_variables` on the loop container node. They are accessible anywhere in the workflow using the loop node's ID as the scope:

- **Inside the loop** (any inner node): `{{#loop_node_id.variable_name#}}`
- **Outside the loop** (any downstream node after the loop exits): `{{#loop_node_id.variable_name#}}`

### Supported `operation` values in variable-assigner

| Operation | Behaviour | Use case |
| --- | --- | --- |
| `over-write` | Replaces the current value entirely | Storing a verdict, updating a search term |
| `extend` | Appends items to an `array` loop variable | Accumulating KR results across cycles |
| `+=` | Numeric increment | Counters |

**Accumulating results with `extend`:**

```yaml
items:
  - variable_selector:
      - "{loop_node_id}"
      - knowledge                # array[object] loop variable
    operation: extend            # appends — does NOT overwrite previous cycles
    input_type: variable
    value:
      - "{kr_node_id}"
      - result                   # KR result array for this cycle
    write_mode: over-write
```

Use `extend` when you want to build up a growing array of retrieved chunks across iterations rather than replacing the previous cycle's results.

**Updating a string loop variable from a node output:**

```yaml
items:
  - variable_selector:
      - "{loop_node_id}"
      - search_word
    operation: over-write
    input_type: variable
    value:
      - "{inner_llm_node_id}"
      - structured_output        # top-level output field
      - search_word              # nested field inside structured output
    write_mode: over-write
```

**Accessing a loop variable outside the loop** — after the loop exits, read it like any node output:

```yaml
# In a code node downstream of the loop:
variables:
  - value_selector:
      - "{loop_node_id}"
      - knowledge
    value_type: array[object]
    variable: knowledge_results
```

---

## Termination

There are **two independent methods** to exit a loop early. You can use one or both.

### Method 1 — `break_conditions` on the loop container

Declare conditions directly on the loop node. After each cycle completes, Dify evaluates all break conditions. If the condition is true, the loop exits before starting the next cycle.

```yaml
break_conditions:
  - comparison_operator: "is"
    id: "uuid"
    value: "yes"
    varType: string
    variable_selector:
      - "{loop_node_id}"
      - is_sufficient            # must be a loop variable
```

Use when: the exit decision is simple (one variable equals one value) and you want the check to happen automatically after the cycle completes.

**`break_conditions: []` is valid** — means the loop runs exactly `loop_count` times with no early exit. This is fine when the number of iterations is fixed by design.

### Method 2 — Exit Loop node (`loop-end`) inside the sub-workflow

Place a `loop-end` node inside the loop. When execution reaches it, the loop exits immediately — even mid-cycle, before the variable-assigner at the end of the cycle runs.

```yaml
# The loop-end node (inner node):
- data:
    isInLoop: true
    loop_id: "{loop_node_id}"
    selected: false
    title: Exit Loop
    type: loop-end
  height: 54
  id: "{some_unique_id}"
  parentId: "{loop_node_id}"
  position:
    x: 900        # Relative to container top-left
    y: 65
  positionAbsolute:
    x: {container_x + 900}
    y: {container_y + 65}
  sourcePosition: right
  targetPosition: left
  type: custom-simple           # Note: custom-simple, NOT custom
  width: 244
  zIndex: 1002
```

The edge from an `if-else` node to the loop-end uses `sourceHandle: 'true'`:

```yaml
- data:
    isInIteration: false
    isInLoop: true
    loop_id: "{loop_node_id}"
    sourceType: if-else
    targetType: loop-end
  source: "{if_else_node_id}"
  sourceHandle: 'true'          # true branch exits; false branch continues loop
  target: "{loop_end_node_id}"
  targetHandle: target
  type: custom
  zIndex: 1002
```

**Typical pattern:**

```text
loop-start → KR → LLM (structured output) → if-else
                                               ├── true  → loop-end (EXIT — sufficient context)
                                               └── false → assigner (update search_word for next cycle)
```

**`break_conditions` vs loop-end — when to use each:**

| Situation | Use |
| --- | --- |
| Simple: one variable equals one value, check after full cycle | `break_conditions` |
| Complex: exit depends on a node's structured output field | if-else + loop-end |
| Need to exit mid-cycle before the assigner runs | loop-end only |
| Both a declarative condition AND a mid-cycle abort | Both together |

---

## Evolving Query Pattern

A powerful loop pattern for agentic RAG: the KR query changes each cycle based on what the LLM decides to search for next.

```text
loop-start → KR (query = search_word loop var) ─┬─ LLM (structured output: more_info_required, search_word)
                                                 └─ assigner (extend knowledge array)
                                                          ↓
                                                    if-else (more_info_required = false)
                                                       ├── true  → loop-end (EXIT)
                                                       └── false → assigner (update search_word)
```

**How it works:**

1. `search_word` is a loop variable initialized from an upstream node's output (`value_type: variable`)
2. The KR node uses `search_word` as its query: `query_variable_selector: [loop_node_id, search_word]`
3. The KR result is **accumulated** (not replaced) into a `knowledge` loop variable (`var_type: array[object]`, `operation: extend`)
4. The LLM evaluates sufficiency with structured output: `{more_info_required: boolean, search_word: string}`
5. If sufficient → if-else true branch → loop-end exits
6. If not sufficient → false branch assigner updates `search_word` from `LLM.structured_output.search_word` → next cycle searches with the new term
7. After the loop, the `knowledge` loop variable holds all accumulated KR results from every cycle

**Initialization of `search_word` from an upstream variable:**

```yaml
loop_variables:
  - id: "uuid"
    label: search_word
    value:
      - "{upstream_node_id}"    # e.g. a parameter-extractor or start node
      - substance               # the output field to initialize from
    value_type: variable        # NOT constant — pulls initial value from a node output
    var_type: string
  - id: "uuid"
    label: knowledge
    value: '[]'                 # starts as empty array
    value_type: constant
    var_type: array[object]
```

**Accessing the accumulated knowledge after the loop** — the `knowledge` array of objects can be passed into a code node (to merge, filter, or reformat) before feeding into the context block of a downstream LLM:

```yaml
# Code node downstream of the loop:
variables:
  - value_selector:
      - "{loop_node_id}"
      - knowledge
    value_type: array[object]
    variable: accumulated_knowledge
```

The downstream LLM's `context` block then points to this code node's output (the merged/formatted array), and `{{#context#}}` injects it into the prompt.

---

## Internal Node Structure

Inside the loop container, you define a mini sub-workflow. All inner nodes share these properties:

```yaml
# Every inner node must include these fields in its data block:
isInLoop: true
loop_id: "{loop_node_id}"

# And on the node itself (not in data):
parentId: "{loop_node_id}"
zIndex: 1002
```

### Loop-Start Node

The loop-start node is the entry point of the sub-workflow. It has a special node type:

```yaml
- data:
    desc: ''
    isInLoop: true
    title: ''
    type: loop-start
  draggable: false
  height: 48
  id: "{loop_node_id}start"        # No separator — just "start" appended
  parentId: "{loop_node_id}"
  position:
    x: 60                          # Relative to container top-left
    y: 86
  positionAbsolute:
    x: {container_x + 60}
    y: {container_y + 86}
  selectable: false
  sourcePosition: right
  targetPosition: left
  type: custom-loop-start           # Note: different from regular nodes
  width: 44
  zIndex: 1002
```

### Internal Edges

Edges between nodes inside the loop container must include the `isInLoop` and `loop_id` flags:

```yaml
- data:
    isInIteration: false
    isInLoop: true
    loop_id: "{loop_node_id}"
    sourceType: loop-start
    targetType: llm              # or any inner node type
  id: "{source_id}-source-{target_id}-target"
  source: "{source_id}"
  sourceHandle: source
  target: "{target_id}"
  targetHandle: target
  type: custom
  zIndex: 1002
```

Edges that enter or exit the loop container (outer graph edges) use `isInLoop: false`:

```yaml
- data:
    isInIteration: false
    isInLoop: false
    sourceType: start
    targetType: loop
  ...
```

### Container Dimensions

The loop container node has `width` and `height` set both on the outer node and inside `data`:

```yaml
# In data block:
data:
  width: 700    # Container width — must be wide enough to fit all inner nodes
  height: 220   # Container height — must be tall enough for the inner sub-workflow

# On the outer node:
width: 700
height: 220
```

The container's x/y position is its top-left corner on the canvas. Inner nodes use positions relative to the container's top-left.

---

## Complete YAML Example — Agentic RAG Quality Loop (Chatflow)

This example demonstrates iterative RAG with up to 3 retrieval cycles. Each cycle: retrieves documents (via `context` block), asks the LLM to evaluate sufficiency AND draft an answer, then a `code` node splits the LLM text output into a verdict (`yes`/`no`) and a draft answer string. Both are written into loop variables via variable-assigner. The loop exits when `is_sufficient = "yes"` or after 3 cycles. The answer node at the end uses the `answer` loop variable directly — a plain string, safe to output.

**Why a code node instead of structured output:** The variable-assigner can only write to loop variables from top-level node output fields. A code node that outputs `is_sufficient` and `answer` as separate top-level fields gives the assigner clean, flat selectors (`[code_node_id, is_sufficient]`, `[code_node_id, answer]`) with no nesting required.

**Key positions** (outer canvas):

| Node | x | y |
|------|---|---|
| start | 30 | 303 |
| loop container | 334 | 303 |
| answer | 1774 | 303 |

Inner nodes (relative to container top-left):

| Node | x | y |
|------|---|---|
| loop-start | 60 | 101 |
| knowledge-retrieval | 164 | 91 |
| llm | 468 | 83 |
| code (parse verdict) | 772 | 83 |
| variable-assigner | 1076 | 83 |

```yaml
app:
  description: "Agentic RAG loop: retrieves up to 3 times until context is sufficient, then answers."
  icon: "\U0001F50D"
  icon_background: "#EEF4FF"
  mode: advanced-chat
  name: Agentic RAG Loop
dependencies: []
features:
  file_upload:
    enabled: false
  opening_statement: "Ask me anything. I'll search until I have a solid answer."
  speech_to_text:
    enabled: false
  suggested_questions: []
  suggested_questions_after_answer:
    enabled: false
  text_to_speech:
    enabled: false
kind: app
version: "0.3.1"
workflow:
  conversation_variables: []
  environment_variables: []
  graph:
    edges:
      # ── Outer edges ──────────────────────────────────────────────────────
      - data:
          isInIteration: false
          isInLoop: false
          sourceType: start
          targetType: loop
        id: "1748000000010-source-1748000000001-target"
        source: "1748000000010"
        sourceHandle: source
        target: "1748000000001"
        targetHandle: target
        type: custom
        zIndex: 0

      - data:
          isInIteration: false
          isInLoop: false
          sourceType: loop
          targetType: answer
        id: "1748000000001-source-1748000000012-target"
        source: "1748000000001"
        sourceHandle: source
        target: "1748000000012"
        targetHandle: target
        type: custom
        zIndex: 0

      # Inner graph: loop-start → knowledge-retrieval → llm (check) → assigner
      - data:
          isInIteration: false
          isInLoop: true
          loop_id: "1748000000001"
          sourceType: loop-start
          targetType: knowledge-retrieval
        id: "1748000000001start-source-1748000000002-target"
        source: "1748000000001start"
        sourceHandle: source
        target: "1748000000002"
        targetHandle: target
        type: custom
        zIndex: 1002

      - data:
          isInIteration: false
          isInLoop: true
          loop_id: "1748000000001"
          sourceType: knowledge-retrieval
          targetType: llm
        id: "1748000000002-source-1748000000003-target"
        source: "1748000000002"
        sourceHandle: source
        target: "1748000000003"
        targetHandle: target
        type: custom
        zIndex: 1002

      - data:
          isInIteration: false
          isInLoop: true
          loop_id: "1748000000001"
          sourceType: llm
          targetType: code
        id: "1748000000003-source-1748000000004-target"
        source: "1748000000003"
        sourceHandle: source
        target: "1748000000004"
        targetHandle: target
        type: custom
        zIndex: 1002

      - data:
          isInIteration: false
          isInLoop: true
          loop_id: "1748000000001"
          sourceType: code
          targetType: assigner
        id: "1748000000004-source-1748000000005-target"
        source: "1748000000004"
        sourceHandle: source
        target: "1748000000005"
        targetHandle: target
        type: custom
        zIndex: 1002

    nodes:
      # ── Outer nodes ──────────────────────────────────────────────────────
      - data:
          desc: ""
          title: Start
          type: start
          variables: []
        height: 54
        id: "1748000000010"
        position:
          x: 30
          y: 303
        positionAbsolute:
          x: 30
          y: 303
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      # ── Loop container ───────────────────────────────────────────────────
      - data:
          break_conditions:
            - comparison_operator: "is"
              id: "a1b2c3d4-0001-0001-0001-000000000001"
              value: "yes"
              varType: string
              variable_selector:
                - "1748000000001"
                - is_sufficient
          desc: "Retrieve and answer until context is sufficient, up to 3 cycles."
          error_handle_mode: terminated
          height: 250
          logical_operator: and
          loop_count: 3
          loop_variables:
            - id: "a1b2c3d4-0002-0002-0002-000000000002"
              label: is_sufficient
              value: "no"
              value_type: constant
              var_type: string
            - id: "a1b2c3d4-0003-0003-0003-000000000003"
              label: answer
              value: ""
              value_type: constant
              var_type: string
          selected: false
          start_node_id: "1748000000001start"
          title: RAG Refinement Loop
          type: loop
          width: 1380
        height: 250
        id: "1748000000001"
        position:
          x: 334
          y: 303
        positionAbsolute:
          x: 334
          y: 303
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 1380
        zIndex: 1

      # ── Loop-start (internal entry point) ────────────────────────────────
      - data:
          desc: ""
          isInLoop: true
          selected: false
          title: ""
          type: loop-start
        draggable: false
        height: 48
        id: "1748000000001start"
        parentId: "1748000000001"
        position:
          x: 60
          y: 101
        positionAbsolute:
          x: 394
          y: 404
        selectable: false
        sourcePosition: right
        targetPosition: left
        type: custom-loop-start
        width: 44
        zIndex: 1002

      # ── Knowledge retrieval (inner) ───────────────────────────────────────
      - data:
          dataset_ids:
            - "YOUR_DATASET_ID_HERE"             # Replace after creating KB in Dify
          desc: "Search the knowledge base."
          isInIteration: false
          isInLoop: true
          loop_id: "1748000000001"
          multiple_retrieval_config:
            reranking_enable: false
            top_k: 5
            weights:
              keyword_setting:
                keyword_weight: 0.3
              vector_setting:
                vector_weight: 0.7
              weight_type: customized
          query_attachment_selector: []
          query_variable_selector:
            - "1748000000010"
            - sys.query
          retrieval_mode: multiple
          title: Knowledge Retrieval
          type: knowledge-retrieval
        height: 92
        id: "1748000000002"
        parentId: "1748000000001"
        position:
          x: 164
          y: 91
        positionAbsolute:
          x: 498
          y: 394
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
        zIndex: 1002

      # ── LLM: evaluate + draft answer (inner) ─────────────────────────────
      # Uses context block to inject KR results (the ONLY correct way for arrays).
      # Outputs two lines: line 1 is "yes"/"no", line 2+ is the answer draft.
      - data:
          context:
            enabled: true
            variable_selector:
              - "1748000000002"
              - result
          desc: "Evaluate sufficiency and draft an answer using retrieved context."
          isInIteration: false
          isInLoop: true
          loop_id: "1748000000001"
          model:
            completion_params:
              temperature: 0.3
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: "eval-system"
              role: system
              text: |
                You are a research assistant. Review the retrieved context and answer the question.

                Format your response as exactly two parts:
                Line 1: yes   (if context is sufficient for a complete answer)
                        no    (if context is missing key information)
                Line 2 onwards: Your best answer based on the context. Always write something,
                even if the context is incomplete — say what you do know and what is missing.
            - id: "eval-user"
              role: user
              text: "Question: {{#1748000000010.sys.query#}}\n\n{{#context#}}"
          title: Evaluate and Draft Answer
          type: llm
          vision:
            enabled: false
        height: 98
        id: "1748000000003"
        parentId: "1748000000001"
        position:
          x: 468
          y: 83
        positionAbsolute:
          x: 802
          y: 386
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
        zIndex: 1002

      # ── Code node: parse verdict and answer from LLM text (inner) ────────
      # Splits the LLM's two-part text output into separate flat fields so the
      # variable-assigner can write each to a loop variable with a simple selector.
      - data:
          code: |
            def main(llm_text: str) -> dict:
                lines = llm_text.strip().split('\n', 1)
                verdict = lines[0].strip().lower()
                answer = lines[1].strip() if len(lines) > 1 else llm_text.strip()
                return {'is_sufficient': verdict, 'answer': answer}
          code_language: python3
          desc: "Split LLM output into verdict and answer."
          isInIteration: false
          isInLoop: true
          loop_id: "1748000000001"
          outputs:
            is_sufficient:
              children: null
              type: string
            answer:
              children: null
              type: string
          title: Parse Verdict
          type: code
          variables:
            - label: llm_text
              value_selector:
                - "1748000000003"
                - text
              variable: llm_text
        height: 90
        id: "1748000000004"
        parentId: "1748000000001"
        position:
          x: 772
          y: 83
        positionAbsolute:
          x: 1106
          y: 386
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
        zIndex: 1002

      # ── Variable assigner: write verdict + answer into loop variables ─────
      - data:
          desc: "Persist verdict and answer draft as loop variables."
          isInIteration: false
          isInLoop: true
          items:
            - input_type: variable
              operation: over-write
              value:
                - "1748000000004"
                - is_sufficient
              variable_selector:
                - "1748000000001"
                - is_sufficient
              write_mode: over-write
            - input_type: variable
              operation: over-write
              value:
                - "1748000000004"
                - answer
              variable_selector:
                - "1748000000001"
                - answer
              write_mode: over-write
          loop_id: "1748000000001"
          title: Update Loop Variables
          type: assigner
          version: "2"
        height: 110
        id: "1748000000005"
        parentId: "1748000000001"
        position:
          x: 1076
          y: 83
        positionAbsolute:
          x: 1410
          y: 386
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
        zIndex: 1002

      # ── Answer node (outer) — uses the loop variable directly ─────────────
      # {{#1748000000001.answer#}} is a plain string — safe to output directly.
      # No outer LLM needed: the answer was already drafted inside the loop.
      - data:
          answer: "{{#1748000000001.answer#}}"
          desc: ""
          title: Answer
          type: answer
        height: 54
        id: "1748000000012"
        position:
          x: 1774
          y: 303
        positionAbsolute:
          x: 1774
          y: 303
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
```

---

## Comparison with Iteration Node

| Property | Loop | Iteration |
|----------|------|-----------|
| **Input** | No array needed — loops until a condition | Requires an array to iterate over |
| **State** | Loop variables persist across cycles | Each item is independent; no shared state |
| **Termination** | Break condition expression or exit-loop node | All array items processed |
| **Processing** | Always sequential | Sequential (`parallelism: 1`) or parallel (`parallelism: N`) |
| **Built-in vars** | None — all variables are user-defined loop variables | `item` (current element), `index` (0-based position) |
| **Cycle counter** | User must define a counter loop variable manually | `index` is available automatically |
| **YAML type** | `loop` | `iteration` |
| **Start node type** | `custom-loop-start` | `custom` (with `type: iteration-start` in data) |
| **Inner edge flag** | `isInLoop: true` | `isInIteration: true` |
| **Output after exit** | Loop variables accessible by name | `output` array of results |
| **Best for** | Refinement, quality gates, self-checking RAG | Batch processing, per-item transformation |

**Decision rule:** If you have an array, use iteration. If you have a condition, use loop.

---

## Max Loop Count Limit

The `loop_count` field sets the safety cap for a single loop node. The absolute maximum is controlled by the `LOOP_NODE_MAX_COUNT` environment variable on the Dify server (default: 100). For RAG refinement patterns, a `loop_count` of 3 is typically sufficient — more than 3 retrieval passes rarely yields meaningfully better context.

---

## Common Mistakes

1. **Using loop when you have an array.** If you have a list of items to process, use `iteration`. Loop requires you to explicitly manage what changes each cycle via `loop_variables` — it does not know how to advance through a list automatically.

2. **Forgetting to update the loop variable that the break condition checks.** If `is_sufficient` starts as `"no"` and the variable-assigner inside the loop never updates it, the loop will always run until `loop_count` is exhausted. Always verify there is a clear path from the inner LLM output to a variable-assigner that writes the break-condition variable.

3. **Referencing inner node outputs outside the loop without loop variables.** After the loop exits, only `loop_variables` are accessible. A node inside the loop (e.g., the last knowledge-retrieval result) is NOT directly accessible outside the loop unless you store its output into a loop variable using a variable-assigner.

4. **Setting `loop_count` too high.** Each cycle makes at least one LLM call. A `loop_count` of 10 on a complex sub-workflow can produce 10 LLM calls per user request. Set the minimum needed: 3 for RAG refinement, 5 for content optimization, never exceed what your latency budget allows.

5. **Inner nodes missing `parentId`, `isInLoop`, or `loop_id`.** All nodes inside the loop container must have `parentId` set to the loop node's ID on the outer node object, and `isInLoop: true` and `loop_id` in their `data` block. Missing any of these causes the Dify canvas to render the node outside the container.

---

## See Also

- `skills/dify/references/nodes/iteration.md` — loop over a fixed array of items
- `skills/dify/references/nodes/variable-assigner.md` — update loop variables inside the loop
- `skills/dify/references/patterns/rag-pattern.md` — Agentic Loop RAG topology with full node graph
- `skills/dify/references/patterns/agentic-pattern.md` — agent-node alternative for dynamic tool-call loops
