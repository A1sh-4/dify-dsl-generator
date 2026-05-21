# Dify Variable Reference Syntax

## Overview

Dify uses a special syntax to reference variables across nodes. Understanding this is critical — it is the **most common source of DSL errors**. Every time a node needs to consume the output of another node, it uses a variable reference. Misconfigured references will cause runtime failures that are often silent or cryptic.

---

## The Core Syntax

```
{{#node_id.field_name#}}
```

| Part | Value | Description |
|---|---|---|
| Opening delimiter | `{{#` | Always this exact sequence |
| node_id | e.g. `1712345678901` | The exact `id` string of the source node |
| Separator | `.` | Single dot between node_id and field_name |
| field_name | e.g. `text` | The output variable name that node produces |
| Closing delimiter | `#}}` | Always this exact sequence |

**Regex for parsing:** `\{\{#([^.#]+)\.([^#]+)#\}\}`

The `node_id` must match the `id` field of an upstream node exactly — including any numeric or UUID format. There is no aliasing: you must use the raw id string.

---

## Complete System Variables Reference

System variables are built in to every Dify app. Reference them as `{{#sys.variable_name#}}`.

| Variable | Type | Available In | Description |
|---|---|---|---|
| `sys.query` | string | chatflow | Current user message text |
| `sys.files` | array | chatflow | Files uploaded by user in current turn |
| `sys.user_id` | string | both | Unique identifier of the user |
| `sys.app_id` | string | both | Unique identifier of the app |
| `sys.workflow_id` | string | both | Unique identifier of this workflow definition |
| `sys.workflow_run_id` | string | both | Unique identifier of this specific run |
| `sys.timestamp` | number | both | Unix timestamp of when the run started |
| `sys.conversation_id` | string | chatflow only | Unique ID of the current conversation session |
| `sys.dialogue_count` | number | chatflow only | Number of turns in the current conversation |

> **Note:** `sys.conversation_id` and `sys.dialogue_count` are only available in chatflow apps. Referencing them inside a plain workflow will produce a runtime error.

---

## Variable Type Reference

All types a Dify variable can be:

| Type | Description |
|---|---|
| `string` | Plain text |
| `number` | Integer or float |
| `boolean` | `true` or `false` |
| `object` | JSON object; access fields with dot notation |
| `array[string]` | Array of strings |
| `array[number]` | Array of numbers |
| `array[object]` | Array of JSON objects |
| `file` | A single file reference |
| `array[file]` | List of file references |

When declaring variables in node configuration (e.g. start node inputs, code node outputs), use these exact type strings. Mismatched types between a producer and consumer may cause silent type coercion or runtime errors.

---

## Nested Object Access

For `object` type outputs, you can access nested fields using dot notation inside the reference:

```
{{#api_node.body.data.items[0].name#}}
```

- **Dot notation** for nested object fields: `.data.name`
- **Array indexing** uses bracket notation: `[0]`, `[1]`, etc.
- These can be combined arbitrarily deep

Example from an HTTP node returning JSON:

```
{{#http_call_1.body.results[0].title#}}
{{#http_call_1.status_code#}}
{{#http_call_1.headers.content-type#}}
```

---

## Variable Scope Rules

Variables are only accessible from nodes that appear **upstream** in the graph. A node cannot reference outputs of a node that has not yet executed.

### By node type and what each outputs:

1. **Start node** — outputs accessible from ANY downstream node; all user-defined input variables are available
2. **LLM node** — outputs: `text` (string), `usage` (object), `finish_reason` (string)
3. **Code node** — outputs: whatever variables you declare in the `outputs` block of the code node config
4. **HTTP node** — outputs: `body` (string or object depending on content-type), `status_code` (number), `headers` (object)
5. **Knowledge retrieval node** — outputs: `result` (array of chunk objects, each with `content`, `score`, `title`, and source metadata)
6. **Parameter extractor node** — outputs: one variable per declared parameter, using the parameter name as the field name
7. **Iteration node** — outputs: the collected results array after all iterations complete (field name matches the declared output)

---

## Special Variables in Special Contexts

### Inside Iteration Containers

When writing expressions or templates **inside** an iteration node's body, two implicit variables are available without the `{{# #}}` delimiters:

- Current item: `{{item}}`
- Current index: `{{index}}`

These use double curly braces without the `#` sigils and are scoped to the current iteration loop only.

### Conversation Variables (chatflow)

Conversation variables persist across turns within a single conversation session.

- **Access:** `{{#conversation.variable_name#}}`
- **Update:** via a variable-assigner node (not by direct assignment in code or LLM prompts)

### Environment Variables

Environment variables are declared in the app's settings and are available globally.

- **Access:** `{{#env.variable_name#}}`
- **Best practice:** Never hardcode sensitive values such as API keys. Always declare them as environment variables and reference them via `{{#env.api_key#}}`.

---

## The Critical Distinction: DSL References vs Jinja2 Templates

Dify uses **two completely different syntaxes** that look superficially similar. Confusing them is one of the most common DSL authoring mistakes.

| Context | Syntax | Example |
|---|---|---|
| DSL variable reference (in node config) | `{{#node_id.field#}}` | `{{#start.user_query#}}` |
| Jinja2 template (inside template-transform node body) | `{{ variable }}` | `{{ user_query }}` |
| Jinja2 conditional | `{% if condition %}` | `{% if items %}` |
| Jinja2 loop | `{% for item in list %}` | `{% for item in results %}` |

**Key rule:** Inside a `template-transform` node, the template content itself is rendered with Jinja2. However, the **inputs** that feed data into that node are still configured using DSL `{{# #}}` syntax. The two syntaxes exist at different layers and must not be mixed in the wrong context.

---

## Common Variable Reference Mistakes

1. **Wrong node_id** — copy-paste error from a different workflow; always verify the `id` field of the source node
2. **Forward reference** — referencing a node that comes after the current node in execution order; Dify does not allow this
3. **Using Jinja2 `{{ }}` in node config fields** — these fields require DSL `{{# #}}` syntax, not Jinja2
4. **Missing `#` inside delimiters** — writing `{{node_id.field}}` instead of `{{#node_id.field#}}`
5. **Missing array indexing** — writing `.result` to access the first knowledge retrieval chunk instead of `.result[0].content`
6. **Using chatflow-only variables in a workflow** — referencing `sys.conversation_id` or `sys.dialogue_count` in a plain workflow app
7. **Referencing undeclared code node outputs** — a variable must appear in the code node's `outputs` declaration block, not just be assigned inside the code body
8. **Accessing `env` variables without the `env.` prefix** — writing `{{#api_key#}}` instead of `{{#env.api_key#}}`
