# Human Input Node

## Overview

The human-input node pauses workflow execution and presents a form to the user, waiting for them to submit data before the workflow continues. It is designed for workflows that require human interaction mid-process — approval decisions, data collection that cannot be inferred from context, clarification requests, or any point where automated processing must yield to human judgment.

When execution reaches a human-input node, the workflow suspends. The user sees the configured form and fills it out. Upon submission, the workflow resumes from the human-input node with the submitted values available as output variables.

## When to Use

Use human-input when:

- You need explicit human approval before proceeding (e.g., approve a draft before sending)
- Data is needed mid-workflow that the user must provide interactively
- You want to present intermediate results and ask a follow-up question
- The workflow involves multi-step forms where later steps depend on earlier answers

Do not use human-input in fully automated pipelines where no user interaction is expected, or in API-triggered workflows where there is no interactive user session present.

## How It Works

1. Workflow execution reaches the human-input node
2. The configured form is presented to the user in the application interface
3. Execution pauses — no timeout by default, but a timeout can be configured
4. The user fills out the form and submits
5. Workflow resumes, and submitted values are available as the node's output variables

## Form Field Types

| Type | Description | Example Use |
|------|-------------|-------------|
| `text` | Single-line or multi-line text input | Name, reason, notes |
| `number` | Numeric input with optional min/max | Quantity, budget, rating |
| `select` | Dropdown or radio buttons from a defined option list | Approval decision, category |
| `checkbox` | Boolean toggle (true/false) | Agree to terms, enable feature |

Each field can be marked as required or optional. Required fields must be filled before the user can submit.

## Field Configuration

For each field in the form:

| Property | Description |
|----------|-------------|
| `variable` | The output variable name for this field |
| `label` | Display label shown to the user |
| `type` | One of: `text`, `number`, `select`, `checkbox` |
| `required` | Whether the field must be filled |
| `options` | For `select` type — list of allowed values |
| `default` | Default value pre-filled in the form |
| `placeholder` | Hint text shown inside the empty field |

## Timeout Configuration

You can configure a timeout (in seconds) after which the workflow either fails or takes a default action. Without a timeout, the workflow waits indefinitely for the user's response.

```yaml
timeout:
  enabled: true
  seconds: 300
  action: fail  # or: use_default
```

If `action: use_default`, each field's `default` value is used and the workflow continues automatically when the timeout expires.

## Output Variables

Each form field becomes a separate output variable, accessible by the field's `variable` name:

```
{{#human_input_node_id.approval_decision#}}
{{#human_input_node_id.reviewer_notes#}}
```

## Limitations

The human-input node works best in web application deployments where a UI can render the form. In API mode (calling the workflow via API without a front-end UI), the pause-and-wait mechanism may not function correctly — API callers receive a suspended state response and must poll or use webhooks to detect when to resume. This makes human-input poorly suited for fully programmatic API integrations.

Human-input is not available in schedule-triggered or webhook-triggered headless workflows.

## Complete YAML Example: Document Approval Workflow

This example processes a document, presents a draft summary to the user, and asks for approval before sending:

```yaml
nodes:
  - id: start
    type: start
    data:
      variables:
        - variable: document
          type: file
          label: Upload document for review
          required: true

  - id: extract_text
    type: document-extractor
    data:
      variable_selector:
        - start
        - document

  - id: generate_summary
    type: llm
    data:
      title: Generate Summary Draft
      prompt_template:
        - role: user
          text: |
            Summarize this document in 3-5 bullet points:
            {{#extract_text.text#}}

  - id: approval_form
    type: human-input
    data:
      title: Review and Approve Summary
      description: |
        Please review the generated summary below and indicate your decision.
        
        Summary:
        {{#generate_summary.text#}}
      timeout:
        enabled: true
        seconds: 600
        action: fail
      inputs:
        - variable: decision
          label: Approval Decision
          type: select
          required: true
          options:
            - label: Approve
              value: approved
            - label: Request Changes
              value: changes_requested
            - label: Reject
              value: rejected
        - variable: reviewer_notes
          label: Notes for the author
          type: text
          required: false
          placeholder: Optional feedback or requested changes

  - id: check_decision
    type: if-else
    data:
      conditions:
        - variable_selector:
            - approval_form
            - decision
          comparison_operator: is
          value: approved

  - id: send_approved
    type: llm
    data:
      title: Format Approved Summary
      prompt_template:
        - role: user
          text: |
            Format this approved summary for distribution:
            {{#generate_summary.text#}}

  - id: request_changes
    type: answer
    data:
      answer: |
        Your summary requires changes before approval.
        Reviewer notes: {{#approval_form.reviewer_notes#}}

  - id: answer_approved
    type: answer
    data:
      answer: "{{#send_approved.text#}}"

edges:
  - source: start
    target: extract_text
  - source: extract_text
    target: generate_summary
  - source: generate_summary
    target: approval_form
  - source: approval_form
    target: check_decision
  - source: check_decision
    target: send_approved
    sourceHandle: "true"
  - source: check_decision
    target: request_changes
    sourceHandle: "false"
  - source: send_approved
    target: answer_approved
```

## Pattern: Mid-Process Data Entry

Use human-input to collect information that could not be determined upfront:

```yaml
- id: collect_details
  type: human-input
  data:
    title: Provide Additional Details
    inputs:
      - variable: budget
        label: What is your budget?
        type: number
        required: true
      - variable: deadline
        label: Target completion date
        type: text
        required: true
        placeholder: e.g., 2026-06-30
      - variable: priority
        label: Priority level
        type: select
        required: true
        options:
          - label: High
            value: high
          - label: Medium
            value: medium
          - label: Low
            value: low
```

## Common Mistakes

1. **Using human-input in headless API workflows.** Without a UI to render the form and return responses, the workflow will pause indefinitely. Only use human-input when the application has an interactive user interface.

2. **Not setting a timeout for approval workflows.** If an approver is unavailable, a workflow without a timeout waits forever, consuming resources. Always set a reasonable timeout for approval scenarios.

3. **Using human-input when a start node variable would suffice.** If you know all required data at the beginning of the workflow, collect it in the start node instead. Human-input is for mid-workflow interruptions only.

4. **Forgetting that output variable names must match the field's `variable` property.** The downstream reference `{{#human_input_id.decision#}}` works only if the field was configured with `variable: decision`.

5. **Nesting human-input inside an iteration node.** Pausing a workflow inside a loop creates a complex state management problem. Human-input should be used at the top level of the workflow, not inside iterating sub-workflows.
