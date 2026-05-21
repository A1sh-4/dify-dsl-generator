# Question Classifier Node

## Overview

The question-classifier node uses a language model to route user queries into multiple semantic categories. Unlike the if-else node, which applies deterministic string matching, the question-classifier understands the meaning and intent of the input text. A query can be classified correctly even when its exact wording does not match any keyword or pattern — the LLM infers which category the query belongs to based on semantic similarity to the class descriptions.

This node is the primary tool for multi-way intent routing in conversational workflows. It does not produce an output variable — its only function is to direct execution flow to one of its configured class branches.

## When to Use

Use question-classifier when:

- You need to route queries into three or more categories based on meaning, not exact text
- User phrasing varies widely and keyword matching would miss too many cases
- You want the routing decision to be context-aware (e.g., "I can't login" → Technical, not Billing)
- You are building a customer support, FAQ, or intake router

Use if-else instead when:

- You have exactly two outcomes and the condition is simple and deterministic
- You are checking a numeric value, empty state, or a known fixed string
- Speed and predictability matter more than semantic flexibility

## Difference from If-Else

| Aspect | If-Else | Question Classifier |
|--------|---------|---------------------|
| Decision method | Deterministic logic | LLM inference |
| Number of branches | Always 2 | 2 or more |
| Understanding | Literal comparison | Semantic meaning |
| Speed | Very fast | Requires LLM call |
| Handles paraphrasing | No | Yes |
| Requires model | No | Yes |

## Class Definition

Each class has two properties:

| Field | Description |
|-------|-------------|
| `name` | The class identifier. This becomes the edge handle for routing. Must be unique. |
| `description` | Natural language description of what belongs in this class. The LLM uses this to make its decision. |

Write class descriptions carefully. They are the instructions given to the LLM. More specific descriptions produce more accurate classification. Include examples if the distinction between classes is subtle.

**Good description example:**
> "Questions about payment methods, billing cycles, invoice requests, refunds, subscription pricing, or charges on the user's account."

**Poor description example:**
> "Billing stuff."

## The Class Name as Edge Handle

The `name` field of each class becomes the `sourceHandle` value used in the `edges` array to connect that branch to the next node. For example, if a class has `name: billing`, the edge from the classifier to the billing handler node uses `sourceHandle: "billing"`.

This means class names must be:
- Unique within the node
- Valid as identifiers (avoid spaces; use underscores or hyphens)
- Consistent between the class definition and the edges array

## Model Configuration

You can specify which LLM performs the classification. Using a faster, smaller model (like gpt-4o-mini or Claude Haiku) reduces latency and cost since classification is a lightweight task that does not require the most capable model.

```yaml
model:
  provider: openai
  name: gpt-4o-mini
  mode: chat
```

## Output Variables

The question-classifier node produces no output variables. It is a routing-only node. The classified query is not transformed or returned — execution simply flows to the matched class's branch.

If the query does not clearly match any class, the LLM will route it to the most likely class based on the descriptions. There is no explicit "unmatched" output — the last class in the list often serves as a catch-all when its description includes language like "any other question."

## Complete YAML Example: Customer Support Router (3 Classes)

```yaml
nodes:
  - id: start
    type: start
    data:
      variables:
        - variable: user_message
          type: string
          label: Your question
          required: true

  - id: classify_intent
    type: question-classifier
    data:
      title: Classify Support Request
      query_variable_selector:
        - start
        - user_message
      model:
        provider: openai
        name: gpt-4o-mini
        mode: chat
      classes:
        - id: billing_class
          name: billing
          description: >
            Questions about invoices, payment methods, subscription costs,
            pricing plans, refunds, charges, or account billing history.
        - id: technical_class
          name: technical
          description: >
            Questions about product features, bugs, errors, login issues,
            integrations, API usage, or technical troubleshooting.
        - id: general_class
          name: general
          description: >
            General inquiries, feature requests, company information,
            or any question that does not fit billing or technical categories.

  - id: billing_handler
    type: llm
    data:
      title: Handle Billing Question
      prompt_template:
        - role: system
          text: You are a billing support specialist. Help the user with their billing question.
        - role: user
          text: "{{#start.user_message#}}"

  - id: technical_handler
    type: llm
    data:
      title: Handle Technical Question
      prompt_template:
        - role: system
          text: You are a technical support engineer. Help the user troubleshoot their issue.
        - role: user
          text: "{{#start.user_message#}}"

  - id: general_handler
    type: llm
    data:
      title: Handle General Question
      prompt_template:
        - role: system
          text: You are a helpful customer service agent. Answer the user's question.
        - role: user
          text: "{{#start.user_message#}}"

edges:
  - source: start
    target: classify_intent
  - source: classify_intent
    target: billing_handler
    sourceHandle: billing
  - source: classify_intent
    target: technical_handler
    sourceHandle: technical
  - source: classify_intent
    target: general_handler
    sourceHandle: general
```

## Pattern: After Classification — Convergence

After the classifier routes to branch-specific handlers, use a variable-aggregator to merge the outputs before passing them to an answer node:

```yaml
- id: merge_responses
  type: variable-aggregator
  data:
    variables:
      - [billing_handler, text]
      - [technical_handler, text]
      - [general_handler, text]
```

## Common Mistakes

1. **Vague class descriptions.** If all descriptions are one or two words, the LLM has insufficient guidance to distinguish classes accurately. Write descriptive sentences with concrete examples of what belongs in each class.

2. **Mismatching class name and edge sourceHandle.** If the class is named `billing` but the edge uses `sourceHandle: "Billing"` (capital B), the edge will not match. Names are case-sensitive.

3. **Forgetting to wire all class branches.** Every class must have a corresponding edge. If a class has no connected edge, queries classified into that class will dead-end and the workflow will error.

4. **Using question-classifier for binary yes/no routing.** For simple two-branch logic with deterministic conditions, if-else is faster and cheaper. Question-classifier involves a full LLM call.

5. **Overlapping class descriptions.** If two classes have very similar descriptions, the LLM may route ambiguous queries inconsistently. Make class descriptions as distinct and mutually exclusive as possible.
