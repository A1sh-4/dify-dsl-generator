# If-Else Node

## Overview

The if-else node creates conditional branches in a workflow based on variable values. It evaluates one or more conditions against runtime data and routes execution to either the `true` branch (when conditions pass) or the `false` branch (when they do not). This is the primary tool for logic-based routing in Dify workflows — directing flow based on content, thresholds, data types, or the presence or absence of values.

Unlike the question-classifier node, which uses an LLM to understand intent semantically, the if-else node applies deterministic logical conditions. It is faster and more predictable, but requires conditions to be expressible as comparisons against known variable fields.

## When to Use

Use if-else when:

- You need to check a numeric threshold (e.g., confidence score > 0.8)
- You want to route based on a known string value (e.g., language == "en")
- You need to check whether a variable is empty or populated
- You want to detect a keyword or pattern in text (contains, starts with)
- The routing logic can be expressed without semantic understanding

Use question-classifier instead when the distinction between branches requires understanding the meaning or intent of natural language text.

## Condition Structure

The if-else node supports multiple condition groups. Within a single group, conditions are combined with AND logic (all must be true). Multiple groups are combined with OR logic (any group passing triggers the true branch).

Each condition specifies:

| Field | Description |
|-------|-------------|
| `variable_selector` | Path to the variable to evaluate |
| `comparison_operator` | The comparison to perform |
| `value` | The value to compare against (not required for empty/not-empty) |

## All Comparison Operators

| Operator | Description | Data Type |
|----------|-------------|-----------|
| `contains` | Variable contains the substring or value | string, array |
| `not contains` | Variable does not contain the value | string, array |
| `starts with` | Variable begins with the string | string |
| `ends with` | Variable ends with the string | string |
| `is` | Exact equality | string, number, boolean |
| `is not` | Not equal | string, number, boolean |
| `empty` | Variable is null, empty string, or empty array | any |
| `not empty` | Variable has a non-empty value | any |
| `>` | Greater than | number |
| `<` | Less than | number |
| `>=` | Greater than or equal to | number |
| `<=` | Less than or equal to | number |

## Branch Handles

The if-else node always produces exactly two output edges:

- `true` — taken when the condition(s) evaluate to true
- `false` — taken when the condition(s) evaluate to false

In the `edges` section, use `sourceHandle: "true"` and `sourceHandle: "false"` to specify which branch each edge belongs to.

## Multiple Elif Branches

Dify's if-else node is binary (true/false only). To create multiple branches (elif logic), chain multiple if-else nodes:

```
if-else-1 (true) → path A
if-else-1 (false) → if-else-2 (true) → path B
                    if-else-2 (false) → path C (default)
```

Alternatively, use the question-classifier node when the number of categories is large.

## Why You Need Variable-Aggregator After Branching

After an if-else node creates two branches, downstream nodes typically need a single input variable — but each branch produces its own copy of the result. Without a variable-aggregator, you would need to duplicate every downstream node for each branch. 

The variable-aggregator node merges outputs from both branches into one variable, allowing the workflow to converge and continue as a single path. Always add a variable-aggregator after any branching structure when the branches produce outputs that need to be combined.

## Complete YAML Example

Real Dify export structure — if-else node that checks whether a select input equals "code":

```yaml
- data:
    cases:
    - case_id: 'true'
      conditions:
      - comparison_operator: is
        id: 11928117-9311-43f3-ae7c-22fd5775b09c   # UUIDv4 per condition
        value: code
        varType: string                              # matches the variable's data type
        variable_selector:
        - '1718002000001'   # node ID of the upstream node
        - input_type        # field name on that node
      id: 'true'            # same value as case_id — both fields are required
      logical_operator: and
    selected: false
    title: Route by Input Type
    type: if-else
  height: 124
  id: '1718002000002'
  position:
    x: 379
    y: 303
  positionAbsolute:
    x: 379
    y: 303
  selected: false
  sourcePosition: right
  targetPosition: left
  type: custom
  width: 243
```

**Critical structural rules (from real Dify exports):**

- The top-level key inside `data` is `cases` (not `conditions`)
- Only the **true** cases are listed — the false/else branch is implicit and never appears as a case entry
- Each case needs **both** `case_id` and `id` fields set to the same value (`'true'`, `'1'`, `'2'`, etc.)
- Each condition requires three extra fields beyond `variable_selector`/`comparison_operator`/`value`:
  - `id` — a UUIDv4, unique per condition
  - `varType` — the data type of the variable being tested (`string`, `number`, `array[string]`, etc.)
- `logical_operator: and` lives on the **case** object, not at the top level of `data`

## Pattern: Content-Based Routing

Route based on a select variable value:

```yaml
- data:
    cases:
    - case_id: 'true'
      conditions:
      - comparison_operator: is
        id: a1b2c3d4-0000-0000-0000-000000000001
        value: fr
        varType: string
        variable_selector:
        - '[start_node_id]'
        - language
      id: 'true'
      logical_operator: and
    selected: false
    title: Check Response Language
    type: if-else
```

## Pattern: Threshold-Based Routing

Route based on a numeric score:

```yaml
- data:
    cases:
    - case_id: 'true'
      conditions:
      - comparison_operator: '>='
        id: b2c3d4e5-0000-0000-0000-000000000001
        value: '0.75'
        varType: number
        variable_selector:
        - '[retrieval_node_id]'
        - score
      id: 'true'
      logical_operator: and
    selected: false
    title: Check Confidence Score
    type: if-else
```

## Common Mistakes

1. **Forgetting to add a variable-aggregator after branching.** If both branches produce output and you need that output downstream, you must merge with a variable-aggregator. Skipping this step means only one branch's output is available after convergence.

2. **Comparing numbers as strings.** If a score variable is stored as a string `"0.85"` and you compare it using `>` to `0.75`, the comparison may fail or produce unexpected results. Ensure numeric variables are actually numeric types.

3. **Using if-else for semantic intent detection.** The if-else node cannot understand meaning. Checking if text "contains" a keyword will miss paraphrases and variants. Use question-classifier for semantic routing.

4. **Not handling the false branch.** Every if-else node has a false branch. If you do not connect the false branch to a node, the workflow will have an unconnected edge and may error or silently stop. Always connect both branches to something.

5. **Nesting too many if-else nodes.** Deeply chained if-else nodes (5+) become hard to maintain. When you need many categories, use question-classifier or a code node with a switch-style logic block.
