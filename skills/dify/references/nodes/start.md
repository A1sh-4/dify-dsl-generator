# Start Node

## Overview

The Start node is the entry point for every Dify Chatflow and Workflow. Every app has **exactly one** Start node — it is required and cannot be removed. The Start node defines what inputs the user or API caller must supply before the workflow begins executing. Think of it as the contract between the outside world and your automation: anything the workflow needs from the person or system that triggered it must be declared here.

In the Dify visual editor, the Start node sits at the far left of the canvas. All other nodes receive data that either flows from Start or is produced by intermediate nodes along the path.

## When to Use

The Start node is always present — you cannot opt out of it. However, you do control **what input fields** it exposes:

- **Chatflows**: The user's message is automatically captured in `{{#sys.query#}}`. You only need to declare additional input variables beyond the message itself (e.g., a language preference, a document to analyse, a numeric limit).
- **Workflows**: There is no implicit message. Every piece of external input that the workflow needs must be explicitly declared as a variable on the Start node.
- **API callers**: Whatever variables you declare on the Start node become required or optional parameters in the workflow's REST API. Callers must pass these in the request body.
- **Structured inputs**: Use Start node variables to enforce data types and validation — for example, making a language selector a `select` field instead of free text prevents unexpected values from reaching your LLM prompt.

## Input Field Types

Dify supports six distinct variable types on the Start node. Each type controls the UI widget shown to users and the validation rules applied.

### 1. text-input

Short free-form text, capped at 256 characters. Use this for names, keywords, brief instructions, or any short string.

```yaml
- label: 'User Question'
  max_length: 256
  options: []
  required: true
  type: text-input
  variable: user_question
```

Key fields:
- `max_length` (integer): Character cap, maximum 256.
- `options`: Must be present but empty (`[]`) for text-input.

### 2. paragraph

Unlimited-length text input. Use this for long prompts, pasted documents, email drafts, or any content that routinely exceeds 256 characters.

```yaml
- label: 'Document Content'
  options: []
  required: false
  type: paragraph
  variable: document_content
```

There is no `max_length` field for paragraph — the field accepts any length of text.

### 3. select

A dropdown that restricts the user to a predefined list of choices. Use this when you need controlled vocabulary — language codes, tone options, report types, etc.

```yaml
- label: 'Language'
  options:
    - English
    - Chinese
    - Spanish
  required: false
  type: select
  variable: language
```

Key fields:
- `options` (array of strings): The allowed values. The user picks one; the workflow receives the exact string.

### 4. number

Numeric input. The Dify UI renders a number spinner. Downstream nodes receive the value as a number (not a string), so arithmetic and comparisons work without type conversion.

```yaml
- label: 'Max Results'
  required: false
  type: number
  variable: max_results
```

No additional type-specific fields are required beyond `label`, `required`, `type`, and `variable`.

### 5. single-file

A file upload field accepting exactly one file. You specify which file categories are permitted and which upload methods are allowed (local disk or remote URL).

```yaml
- allowed_file_types:
    - document
    - image
  allowed_file_upload_methods:
    - local_file
    - remote_url
  label: 'Upload Document'
  max_number_of_files: 1
  required: false
  type: single-file
  variable: uploaded_file
```

Key fields: see the **File Upload Configuration** section below.

### 6. file-list

A multi-file upload field. Works identically to `single-file` but accepts more than one file per submission.

```yaml
- allowed_file_types:
    - document
    - image
  allowed_file_upload_methods:
    - local_file
  label: 'Supporting Documents'
  max_number_of_files: 5
  required: false
  type: file-list
  variable: supporting_docs
```

## Complete YAML Example

The following shows a Start node with four different variable types:

```yaml
- data:
    selected: false
    title: Start
    type: start
    variables:
      - label: 'User Question'
        max_length: 256
        options: []
        required: true
        type: text-input
        variable: user_question
      - label: 'Language'
        options:
          - English
          - Chinese
          - Spanish
        required: false
        type: select
        variable: language
      - label: 'Max Results'
        required: false
        type: number
        variable: max_results
      - allowed_file_types:
          - document
          - image
        allowed_file_upload_methods:
          - local_file
          - remote_url
        label: 'Upload Document'
        max_number_of_files: 1
        required: false
        type: single-file
        variable: uploaded_file
  height: 116
  id: 'start'
  position:
    x: 80
    y: 282
  positionAbsolute:
    x: 80
    y: 282
  selected: false
  sourcePosition: right
  targetPosition: left
  type: custom
  width: 243
```

## Output Variables

Variables declared on the Start node are referenced downstream using the pattern:

```
{{#<node_id>.<variable_name>#}}
```

For simple workflows, the Start node's `id` is often literally `'start'`, so references look like `{{#start.user_question#}}`. In more complex workflows generated programmatically, the id may be a numeric timestamp (e.g., `1732001000000`), in which case references use that timestamp.

### System Variables

In addition to user-declared variables, Dify injects a set of system variables that are always available without being declared on the Start node:

| Variable | Description |
|---|---|
| `{{#sys.query#}}` | The current user message (chatflow only) |
| `{{#sys.files#}}` | Files uploaded in the current turn (chatflow only) |
| `{{#sys.user_id#}}` | Identifier of the user who triggered the run |
| `{{#sys.app_id#}}` | The Dify application ID |
| `{{#sys.workflow_id#}}` | The workflow definition ID |
| `{{#sys.workflow_run_id#}}` | Unique identifier for this specific execution |
| `{{#sys.timestamp#}}` | Unix timestamp of when the run started |

System variables are accessed via the `sys` namespace and do not need to be declared anywhere — they are always present.

## File Upload Configuration

When using `single-file` or `file-list` variable types, three sub-fields control what the user can upload:

### allowed_file_types

Controls which categories of files are accepted. Multiple categories can be specified:

| Value | Description |
|---|---|
| `document` | PDFs, Word documents, text files, spreadsheets |
| `image` | PNG, JPG, GIF, WebP, and other image formats |
| `audio` | MP3, WAV, OGG, and other audio formats |
| `video` | MP4, MOV, AVI, and other video formats |
| `custom` | Any file type not covered by the above categories |

### allowed_file_upload_methods

Controls how the user provides the file:

| Value | Description |
|---|---|
| `local_file` | User uploads a file from their device |
| `remote_url` | User provides a URL pointing to the file |

Both methods can be allowed simultaneously by listing both values.

### max_number_of_files

An integer from 1 to 10. For `single-file`, set this to `1`. For `file-list`, set it to however many files you want to allow (up to 10).

## Key Rules

1. **One per workflow**: Every Dify Chatflow and Workflow has exactly one Start node. You cannot add a second one or delete the existing one.

2. **Chatflow sys.query is automatic**: In chatflows, `sys.query` captures the user's message automatically. Do not declare a `text-input` variable called `query` to try to replicate this — it is redundant and confusing.

3. **Variable naming conventions**: Variable names must use lowercase letters and underscores only. No spaces, no hyphens, no uppercase. Examples: `user_question`, `max_results`, `uploaded_file`.

4. **The node id**: In simple hand-authored DSL files, the Start node's `id` field is often set to the string `'start'`. When Dify auto-generates a workflow, the id is typically a 13-digit numeric timestamp. Both are valid; downstream variable references must match whichever id is used.

5. **Required vs optional**: Mark a field `required: true` only when the workflow cannot function without it. Optional fields should use sensible defaults or guard conditions downstream (e.g., an If-Else node that checks whether the optional file was provided before routing to a document-analysis branch).

6. **Text-input max_length**: The `max_length` field is mandatory for `text-input` type and must be 256 or less. For longer content, use `paragraph` instead.
