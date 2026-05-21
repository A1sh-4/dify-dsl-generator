# RAG Pattern: Retrieval-Augmented Generation

## Overview

RAG (Retrieval-Augmented Generation) is the pattern of injecting relevant context from a knowledge base into an LLM prompt before asking it to answer. Dify provides a first-class `knowledge-retrieval` node that handles chunked document retrieval, embedding-based similarity search, optional reranking, and score filtering. This document covers both the basic 4-node RAG pipeline and the advanced 6-node pipeline with query rewriting.

---

## The Core Wiring Rule

The `knowledge-retrieval` node outputs a single variable: `result`. This variable is a formatted string of retrieved document chunks. It must be injected into the LLM's system or user prompt using the variable reference syntax:

```
{{#node_id.result#}}
```

Where `node_id` is the `id` of the `knowledge-retrieval` node. This is the **only** correct way to pass retrieved context into an LLM node.

---

## Basic RAG (4 Nodes)

### Node Graph

```
start → knowledge-retrieval → llm → answer
```

- **start**: captures `sys.query` (the user's question)
- **knowledge-retrieval**: searches the knowledge base using `sys.query` as the query
- **llm**: generates an answer with the retrieved context injected into the prompt
- **answer**: streams the response back to the user

### Node Positions

| Node | x | y |
|------|---|---|
| start | 80 | 282 |
| knowledge-retrieval | 380 | 282 |
| llm | 680 | 282 |
| answer | 980 | 282 |

### Complete YAML — Basic RAG Chatflow

```yaml
app:
  description: "Answers user questions using a knowledge base."
  icon: "\U0001F4DA"
  icon_background: "#EEF4FF"
  mode: advanced-chat
  name: Basic RAG Chatflow
dependencies: []
features:
  file_upload:
    enabled: false
  opening_statement: "Hello! Ask me anything about the knowledge base."
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
          targetType: knowledge-retrieval
        id: "1747000000001-source-1747000000002-target"
        source: "1747000000001"
        sourceHandle: source
        target: "1747000000002"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: knowledge-retrieval
          targetType: llm
        id: "1747000000002-source-1747000000003-target"
        source: "1747000000002"
        sourceHandle: source
        target: "1747000000003"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: llm
          targetType: answer
        id: "1747000000003-source-1747000000004-target"
        source: "1747000000003"
        sourceHandle: source
        target: "1747000000004"
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
        id: "1747000000001"
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
          dataset_configs:
            datasets:
              - dataset:
                  enabled: true
                  id: "YOUR_DATASET_ID"
            reranking_enable: false
            reranking_mode: null
            reranking_model:
              provider_name: ""
              model_name: ""
            retrieval_model: semantic_search
            score_threshold: 0.5
            score_threshold_enabled: true
            top_k: 5
          desc: "Retrieve relevant documents from the knowledge base."
          query_variable_selector:
            - "1747000000001"
            - sys.query
          title: Knowledge Retrieval
          type: knowledge-retrieval
        height: 90
        id: "1747000000002"
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
          context:
            enabled: true
            variable_selector:
              - "1747000000002"
              - result
          desc: "Generate an answer grounded in the retrieved context."
          model:
            completion_params:
              max_tokens: 1024
              temperature: 0.3
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: system-prompt
              role: system
              text: |
                You are a helpful assistant. Answer the user's question based ONLY on the following context:

                {{#1747000000002.result#}}

                If the answer is not in the context, say "I don't have that information in my knowledge base." Do not use outside knowledge.
            - id: user-prompt
              role: user
              text: "{{#start.sys.query#}}"
          title: Answer LLM
          type: llm
          vision:
            enabled: false
        height: 98
        id: "1747000000003"
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
          answer: "{{#1747000000003.text#}}"
          desc: ""
          title: Answer
          type: answer
        height: 54
        id: "1747000000004"
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

## Advanced RAG (6 Nodes) — With Query Rewriting

Query rewriting improves retrieval quality when user questions are ambiguous, too short, or use pronouns that reference prior context ("Can you tell me more about it?"). The rewrite LLM rephrases the user's question into a self-contained, search-optimized query before hitting the knowledge base.

### Node Graph

```
start → llm (query rewrite) → knowledge-retrieval → llm (answer) → answer
                                      ↑
                      Uses rewritten query instead of raw user input
```

### Node Configuration Details

- **llm (query rewrite)**: takes `{{#start.sys.query#}}` and conversation history; outputs a clean search query as `text`
- **knowledge-retrieval**: uses `{{#llm_rewrite_node_id.text#}}` as the query variable (not `sys.query`)
- **llm (answer)**: uses `{{#knowledge_retrieval_node_id.result#}}` as the RAG context
- Reranking enabled, top_k=5, score_threshold=0.5

### Node Positions

| Node | x | y |
|------|---|---|
| start | 80 | 282 |
| llm (rewrite) | 380 | 282 |
| knowledge-retrieval | 680 | 282 |
| llm (answer) | 980 | 282 |
| answer | 1280 | 282 |

### Complete YAML — Advanced RAG with Query Rewriting

```yaml
app:
  description: "RAG chatflow with query rewriting for improved retrieval."
  icon: "\U0001F50D"
  icon_background: "#EEF4FF"
  mode: advanced-chat
  name: Advanced RAG Chatflow
dependencies: []
features:
  file_upload:
    enabled: false
  opening_statement: "Hello! I'll help you find answers from the knowledge base."
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
          targetType: llm
        id: "1747000000010-source-1747000000011-target"
        source: "1747000000010"
        sourceHandle: source
        target: "1747000000011"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: llm
          targetType: knowledge-retrieval
        id: "1747000000011-source-1747000000012-target"
        source: "1747000000011"
        sourceHandle: source
        target: "1747000000012"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: knowledge-retrieval
          targetType: llm
        id: "1747000000012-source-1747000000013-target"
        source: "1747000000012"
        sourceHandle: source
        target: "1747000000013"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: llm
          targetType: answer
        id: "1747000000013-source-1747000000014-target"
        source: "1747000000013"
        sourceHandle: source
        target: "1747000000014"
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
        id: "1747000000010"
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
          desc: "Rewrite the user query into a self-contained search query."
          model:
            completion_params:
              max_tokens: 256
              temperature: 0.1
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: system-rewrite
              role: system
              text: |
                You are a search query optimizer. Your ONLY job is to rewrite the user's question into a clear, specific, self-contained search query that can be used to retrieve relevant documents from a knowledge base.

                Rules:
                - Remove pronouns and replace them with explicit nouns
                - Expand abbreviations
                - Make the query standalone (as if there is no prior context)
                - Output ONLY the rewritten query — no explanation, no punctuation wrapping

                Example:
                User: "What about the pricing?"
                Rewritten: "What is the pricing structure and cost breakdown?"
            - id: user-rewrite
              role: user
              text: "{{#start.sys.query#}}"
          title: Query Rewrite LLM
          type: llm
          vision:
            enabled: false
        height: 98
        id: "1747000000011"
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
          dataset_configs:
            datasets:
              - dataset:
                  enabled: true
                  id: "YOUR_DATASET_ID"
            reranking_enable: true
            reranking_mode: reranking_model
            reranking_model:
              provider_name: cohere
              model_name: rerank-english-v3.0
            retrieval_model: hybrid_search
            score_threshold: 0.5
            score_threshold_enabled: true
            top_k: 5
          desc: "Retrieve documents using the rewritten query."
          query_variable_selector:
            - "1747000000011"
            - text
          title: Knowledge Retrieval
          type: knowledge-retrieval
        height: 90
        id: "1747000000012"
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
          context:
            enabled: true
            variable_selector:
              - "1747000000012"
              - result
          desc: "Generate a grounded answer using retrieved context."
          model:
            completion_params:
              max_tokens: 2048
              temperature: 0.3
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: system-answer
              role: system
              text: |
                You are a helpful assistant. Answer the user's question based ONLY on the following context retrieved from the knowledge base:

                {{#1747000000012.result#}}

                Rules:
                - Answer only from the provided context
                - If the answer is not in the context, say: "I don't have that information in my knowledge base."
                - Do not use outside knowledge or make assumptions
                - Be concise and direct
                - Cite relevant sections when helpful
            - id: user-answer
              role: user
              text: "{{#start.sys.query#}}"
          title: Answer LLM
          type: llm
          vision:
            enabled: false
        height: 98
        id: "1747000000013"
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

      - data:
          answer: "{{#1747000000013.text#}}"
          desc: ""
          title: Answer
          type: answer
        height: 54
        id: "1747000000014"
        position:
          x: 1280
          y: 282
        positionAbsolute:
          x: 1280
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
```

---

## LLM Prompt for RAG — Standard Template

Use this prompt structure in any LLM node that receives knowledge base output:

```
System:
You are a helpful assistant. Answer based ONLY on the following context:

{{#KNOWLEDGE_RETRIEVAL_NODE_ID.result#}}

If the answer is not in the context, say "I don't have that information in my knowledge base."

Do not use outside knowledge. Do not make assumptions. Be concise.

Format: [adapt based on use case — paragraph, bullet list, JSON, etc.]

User:
{{#start.sys.query#}}
```

Replace `KNOWLEDGE_RETRIEVAL_NODE_ID` with the actual `id` of the knowledge-retrieval node.

**Critical:** The `context` block in the LLM node data must reference the same node:
```yaml
context:
  enabled: true
  variable_selector:
    - "KNOWLEDGE_RETRIEVAL_NODE_ID"
    - result
```

Both the inline prompt reference (`{{#id.result#}}`) and the `context` variable_selector must point to the same knowledge-retrieval node. The `context` block enables Dify's citation tracking; the inline reference is what actually injects the text.

---

## Retrieval Quality Tuning Guide

### top_k — Number of Chunks Retrieved

| Value | Use Case |
|-------|----------|
| 3–5 | Focused Q&A, factual lookup — fewer but more relevant chunks |
| 6–8 | Balanced — good default for most applications |
| 8–10 | Comprehensive research — broader coverage, higher noise risk |

Start with `top_k: 5`. Increase if users report missing information; decrease if answers contain too much irrelevant content.

### score_threshold — Minimum Similarity Score

| Value | Effect |
|-------|--------|
| 0.3 | High recall — returns many results, more noise |
| 0.5 | Balanced — good default |
| 0.7 | High precision — only strong matches, may miss relevant content |

Use `score_threshold_enabled: true` to activate filtering. Without it, all top_k results are returned regardless of relevance score.

### retrieval_model — Search Mode

| Mode | Description | Best For |
|------|-------------|----------|
| `semantic_search` | Dense embedding similarity | Natural language questions |
| `full_text_search` | BM25 keyword matching | Exact terms, product names, codes |
| `hybrid_search` | Combines both | General purpose, best quality |

Use `hybrid_search` as the default for most applications. Fall back to `semantic_search` for question-answer datasets. Use `full_text_search` when users query with exact identifiers.

### Reranking

Enable reranking (`reranking_enable: true`) when:
- Retrieval quality is critical and user satisfaction is a key metric
- Your knowledge base has many similar chunks that embedding search struggles to differentiate
- You have a reranking model available (e.g., Cohere Rerank, BGE Reranker)

Reranking adds latency (~200–500ms) but significantly improves result ordering.

---

## Context Variable: How Dify Injects Retrieved Text

The `result` output of the `knowledge-retrieval` node is a formatted string that looks like:

```
[Document 1]
<title>Product FAQ</title>
<content>Our return policy allows returns within 30 days...</content>

[Document 2]
<title>Shipping Guide</title>
<content>Standard shipping takes 3-5 business days...</content>
```

This formatted string is what gets substituted into `{{#node_id.result#}}` in the LLM prompt.

See also:
- `docs/nodes/knowledge-retrieval.md` — full node reference
- `docs/config/llm-settings.md` — LLM model configuration
- `docs/patterns/agentic-pattern.md` — when to use agent-based RAG instead
