# Iteration Node

## Overview

The iteration node loops over an array and executes a contained sub-workflow for each item. It is the primary tool for batch processing in Dify workflows — whenever you need to apply the same sequence of operations to every element of a list, the iteration node handles the looping, item access, and result collection automatically.

After all items have been processed, the iteration node outputs an array of results — one result per input item, in the same order. This output array can then be passed to a template-transform, LLM, or end node for further processing.

Common use cases include summarizing each document in a list, scraping and analyzing a list of URLs, processing a batch of user records, or transforming each element in an array with LLM assistance.

## When to Use

Use iteration when:

- You have an array of items and need to process each one with the same sub-workflow
- You want to apply LLM calls, tool calls, or transformations to every element in a list
- You need parallel processing of array elements to reduce total latency
- You are building a batch pipeline (process N files, N URLs, N records)

Do not use iteration when you only need to filter or reshape an array without processing each item individually — use the list-operator node instead.

## Input Configuration

| Field | Description |
|-------|-------------|
| `iterator_selector` | Path to the array variable to iterate over |
| `output_selector` | Path to the variable inside the sub-workflow that produces each item's result |
| `max_iterations` | Safety cap on the number of iterations (prevents runaway loops) |

## Context Variables Inside Iteration

Inside the iteration's sub-workflow, two special variables are always available:

| Variable | Description |
|----------|-------------|
| `{{item}}` | The current array element being processed |
| `{{index}}` | The 0-based index of the current element (0 for first, 1 for second, etc.) |

These variables are available in any node within the iteration sub-workflow. Reference them using the iteration's internal start node, which exposes `item` and `index` as output variables.

If the array contains objects (e.g., `[{"url": "...", "title": "..."}, ...]`), access fields with `{{item.url}}` and `{{item.title}}` inside templates, or reference them as `{{#iteration_start.item.url#}}` in YAML selectors.

## Processing Modes

### Sequential Mode (Default)

Items are processed one at a time, in order. The sub-workflow completes for item 0 before starting item 1. This mode is safe and predictable but slower for large arrays.

```yaml
parallelism: 1
```

### Parallel Mode

Multiple items are processed concurrently. Set `max_parallelism` to control how many items run at the same time. Useful when each item's processing involves waiting (API calls, LLM inference) and items are independent of each other.

```yaml
parallelism: 4  # Process up to 4 items at once
```

**Constraints on parallel mode:**
- `max_parallelism` must be between 2 and 10
- Items must be independent (results from one should not affect another)
- External API rate limits still apply — parallelism may cause throttling

## Output

The iteration node collects results from each iteration and assembles them into an array. The `output_selector` field specifies which variable from the sub-workflow's output represents each item's result.

| Variable | Type | Description |
|----------|------|-------------|
| `output` | array | Array of results, one per input item, in input order |

Reference downstream as `{{#iteration_node_id.output#}}`.

## Max Iterations Safety Limit

The `max_iterations` field prevents infinite or excessively long loops. If the input array contains more elements than `max_iterations`, the loop stops after processing that many items. The remaining items are not processed. Always set this to a reasonable upper bound based on expected data sizes.

## Sub-Workflow Structure

Inside the iteration container, you define a complete mini-workflow with its own start and end (output) nodes. The internal start node exposes `item` and `index`. The internal end node (or designated output node) defines what value is collected as that iteration's result.

The internal nodes are nested under the `nodes` key within the iteration's `data` block.

## Complete YAML Example

This example iterates over a list of URLs, fetches each one using a tool node, and collects the scraped text:

```yaml
nodes:
  - id: start
    type: start
    data:
      variables:
        - variable: url_list
          type: array[string]
          label: List of URLs to process
          required: true

  - id: process_urls
    type: iteration
    data:
      title: Process Each URL
      iterator_selector:
        - start
        - url_list
      output_selector:
        - scrape_page
        - text
      is_parallel: false
      parallelism: 1
      max_iterations: 20
      nodes:
        - id: iteration_start
          type: iteration-start
          data: {}

        - id: scrape_page
          type: tool
          data:
            title: Scrape URL
            provider_id: jina
            tool_name: jina_reader
            tool_parameters:
              url:
                type: mixed
                value: "{{#iteration_start.item#}}"

      edges:
        - source: iteration_start
          target: scrape_page

  - id: summarize_all
    type: llm
    data:
      title: Summarize All Pages
      prompt_template:
        - role: user
          text: |
            Here are the contents of {{#start.url_list.length#}} web pages:
            {{#process_urls.output#}}
            
            Provide a combined summary.

  - id: end
    type: end
    data:
      outputs:
        - variable: summary
          value_selector:
            - summarize_all
            - text

edges:
  - source: start
    target: process_urls
  - source: process_urls
    target: summarize_all
  - source: summarize_all
    target: end
```

## Pattern: Parallel Processing with Max Parallelism

```yaml
- id: process_documents
  type: iteration
  data:
    title: Summarize Each Document
    iterator_selector:
      - start
      - documents
    output_selector:
      - llm_summarize
      - text
    is_parallel: true
    parallelism: 4
    max_iterations: 50
    nodes:
      - id: iteration_start
        type: iteration-start
        data: {}
      - id: extract
        type: document-extractor
        data:
          variable_selector:
            - iteration_start
            - item
      - id: llm_summarize
        type: llm
        data:
          prompt_template:
            - role: user
              text: "Summarize: {{#extract.text#}}"
    edges:
      - source: iteration_start
        target: extract
      - source: extract
        target: llm_summarize
```

## Common Mistakes

1. **Referencing `{{item}}` in YAML value_selector instead of using the iteration-start node.** Inside the sub-workflow YAML, use `value_selector: [iteration_start, item]` to access the current item — not a bare `{{item}}` reference.

2. **Not setting output_selector correctly.** If the output_selector points to a node or field that does not exist in the sub-workflow, the iteration output array will contain null values.

3. **Setting max_parallelism too high.** High parallelism can exhaust API rate limits quickly. Start with 2–4 and test under realistic conditions.

4. **Mutating shared state inside a parallel iteration.** In parallel mode, each iteration runs concurrently. If iterations write to the same conversation variable (using variable-assigner), race conditions can occur. Avoid shared mutable state in parallel iterations.

5. **Forgetting that index is 0-based.** The `index` variable starts at 0, not 1. If you use it in display strings, add 1 for human-friendly numbering: `Item {{ index + 1 }}`.
