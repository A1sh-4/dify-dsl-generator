# Template Transform Node

## Overview

The template-transform node renders a Jinja2 template using variables from upstream nodes and produces a single `output` string. It is the standard output formatter in Dify — use it as the second-to-last node in almost every flow to produce styled, structured output before the `answer` or `end` node.

The output can be plain text, Markdown, HTML, or a mix of all three. It can contain static styled cards, dynamic tables built from lists, collapsible accordion sections, interactive forms, and one-click action buttons — rendered directly in the Dify chat interface.

---

## Supported Input Variable Types

The `variables` array can receive any of these types from upstream nodes:

| Type | Description | Common source |
|---|---|---|
| `string` | Plain text, raw Markdown, or HTML | LLM output, code node, start node |
| `number` | Integer or float | Code node calculation, parameter-extractor |
| `boolean` | `true` or `false` | If-else result, code node |
| `object` | Key-value dictionary (JSON object) | Structured LLM output, API response parsed by code node |
| `array[string]` | List of text items | Code node, LLM structured output |
| `array[number]` | List of numeric values | Code node |
| `array[boolean]` | List of true/false values | Code node |
| `array[object]` | List of dictionaries — most common for RAG results, database rows, structured LLM outputs | Knowledge retrieval, code node, HTTP response parsed by code |

For `array[object]` inputs, access fields inside the loop with `{{ item['key'] }}` or `{{ item.key }}`.

---

## Structured-then-Rendered Input Pattern

When the upstream LLM node uses `structured_output_enabled: true`, its full parsed JSON response is available as the `structured_output` field. Map the entire object to one template variable — then use Jinja2 dot notation to navigate nested keys, arrays, and objects.

**YAML wiring:**
```yaml
variables:
  - value_selector:
      - 'llm_node_id'
      - structured_output       # field exposed by the LLM node — NOT "output"
    value_type: object           # required when consuming a structured output object
    variable: analysis_result    # user-chosen descriptive name; use in Jinja2 as {{ analysis_result.field }}
```

**Jinja2 access patterns:**
```jinja2
{# Top-level string field #}
{{ analysis_result.summary }}

{# Nested object field #}
{{ analysis_result.achievement_status.annual_target_rate }}

{# Array of objects — iterate #}
{%- for kpi in analysis_result.achievement_status.process_kpis -%}
  {{ kpi.metric_name }}: {{ kpi.current_value }} / {{ kpi.target_value }}
{%- endfor -%}

{# Array of strings — iterate directly #}
{%- for trend in analysis_result.analysis_results.deal_trends -%}
  <li>{{ trend }}</li>
{%- endfor -%}
```

Map `structured_output` as a whole — that is the field name exposed by the LLM node when structured output is enabled. Choose a descriptive `variable:` name that says what the data represents (e.g., `analysis_result`, `kpi_report`, `pipeline_summary`) rather than a generic name like `data`. Inside the template, access only the fields you actually need. Use `analysis_result.field` for what each section requires and ignore the rest.

**Variable naming rule (applies to both template-transform and code nodes):**

The `variable:` name in the `variables` array is yours to define — it is not fixed by Dify. Choose a name that communicates what the data contains:

| Instead of | Use |
| --- | --- |
| `data` | `kpi_report`, `analysis_result`, `pipeline_summary` |
| `result` | `extracted_text`, `classification_output`, `search_result` |
| `input` | `user_query`, `uploaded_doc`, `form_fields` |

For code nodes: the `variable:` in the `outputs` list must **exactly match** the dict key your Python `main()` returns — this is a correctness requirement, not just a naming preference.

---

## Critical Distinction: Two Syntaxes

**Inside the Jinja2 template string** — use plain Jinja2 double-brace syntax:
```
{{ variable_name }}
{% if condition %}...{% endif %}
```

**In the YAML node wiring** (mapping upstream node outputs to this node) — use Dify's reference syntax:
```
value_selector: ["node_id", "field_name"]
```

Never write `{{#node_id.field#}}` inside the template string. That syntax only works in YAML fields outside the template.

---

## Whitespace Rules — HTML vs Pure Markdown

The rules are completely different depending on whether your template outputs HTML or pure Markdown. Choose one approach per template — mixing them is where problems occur.

---

### Pure Markdown Templates — blank lines are fine

If your template outputs only Markdown (no `<div>`, `<table>`, or other HTML tags), Markdown handles whitespace naturally. Blank lines create paragraph breaks exactly as expected. You can write the template like a normal document:

```jinja2
**{{ title }}**

{{ summary }}

{% if items %}
Items found: {{ items|length }}
{% for item in items %}
- {{ item.name }}: {{ item.value }}
{% endfor %}
{% endif %}
```

Blank lines between sections, between paragraphs, between a heading and its body — all fine in pure Markdown output.

---

### HTML Templates — strict no-blank-line rule

When your template is wrapped in HTML elements (`<div>`, `<table>`, `<span>`, etc.), blank lines become destructive.

**Why it breaks:** Dify's Markdown parser aggressively wraps any text it sees between blank lines inside `<p>` tags. When this happens inside a custom HTML layout, the injected `<p>` tags destroy the structure and everything after the blank line may stop rendering.

**No blank lines anywhere in HTML template code:**
```jinja2
{# Wrong — blank line inside HTML #}
<div style="padding:16px;">

  <h3>{{ title }}</h3>

</div>

{# Correct — no blank lines #}
<div style="padding:16px;">
  <h3>{{ title }}</h3>
</div>
```

**Use `{%- -%}` dash operators to strip newlines Jinja tags produce:**
- `{%- tag %}` — strips whitespace/newline before the tag
- `{% tag -%}` — strips whitespace/newline after the tag
- `{%- tag -%}` — strips both sides — use this on all loop and conditional tags inside HTML

```jinja2
<tbody>
{%- for row in results %}
  <tr>
    <td>{{ row['name'] }}</td>
    <td>{{ row['value'] }}</td>
  </tr>
{%- endfor %}
</tbody>
```

**Use `<br>` for visual spacing, not blank lines:**
```jinja2
{# Wrong #}
<p>First paragraph.</p>

<p>Second paragraph.</p>

{# Correct #}
<p>First paragraph.</p><br>
<p>Second paragraph.</p>
```

**Also applies inside HTML — `\n` in variable content:**
If a variable contains newlines (e.g. LLM output), inject it into HTML with `| replace('\n', '<br>')` so the line breaks render visually:
```jinja2
<p>{{ llm_text | replace('\n', '<br>') }}</p>
```
This is only needed when injecting the variable into an HTML context. In a pure Markdown template, `{{ llm_text }}` renders newlines naturally.

---

## Jinja2 Features Supported

### Variable Output

```jinja2
{{ variable_name }}
{{ obj.property }}
{{ obj['key with spaces'] }}
```

### Conditionals

```jinja2
{% if status == 'success' %}
Operation completed successfully.
{% elif status == 'partial' %}
Completed with warnings.
{% else %}
An error occurred.
{% endif %}
```

Null / empty guard pattern (always use this before rendering a section that may be empty):
```jinja2
{% if results and results|length > 0 %}
... render results ...
{% endif %}
```

**Ternary expression** — inline if/else that produces a value:
```jinja2
{{ 'Achieved' if score >= 100 else 'Not achieved' }}
{{ '#16a34a' if is_good else '#dc2626' }}
```

**Containment check (`in`)** — tests if a substring exists in a string, or an item exists in a list:
```jinja2
{% if '未達' in kpi.is_achieved %}
{%- set is_unmet = '未達' in kpi.is_achieved -%}
{% if 'error' in status_message %}
```

**Conditional CSS values** — compute CSS colors or styles based on data, then inject into `style="..."`. This is the idiomatic way to produce color-coded status cards:
```jinja2
{%- set is_unmet = '未達' in kpi.is_achieved -%}
{%- set badge_color = '#dc2626' if is_unmet else '#16a34a' -%}
{%- set bg_color = '#fef2f2' if is_unmet else '#f0fdf4' -%}
<div style="background:{{ bg_color }}; border-left:4px solid {{ badge_color }}; padding:14px; border-radius:6px;">
  <div style="color:{{ badge_color }}; font-weight:bold;">{{ kpi.is_achieved }}</div>
</div>
```

Always compute CSS values with `{%- set -%}` (both dashes) immediately before the HTML element that uses them, and keep no blank lines between the set tags and the HTML.

### For Loops

```jinja2
{%- for item in items %}
- {{ item.name }}: {{ item.value }}
{%- endfor %}
```

Access loop metadata inside the loop:
- `{{ loop.index }}` — 1-based position
- `{{ loop.index0 }}` — 0-based position
- `{{ loop.first }}` — true on first iteration
- `{{ loop.last }}` — true on last iteration

### Variable Assignment

Assign a simple value:
```jinja2
{% set count = items|length %}
Total: {{ count }} items
```

Capture a block of content into a variable (section accumulation pattern):
```jinja2
{%- set sections = "" -%}
{% if section_a_data %}
{% set section_a %}
**Section A:** {{ section_a_data|length }} items
{% endset %}
{% set sections = sections + section_a + "\n---\n" %}
{% endif %}
{% if sections|trim != "" %}
{{ sections }}
{% else %}
No data found.
{% endif %}
```

This pattern lets you build a multi-section report conditionally, appending only sections that have data.

### Comments

Comments are stripped from the rendered output entirely:
```jinja2
{# This is a comment — will not appear in output #}
{# ===== Section: Results ===== #}
```

### Filters

| Filter | Example | Result |
|---|---|---|
| `length` | `{{ items\|length }}` | Count of items in a list |
| `default` | `{{ val\|default('N/A') }}` | Fallback if value is None/undefined |
| `join` | `{{ list\|join(', ') }}` | Joins list items with separator |
| `map(attribute=)` | `{{ list\|map(attribute='name') }}` | Extracts a field from each object |
| `map('default', x)` | `{{ list\|map('default', 0) }}` | Applies default across a mapped list |
| `map('int')` | `{{ list\|map('int') }}` | Converts each item to integer |
| `sum` | `{{ numbers\|sum }}` | Sum of numeric list |
| `unique` | `{{ list\|unique }}` | Removes duplicates |
| `list` | `{{ generator\|list }}` | Converts to list |
| `groupby` | `{% for g in list\|groupby('dept') %}` | Groups list by field value |
| `trim` | `{{ text\|trim }}` | Strips leading/trailing whitespace |
| `int` | `{{ val\|int }}` | Converts to integer |
| `upper` | `{{ text\|upper }}` | Uppercase |
| `lower` | `{{ text\|lower }}` | Lowercase |
| `round` | `{{ num\|round(2) }}` | Rounds to N decimal places |
| `truncate` | `{{ text\|truncate(100) }}` | Truncates string |
| `replace` | `{{ text\|replace('a','b') }}` | String replacement |
| `string` | `{{ value\|string }}` | Convert number or boolean to string for display |
| `upper` | `{{ text\|upper }}` | Uppercase |
| `lower` | `{{ text\|lower }}` | Lowercase |
| `round` | `{{ num\|round(2) }}` | Rounds to N decimal places |
| `truncate` | `{{ text\|truncate(100) }}` | Truncates string to N characters |

**Common string manipulation patterns:**

Convert raw newlines to HTML line breaks (for LLM text injected into an HTML context):
```jinja2
{{ llm_text | replace('\n', '<br>') }}
```

Insert visual breaks at specific sentence-ending characters (e.g. Japanese `。`):
```jinja2
{{ text | replace('。', '。<br><br>') }}
```

Replace separator characters with display-friendly equivalents:
```jinja2
{{ tags | replace('、', ' / ') }}
{{ csv_line | replace(',', ' · ') }}
```

Convert a number or boolean to a display string:
```jinja2
{{ score | string }}
{{ is_approved | string | upper }}
```

**Chaining filters** — filters can be chained left to right:
```jinja2
{{ items | map(attribute='score') | map('default', 0) | map('int') | sum }}
{{ items | map(attribute='name') | unique | list | join(', ') }}
```

### Mathematical Operations

Basic arithmetic can be performed directly in the template without a code node:

```jinja2
{{ price * quantity }}
{{ total / count | round(2) }}
{{ (score * 100) | round(1) }}%
{{ items | map(attribute='amount') | map('int') | sum }}
```

Operators supported: `+`, `-`, `*`, `/`, `//` (integer division), `%` (modulo), `**` (power).

Use parentheses to control order: `{{ (a + b) * c }}`.

### Groupby Pattern

Groups a list of objects by a field, then aggregates within each group:
```jinja2
{%- for group in results | groupby('department') %}
| {{ group.grouper }} | {{ group.list | length }} | {{ group.list | map(attribute='amount') | map('int', 0) | sum }} |
{%- endfor %}
```
- `group.grouper` — the value of the groupby field
- `group.list` — the list of items in this group

---

## Output Formats

The template can output any combination of Markdown, HTML, and interactive elements.

### Markdown

```jinja2
**{{ title }}**
*{{ subtitle }}*
[Link text]({{ url_variable }})
```

Code block (the variable content renders inside the fence):
```
\```text
{{ download_url }}
\```
```

Horizontal rule: `---` or `<hr>`

Markdown table (use `{%- -%}` on row loop to prevent blank rows):
```jinja2
| No. | Name | Value |
| :--- | :--- | :--- |
{%- for row in items %}
| {{ loop.index }} | {{ row['name'] }} | {{ row['value'] | default('N/A') }} |
{%- endfor %}
```

### HTML

Full inline CSS is supported. Use HTML when you need precise styling control.

**IMPORTANT — no `<style>` blocks:** External stylesheets and `<style>` tags are stripped or scoped incorrectly. All styling must be written as inline `style="..."` attributes on individual elements.

**Supported CSS properties (confirmed working):**
- Layout: `display:flex`, `gap`, `align-items`, `justify-content`, `flex-wrap`, `flex-direction`, `display:inline-block`
- Backgrounds: `background-color`, `background:linear-gradient(...)`, `rgba()` transparency
- Box model: `border-radius`, `border`, `border-top` (accent line), `box-shadow`, `padding`, `margin`, `max-width`, `width`, `min-width`
- Typography: `font-family`, `font-size`, `font-weight`, `color`, `line-height`, `letter-spacing`, `text-align`
- Text wrapping: `word-wrap:break-word`, `word-break:break-word`, `white-space:pre-wrap`
- Table layout: `table-layout:fixed` (use with `word-wrap` to enforce column widths)

**Section card pattern** — `border-top: 5px solid [accent-color]` on a card creates a strong visual section divider. Use different accent colors per section to produce a dashboard-like multi-section layout:
```html
<div style="background:#ffffff; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05); padding:20px; margin-bottom:20px; border:1px solid #e2e8f0; border-top:5px solid #1c64f2;">
  {# blue section — achievement status #}
</div>
<div style="background:#fffbeb; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05); padding:20px; margin-bottom:20px; border:1px solid #fde68a; border-top:5px solid #d97706;">
  {# amber section — focus areas #}
</div>
<div style="background:#ffffff; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05); padding:20px; margin-bottom:20px; border:1px solid #e2e8f0; border-top:5px solid #8b5cf6;">
  {# purple section — next actions #}
</div>
```

**Hyperlinks** — standard `<a>` tags work for external URLs, OAuth flows, and deep-links:
```html
<a href="{{ url_variable }}" target="_blank">Open link</a>
```
Dynamic URLs from variables work fully. Use `target="_blank"` to open in a new tab.

**Inline SVGs** — most stable way to include icons; scale perfectly and can be colored with `fill="currentColor"` to inherit the parent element's text color:
```html
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
</svg>
```
Use `fill="currentColor"` on the `<svg>` or `<path>` to inherit color from the parent CSS `color` property.

**Styled table — fixed column widths:**

Use `table-layout:fixed` with `word-wrap:break-word; word-break:break-word` on the table so long text wraps within its column instead of overflowing. Set `width:%` on each `<th>` to control proportions (must sum to 100%):
```html
<div style="border-radius:8px; border:1px solid #e2e8f0; overflow:hidden;">
<table style="table-layout:fixed; width:100%; border-collapse:collapse; font-size:14px; background:#ffffff; word-wrap:break-word; word-break:break-word;">
<thead>
<tr style="background:#f8fafc; border-bottom:2px solid #cbd5e1;">
<th style="width:25%; padding:12px; font-weight:bold; color:#0f172a; text-align:left;">Column A</th>
<th style="width:15%; padding:12px; font-weight:bold; color:#0f172a; text-align:left;">Column B</th>
<th style="width:60%; padding:12px; font-weight:bold; color:#0f172a; text-align:left;">Column C</th>
</tr>
</thead>
<tbody>
{%- for row in items -%}
<tr style="border-bottom:1px solid #e2e8f0;">
<td style="padding:12px; color:#1e293b; font-weight:bold;">{{ row.field_a }}</td>
<td style="padding:12px; color:#64748b;">{{ row.field_b }}</td>
<td style="padding:12px; color:#334155; line-height:1.5;">{{ row.field_c }}</td>
</tr>
{%- endfor -%}
</tbody>
</table>
</div>
```

Wrap the table in a `<div style="border-radius:8px; border:1px solid ...; overflow:hidden;">` to get rounded corners — `border-radius` on a table itself is unreliable across renderers.

**Collapsible accordion** (`<details>`/`<summary>`):
```html
<details>
<summary><strong>Click to expand results</strong></summary>
{{ content_variable }}
</details>
```
By default only the `<summary>` text is visible. Clicking it reveals the content inside `<details>`.

**Styled span in table headers** (for colored column headers):
```html
<span style="color:blue; min-width:100px; display:inline-block">Column Name</span>
```

### Mixed Markdown + HTML

Markdown and HTML can be mixed freely in the same template:
```jinja2
{% if status == 'success' %}
[Open in Google Sheets]({{ sheet_url }})
{% else %}
**Error:** Save the output manually.
{% endif %}
<hr>
<details>
<summary><strong>Full Report (click to expand)</strong></summary>
{{ report_text }}
</details>
<hr>
{{ mermaid_diagram_code }}
```

### Interactive Elements in Output

The template-transform output can contain interactive buttons and forms. These render as clickable UI elements in the chat.

**Note on buttons:** `data-message` buttons are most reliably used in the conversation opener. In template-transform output they render visually but may behave differently depending on the Dify version. Forms with submit buttons work reliably in both contexts. When in doubt, use a form for template-transform interactive output.

**One-click action button:**
```html
<button data-variant="primary" data-message="text that gets sent when clicked">
  Button label — must match data-message exactly
</button>
```
Button variants: `primary` | `secondary` | `secondary-accent` | `ghost` | `ghost-accent` | `warning` | `tertiary`
Button sizes: `data-size="small"` | `"medium"` | `"large"`

**Dynamic form rendered from a loop:**
```html
<form data-format="text">
{%- for task in task_list %}
<label style="display:block; margin-top:15px; font-weight:bold;">{{ loop.index }}. {{ task.name }}</label>
<input type="select" name="{{ loop.index }}" value="No" data-options='["No", "Yes"]' />
{%- endfor %}
<button data-variant="primary" style="margin-top:16px; padding:10px 20px;">Submit</button>
</form>
```

All form input types: `text`, `email`, `password`, `number`, `date`, `time`, `select` (with `data-options='["A","B"]'`), `checkbox`, `textarea`.
Always use `data-format="text"` — never `data-format="json"` (produces unreadable output).

---

## YAML Structure

```yaml
- data:
    desc: ""
    selected: false
    title: "Format Output"
    type: template-transform
    template: |
      <div style="font-family:system-ui,sans-serif; padding:16px; border-radius:8px; background:#f8fafc;">
        <h3 style="margin:0 0 12px 0;">{{ title }}</h3>
        <p>{{ summary }}</p>
        {% if items and items|length > 0 %}
        <ul>
        {%- for item in items %}
          <li>{{ item }}</li>
        {%- endfor %}
        </ul>
        {% endif %}
      </div>
    variables:
      - value_selector:
          - "[source_node_id]"
          - field_name
        variable: title
      - value_selector:
          - "[source_node_id]"
          - field_name
        variable: summary
      - value_selector:
          - "[source_node_id]"
          - field_name
        variable: items
  height: 54
  id: "[13-digit node ID]"
  position:
    x: [x]
    y: [y]
  positionAbsolute:
    x: [x]
    y: [y]
  selected: false
  sourcePosition: right
  targetPosition: left
  type: custom
  width: 244
```

Key points:
- The `template` field uses YAML block scalar (`|`) for multi-line content
- The `variables` array maps upstream node outputs to local Jinja2 variable names
- `value_selector` is a 2-element array: `["node_id", "field_name"]`
- The node outputs exactly one field: `output` (referenced downstream as `{{#node_id.output#}}`)
- The answer node should reference `{{#template_node_id.output#}}`, not raw LLM text

---

## Complete Examples

### Example 1 — Conditional status + collapsible report

```jinja2
{% if status == 'success' %}
✅ **Process completed successfully.**
[View results in Google Sheets]({{ sheet_url }})
{% else %}
❌ **An error occurred.** Please save the output below manually.
{% endif %}
<hr>
<details>
<summary><strong>Full report — click to expand</strong></summary>
{{ report_text }}
</details>
```

### Example 2 — Dynamic table from list with groupby

```jinja2
**Results: {{ results|length }} records**
<details>
<summary>View table</summary>

| No. | Company | Department | Count |
| :--- | :--- | :--- | :--- |
{%- for group in results | groupby('department') %}
| {{ loop.index }} | {{ group.list | map(attribute='company') | unique | list | join(', ') }} | {{ group.grouper }} | {{ group.list | length }} |
{%- endfor %}

</details>
```

### Example 3 — Multi-section conditional report (section accumulation)

```jinja2
{%- set sections = "" -%}
{# Section A #}
{% if data_a and data_a|length > 0 %}
{% set sec_a %}
**Section A:** {{ data_a|length }} items
| Name | Value |
| :--- | :--- |
{%- for row in data_a %}
| {{ row['name'] }} | {{ row['value'] | default('N/A') }} |
{%- endfor %}
{% endset %}
{% set sections = sections + sec_a + "\n---\n" %}
{% endif %}
{# Section B #}
{% if data_b and data_b|length > 0 %}
{% set sec_b %}
**Section B:** {{ data_b|length }} items
{% endset %}
{% set sections = sections + sec_b + "\n---\n" %}
{% endif %}
{# Final output #}
{% if sections|trim != "" %}
{{ sections }}
{% else %}
No data found for any section.
{% endif %}
```

### Example 4 — Dynamic form from upstream list

```jinja2
<p>Select an option for each item and click Submit.</p>
<form data-format="text">
{%- for task in task_list %}
<label style="display:block; margin-top:15px; font-weight:bold;">{{ loop.index }}. {{ task.name }}</label>
<input type="select" name="{{ loop.index }}" value="Not needed" data-options='["Not needed", "Use AI"]' />
{%- endfor %}
<button data-variant="primary" style="margin-top:16px; padding:10px 20px;">Submit decisions</button>
</form>
```

### Example 5 — Multi-section dashboard from structured LLM output

This example renders a full dashboard from a `data` variable that holds the parsed JSON object produced by an LLM node with `structured_output_enabled: true`. It shows: multi-colored section cards with `border-top`, conditional badge coloring, `<details>` accordion, and a fixed-column table.

**Variable mapping (YAML):**
```yaml
variables:
  - value_selector:
      - 'llm_node_id'
      - structured_output       # the field exposed by the LLM node with structured_output_enabled: true
    value_type: object
    variable: data              # NOTE: "data" is used here only because the Jinja2 template
                                # below has 40+ {{ data.xxx }} references that would all need
                                # updating. In YOUR flows, always use a descriptive name like
                                # "kpi_report", "analysis_result", or "pipeline_summary".
```

**Template:**
```jinja2
<div style="font-family:system-ui,sans-serif; max-width:800px; color:#222222;">
<div style="background:#ffffff; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05); padding:20px; margin-bottom:20px; border:1px solid #e2e8f0; border-top:5px solid #1c64f2;">
<h3 style="margin:0 0 16px 0; color:#1e3a8a; font-size:18px;">📊 Achievement Status</h3>
<div style="background:#eff6ff; padding:16px; border-radius:8px; margin-bottom:16px; color:#1e40af; font-size:15px; line-height:1.6;">
<strong style="display:block; margin-bottom:8px;">Annual Target Rate:</strong>
{{ data.achievement_status.annual_target_rate | replace('。', '。<br><br>') }}
</div>
<div style="display:flex; flex-direction:column; gap:8px;">
{%- for kpi in data.achievement_status.process_kpis -%}
{%- set is_unmet = '未達' in kpi.is_achieved -%}
{%- set badge_color = '#dc2626' if is_unmet else '#16a34a' -%}
{%- set bg_color = '#fef2f2' if is_unmet else '#f0fdf4' -%}
<div style="background:{{ bg_color }}; padding:14px; border-radius:6px; font-size:15px; border-left:4px solid {{ badge_color }};">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
<strong style="color:#0f172a; font-size:16px;">{{ kpi.metric_name }}</strong>
<div style="color:#ffffff; background:{{ badge_color }}; padding:4px 10px; border-radius:12px; font-weight:bold; font-size:13px;">{{ kpi.is_achieved }}</div>
</div>
<div style="font-size:14px; color:#475569;"><strong>Current:</strong> {{ kpi.current_value }} / <strong>Target:</strong> {{ kpi.target_value }}<br><span style="color:#334155;">{{ kpi.calculation_details }}</span></div>
</div>
{%- endfor -%}
</div>
</div>
<details style="margin-bottom:20px; background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:20px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
<summary style="font-weight:bold; cursor:pointer; color:#1e3a8a; font-size:18px; outline:none;">📈 Analysis Results (click to expand)</summary>
<div style="margin-top:16px; line-height:1.6; font-size:15px; border-top:1px dashed #cbd5e1; padding-top:16px;">
<h4 style="margin:0 0 8px 0; color:#334155; font-size:16px;">Deal Trends</h4>
<ul style="margin:0 0 16px 0; padding:12px 12px 12px 32px; color:#222222; background:#f8fafc; border-radius:6px;">
{%- for trend in data.analysis_results.deal_trends -%}
<li style="margin-bottom:6px;">{{ trend }}</li>
{%- endfor -%}
</ul>
<h4 style="margin:0 0 8px 0; color:#334155; font-size:16px;">Issues</h4>
<ul style="margin:0; padding-left:20px; color:#222222;">
{%- for issue in data.analysis_results.extracted_issues -%}
<li style="margin-bottom:8px;">{{ issue }}</li>
{%- endfor -%}
</ul>
</div>
</details>
<div style="background:#ffffff; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05); padding:20px; margin-bottom:20px; border:1px solid #e2e8f0; border-top:5px solid #8b5cf6;">
<h3 style="margin:0 0 16px 0; color:#5b21b6; font-size:18px;">🚀 Next Actions</h3>
{%- for group in data.next_actions.timeline_groups -%}
<h4 style="margin:0 0 10px 0; color:#4338ca; font-size:16px; background:#e0e7ff; padding:6px 12px; border-radius:6px; display:inline-block;">⏱️ {{ group.timeframe }}</h4>
<ul style="margin:0 0 20px 0; padding-left:20px; font-size:15px; line-height:1.6; color:#222222;">
{%- for action in group.actions -%}
<li style="margin-bottom:6px;">{{ action }}</li>
{%- endfor -%}
</ul>
{%- endfor -%}
<h4 style="margin:0 0 10px 0; color:#334155; font-size:16px;">Reassignments</h4>
<div style="border-radius:8px; border:1px solid #e2e8f0; overflow:hidden;">
<table style="table-layout:fixed; width:100%; border-collapse:collapse; font-size:14px; background:#ffffff; word-wrap:break-word; word-break:break-word;">
<thead>
<tr style="background:#f8fafc; border-bottom:2px solid #cbd5e1;">
<th style="width:30%; padding:12px; font-weight:bold; color:#0f172a; text-align:left;">Company</th>
<th style="width:20%; padding:12px; font-weight:bold; color:#0f172a; text-align:left;">Old Owner</th>
<th style="width:20%; padding:12px; font-weight:bold; color:#0f172a; text-align:left;">New Owner</th>
<th style="width:30%; padding:12px; font-weight:bold; color:#0f172a; text-align:left;">Reason</th>
</tr>
</thead>
<tbody>
{%- for r in data.next_actions.reassignments -%}
<tr style="border-bottom:1px solid #e2e8f0;">
<td style="padding:12px; color:#1e293b; font-weight:bold;">{{ r.company_name }}</td>
<td style="padding:12px; color:#64748b;">{{ r.old_owner }}</td>
<td style="padding:12px; color:#0369a1; font-weight:bold;">{{ r.new_owner }}</td>
<td style="padding:12px; color:#334155; line-height:1.5;">{{ r.reason }}</td>
</tr>
{%- endfor -%}
</tbody>
</table>
</div>
</div>
</div>
```

Key patterns demonstrated:
- **`border-top:5px solid [color]`** — distinct accent per section card
- **`{%- set badge_color = '#dc2626' if is_unmet else '#16a34a' -%}`** — conditional CSS value
- **`'未達' in kpi.is_achieved`** — substring containment to drive conditional logic
- **`| replace('。', '。<br><br>')`** — insert breaks at specific characters
- **`<details>/<summary>`** — collapsible accordion section
- **`table-layout:fixed` + `word-wrap:break-word`** — fixed-column table that wraps long text
- **`<div style="overflow:hidden; border-radius:8px;">`** wrapping table for rounded corners

---

## Common Mistakes

1. **Blank lines in HTML templates** — the #1 rendering killer for HTML output. A blank line inside an HTML-wrapped template causes Dify's Markdown parser to inject `<p>` tags that break the layout. Use `<br>` for spacing, `{%- -%}` to strip tag newlines. This rule does NOT apply to pure-Markdown templates — blank lines are fine there.

2. **Using `{{#...#}}` inside the template string** — this only works in YAML fields, not inside the Jinja2 template. Inside the template always use `{{ variable_name }}`.

3. **Not declaring a variable in `variables`** — if you use `{{ my_var }}` but do not add `my_var` to the `variables` array, it renders empty silently.

4. **Using `data-format="json"` in forms** — the JSON output is unreadable in the chat window. Always use `data-format="text"`.

5. **Accessing object keys with special characters without bracket notation** — use `{{ row['key with spaces'] }}` not `{{ row.key with spaces }}`.

6. **Forgetting null guard before rendering a section** — always wrap conditional sections with `{% if var and var|length > 0 %}` to avoid rendering empty tables or headers with no content.

7. **Using a `<style>` block for CSS** — `<style>` tags are stripped or scoped incorrectly. All CSS must be inline `style="..."` on individual elements.

8. **Not converting LLM newlines to `<br>`** — if an LLM node returns text with `\n` line breaks and you inject it directly into HTML, the newlines become invisible. Use `{{ text | replace('\n', '<br>') }}` to render them as visible line breaks.

9. **Doing math in a code node when the template can handle it** — simple arithmetic (`price * qty`, `total / count | round(2)`) can be done directly in Jinja2. Only use a code node for complex logic that Jinja2 cannot express.
