# Variable Aggregator Node

## Overview

The variable-aggregator node merges outputs from multiple branches of a workflow into a single unified variable. It is the convergence mechanism that allows a workflow to rejoin after a branching point — such as an if-else or question-classifier split — and continue as a single path with one consistent variable that downstream nodes can reference.

Without a variable-aggregator, each branch of a split workflow produces its own separate outputs. Downstream nodes cannot reference both branches simultaneously, so you would need to duplicate every downstream node for every branch. The aggregator solves this by selecting whichever branch actually produced a value (the active branch) and surfacing that value as a single output variable.

## Why It Is Needed

When a workflow splits at an if-else or question-classifier node, exactly one branch executes at runtime. The other branch(es) do not run and produce no output. However, from the YAML structure's perspective, downstream nodes need to declare a single input variable.

The variable-aggregator waits for the first (and only) branch to complete, takes that branch's output, and passes it forward as its own output variable. Branches that did not execute contribute nothing — the aggregator simply returns whichever branch was active.

This pattern is essential for:

- Converging if-else branches before a shared answer or end node
- Combining multiple question-classifier branch outputs
- Merging iteration results with non-iterated paths
- Any workflow that branches and must reconverge

## Input

The aggregator accepts any number of input variable references, one per branch. Each entry in the `variables` array points to an output variable from one of the upstream branches:

```yaml
variables:
  - - branch_a_node_id
    - output_variable_name
  - - branch_b_node_id
    - output_variable_name
  - - branch_c_node_id
    - output_variable_name
```

At runtime, only one of these will have a value. The aggregator returns that value.

## Output Variables

| Variable | Type | Description |
|----------|------|-------------|
| `output` | any | The value from whichever input branch was active |

Reference downstream as `{{#aggregator_node_id.output#}}`.

## Type Enforcement

All variables listed as inputs to the aggregator must be of compatible types. If branch A produces a string and branch B produces an array, the aggregator cannot reliably produce a single typed output. Dify enforces or warns about type mismatches depending on the configured output type.

To avoid type issues:
- Ensure all branches produce the same type of output
- Use template-transform to convert branch outputs to strings before aggregating
- Declare the expected output type in the aggregator's configuration

## Advanced Mode: Group Outputs with Metadata

In advanced mode, the aggregator can also attach metadata — such as which branch was taken — to the output. This allows downstream nodes to behave differently based on which path was followed, without needing an additional if-else check.

```yaml
output_type: object
group_by_branch: true
```

When grouping is enabled, the output includes a `branch` field alongside the `value`, allowing the answer node or LLM to reference which path was taken.

## Complete YAML Example

This example shows an if-else branch with two different LLM responses converging at a variable-aggregator before the final answer node:

```yaml
nodes:
  - id: start
    type: start
    data:
      variables:
        - variable: user_message
          type: string

  - id: check_urgency
    type: if-else
    data:
      title: Is Urgent?
      logical_operator: and
      conditions:
        - variable_selector:
            - start
            - user_message
          comparison_operator: contains
          value: urgent

  - id: urgent_response
    type: llm
    data:
      title: Generate Urgent Response
      prompt_template:
        - role: system
          text: You handle urgent escalations. Be immediate and action-oriented.
        - role: user
          text: "{{#start.user_message#}}"

  - id: standard_response
    type: llm
    data:
      title: Generate Standard Response
      prompt_template:
        - role: system
          text: You are a helpful assistant.
        - role: user
          text: "{{#start.user_message#}}"

  - id: merge_response
    type: variable-aggregator
    data:
      title: Merge Branch Outputs
      variables:
        - - urgent_response
          - text
        - - standard_response
          - text
      output_type: string

  - id: answer
    type: answer
    data:
      answer: "{{#merge_response.output#}}"

edges:
  - source: start
    target: check_urgency
  - source: check_urgency
    target: urgent_response
    sourceHandle: "true"
  - source: check_urgency
    target: standard_response
    sourceHandle: "false"
  - source: urgent_response
    target: merge_response
  - source: standard_response
    target: merge_response
  - source: merge_response
    target: answer
```

## Pattern: Three-Way Classifier Convergence

After a question-classifier with three categories, aggregate all three branch outputs:

```yaml
- id: aggregate_all_branches
  type: variable-aggregator
  data:
    title: Merge Classifier Outputs
    variables:
      - - billing_llm
        - text
      - - technical_llm
        - text
      - - general_llm
        - text
    output_type: string
```

## Pattern: If-Else → Branch A produces text → Branch B produces text → Aggregator → End

This is the canonical branching-and-convergence pattern in Dify:

```
Start
  ↓
If-Else
  ↓ (true)                    ↓ (false)
LLM Node A               LLM Node B
(produces text)          (produces text)
  ↓                           ↓
Variable Aggregator ←←←←←←←←←←
  ↓
Answer / End Node
```

## Common Mistakes

1. **Skipping the aggregator and wiring both branches directly to the next node.** A downstream node cannot receive input from two different upstream nodes that represent mutually exclusive branches. This creates ambiguous wiring and often causes runtime errors. Always use an aggregator.

2. **Aggregating variables of incompatible types.** If one branch produces a string and another produces an array, the aggregator behavior is undefined. Normalize all branch outputs to the same type before aggregation.

3. **Not connecting all active branches to the aggregator.** If a question-classifier has three classes but only two are wired to the aggregator, the third class's execution will have no downstream path, causing a workflow error.

4. **Referencing aggregator output before it resolves.** The aggregator output is only available after the active branch completes. Nodes placed before the aggregator in the graph cannot reference `{{#aggregator_id.output#}}`.

5. **Using variable-aggregator when variable-assigner is what you need.** Variable-aggregator is for combining branch outputs in a single execution. If you need to persist a value across conversation turns, use variable-assigner (chatflow only).
