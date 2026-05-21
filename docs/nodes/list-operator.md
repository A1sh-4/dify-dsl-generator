# List Operator Node

## Overview

The list-operator node filters, transforms, and manipulates arrays. It takes an array variable from an upstream node and returns a modified array based on the operation you configure. This node is the primary tool for working with collections of data in Dify workflows — whether you need to narrow a list, reshape its contents, take a subset, or sort it for display.

Typical use cases include filtering a list of uploaded files to only images before processing, extracting a specific field from every object in an API response array, taking only the top N results from a ranked list, or sorting records before presenting them to a user.

## Operations

### Filter

Removes items from the array that do not match a condition. The filter operation evaluates each element against a condition and keeps only those that pass.

**Filter operators:**

| Operator | Description | Example |
|----------|-------------|---------|
| `is` | Exact equality | `status is "active"` |
| `is not` | Not equal | `type is not "folder"` |
| `contains` | Substring or value present | `name contains "invoice"` |
| `not contains` | Substring or value absent | `mime_type not contains "video"` |
| `starts with` | String prefix match | `filename starts with "report_"` |
| `ends with` | String suffix match | `filename ends with ".pdf"` |
| `empty` | Value is null or empty string | `description empty` |
| `not empty` | Value is not null or empty | `url not empty` |
| `>` / `<` / `>=` / `<=` | Numeric comparison | `score >= 0.7` |
| `regex match` | Regular expression match | `email regex match ".*@company\.com"` |
| `type is` | Type check | `type is "image"` (for file arrays) |

### Extract (Map)

Pulls a specific field from each object in the array, producing a new array of just those values. This is equivalent to a `map` operation in other languages.

For example, given an array of result objects each with `title`, `content`, and `score` fields, you can extract just the `title` field to get an array of title strings.

### Slice

Returns a subset of the array by position. Options include:

- **First N**: Keep only the first N elements
- **Last N**: Keep only the last N elements  
- **Range**: Keep elements from index A to index B (0-based)

### Sort

Reorders the array. Configuration options:

- **Field**: The object field to sort by (for arrays of objects)
- **Order**: `asc` (ascending) or `desc` (descending)

## Input

| Field | Type | Description |
|-------|------|-------------|
| `variable` | array | Any array variable from an upstream node |

## Output Variables

| Variable | Type | Description |
|----------|------|-------------|
| `result` | array | The transformed array after the operation |

Reference downstream as `{{#list_operator_node_id.result#}}`.

## Complete YAML Example: Filter Operation

This example filters a list of uploaded files to keep only image files before passing them to an image processing node:

```yaml
- id: filter_images
  type: list-operator
  data:
    title: Filter to Image Files Only
    variable:
      variable_selector:
        - start
        - uploaded_files
    filter_by:
      enabled: true
      conditions:
        - variable: mime_type
          comparison_operator: contains
          value: "image/"
    order_by:
      enabled: false
    limit:
      enabled: false
    extract:
      enabled: false
```

## YAML Example: Extract Field from API Response

Given an API response that returns an array of objects like `[{"id": 1, "name": "Alice", "score": 0.9}, ...]`, extract just the `name` field:

```yaml
- id: extract_names
  type: list-operator
  data:
    title: Extract Names from Results
    variable:
      variable_selector:
        - http_node
        - body.results
    extract:
      enabled: true
      field: name
    filter_by:
      enabled: false
    order_by:
      enabled: false
    limit:
      enabled: false
```

## YAML Example: Slice and Sort

Take the top 5 results sorted by score descending:

```yaml
- id: top_results
  type: list-operator
  data:
    title: Top 5 Results by Score
    variable:
      variable_selector:
        - knowledge_retrieval
        - result
    order_by:
      enabled: true
      field: score
      direction: desc
    limit:
      enabled: true
      size: 5
      offset: 0
    filter_by:
      enabled: false
    extract:
      enabled: false
```

## Pattern: Filter File List to Images

```yaml
# Start node accepts a list of files
# → list-operator filters to images only
# → iteration processes each image

- id: filter_to_images
  type: list-operator
  data:
    variable:
      variable_selector:
        - start
        - files
    filter_by:
      enabled: true
      conditions:
        - variable: mime_type
          comparison_operator: starts_with
          value: "image/"
```

## Pattern: Extract Field from API Response Array

When an HTTP node returns `{"items": [{"url": "...", "title": "..."}, ...]}`, extract just the URLs:

```yaml
- id: extract_urls
  type: list-operator
  data:
    variable:
      variable_selector:
        - http_request
        - body.items
    extract:
      enabled: true
      field: url
```

## Common Mistakes

1. **Applying list-operator to a non-array variable.** The input must be an array. If your upstream node returns a single object or string, the node will error. Use parameter-extractor or an HTTP node that returns arrays.

2. **Chaining multiple operations — only one operation type applies.** If you enable both filter and extract, only one takes effect depending on the node's evaluation order. Use two separate list-operator nodes in sequence if you need to filter and then extract.

3. **Using 0-based vs 1-based indexing for slice range.** Dify's list-operator uses 0-based indexing for range slicing. Element 0 is the first element.

4. **Sorting objects without specifying a field.** If the array contains objects and you enable sort without specifying the `field` property, sorting may produce unexpected results or errors.

5. **Expecting list-operator to handle nested arrays.** The node operates on a single-level array. If each array element is itself an array, you need to process that nesting with an iteration node or a code node.
