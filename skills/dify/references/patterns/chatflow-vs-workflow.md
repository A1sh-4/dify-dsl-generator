# Chatflow vs Workflow: Decision Framework

## Overview

Dify supports two application modes: **chatflow** (`advanced-chat`) and **workflow** (`workflow`). Choosing the wrong mode causes structural problems that cannot be fixed without rebuilding the app — the output nodes differ, memory is only available in one mode, and trigger types are mode-specific. Use this guide to make the correct choice before the node-planner begins.

---

## Decision Framework: 6 Questions

Work through these questions in order. The first YES answer usually determines the mode.

### Q1: Does the user need conversation history across turns?

If the user expects the application to remember what they said in earlier messages within the same session ("I mentioned my order number above — can you look it up?"), **this is a chatflow**. Chatflows maintain a rolling window of the conversation and inject it into each LLM call automatically.

Workflows have no message memory. Each run is independent and stateless.

**YES → chatflow**

### Q2: Is this triggered by a schedule or a webhook?

Trigger nodes (`trigger-webhook` and `trigger-schedule`) are **workflow-only**. They do not exist in chatflow mode. If the application must:
- Fire on a cron schedule (e.g., send a daily digest at 08:00)
- Accept incoming HTTP POSTs from an external system (e.g., Stripe webhook, GitHub Actions callback)

...it must be a workflow.

**YES → workflow**

### Q3: Does it need to remember things between separate conversations?

Conversation variables exist in chatflow but they reset at the start of each new conversation (not each turn — each new session). They are useful for tracking state across turns within one conversation (e.g., "has the user confirmed their order?").

If you need to remember something across separate conversation sessions (e.g., a user's preference from a previous day), conversation variables alone are not enough. You need an external database (accessed via HTTP node or plugin) to persist and retrieve that state.

**Persistent cross-session memory → neither mode solves this alone; use external DB**

### Q4: Does it produce a streaming real-time answer to a human?

The `answer` node — which exists only in chatflow — streams text tokens to the user as they are generated. This produces the familiar "typing" effect users expect from chat interfaces.

The `end` node in a workflow returns a structured output object after the entire pipeline completes. There is no incremental streaming.

If the UX requires a live streaming reply: **chatflow**.

If the output is a JSON object, a file, or a structured report that is consumed programmatically: **workflow**.

**YES (streaming) → chatflow**

### Q5: Is this a single automated pipeline that runs to completion without user interaction?

Pipelines that run headlessly — document processing, batch classification, data enrichment, report generation — fit naturally into workflow mode. They have a defined start (inputs), a defined end (structured outputs), and no need for conversation turns.

**YES → workflow**

### Q6: Does it need to be called via API with a simple request/response?

Both modes expose an API. However:
- Workflow API: `POST /v1/workflows/run` — returns a synchronous structured result or streams events
- Chatflow API: `POST /v1/chat-messages` — maintains session state, designed for chat clients

For machine-to-machine integration where a caller sends inputs and expects structured JSON back, workflow is typically cleaner. But either can work depending on whether session state is needed.

**Structured M2M API → prefer workflow; stateful chat API → chatflow**

---

## Feature Comparison Table

| Feature | Chatflow (`advanced-chat`) | Workflow (`workflow`) |
|---|---|---|
| Entry nodes | `start` (user input only) | `start`, `trigger-webhook`, `trigger-schedule` |
| Output nodes | `answer` (streaming text) | `end` (structured key-value outputs) |
| Memory / conversation history | Yes (window-based, configurable turns) | No |
| Conversation variables | Yes (persist across turns in session) | No |
| Suggested follow-up questions | Yes | No |
| Speech input / output | Yes | No |
| Publish as MCP server | No | Yes (`start`-node workflows only) |
| File upload from user | Yes | Yes |
| Knowledge base retrieval | Yes | Yes |
| Plugin tools | Yes | Yes |
| HTTP nodes | Yes | Yes |
| Iteration nodes | Yes | Yes |
| Parallel fan-out | Yes | Yes |
| Error handling strategies | Yes (all 4) | Yes (all 4) |

---

## Common Mistakes

These mistakes cause import failures or silent misbehavior. The dsl-generator must never produce them.

### Using `end` node in a chatflow
**Wrong:** chatflow graph contains a node with `type: end`
**Correct:** chatflow must use `type: answer` as the terminal node

The `answer` node has a `answer` field (the text to stream) and connects to the `__end__` implicit node. The `end` node has an `outputs` field and is incompatible with chatflow's streaming mechanism.

### Using `answer` node in a workflow
**Wrong:** workflow graph contains a node with `type: answer`
**Correct:** workflow must use `type: end` with configured output variables

### Building a multi-turn chatbot as a workflow
Workflows cannot persist conversation history between runs. Each workflow execution is isolated. A chatbot built as a workflow will have no memory of previous turns, and users will need to repeat context every time. Use chatflow.

### Building a webhook handler as a chatflow
`trigger-webhook` and `trigger-schedule` are workflow-only node types. Attempting to use them in a chatflow will cause the YAML to fail validation. If the app must respond to external webhooks, it must be a workflow.

### Trying to publish a chatflow as an MCP server
Only workflows with a `start` node can be published as MCP servers in Dify. Chatflows are not MCP-publishable.

---

## Hybrid Patterns

Sometimes a single mode cannot cover all requirements. Common hybrid approaches:

**Chatflow → Workflow API call for heavy processing:**
A user chats with a chatflow to specify parameters, then the chatflow's HTTP node POSTs to a workflow API endpoint to run a long batch job. The chatflow streams a "your job is submitted" response while the workflow runs independently.

**Workflow → Chatflow API for conversational sub-tasks:**
A workflow pipeline, triggered by a webhook, needs to rephrase content in a conversational style. It calls a chatflow API endpoint (or directly calls an LLM with a chat prompt) as one of its HTTP nodes.

**Pattern: External memory in chatflow:**
Use conversation variables to cache a user ID or session token. Use an HTTP node (or plugin) to write/read from a database. This extends chatflow with cross-session persistence without changing the mode.

---

## Quick Reference Card

```
User chats with it?                    → chatflow
Triggered by schedule or webhook?      → workflow
Needs conversation memory?             → chatflow
Outputs structured JSON/data?          → workflow
Streams text answers to user?          → chatflow
Runs headlessly without user?          → workflow
Needs to be published as MCP server?   → workflow
```

See also:
- `skills/dify/references/schema/chatflow-schema.md` — full chatflow DSL reference
- `skills/dify/references/schema/workflow-schema.md` — full workflow DSL reference
- `skills/dify/references/nodes/answer.md` — answer node configuration
- `skills/dify/references/nodes/end.md` — end node configuration
- `skills/dify/references/nodes/trigger-webhook.md` — webhook trigger node
