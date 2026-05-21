# Answer Node

## Overview

The answer node streams text output to the user in real time. It is the terminal output node for chatflows — the point where the workflow delivers its response back to the user interface. Unlike the end node (which returns structured data to API callers), the answer node is designed for conversational delivery: it streams tokens to the chat interface as they are assembled, producing a real-time typing effect.

The answer node is exclusively available in chatflows. In regular workflows, use the end node to return output.

## Chatflow Only

The answer node is not available in non-chat workflows. It is specifically designed for the conversational context where a user is interacting in real time and expects to see a response stream in. If you are building a workflow (not a chatflow), use the end node to define output.

## Streaming Behavior

When execution reaches an answer node, the content is streamed token by token to the user interface. If the answer content includes a reference to an LLM node's output (`{{#llm_node.text#}}`), and that LLM node is configured to stream, the tokens flow through the answer node in real time as the LLM generates them.

This creates a natural, responsive conversational experience — the user sees the response appearing word by word rather than waiting for the full response to generate before anything appears.

## Answer Content

The `answer` field in the node configuration is a template string that can contain:

- Plain text
- Variable references using `{{#node_id.field#}}` syntax
- Markdown formatting (rendered in the chat UI)
- Newlines and multi-paragraph content

Variable references are resolved before streaming. If the referenced variable contains a long string (such as LLM output), it streams the entire string. Markdown such as bold text, headers, code blocks, and lists is rendered in supported chat interfaces.

## Markdown Formatting

The answer node fully supports Markdown. Use it to structure responses clearly:

```markdown
## Summary

**Key finding:** {{#llm_node.text#}}

---
*Source: {{#retrieval_node.result[0].title#}}*
```

Bold text, headers, horizontal rules, code blocks (triple backticks), bullet lists, and numbered lists all render in the Dify chat interface.

## Multiple Answer Nodes: One Per Branch

A chatflow can have multiple answer nodes — one per branch of an if-else or question-classifier split. This is the recommended pattern for branch-specific responses:

```
If-Else (true)  → answer_for_urgent_case
If-Else (false) → answer_for_standard_case
```

Each branch ends at its own answer node with content appropriate to that branch. You do NOT need to merge branches before answering — the answer node is a terminal node and the workflow ends when it is reached.

This is the main difference from the variable-aggregator pattern: if you only need to deliver a response, let each branch end at its own answer node. Only use variable-aggregator if you need the output value for further processing before the final response.

## Output Variables

The answer node has no output variables. It is a terminal node — it delivers output to the user and the current turn of the workflow ends. No downstream node can reference the answer node's content.

If you need the response text to be available for further processing, compute it in an LLM node first, then reference that LLM node's output in both the downstream processing and the answer node.

## Complete YAML Example: Conditional Responses with Streaming LLM Output

```yaml
nodes:
  - id: start
    type: start
    data:
      variables:
        - variable: user_question
          type: string
          label: Ask a question

  - id: check_question_type
    type: if-else
    data:
      title: Is it a greeting?
      conditions:
        - variable_selector:
            - start
            - user_question
          comparison_operator: contains
          value: hello

  - id: llm_full_response
    type: llm
    data:
      title: Generate Full Answer
      model:
        provider: openai
        name: gpt-4o
        mode: chat
        stream: true
      prompt_template:
        - role: system
          text: You are a helpful assistant.
        - role: user
          text: "{{#start.user_question#}}"

  - id: answer_greeting
    type: answer
    data:
      answer: |
        Hello! How can I help you today?
        
        Feel free to ask me anything.

  - id: answer_full
    type: answer
    data:
      answer: "{{#llm_full_response.text#}}"

edges:
  - source: start
    target: check_question_type
  - source: check_question_type
    target: answer_greeting
    sourceHandle: "true"
  - source: check_question_type
    target: llm_full_response
    sourceHandle: "false"
  - source: llm_full_response
    target: answer_full
```

## Pattern: Direct LLM Output Streaming

The simplest chatflow — stream the LLM response directly to the user:

```yaml
nodes:
  - id: start
    type: start
    data:
      variables:
        - variable: user_message
          type: string

  - id: llm
    type: llm
    data:
      prompt_template:
        - role: user
          text: "{{#start.user_message#}}"

  - id: answer
    type: answer
    data:
      answer: "{{#llm.text#}}"

edges:
  - source: start
    target: llm
  - source: llm
    target: answer
```

## Pattern: Rich Formatted Response

```yaml
- id: formatted_answer
  type: answer
  data:
    answer: |
      ## Answer

      {{#llm_node.text#}}

      ---

      **Sources:**
      {% for source in retrieval_node.result %}
      - {{ source.title }}
      {% endfor %}
```

Note: Jinja2 templating within the answer node content is not supported — use template-transform first if you need loop-based formatting, then reference the template-transform output in the answer node.

## Common Mistakes

1. **Using the answer node in a non-chatflow workflow.** The answer node does not exist in regular workflows. If you add one, it will be ignored or cause an error. Use the end node for workflow output.

2. **Trying to reference the answer node's output downstream.** The answer node is terminal — its content is delivered to the user and not available as a variable. If you need the response text for further processing, store it in an LLM node's output before the answer node.

3. **Using Jinja2 template syntax inside the answer content.** The answer field does not support Jinja2 loops or conditionals. Use `{{#node_id.field#}}` references only. For conditional or loop-based content, build the string in a template-transform node and reference its output.

4. **Forgetting to connect all branches to answer nodes.** If a question-classifier has three branches but only two are connected to answer nodes, the third branch will produce no output and the user will receive nothing.

5. **Placing variable-aggregator before answer unnecessarily.** If each branch only needs to deliver a response (not compute further), skip the aggregator and connect each branch directly to its own answer node. Aggregation is only needed when the merged value must be used by further nodes.
