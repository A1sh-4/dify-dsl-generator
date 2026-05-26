# Agentic Pattern: LLM-Driven Tool Use

## Overview

An agentic flow is a pipeline where an LLM autonomously decides which tools to call, calls them, observes the results, and then decides what to do next — repeating this loop until it has enough information to produce a final answer. Unlike a manual tool chain where the DSL author specifies the exact sequence of calls, an agentic flow delegates that sequencing to the LLM at runtime.

Dify's `agent` node implements this pattern natively. It manages the tool-call loop, passing tool results back to the LLM context automatically, and stopping when the LLM produces a final text output or when `max_iterations` is reached.

---

## What Makes a Flow "Agentic"

A flow is agentic when:
1. The LLM receives a goal, not a fixed sequence of steps
2. The LLM decides which available tool(s) to call based on current context
3. Tool results are fed back to the LLM for the next decision
4. This continues until the LLM decides it has enough information to answer

This is in contrast to a **manual tool chain** where the YAML specifies: call search, then call scraper, then call LLM — regardless of whether each step's output is actually needed.

---

## Agent Node vs Manual Tool Nodes

| Aspect | Agent Node | Manual Tool Chain |
|--------|-----------|-------------------|
| Who decides tool order | LLM at runtime | DSL author at design time |
| Flexibility | High — adapts to query | Low — always same steps |
| Predictability | Lower — paths vary | High — same path every run |
| Debugging | Harder (dynamic) | Easier (fixed flow) |
| Token cost | Higher (multiple LLM calls) | Lower (one LLM call) |
| Best for | Open-ended research, Q&A | ETL, structured data processing |

**Use the agent node when:** the task is open-ended, the tools needed depend on the specific query, or the number of required tool calls is unknown.

**Use manual tool nodes when:** you always call the same tools in the same sequence, the pipeline is deterministic, or token efficiency is critical.

---

## Agent Strategies

The `agent_strategy` field controls how the LLM reasons about tool use.

### `function_call` (Default)

Uses the model's native function-calling API (OpenAI tool calls, Claude tool_use, etc.). The model outputs structured JSON specifying which function to call and with what arguments. Dify invokes the tool and returns the result.

- **Speed:** Fastest — single round-trip per tool call
- **Reliability:** Highest — structured JSON output, no parsing ambiguity
- **Support:** Available on all major function-calling models (GPT-4o, Claude 3.x, Gemini 1.5+)
- **When to use:** Default choice for most agent tasks

### `react` (ReAct — Reason + Act)

The LLM follows a Thought → Action → Observation loop. Before each action, it outputs a `Thought:` explaining its reasoning. After each tool call, it receives an `Observation:` and then produces the next `Thought:`.

- **Transparency:** High — reasoning steps are visible in the output
- **Speed:** Slower — more tokens per step
- **Reliability:** Moderate — depends on the model following the format
- **When to use:** Complex multi-step research where intermediate reasoning should be auditable; debugging agent behavior; tasks requiring explicit justification

### `cot` (Chain of Thought)

The LLM reasons through the full problem before selecting a tool. It produces a structured reasoning block, then executes.

- **Quality:** High for structured problem-solving
- **When to use:** Tasks with a well-defined problem-solving structure (e.g., code debugging, math, legal analysis)

---

## Max Iterations Guide

`max_iterations` caps how many tool-call cycles the agent can make before being forced to stop and return whatever answer it has accumulated.

| Task Type | Recommended `max_iterations` |
|-----------|-------------------------------|
| Simple lookup / single fact check | 3–5 |
| Multi-hop research (cross-referencing sources) | 8–12 |
| Complex analysis (compare, evaluate, synthesize) | 15–20 |

**Warning:** Higher values increase latency and cost proportionally. Set the lowest value that reliably completes the task. If the agent frequently hits the limit, either increase `max_iterations` or decompose the task into simpler sub-agents.

---

## System Prompt Pattern for Agents

The system prompt for an agent node must clearly specify:
1. The agent's goal
2. What tools are available and what each does
3. Stopping criteria — how the agent knows it has enough information

```
You are a research assistant. Your goal: [specific, measurable goal]

Available tools:
- brave_search: Search the web for current information. Input: a search query string.
- jina_reader: Extract full text content from a webpage URL. Input: a URL string.

Instructions:
1. Search for information relevant to the user's question
2. If a search result looks promising, use jina_reader to get the full content
3. Synthesize findings into a comprehensive answer
4. Stop when you have enough information to answer confidently — do not over-search

User query: {{#start.sys.query#}}
```

**Key rules for agent system prompts:**
- Name each tool with its exact Dify tool name
- Describe the input format each tool expects
- Give the LLM a clear stopping condition
- Do not mention tools that are not actually wired in the agent node's tool list

---

## Complete YAML — Basic Research Agent Chatflow

### Node Graph

```
start → agent (brave_search) → answer
```

Node IDs: `"1747100000001"`, `"1747100000002"`, `"1747100000003"`

```yaml
app:
  description: "An agentic chatflow that searches the web to answer user questions."
  icon: "\U0001F50E"
  icon_background: "#FFF3E0"
  mode: advanced-chat
  name: Research Agent Chatflow
dependencies:
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/brave:0.0.3/brave"
features:
  file_upload:
    enabled: false
  opening_statement: "Ask me anything — I'll search the web for current answers."
  speech_to_text:
    enabled: false
  suggested_questions: []
  suggested_questions_after_answer:
    enabled: false
  text_to_speech:
    enabled: false
kind: app
version: "0.1.0"
workflow:
  conversation_variables: []
  environment_variables: []
  graph:
    edges:
      - data:
          isInIteration: false
          sourceType: start
          targetType: agent
        id: "1747100000001-source-1747100000002-target"
        source: "1747100000001"
        sourceHandle: source
        target: "1747100000002"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: agent
          targetType: answer
        id: "1747100000002-source-1747100000003-target"
        source: "1747100000002"
        sourceHandle: source
        target: "1747100000003"
        targetHandle: target
        type: custom
        zIndex: 0
    nodes:
      - data:
          desc: ""
          title: Start
          type: start
          variables: []
        height: 54
        id: "1747100000001"
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
        width: 244

      - data:
          agent_config:
            max_iterations: 5
            strategy: function_call
          desc: "Search the web autonomously to answer the user's question."
          model:
            completion_params:
              max_tokens: 2048
              temperature: 0.5
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt:
            - id: agent-system
              role: system
              text: |
                You are a research assistant. Your goal: find accurate, current information to answer the user's question.

                Available tools:
                - brave_search: Search the web. Input: a search query string.

                Instructions:
                1. Search for information relevant to the user's question
                2. If the first search result is insufficient, search with a refined query
                3. Stop when you have enough information to give a confident, complete answer
                4. Synthesize results into a clear, direct response

                User query: {{#start.sys.query#}}
          title: Research Agent
          tools:
            - provider_id: langgenius/brave/brave
              provider_name: Brave Search
              provider_type: builtin
              tool_name: brave_search
              tool_parameters:
                count: 5
                query:
                  type: mixed
                  value: ""
              tool_label: Brave Search
          type: agent
        height: 98
        id: "1747100000002"
        position:
          x: 380
          y: 282
        positionAbsolute:
          x: 380
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          answer: "{{#1747100000002.text#}}"
          desc: ""
          title: Answer
          type: answer
        height: 54
        id: "1747100000003"
        position:
          x: 680
          y: 282
        positionAbsolute:
          x: 680
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
```

---

## Complete YAML — Multi-Tool Research Workflow

### Node Graph

```
start → agent (search + scrape) → llm (summarize) → end
```

The agent collects raw information from multiple sources. The downstream LLM synthesizes it into a structured report. This separation is intentional: the agent focuses on information gathering, and the synthesis LLM has a stable prompt optimized for structuring output.

Node IDs: `"1747100000010"`, `"1747100000011"`, `"1747100000012"`, `"1747100000013"`

```yaml
app:
  description: "Multi-tool research workflow: agent gathers info, LLM structures the report."
  icon: "\U0001F4CB"
  icon_background: "#E8F5E9"
  mode: workflow
  name: Multi-Tool Research Workflow
dependencies:
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/brave:0.0.3/brave"
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/jina:0.0.2/jina"
features: {}
kind: app
version: "0.1.0"
workflow:
  conversation_variables: []
  environment_variables: []
  graph:
    edges:
      - data:
          isInIteration: false
          sourceType: start
          targetType: agent
        id: "1747100000010-source-1747100000011-target"
        source: "1747100000010"
        sourceHandle: source
        target: "1747100000011"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: agent
          targetType: llm
        id: "1747100000011-source-1747100000012-target"
        source: "1747100000011"
        sourceHandle: source
        target: "1747100000012"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: llm
          targetType: end
        id: "1747100000012-source-1747100000013-target"
        source: "1747100000012"
        sourceHandle: source
        target: "1747100000013"
        targetHandle: target
        type: custom
        zIndex: 0
    nodes:
      - data:
          desc: ""
          title: Start
          type: start
          variables:
            - label: Research Topic
              max_length: 500
              options: []
              required: true
              type: text-input
              variable: topic
        height: 54
        id: "1747100000010"
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
        width: 244

      - data:
          agent_config:
            max_iterations: 10
            strategy: react
          desc: "Search and scrape the web to gather comprehensive information."
          model:
            completion_params:
              max_tokens: 4096
              temperature: 0.3
            mode: chat
            name: gpt-4o
            provider: openai
          prompt:
            - id: multi-agent-system
              role: system
              text: |
                You are a thorough research agent. Your goal: gather comprehensive, accurate information on the given topic.

                Available tools:
                - brave_search: Search the web for current information. Input: a search query string.
                - jina_reader: Extract full text content from a URL. Input: a URL string.

                Research strategy:
                1. Start with 2-3 different search queries to get diverse coverage
                2. For each promising search result, use jina_reader to extract the full article
                3. Collect at minimum 3 substantial sources
                4. Output a structured dump of all gathered information (raw findings, not summarized)

                Topic to research: {{#1747100000010.topic#}}
          title: Research Agent
          tools:
            - provider_id: langgenius/brave/brave
              provider_name: Brave Search
              provider_type: builtin
              tool_name: brave_search
              tool_parameters:
                count: 5
                query:
                  type: mixed
                  value: ""
              tool_label: Brave Search
            - provider_id: langgenius/jina/jina
              provider_name: Jina Reader
              provider_type: builtin
              tool_name: jina_reader
              tool_parameters:
                url:
                  type: mixed
                  value: ""
              tool_label: Jina Reader
          type: agent
        height: 98
        id: "1747100000011"
        position:
          x: 380
          y: 282
        positionAbsolute:
          x: 380
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          desc: "Synthesize raw research findings into a structured report."
          model:
            completion_params:
              max_tokens: 3000
              temperature: 0.2
            mode: chat
            name: gpt-4o
            provider: openai
          prompt_template:
            - id: synth-system
              role: system
              text: |
                You are a professional research analyst. Synthesize the raw research findings below into a well-structured report.

                Output format:
                ## Executive Summary
                [2-3 sentence overview]

                ## Key Findings
                [Bullet list of the most important facts]

                ## Detailed Analysis
                [Organized paragraphs covering the main aspects]

                ## Sources
                [List of URLs referenced]

                Raw research findings:
                {{#1747100000011.text#}}
            - id: synth-user
              role: user
              text: "Synthesize the research on: {{#1747100000010.topic#}}"
          title: Synthesis LLM
          type: llm
          vision:
            enabled: false
        height: 98
        id: "1747100000012"
        position:
          x: 680
          y: 282
        positionAbsolute:
          x: 680
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          desc: ""
          outputs:
            - label: Research Report
              name: report
              type: string
              value_selector:
                - "1747100000012"
                - text
          title: End
          type: end
        height: 54
        id: "1747100000013"
        position:
          x: 980
          y: 282
        positionAbsolute:
          x: 980
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
```

---

## Agent Output Variable

The `agent` node exposes a `text` output variable, the same as an `llm` node. Reference it with:

```
{{#agent_node_id.text#}}
```

Use this to pass the agent's final synthesized answer into downstream nodes (answer, llm, end).

---

## When Not to Use the Agent Node

- **Fixed, predictable tool sequences:** Use manual tool nodes — cheaper, faster, more debuggable
- **Single tool call:** Use a `tool` node directly — agent overhead is unnecessary
- **High-stakes production flows:** Agent paths are non-deterministic; for compliance-critical flows, use manual chains with explicit error handling

See also:
- `skills/dify/references/nodes/agent.md` — agent node field reference
- `skills/dify/references/patterns/error-handling.md` — adding fail-branch to agent nodes
- `skills/dify/references/patterns/parallel-execution.md` — running multiple agents in parallel
- `skills/dify/references/features/plugins-marketplace.md` — finding tools to wire into an agent
