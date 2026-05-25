# Node Positioning Reference

## Overview

Dify workflows are rendered on a **React Flow canvas** — a 2D plane where each node has an explicit pixel position. Node positions are `x, y` coordinate pairs where:

- **X increases rightward** (nodes further right have larger X values)
- **Y increases downward** (nodes lower on the canvas have larger Y values)
- The **origin (0, 0)** is the top-left corner of the canvas

Positions are measured in pixels and stored directly in the DSL. Because nodes have fixed dimensions, carefully chosen positions ensure the workflow renders cleanly without overlaps, crossed edges, or visual clutter. Poorly positioned nodes are technically valid DSL but render as an unreadable tangle in the visual editor.

---

## Node Dimensions

Understanding node dimensions is necessary to calculate non-overlapping positions.

### Width

- **Standard node width: 244px** — this is the display width stored in the `width` field for all standard node types. (The Dify source code constant `NODE_WIDTH` is 240px, but the rendered width with borders is 244px.)

### Height

Node height varies by type and content complexity:

| Node Type | Approximate Height |
|---|---|
| start | 54px |
| end / answer | 54px |
| variable-aggregator | 54px |
| llm | 98px |
| code | 98px |
| http-request | 98px |
| if-else | 126px |
| question-classifier | 154px |
| iteration (container) | Variable (depends on inner graph) |

Heights can vary further based on the number of configured variables, model settings, or custom labels. These are approximations suitable for layout calculations.

### Spacing Constants

These constants are derived from the Dify source (`workflow/constants.ts`) and define the standard spacing used by the auto-layout engine:

| Constant | Value | Description |
|---|---|---|
| `NODE_WIDTH` | 240px | Node display width |
| `X_OFFSET` | 60px | Horizontal gap between nodes |
| `NODE_WIDTH_X_OFFSET` | 300px | `NODE_WIDTH + X_OFFSET` — total horizontal step |
| `Y_OFFSET` | 39px | Baseline vertical offset |
| `START_INITIAL_POSITION` | `x: 80, y: 282` | Canvas position of the first (start) node |

**Use 300px as the horizontal spacing offset** between sequential nodes (node width plus gap). Use **150px as the vertical offset** between parallel branches to achieve clear visual separation.

---

## Default Starting Position

The first node in any workflow is always the `start` node. Its canonical position is:

```
x: 80
y: 282
```

This is the Dify standard starting point (`START_INITIAL_POSITION`). All other node positions are calculated relative to this anchor. When generating DSL programmatically, always place the start node at `x=80, y=282` unless there is a specific reason to deviate.

---

## Grid Snapping

Dify's canvas uses a **50px grid**. While grid snapping is optional in the visual editor, generated DSL should use positions that align to (or near) 50px multiples for the cleanest rendering:

- Prefer: `80, 100, 150, 200, 250, 300, 350, 400, 450, 500, ...`
- The start position `x=80, y=282` is slightly off-grid by convention — this is acceptable since it is the Dify standard
- For all other nodes, rounding to the nearest 50px produces the cleanest results

Example of grid-snapped positions:

```
Unsnapped: x=437, y=289
Snapped:   x=450, y=300
```

---

## Layout Algorithms

### Linear Chain (Most Common)

The default layout for sequential workflows. Nodes flow left to right with 300px horizontal spacing, all at the same Y coordinate:

```
Node index 0: x=80,  y=282
Node index 1: x=380, y=282
Node index 2: x=680, y=282
Node index 3: x=980, y=282

Formula: x = 80 + (index * 300), y = 282
```

Visual representation:
```
Start → LLM → Code → End
```

This is the correct layout for: start → llm → template-transform → answer, or any other purely sequential chain.

---

### If-Else Branching

If-else nodes split the flow into two parallel paths that typically converge at a variable-aggregator. The branches are positioned symmetrically above and below the main flow line:

```
Parent node (if-else):   x=P,     y=282
True branch node:         x=P+300, y=132   (150px above center)
False branch node:        x=P+300, y=432   (150px below center)
Merge node (aggregator):  x=P+600, y=282   (back to center)
```

Visual representation:
```
              ┌─ True branch  ─┐
... → If-Else ┤                 ├─ Aggregator → ...
              └─ False branch ─┘
```

If the branches contain multiple nodes, extend horizontally within each branch row before converging:
```
True branch:  x=P+300 (node 1), x=P+600 (node 2), then aggregator at x=P+900
False branch: x=P+300 (node 1), then aggregator at x=P+900
```

---

### Three-Way Branch (Question-Classifier with 3 Classes)

Three-way branching fans out above, at, and below the center line:

```
Parent node (classifier):  x=P,     y=282
Branch 1 (top):            x=P+300, y=82
Branch 2 (center):         x=P+300, y=282
Branch 3 (bottom):         x=P+300, y=482
Aggregator (convergence):  x=P+600, y=282
```

For four or more branches, increase the vertical spread proportionally (approximately 200px per additional branch).

---

### Iteration Container

Iteration nodes have a larger bounding box that contains an inner subgraph. The inner nodes are positioned within the container's coordinate space:

```
Iteration container:  x=P, y=282  (position of the container node itself)
Inner start node:     offset from the container's top-left corner
```

For iteration containers, `positionAbsolute` of inner nodes reflects their true canvas position (container position + inner offset). Edges inside the iteration must have `data.isInIteration: true` and `data.iteration_id` set to the container node's ID.

---

## The positionAbsolute Field

Every node in the Dify DSL has **two position fields**: `position` and `positionAbsolute`.

For **top-level nodes** (nodes not inside an iteration container), these two fields are always **identical**. The runtime uses `positionAbsolute` for actual rendering; `position` is the React Flow local position. For top-level nodes they are the same value.

```yaml
position:
  x: 380
  y: 282
positionAbsolute:
  x: 380
  y: 282
```

For **nodes inside iteration containers**, `position` may be relative to the container while `positionAbsolute` reflects the true canvas coordinates. When generating DSL, always set both fields to the same absolute canvas coordinates for top-level nodes. For inner iteration nodes, follow the same rule unless you are explicitly computing relative offsets.

---

## Standard Node YAML Fields for Positioning

The complete set of positioning-related fields for a standard node:

```yaml
height: 54              # Approximate rendered height in pixels (54, 98, 126, 154, etc.)
width: 244              # Always 244 for standard nodes
position:
  x: 380
  y: 282
positionAbsolute:
  x: 380               # Same as position.x for top-level nodes
  y: 282               # Same as position.y for top-level nodes
sourcePosition: right   # Always "right" — edges exit from the right side
targetPosition: left    # Always "left" — edges enter from the left side
```

The `sourcePosition: right` and `targetPosition: left` fields enforce the left-to-right flow direction. Do not change these values — they are fixed conventions in Dify workflows.

---

## Worked Example: 5-Node Linear Flow with Branching

Workflow: `start(0)` → `llm(1)` → `if-else(2)` → `[true: llm(3), false: llm(4)]` → `aggregator(5)` → `end(6)`

```
Node             Index  Position           Notes
-----------      -----  ----------------   -------------------------
start            0      x=80,   y=282      START_INITIAL_POSITION
llm              1      x=380,  y=282      80 + 1*300
if-else          2      x=680,  y=282      80 + 2*300
llm (true)       3      x=980,  y=132      680+300, 282-150
llm (false)      4      x=980,  y=432      680+300, 282+150
variable-agg     5      x=1280, y=282      980+300, back to center
end              6      x=1580, y=282      1280+300
```

Complete YAML positioning blocks for each node:

```yaml
# Node 0: start
- id: '1732001000000'
  type: start
  width: 244
  height: 54
  position: { x: 80, y: 282 }
  positionAbsolute: { x: 80, y: 282 }
  sourcePosition: right
  targetPosition: left

# Node 1: llm
- id: '1732001001000'
  type: llm
  width: 244
  height: 98
  position: { x: 380, y: 282 }
  positionAbsolute: { x: 380, y: 282 }
  sourcePosition: right
  targetPosition: left

# Node 2: if-else
- id: '1732001002000'
  type: if-else
  width: 244
  height: 126
  position: { x: 680, y: 282 }
  positionAbsolute: { x: 680, y: 282 }
  sourcePosition: right
  targetPosition: left

# Node 3: llm (true branch — 150px above center)
- id: '1732001003000'
  type: llm
  width: 244
  height: 98
  position: { x: 980, y: 132 }
  positionAbsolute: { x: 980, y: 132 }
  sourcePosition: right
  targetPosition: left

# Node 4: llm (false branch — 150px below center)
- id: '1732001004000'
  type: llm
  width: 244
  height: 98
  position: { x: 980, y: 432 }
  positionAbsolute: { x: 980, y: 432 }
  sourcePosition: right
  targetPosition: left

# Node 5: variable-aggregator (convergence — back to center)
- id: '1732001005000'
  type: variable-aggregator
  width: 244
  height: 54
  position: { x: 1280, y: 282 }
  positionAbsolute: { x: 1280, y: 282 }
  sourcePosition: right
  targetPosition: left

# Node 6: end
- id: '1732001006000'
  type: end
  width: 244
  height: 54
  position: { x: 1580, y: 282 }
  positionAbsolute: { x: 1580, y: 282 }
  sourcePosition: right
  targetPosition: left
```

---

## Canvas Size Guidance

When designing workflow layouts, keep the total canvas footprint within these ranges:

| Workflow Complexity | Recommended Canvas Size |
|---|---|
| Simple (3–6 nodes, linear) | 1200px × 800px |
| Moderate (7–15 nodes, some branching) | 2000px × 1200px |
| Complex (16+ nodes, multi-branch) | 3000px × 1600px |

**General guidelines:**

- Keep the total workflow width within **3000px** for best usability at standard zoom levels (0.5x–2.0x)
- Keep the total workflow height within **1600px** to avoid excessive scrolling
- If a linear chain would exceed 3000px wide, consider restructuring with iteration containers or sub-workflows to compress the layout
- Leave at least **100px margin** on each edge of the canvas so nodes are not clipped at minimum zoom
- The visual editor's initial viewport centers on `x=0, y=0` at zoom 1.0 — position nodes in positive coordinate space (all x and y values greater than 0) to keep them visible by default

**Position validation checklist:**
- No node has negative x or y coordinates
- No two nodes overlap (minimum 50px clearance between bounding boxes)
- All nodes are reachable at standard zoom levels (0.5x–2.0x)
- Branches are symmetrically distributed around the main flow line
- `position` and `positionAbsolute` are identical for all top-level nodes
