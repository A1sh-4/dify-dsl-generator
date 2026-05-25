# End Node

## Overview

The end node terminates a workflow and defines the structured output returned to the caller. It is the required terminal node in all regular (non-chat) Dify workflows — when execution reaches the end node, the workflow completes and any declared output variables are serialized and returned in the API response.

The end node is the contract between your workflow and its consumers. Whatever you declare in the end node's `outputs` array is what API callers, integrations, and downstream systems receive.

## Workflow Only — Not Chatflows

The end node is used exclusively in regular workflows. Chatflows use the answer node for output, which streams text directly to the user interface.

If you are building a chatflow, do not use the end node. If you are building a workflow triggered by an API call, webhook, or schedule, the end node is mandatory.

## What Happens Without an End Node

A workflow without an end node will produce no output and may error at runtime. Dify workflows require at least one end node to define the completion point. If execution reaches a dead-end path with no end node, the workflow run will complete without returning any structured data, and API callers will receive an empty or error response.

Always ensure every execution path in your workflow reaches an end node.

## Output Variable Declaration

The `outputs` array in the end node defines which variables are included in the workflow's response. Each entry maps a named output to a value from an upstream node:

```yaml
outputs:
  - variable: output_name        # Name in the API response
    value_selector:
      - upstream_node_id         # Node that produced the value
      - field_name               # Specific field from that node
```

You can declare as many outputs as needed. Outputs can be any type: string, number, boolean, array, or object.

## Multiple Outputs

A single end node can return multiple output variables. This allows a workflow to return a structured response with several fields — for example, a generated text answer, a confidence score, and a list of source documents:

```yaml
outputs:
  - variable: answer
    value_selector:
      - llm_node
      - text
  - variable: confidence
    value_selector:
      - retrieval_node
      - result[0].score
  - variable: sources
    value_selector:
      - retrieval_node
      - result
```

## Multiple End Nodes (One Per Branch)

A workflow with conditional branching can have multiple end nodes — one at the end of each branch. Each end node can declare different outputs appropriate to its branch:

```
If-Else (true)  → process_urgent → end_node_urgent (outputs: urgent_response)
If-Else (false) → process_normal → end_node_normal (outputs: normal_response)
```

This is valid and correct. Dify allows multiple end nodes. Whichever branch executes will reach its corresponding end node and return its outputs.

## API Response Format

When a workflow completes, the API response includes the end node's outputs under a `data` or `outputs` key (depending on the Dify version and API endpoint). Callers can then parse the response to extract specific fields by the variable names you declared.

This makes the end node's output declaration important for integration design — the variable names you choose become the API response field names that consumers depend on.

## Complete YAML Example: Two Output Variables

This example processes a user query with knowledge retrieval and returns both the answer and the source document title:

```yaml
nodes:
  - id: start
    type: start
    data:
      variables:
        - variable: user_query
          type: string
          label: Query
          required: true

  - id: retrieve
    type: knowledge-retrieval
    data:
      title: Retrieve Relevant Chunks
      query_variable_selector:
        - start
        - user_query
      dataset_ids:
        - your-dataset-id
      retrieval_mode: hybrid_search
      top_k: 3
      score_threshold_enabled: false

  - id: generate_answer
    type: llm
    data:
      title: Generate Answer
      model:
        provider: openai
        name: gpt-4o
        mode: chat
      context:
        enabled: true
        variable_selector:
          - retrieve
          - result
      prompt_template:
        - role: system
          text: Answer the question using the provided context only.
        - role: user
          text: "{{#start.user_query#}}"

  - id: end
    type: end
    data:
      title: Return Results
      outputs:
        - variable: answer
          value_selector:
            - generate_answer
            - text
        - variable: source_title
          value_selector:
            - retrieve
            - result[0].title

edges:
  - source: start
    target: retrieve
  - source: retrieve
    target: generate_answer
  - source: generate_answer
    target: end
```

The API caller receives a response like:

```json
{
  "data": {
    "outputs": {
      "answer": "The answer to your question is...",
      "source_title": "Product Documentation v2.1"
    }
  }
}
```

## Pattern: Structured Output for API Consumers

Design end node outputs to match the interface contract expected by downstream systems:

```yaml
- id: end
  type: end
  data:
    outputs:
      - variable: summary
        value_selector:
          - summarize_llm
          - text
      - variable: sentiment
        value_selector:
          - sentiment_extractor
          - sentiment
      - variable: key_topics
        value_selector:
          - topic_extractor
          - topics
      - variable: processed_at
        value_selector:
          - timestamp_node
          - iso_timestamp
```

## Pattern: Branching Workflow with Multiple End Nodes

```yaml
# Branch A end node
- id: end_approved
  type: end
  data:
    outputs:
      - variable: status
        value_selector:
          - approval_node
          - decision
      - variable: approved_content
        value_selector:
          - format_content
          - output

# Branch B end node
- id: end_rejected
  type: end
  data:
    outputs:
      - variable: status
        value_selector:
          - rejection_node
          - reason
      - variable: feedback
        value_selector:
          - rejection_node
          - feedback
```

## Common Mistakes

1. **Using end node in a chatflow.** End nodes do not stream output to chat users. In chatflows, use the answer node. The end node only applies to non-chat workflows.

2. **Forgetting to connect all execution paths to an end node.** If an if-else branch leads to nodes but has no end node, that path silently terminates without returning output. Always trace every possible execution path and ensure it ends at an end node.

3. **Declaring output variables that reference non-existent nodes or fields.** If `value_selector` points to a node ID or field name that does not exist, the end node will return null for that output — often silently. Double-check node IDs and field names.

4. **Returning an entire large array when only one field is needed.** If you return a full retrieval result array but the caller only needs the top result's text, extract just the text with a template-transform or direct field reference like `result[0].content`.

5. **Not using consistent output variable names across multiple end nodes in a branched workflow.** If one branch returns `{ "result": "..." }` and another branch returns `{ "answer": "..." }`, API consumers must handle both schemas. Standardize variable names across all end nodes in the same workflow.
