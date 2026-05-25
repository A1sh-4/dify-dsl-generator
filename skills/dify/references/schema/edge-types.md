# Edge Types Reference

## Overview

In the Dify DSL, **edges** define the execution flow between nodes. Every edge connects a source node to a target node and specifies exactly which output handle on the source node leads to which input handle on the target node. Without edges, nodes are isolated and no data or control flow occurs. Edges are what transform a collection of nodes into an executable workflow graph.

Edges are declarative — they do not contain logic themselves. Instead, they describe paths that the runtime may or may not follow depending on which branches are taken during execution. In branching workflows (if-else, question-classifier, error handling), multiple edges can originate from a single source node, but only some will be traversed at runtime.

---

## Edge States

During workflow execution, every edge is assigned one of three execution states. Understanding these states is essential for debugging workflow traces and generating accurate runtime visualizations.

### UNKNOWN

The **default state** before a workflow runs, and also the state of any edge whose traversal has not yet been determined. An edge stays in UNKNOWN if its source node has not yet completed execution. In long-running or asynchronous workflows, many edges may remain UNKNOWN for a period before being resolved.

Use case: Any edge in a workflow that has not started executing yet.

### TAKEN

The edge **was followed** — the runtime traversed this path. The source node completed and the execution control (or data) passed along this specific edge to the target node. For conditional branches (if-else true/false, question-classifier classes), TAKEN means this was the winning branch.

Use case: The primary execution path in a successful workflow run; the winning branch of a conditional.

### SKIPPED

The edge **was not followed** — the runtime explicitly decided not to traverse this path. This happens when a different branch was chosen. For example, when an if-else node evaluates to `true`, the `false` edge is marked SKIPPED (not UNKNOWN — the decision was made, it just went the other way).

Use case: The losing branch of a conditional; error edges when no error occurred; success edges when an error did occur.

The distinction between UNKNOWN and SKIPPED matters: UNKNOWN means "not yet evaluated," SKIPPED means "evaluated and deliberately not taken."

---

## Edge YAML Structure

Every edge in the Dify DSL is represented as a YAML object with the following fields:

```yaml
- data:
    isInIteration: false      # true if inside an iteration container
    sourceType: start         # type string of the source node
    targetType: llm           # type string of the target node
  id: '1732007415808-source-1732007415900-target'
  source: '1732007415808'     # source node ID
  sourceHandle: source        # handle type on the source node
  target: '1732007415900'     # target node ID
  targetHandle: target        # always "target" on the receiving end
  type: custom                # always "custom"
  zIndex: 0                   # rendering layer, 0 for normal edges
```

### Field Descriptions

| Field | Type | Description |
|---|---|---|
| `data.isInIteration` | boolean | Set `true` if this edge is inside an iteration container |
| `data.sourceType` | string | The BlockEnum type name of the source node (e.g., `"llm"`, `"code"`) |
| `data.targetType` | string | The BlockEnum type name of the target node |
| `id` | string | Unique edge identifier — see naming convention below |
| `source` | string | The node ID of the source node |
| `sourceHandle` | string | The output handle on the source node (e.g., `source`, `true`, `false`) |
| `target` | string | The node ID of the target node |
| `targetHandle` | string | Always `"target"` — the standard input handle on any receiving node |
| `type` | string | Always `"custom"` in Dify workflows |
| `zIndex` | integer | Rendering layer; use `0` for normal edges |

---

## Edge ID Naming Convention

Edge IDs follow a strict pattern that encodes the connection information directly:

```
{source_node_id}-{sourceHandle}-{target_node_id}-target
```

**IMPORTANT:** The last segment is always literally the word `target` — it is NOT the target node's ID repeated. The target node ID appears in the middle of the string, and the string ends with the literal suffix `-target`.

### Examples

| Connection Type | Edge ID |
|---|---|
| Normal flow (source handle) | `1732001000000-source-1732001001000-target` |
| If-else true branch | `1732001000000-true-1732001002000-target` |
| If-else false branch | `1732001000000-false-1732001003000-target` |
| Fail branch (error path) | `1732001000000-fail-branch-1732001004000-target` |
| Success branch | `1732001000000-success-branch-1732001005000-target` |
| Question-classifier class | `1732001000000-support_request-1732001006000-target` |

The pattern makes edge IDs human-readable at a glance — you can extract the source node, the handle used, and the target node just by parsing the ID string.

---

## Handle Types by Node Type

The `sourceHandle` field must match the actual output handles available on the source node type. The `targetHandle` is always `"target"` regardless of node type.

| Node Type | Valid sourceHandles |
|---|---|
| start | `source` |
| llm | `source` |
| code | `source` |
| http-request | `source`, `fail-branch`, `success-branch` |
| knowledge-retrieval | `source` |
| template-transform | `source` |
| doc-extractor | `source` |
| list-operator | `source` |
| if-else | `true`, `false` |
| question-classifier | `[class-name-1]`, `[class-name-2]`, ... (custom class labels) |
| parameter-extractor | `source` |
| variable-aggregator | `source` |
| variable-assigner | `source` |
| iteration | `source` |
| human-input | `source` |
| tool | `source`, `fail-branch`, `success-branch` |
| agent | `source` |
| answer | *(terminal — no outgoing edges)* |
| end | *(terminal — no outgoing edges)* |
| trigger-webhook | `source` |
| trigger-schedule | `source` |

**The `targetHandle` is ALWAYS `"target"` regardless of node type.**

### Notes on Specific Handle Types

**`http-request` and `tool` nodes** support error-handling branches. When `error_strategy: fail-branch` is configured on these nodes, you must provide both a `success-branch` edge and a `fail-branch` edge. Without both edges, the workflow is incomplete.

**`if-else` nodes** always have exactly two outgoing edges: one with `sourceHandle: "true"` and one with `sourceHandle: "false"`. Both must be present.

**`question-classifier` nodes** use the class label strings as handle names. These are the names you define in the node's `classes` configuration — not auto-generated values like `true`/`false`. Each class must have a corresponding outgoing edge.

---

## The isInIteration Field

The `data.isInIteration` boolean flag marks whether an edge is part of an iteration container's internal graph. When nodes and their connecting edges live inside an iteration (loop) container, set `isInIteration: true` on those edges. This affects how the React Flow canvas renders them — internal edges are scoped to the container's bounding box rather than the full canvas.

When `isInIteration` is `true`, you should also set `data.iteration_id` to the parent iteration node's ID so the runtime can associate the edge with the correct container.

```yaml
- data:
    isInIteration: true
    iteration_id: '1732007415808'
    sourceType: llm
    targetType: code
  id: '1732007416000-source-1732007417000-target'
  source: '1732007416000'
  sourceHandle: source
  target: '1732007417000'
  targetHandle: target
  type: custom
  zIndex: 0
```

Edges that are **not** inside an iteration container should have `isInIteration: false` (the default).

---

## Common Edge Mistakes

The following mistakes frequently appear in generated or hand-written DSL and cause validation errors or unexpected runtime behavior:

1. **Wrong handle name** — Using `"success"` instead of `"success-branch"`, or `"fail"` instead of `"fail-branch"`. The hyphens are part of the handle name and cannot be omitted.

2. **Question-classifier handle confusion** — Using `"true"`/`"false"` for question-classifier edges instead of the actual class name strings. Question-classifier routes by class label, not boolean.

3. **Wrong targetHandle** — Setting `targetHandle` to anything other than `"target"`. Every node receives connections on its single `target` handle. Never use the node type name or any other value here.

4. **Duplicate edge IDs** — Using the same `id` string for two different edges. Edge IDs must be globally unique within the DSL.

5. **Missing branch edges** — Defining an if-else node but only providing one outgoing edge (only true or only false). Both branches must have edges even if one leads to an `end` node immediately.

6. **Incorrect ID suffix** — Writing the edge ID as `{source}-{handle}-{target}-{target_again}` using the target node ID instead of the literal word `target`. The suffix is always the literal string `target`.

7. **Missing `data.sourceType` / `data.targetType`** — Omitting the type fields from `data`. These are required for correct rendering and type checking in the visual editor.

---

## Complete Edge Examples

### Example 1: Normal Flow (source → llm)

A standard sequential connection between two nodes:

```yaml
- data:
    isInIteration: false
    sourceType: start
    targetType: llm
  id: '1732001000000-source-1732001001000-target'
  source: '1732001000000'
  sourceHandle: source
  target: '1732001001000'
  targetHandle: target
  type: custom
  zIndex: 0
```

### Example 2: If-Else Branching

Two edges from a single if-else node — one for true, one for false:

```yaml
# True branch
- data:
    isInIteration: false
    sourceType: if-else
    targetType: llm
  id: '1732001002000-true-1732001003000-target'
  source: '1732001002000'
  sourceHandle: "true"
  target: '1732001003000'
  targetHandle: target
  type: custom
  zIndex: 0

# False branch
- data:
    isInIteration: false
    sourceType: if-else
    targetType: code
  id: '1732001002000-false-1732001004000-target'
  source: '1732001002000'
  sourceHandle: "false"
  target: '1732001004000'
  targetHandle: target
  type: custom
  zIndex: 0
```

### Example 3: Fail-Branch (Error Handling)

An http-request node with both success and fail paths:

```yaml
# Success path
- data:
    isInIteration: false
    sourceType: http-request
    targetType: llm
  id: '1732001005000-success-branch-1732001006000-target'
  source: '1732001005000'
  sourceHandle: success-branch
  target: '1732001006000'
  targetHandle: target
  type: custom
  zIndex: 0

# Fail path
- data:
    isInIteration: false
    sourceType: http-request
    targetType: template-transform
  id: '1732001005000-fail-branch-1732001007000-target'
  source: '1732001005000'
  sourceHandle: fail-branch
  target: '1732001007000'
  targetHandle: target
  type: custom
  zIndex: 0
```

### Example 4: Question-Classifier

A question-classifier node with three custom class handles routing to three different handlers:

```yaml
# Support request class
- data:
    isInIteration: false
    sourceType: question-classifier
    targetType: llm
  id: '1732001008000-support_request-1732001009000-target'
  source: '1732001008000'
  sourceHandle: support_request
  target: '1732001009000'
  targetHandle: target
  type: custom
  zIndex: 0

# Sales inquiry class
- data:
    isInIteration: false
    sourceType: question-classifier
    targetType: http-request
  id: '1732001008000-sales_inquiry-1732001010000-target'
  source: '1732001008000'
  sourceHandle: sales_inquiry
  target: '1732001010000'
  targetHandle: target
  type: custom
  zIndex: 0

# General question class
- data:
    isInIteration: false
    sourceType: question-classifier
    targetType: knowledge-retrieval
  id: '1732001008000-general_question-1732001011000-target'
  source: '1732001008000'
  sourceHandle: general_question
  target: '1732001011000'
  targetHandle: target
  type: custom
  zIndex: 0
```
