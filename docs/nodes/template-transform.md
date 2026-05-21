# Template Transform Node

## Overview

The template-transform node renders Jinja2 templates with dynamic variable injection. It takes one or more input variables from upstream nodes and produces a single formatted string output. This node is essential whenever you need to combine, format, or conditionally assemble text before passing it to an LLM or returning it as a final answer.

Common uses include formatting LLM responses with metadata, constructing prompt fragments from multiple data sources, producing human-readable summaries of structured data, and generating conditional text that changes based on variable values.

## When to Use

Use template-transform when:

- You need to merge multiple variables into a single string
- You want to apply text formatting (uppercase, rounding, truncation) before passing data downstream
- You need conditional text — "if the score is high, say X; otherwise say Y"
- You want to build a structured prompt that assembles context from several previous nodes
- You need to loop over an array and produce a formatted list

Do NOT use template-transform when you simply want to pass a single variable through unchanged — use a direct variable reference in the next node instead.

## Critical Distinction: Two Syntaxes

This is the most common source of confusion when working with template-transform nodes:

**Inside the template content** — use standard Jinja2 double-brace syntax:
```
{{ variable_name }}
```

**In the node's input mapping** (wiring upstream node outputs into this node) — use Dify's reference syntax:
```
{{#node_id.field_name#}}
```

The `{{#...#}}` syntax is only used in YAML configuration to reference values from other nodes. Once a value arrives inside the template-transform node, you reference it with plain `{{ variable_name }}` Jinja2 syntax.

## Jinja2 Features Supported

**Variable output:**
```jinja2
{{ user_name }}
{{ response_text }}
```

**Conditional blocks:**
```jinja2
{% if score > 0.8 %}
High confidence result.
{% elif score > 0.5 %}
Moderate confidence result.
{% else %}
Low confidence — please verify manually.
{% endif %}
```

**Loops:**
```jinja2
{% for item in results %}
- {{ item.title }}: {{ item.summary }}
{% endfor %}
```

**Filters:**
```jinja2
{{ name | upper }}
{{ price | round(2) }}
{{ long_text | truncate(200) }}
{{ items | join(', ') }}
```

## Input Variables

Input variables are declared as key-value pairs in the node's `variables` array. Each entry gives the variable a local name (used inside the Jinja2 template) and maps it to an upstream value using `{{#node_id.field#}}` syntax.

## Output Variable

The template-transform node produces exactly one output:

| Variable | Type | Description |
|----------|------|-------------|
| `output` | string | The fully rendered Jinja2 template |

Reference this downstream as `{{#template_node_id.output#}}`.

## Complete YAML Example

This example formats an LLM response with metadata — combining the model's answer, the confidence score, and the original query into a structured report string.

```yaml
- id: format_response
  type: template-transform
  data:
    title: Format LLM Response with Metadata
    variables:
      - variable: query_text
        value_selector:
          - start
          - query
      - variable: llm_answer
        value_selector:
          - llm_node
          - text
      - variable: retrieval_score
        value_selector:
          - knowledge_retrieval
          - result[0].score
    template: |
      ## Query
      {{ query_text }}

      ## Answer
      {{ llm_answer }}

      {% if retrieval_score is defined %}
      ---
      *Source confidence: {{ retrieval_score | round(2) }}*
      {% endif %}
    outputs:
      - variable: output
        type: string
```

## Practical Template: Formatting an LLM Response with Metadata

```jinja2
## Response to: {{ query_text | truncate(100) }}

{{ llm_answer }}

{% if sources %}
### Sources Used
{% for source in sources %}
- {{ source.title }} (score: {{ source.score | round(2) }})
{% endfor %}
{% else %}
*No external sources used.*
{% endif %}

---
Generated {{ timestamp }} | Model: {{ model_name | default('default') }}
```

## Common Mistakes

1. **Using `{{#...#}}` inside the template content.** This syntax only works in YAML field values, not inside the Jinja2 template string itself. Inside the template, always use `{{ variable_name }}`.

2. **Forgetting to declare variables in the `variables` array.** If you reference `{{ my_var }}` in the template but do not map `my_var` in the variables list, the template renders an empty string for that variable with no error.

3. **Whitespace issues with block tags.** Jinja2 `{% %}` blocks often leave blank lines. Use `{%- -%}` (dash variants) to strip surrounding whitespace if clean output matters.

4. **Accessing nested fields directly.** If an upstream variable is an object, you cannot directly access `{{ object.field }}` unless you passed the specific field in the variable mapping. Map the field explicitly using `value_selector: [node_id, field_name]`.

5. **Assuming filters are available.** Dify's Jinja2 sandbox may restrict some filters. Stick to standard filters: `upper`, `lower`, `round`, `truncate`, `join`, `default`, `replace`, `length`.
