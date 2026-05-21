# Parameter Extractor Node

## Overview

The parameter-extractor node uses a language model to extract structured, typed variables from unstructured natural language text. Given a user message or any string input, it identifies and pulls out specific values — such as a name, a date, a number, or a boolean — and returns them as individual, typed output variables. This is how you turn free-form text into clean data that downstream nodes can work with programmatically.

The node is particularly valuable in workflows where users express intent in natural language but the system needs structured inputs: booking forms, payment instructions, search filters, configuration commands, or any scenario where a user describes what they want rather than filling out a form.

## When to Use

Use parameter-extractor when:

- A user's message contains parameters you need to extract (name, date, amount, location)
- You want to parse a command given in natural language ("send 500 USD to Alice on Friday")
- You need to convert user intent into typed variables for API calls or conditional logic
- You want to pre-fill structured data from a free-text description

Do not use parameter-extractor when the data is already structured (use variable references instead) or when you need to transform text rather than extract from it (use template-transform).

## Inference Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| `function_call` | Uses the model's native function calling / tool use capability to extract parameters with type enforcement | Preferred when the model supports it (GPT-4, Claude 3+, etc.) |
| `prompt` | Instructs the model via prompt to output a JSON object; less reliable type enforcement | Fallback for models without function calling |

Use `function_call` mode whenever the model supports it. It produces more reliable output because the model is explicitly guided to fill specific typed slots rather than generating free-form JSON.

## Parameter Schema

Each parameter is defined with the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Variable name for output (used in `{{#node_id.name#}}`) |
| `type` | string | Yes | Data type: `string`, `number`, `boolean`, `array`, `object` |
| `description` | string | Yes | Natural language description of what to extract — guides the LLM |
| `required` | boolean | No | If true, extraction fails when this parameter is missing |
| `enum` | array | No | List of allowed values (for constrained string parameters) |
| `default` | any | No | Default value when parameter is not found and not required |

Write clear, specific descriptions. The description is what tells the LLM what to look for. A description like "the amount of money mentioned" is far more effective than just "amount".

## Input

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | The text to extract parameters from. Usually the user's message. |

## Output Variables

Each declared parameter becomes a separate output variable on the node. Access them individually:

```
{{#parameter_extractor_node_id.recipient#}}
{{#parameter_extractor_node_id.amount#}}
{{#parameter_extractor_node_id.currency#}}
```

There is no single consolidated output object — each parameter is its own variable, which makes them easy to use directly in downstream nodes without additional parsing.

## Handling Extraction Failure

**Required parameters:** If a required parameter cannot be found in the input text, the node fails and the workflow follows the error branch (if configured) or stops.

**Optional parameters:** If an optional parameter is not found, it returns the `default` value if set, or null/empty if no default is specified. Downstream nodes should handle this gracefully.

**Default values:** Always set a sensible default for optional parameters that downstream logic depends on. For example, set `default: "USD"` for a currency field when USD is the most common case.

## Complete YAML Example: Payment Instruction Extraction

This example extracts three parameters of different types from a payment instruction sentence like: "Please transfer 1500 euros to Marcus by tomorrow."

```yaml
nodes:
  - id: start
    type: start
    data:
      variables:
        - variable: instruction
          type: string
          label: Payment instruction
          required: true

  - id: extract_payment_params
    type: parameter-extractor
    data:
      title: Extract Payment Parameters
      query:
        variable_selector:
          - start
          - instruction
      model:
        provider: openai
        name: gpt-4o
        mode: chat
      reasoning_mode: function_call
      parameters:
        - name: recipient
          type: string
          description: >
            The name of the person or entity who should receive the payment.
            Extract the full name as written.
          required: true

        - name: amount
          type: number
          description: >
            The numeric amount of money to transfer. Extract only the number,
            not the currency symbol or unit. For example, "1500" from "1500 euros".
          required: true

        - name: currency
          type: string
          description: >
            The currency code or name mentioned. Normalize to ISO 4217 code
            where possible (USD, EUR, GBP). Default to USD if not specified.
          required: false
          enum:
            - USD
            - EUR
            - GBP
            - JPY
            - CAD
          default: USD

  - id: confirm_payment
    type: llm
    data:
      title: Confirm Payment Details
      prompt_template:
        - role: user
          text: |
            Please confirm this payment:
            - Recipient: {{#extract_payment_params.recipient#}}
            - Amount: {{#extract_payment_params.amount#}} {{#extract_payment_params.currency#}}

  - id: end
    type: end
    data:
      outputs:
        - variable: recipient
          value_selector:
            - extract_payment_params
            - recipient
        - variable: amount
          value_selector:
            - extract_payment_params
            - amount
        - variable: currency
          value_selector:
            - extract_payment_params
            - currency

edges:
  - source: start
    target: extract_payment_params
  - source: extract_payment_params
    target: confirm_payment
  - source: confirm_payment
    target: end
```

## Pattern: Natural Language to Structured Data

Use parameter-extractor at the start of any workflow that accepts free-form user input but needs to operate on typed values:

1. Start node captures free-form text
2. Parameter-extractor converts it to typed variables
3. If-else or code nodes use the typed values for logic
4. HTTP or tool nodes receive the cleaned parameters

## Common Mistakes

1. **Vague parameter descriptions.** The description is the LLM's only guidance. "Extract the date" is not specific enough. Write "The date the payment should be made, in YYYY-MM-DD format if possible; otherwise return the date phrase as written."

2. **Using `prompt` mode with a model that supports function calling.** Function call mode is more reliable and should always be preferred when available. Only use `prompt` mode as a last resort.

3. **Not handling missing required parameters.** If a required parameter cannot be extracted, the node will error. Add error handling (fail-branch) or make the parameter optional with a sensible default.

4. **Expecting complex nested object extraction.** While `object` and `array` types are supported, deeply nested structures are harder for the LLM to extract reliably. Flatten your schema when possible.

5. **Reusing the extracted variable name as the node ID.** If your node is named `amount` and it produces a variable called `amount`, the reference `{{#amount.amount#}}` is confusing and error-prone. Use descriptive node IDs like `extract_payment_params`.
