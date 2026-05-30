# RAG Pattern: Retrieval-Augmented Generation

## Overview

RAG (Retrieval-Augmented Generation) is the pattern of injecting relevant context from a knowledge base into an LLM prompt before asking it to answer. Dify provides a first-class `knowledge-retrieval` node that handles chunked document retrieval, embedding-based similarity search, optional reranking, and score filtering. This document covers both the basic 4-node RAG pipeline and the advanced 6-node pipeline with query rewriting.

---

## The Core Wiring Rule

The `knowledge-retrieval` node outputs a single variable: `result`. To pass it to an LLM node, enable the `context` block in the LLM node and point `variable_selector` to `[knowledge_retrieval_node_id, result]`. In the user prompt, use `{{#context#}}` — Dify expands this to the retrieved chunks at runtime.

```yaml
context:
  enabled: true
  variable_selector:
    - "[knowledge_retrieval_node_id]"
    - result
```

User prompt:

```
{{#context#}}
```

This is the **only** correct way to pass retrieved context into an LLM node. Do NOT inject `{{#node_id.result#}}` directly into the system prompt text — use `{{#context#}}` in the user prompt via the `context` block.

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
          dataset_ids:
          - YOUR_DATASET_ID_HERE
          multiple_retrieval_config:
            reranking_enable: false
            reranking_mode: weighted_score
            score_threshold: null
            top_k: 5
            weights:
              keyword_setting:
                keyword_weight: 0.3
              vector_setting:
                embedding_model_name: YOUR_EMBEDDING_MODEL_HERE
                embedding_provider_name: langgenius/openai_api_compatible/openai_api_compatible
                vector_weight: 0.7
              weight_type: customized
          query_attachment_selector: []
          query_variable_selector:
          - "1747000000001"
          - sys.query
          retrieval_mode: multiple
          selected: false
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
        width: 243

      - data:
          context:
            enabled: true
            variable_selector:
              - "1747000000002"
              - result
          desc: "Generate an answer grounded in the retrieved context."
          model:
            completion_params:
              temperature: 0.3
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: system-prompt
              role: system
              text: |
                You are a helpful assistant. Answer the user's question based ONLY on the
                provided context. If the answer is not in the context, say "I don't have
                that information in my knowledge base." Do not use outside knowledge.
            - id: user-prompt
              role: user
              text: "{{#context#}}"
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
- **llm (answer)**: has a `context` block wired to the knowledge-retrieval node's `result`; uses `{{#context#}}` in the user prompt to inject the retrieved text
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
          dataset_ids:
          - YOUR_DATASET_ID_HERE
          multiple_retrieval_config:
            reranking_enable: true
            reranking_mode: reranking_model
            reranking_model:
              model: rerank-english-v3.0
              provider_name: cohere
            score_threshold: null
            top_k: 5
            weights:
              keyword_setting:
                keyword_weight: 0.3
              vector_setting:
                embedding_model_name: YOUR_EMBEDDING_MODEL_HERE
                embedding_provider_name: langgenius/openai_api_compatible/openai_api_compatible
                vector_weight: 0.7
              weight_type: customized
          query_attachment_selector: []
          query_variable_selector:
          - "1747000000011"
          - text
          retrieval_mode: multiple
          selected: false
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
        width: 243

      - data:
          context:
            enabled: true
            variable_selector:
              - "1747000000012"
              - result
          desc: "Generate a grounded answer using retrieved context."
          model:
            completion_params:
              temperature: 0.3
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: system-answer
              role: system
              text: |
                You are a helpful assistant. Answer the user's question based ONLY on the
                provided context. Rules:
                - Answer only from the provided context
                - If the answer is not in the context, say: "I don't have that information in my knowledge base."
                - Do not use outside knowledge or make assumptions
                - Be concise and direct
                - Cite relevant sections when helpful
            - id: user-answer
              role: user
              text: "{{#context#}}"
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

Use this structure in any LLM node that receives knowledge base output.

**Step 1 — Enable the context block** (this is what makes `{{#context#}}` work):

```yaml
context:
  enabled: true
  variable_selector:
    - "KNOWLEDGE_RETRIEVAL_NODE_ID"
    - result
```

**Step 2 — System prompt** (instructions only — do NOT inject `{{#node_id.result#}}` here):

```
You are a helpful assistant. Answer based ONLY on the provided context.
If the answer is not in the context, say "I don't have that information in my knowledge base."
Do not use outside knowledge. Do not make assumptions. Be concise.
Format: [adapt based on use case — paragraph, bullet list, JSON, etc.]
```

**Step 3 — User prompt** set to `{{#context#}}`:

```
{{#context#}}
```

`{{#context#}}` is expanded by Dify at runtime to the formatted retrieved chunks. It is only available when the `context` block is enabled and pointing to a knowledge-retrieval node. For workflows with a custom start variable, append the user's question after the context:

```
{{#context#}}

{{#START_NODE_ID.user_question#}}
```

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

This formatted string is what Dify provides when the `context` block is enabled and the prompt uses `{{#context#}}`.

See also:
- `skills/dify/references/nodes/knowledge-retrieval.md` — full node reference
- `skills/dify/references/config/llm-settings.md` — LLM model configuration
- `skills/dify/references/patterns/agentic-pattern.md` — when to use agent-based RAG instead

---

## Parallel Multi-KB RAG

**When to use:** The application has two or more separate knowledge bases queried simultaneously. Choose the architecture based on what you need from the results:

| Situation | Architecture |
| --- | --- |
| Both KBs cover the same topic; one unified answer is enough | **Option A** — merge arrays → one context block → one LLM |
| Each KB is specialized; the answer must treat them distinctly | **Option B** — separate parallel LLM per KB → merge text outputs |

**Why `{{#kr_node_id.result#}}` cannot be used in prompts:** The knowledge-retrieval node outputs an array of objects. Dify's prompt engine cannot render an array directly — only the `context` block knows how to format it. All KR results must flow through a `context` block and be referenced as `{{#context#}}` in the prompt.

---

### Option A — Merge via Code Node (same-topic KBs)

```
start ──┬── KR (KB 1) ──┐
        └── KR (KB 2) ──┴── code (merge arrays) ── llm ── answer
                                                    ↑
                                              context block
```

The code node receives both KR result arrays, concatenates them into one array (each item already has a `content` key — the format the context block requires), and outputs the merged array. The LLM's `context` block points to this merged output. One LLM, one `{{#context#}}`, unified answer.

#### Node Positions — Option A

| Node | x | y |
|------|---|---|
| start | 80 | 282 |
| KR (KB 1) | 380 | 132 |
| KR (KB 2) | 380 | 432 |
| code (merge) | 680 | 282 |
| llm | 980 | 282 |
| answer | 1280 | 282 |

#### Complete YAML — Option A

```yaml
app:
  description: "Queries two KBs in parallel, merges context, answers with one LLM."
  icon: "\U0001F4DA"
  icon_background: "#EEF4FF"
  mode: advanced-chat
  name: Parallel Multi-KB RAG (Option A)
dependencies: []
features:
  file_upload:
    enabled: false
  opening_statement: "Ask me anything. I'll search both knowledge bases at once."
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
          isInLoop: false
          sourceType: start
          targetType: knowledge-retrieval
        id: "1748100000001-source-1748100000002-target"
        source: "1748100000001"
        sourceHandle: source
        target: "1748100000002"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          isInLoop: false
          sourceType: start
          targetType: knowledge-retrieval
        id: "1748100000001-source-1748100000003-target"
        source: "1748100000001"
        sourceHandle: source
        target: "1748100000003"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          isInLoop: false
          sourceType: knowledge-retrieval
          targetType: code
        id: "1748100000002-source-1748100000009-target"
        source: "1748100000002"
        sourceHandle: source
        target: "1748100000009"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          isInLoop: false
          sourceType: knowledge-retrieval
          targetType: code
        id: "1748100000003-source-1748100000009-target"
        source: "1748100000003"
        sourceHandle: source
        target: "1748100000009"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          isInLoop: false
          sourceType: code
          targetType: llm
        id: "1748100000009-source-1748100000005-target"
        source: "1748100000009"
        sourceHandle: source
        target: "1748100000005"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          isInLoop: false
          sourceType: llm
          targetType: answer
        id: "1748100000005-source-1748100000006-target"
        source: "1748100000005"
        sourceHandle: source
        target: "1748100000006"
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
        id: "1748100000001"
        position:
          x: 80
          y: 282
        positionAbsolute:
          x: 80
          y: 282
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          dataset_ids:
            - "YOUR_KB1_DATASET_ID_HERE"
          desc: "Search the first knowledge base."
          query_variable_selector:
            - "1748100000001"
            - sys.query
          retrieval_mode: multiple
          multiple_retrieval_config:
            reranking_enable: false
            top_k: 5
            weights:
              keyword_setting:
                keyword_weight: 0.3
              vector_setting:
                vector_weight: 0.7
              weight_type: customized
          query_attachment_selector: []
          title: KB 1 Retrieval
          type: knowledge-retrieval
        height: 92
        id: "1748100000002"
        position:
          x: 380
          y: 132
        positionAbsolute:
          x: 380
          y: 132
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          dataset_ids:
            - "YOUR_KB2_DATASET_ID_HERE"
          desc: "Search the second knowledge base."
          query_variable_selector:
            - "1748100000001"
            - sys.query
          retrieval_mode: multiple
          multiple_retrieval_config:
            reranking_enable: false
            top_k: 5
            weights:
              keyword_setting:
                keyword_weight: 0.3
              vector_setting:
                vector_weight: 0.7
              weight_type: customized
          query_attachment_selector: []
          title: KB 2 Retrieval
          type: knowledge-retrieval
        height: 92
        id: "1748100000003"
        position:
          x: 380
          y: 432
        positionAbsolute:
          x: 380
          y: 432
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      # Code node acts as fan-in AND merger. Receives both KR result arrays,
      # concatenates them. Each item already has a "content" key — the format
      # the LLM context block requires. No labels needed for same-topic KBs.
      - data:
          code: |
            def main(kb1_result: list, kb2_result: list) -> dict:
                return {'merged': kb1_result + kb2_result}
          code_language: python3
          desc: "Merge both KB result arrays into one for the context block."
          outputs:
            merged:
              children: null
              type: array[object]
          title: Merge KB Results
          type: code
          variables:
            - label: kb1_result
              value_selector:
                - "1748100000002"
                - result
              variable: kb1_result
            - label: kb2_result
              value_selector:
                - "1748100000003"
                - result
              variable: kb2_result
        height: 90
        id: "1748100000009"
        position:
          x: 680
          y: 282
        positionAbsolute:
          x: 680
          y: 282
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          context:
            enabled: true
            variable_selector:
              - "1748100000009"
              - merged
          desc: "Answer using the merged context from both KBs."
          model:
            completion_params:
              temperature: 0.3
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: "system-prompt"
              role: system
              text: |
                You are a helpful assistant. Answer the user's question using
                the retrieved context. If the context does not contain the answer,
                say "I could not find relevant information in the knowledge base."
                Do not use outside knowledge.
            - id: "user-prompt"
              role: user
              text: "Question: {{#1748100000001.sys.query#}}\n\n{{#context#}}"
          title: Answer LLM
          type: llm
          vision:
            enabled: false
        height: 98
        id: "1748100000005"
        position:
          x: 980
          y: 282
        positionAbsolute:
          x: 980
          y: 282
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          answer: "{{#1748100000005.text#}}"
          desc: ""
          title: Answer
          type: answer
        height: 54
        id: "1748100000006"
        position:
          x: 1280
          y: 282
        positionAbsolute:
          x: 1280
          y: 282
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
```

---

### Option B — Separate Parallel LLMs (specialized KBs)

```
start ──┬── KR (KB 1) ── llm-1 (context block) ──┐
        └── KR (KB 2) ── llm-2 (context block) ──┴── template-transform ── answer
```

Each LLM has its own `context` block wired to its own KR node. Both KR→LLM chains run in parallel. The `template-transform` waits for both LLMs, binds their text outputs as named variables, and renders a labeled combined response.

**Use this when** the two KBs serve different purposes — e.g., KB1 is policy documents and KB2 is technical procedures — and the answer needs to present each source's findings separately.

#### Node Positions — Option B

| Node | x | y |
|------|---|---|
| start | 80 | 282 |
| KR (KB 1) | 380 | 107 |
| llm-1 | 680 | 107 |
| KR (KB 2) | 380 | 457 |
| llm-2 | 680 | 457 |
| template-transform | 980 | 282 |
| answer | 1280 | 282 |

#### Key Node Configurations — Option B

Each LLM node has its own `context` block and user prompt:

```yaml
# llm-1 (upper branch — KB 1)
context:
  enabled: true
  variable_selector:
    - "kb1_retrieval_node_id"
    - result
prompt_template:
  - role: system
    text: "You are a helpful assistant. Answer based only on the provided context."
  - role: user
    text: "Question: {{#start_node_id.sys.query#}}\n\n{{#context#}}"

# llm-2 (lower branch — KB 2)
context:
  enabled: true
  variable_selector:
    - "kb2_retrieval_node_id"
    - result
prompt_template:
  - role: system
    text: "You are a helpful assistant. Answer based only on the provided context."
  - role: user
    text: "Question: {{#start_node_id.sys.query#}}\n\n{{#context#}}"
```

The `template-transform` binds both LLM text outputs as separate named variables and renders them with distinct labels:

```yaml
# template-transform
variables:
  - value_selector: ["llm1_node_id", "text"]
    variable: kb1_answer
  - value_selector: ["llm2_node_id", "text"]
    variable: kb2_answer

template: |
  **From Knowledge Base 1 (Policy):**
  {{ kb1_answer }}

  **From Knowledge Base 2 (Procedures):**
  {{ kb2_answer }}
```

The `answer` node then outputs `{{#template_transform_node_id.output#}}`.

**No `variable-aggregator` needed** — `template-transform` itself acts as the fan-in barrier. It automatically waits for all its input variables to be ready before executing.

### Node Count Formula

- **Option A** (merge): `1 (start) + N (KR nodes) + 1 (code merge) + 1 (LLM) + 1 (answer) = N + 4`
- **Option B** (separate): `1 (start) + N (KR) + N (LLMs) + 1 (template-transform) + 1 (answer) = 2N + 3`

For 2 KBs: Option A = 6 nodes, Option B = 7 nodes.



---

## Iterative RAG (Iteration Node)

**When to use:** The workflow receives a list of questions (or documents) and must retrieve + answer each one using a shared knowledge base. This is a batch pattern — each item is processed independently using the same retrieval pipeline.

### Node Graph

```
start ── iteration ── template-transform ── answer
              └── [inner: knowledge-retrieval → llm (per-item answer)]
```

The iteration node loops over the input array. For each item, the inner sub-workflow retrieves relevant chunks and generates an answer. The iteration collects all per-item answers into an output array, which the template-transform renders into a final response.

### When NOT to Use This Pattern

- If state must carry from one question to the next (e.g., building a cumulative summary) → use `loop` instead
- If you need parallel processing → set `is_parallel: true` with `parallelism: 2–4`, but note this increases retrieval load on your KB and model rate limits simultaneously

### Complete YAML — Batch Q&A Iteration (Workflow)

```yaml
app:
  description: "Answers a list of questions using a knowledge base, one question at a time."
  icon: "\U0001F4CB"
  icon_background: "#EEF4FF"
  mode: workflow
  name: Batch RAG Q&A
dependencies: []
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
          isInLoop: false
          sourceType: start
          targetType: code
        id: "1748200000001-source-1748200000009-target"
        source: "1748200000001"
        sourceHandle: source
        target: "1748200000009"
        targetHandle: target
        type: custom
        zIndex: 0

      - data:
          isInIteration: false
          isInLoop: false
          sourceType: code
          targetType: iteration
        id: "1748200000009-source-1748200000002-target"
        source: "1748200000009"
        sourceHandle: source
        target: "1748200000002"
        targetHandle: target
        type: custom
        zIndex: 0

      - data:
          isInIteration: false
          isInLoop: false
          sourceType: iteration
          targetType: template-transform
        id: "1748200000002-source-1748200000007-target"
        source: "1748200000002"
        sourceHandle: source
        target: "1748200000007"
        targetHandle: target
        type: custom
        zIndex: 0

      - data:
          isInIteration: false
          isInLoop: false
          sourceType: template-transform
          targetType: end
        id: "1748200000007-source-1748200000008-target"
        source: "1748200000007"
        sourceHandle: source
        target: "1748200000008"
        targetHandle: target
        type: custom
        zIndex: 0

      # Inner edges (inside iteration)
      - data:
          isInIteration: true
          isInLoop: false
          iteration_id: "1748200000002"
          sourceType: iteration-start
          targetType: knowledge-retrieval
        id: "1748200000002start-source-1748200000003-target"
        source: "1748200000002start"
        sourceHandle: source
        target: "1748200000003"
        targetHandle: target
        type: custom
        zIndex: 1002

      - data:
          isInIteration: true
          isInLoop: false
          iteration_id: "1748200000002"
          sourceType: knowledge-retrieval
          targetType: llm
        id: "1748200000003-source-1748200000004-target"
        source: "1748200000003"
        sourceHandle: source
        target: "1748200000004"
        targetHandle: target
        type: custom
        zIndex: 1002

    nodes:
      - data:
          desc: ""
          title: Start
          type: start
          variables:
            - label: Questions
              max_length: 10000
              options: []
              required: true
              type: paragraph          # User pastes a JSON array of questions
              variable: questions_json
        height: 90
        id: "1748200000001"
        position:
          x: 30
          y: 303
        positionAbsolute:
          x: 30
          y: 303
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      # Code node: parse raw JSON string into a list
      - data:
          code: |
            import json

            def main(questions_json: str) -> dict:
                return {'questions': json.loads(questions_json)}
          code_language: python3
          desc: "Parse the JSON string of questions into an array the iteration node can loop over."
          outputs:
            questions:
              children: null
              type: array[string]
          title: Parse Questions
          type: code
          variables:
            - label: questions_json
              value_selector:
                - "1748200000001"
                - questions_json
              variable: questions_json
        height: 90
        id: "1748200000009"
        position:
          x: 334
          y: 303
        positionAbsolute:
          x: 334
          y: 303
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      # Iteration container
      - data:
          desc: "Process each question through the RAG pipeline."
          is_parallel: false
          iterator_selector:
            - "1748200000009"
            - questions
          max_iterations: 50
          output_selector:
            - "1748200000004"
            - text
          parallelism: 1
          title: RAG Q&A Iteration
          type: iteration
          nodes:
            - data:
                desc: ""
                title: ""
                type: iteration-start
              id: "1748200000002start"
              position:
                x: 30
                y: 78
              type: custom
              width: 44
              height: 44

            # Inner knowledge retrieval
            - data:
                dataset_ids:
                  - "YOUR_DATASET_ID_HERE"            # Replace with KB ID
                desc: "Retrieve relevant context for this question."
                multiple_retrieval_config:
                  reranking_enable: false
                  top_k: 5
                  weights:
                    keyword_setting:
                      keyword_weight: 0.3
                    vector_setting:
                      vector_weight: 0.7
                    weight_type: customized
                query_attachment_selector: []
                query_variable_selector:
                  - "1748200000002start"
                  - item                              # Current question from the iteration
                retrieval_mode: multiple
                title: Knowledge Retrieval
                type: knowledge-retrieval
              id: "1748200000003"
              position:
                x: 144
                y: 68
              type: custom
              width: 244
              height: 92

            # Inner LLM: answer this one question
            # context block injects the KR result — the ONLY correct way for arrays.
            # {{#context#}} in the user prompt is where the retrieved text appears.
            - data:
                context:
                  enabled: true
                  variable_selector:
                    - "1748200000003"
                    - result
                desc: "Answer the current question using the retrieved context."
                model:
                  completion_params:
                    temperature: 0.3
                  mode: chat
                  name: gpt-4o-mini
                  provider: openai
                prompt_template:
                  - id: "qa-system"
                    role: system
                    text: |
                      You are a helpful assistant. Answer the question based ONLY
                      on the provided context. Be concise. If the context does not
                      contain the answer, say "Not found in knowledge base."
                  - id: "qa-user"
                    role: user
                    text: "Question: {{#1748200000002start.item#}}\n\n{{#context#}}"
                title: Per-Question LLM
                type: llm
                vision:
                  enabled: false
              id: "1748200000004"
              position:
                x: 448
                y: 68
              type: custom
              width: 244
              height: 98

          edges:
            - source: "1748200000002start"
              target: "1748200000003"
            - source: "1748200000003"
              target: "1748200000004"
        height: 280
        id: "1748200000002"
        position:
          x: 634
          y: 180
        positionAbsolute:
          x: 634
          y: 180
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 780

      # Template-transform: render all answers
      - data:
          desc: "Format all Q&A pairs into a readable report."
          template: |
            {% for answer in answers %}
            **Q{{ loop.index }}: {{ questions[loop.index0] }}**
            {{ answer }}

            {% endfor %}
          title: Format Results
          type: template-transform
          variables:
            - value_selector:
                - "1748200000002"
                - output
              variable: answers
            - value_selector:
                - "1748200000009"
                - questions
              variable: questions
        height: 90
        id: "1748200000007"
        position:
          x: 1474
          y: 303
        positionAbsolute:
          x: 1474
          y: 303
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          desc: ""
          outputs:
            - label: Q&A Report
              name: report
              type: string
              value_selector:
                - "1748200000007"
                - output
          title: End
          type: end
        height: 90
        id: "1748200000008"
        position:
          x: 1774
          y: 303
        positionAbsolute:
          x: 1774
          y: 303
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
```

**Key design choices:**

- The `code` node (`1748200000009`) is mandatory: Dify's start node accepts `questions_json` as a `paragraph` (raw string). The iteration node requires an actual array. Without the `json.loads()` parse step, the iterator would receive a string and iterate over individual characters, not questions.
- `is_parallel: false` / `parallelism: 1` — sequential processing prevents knowledge base rate-limit exhaustion
- `output_selector: ['1748200000004', 'text']` — the iteration collects the LLM's text output for each question into the `output` array
- The template-transform binds `questions` from the code node's parsed output (not the raw `questions_json` string), enabling `questions[loop.index0]` to correctly index into the array

---

## Agentic Loop RAG (Loop Node)

**When to use:** High-stakes Q&A where a single retrieval pass may be insufficient. The loop retrieves, evaluates its own context, and retries — up to `loop_count` times — before producing a final answer. Unlike iterative RAG (fixed list of items), this pattern has no predetermined number of cycles.

### Loop RAG Flow Diagram

```
start ── loop ──────────────────────────────────────── answer
              └── [inner: KR ── llm (context block)
                       ── code (parse verdict+answer)
                       ── variable-assigner]
```

**How it works:**

- Loop variables: `is_sufficient` (string, `"no"`) and `answer` (string, `""`)
- Break condition: `is_sufficient = "yes"`
- Each cycle: KR retrieves → LLM evaluates + drafts answer via `{{#context#}}` → code node splits the two-line output into flat fields → assigner writes them to loop variables
- After the loop: the `answer` loop variable (a plain string) feeds directly into the `answer` node — no outer LLM needed

**Why a code node is needed:** The LLM outputs a single text string containing both the verdict and the answer draft. The variable-assigner can only write to loop variables from top-level node output fields. A code node that splits the text and returns `{is_sufficient, answer}` as separate top-level string fields gives the assigner simple flat selectors.

**Why no outer LLM:** KR result arrays cannot be accessed outside the loop container. The answer is drafted inside the loop where the `context` block has access to the KR result. The `answer` loop variable carries the final string out.

### Canvas Positions

| Node | x | y |
|------|---|---|
| start (outer) | 30 | 303 |
| loop container (w:1380) | 334 | 303 |
| answer (outer) | 1774 | 303 |
| loop-start (inner, relative) | 60 | 101 |
| knowledge-retrieval (inner, relative) | 164 | 91 |
| llm (inner, relative) | 468 | 83 |
| code — parse verdict (inner, relative) | 772 | 83 |
| variable-assigner (inner, relative) | 1076 | 83 |

### Complete YAML

See `skills/dify/references/nodes/loop.md` — the complete importable YAML is the primary example in that file. It covers the full node and edge structure including correct `dataset_ids` + `multiple_retrieval_config` KR structure, context block wiring, code node parsing, and variable-assigner selectors.

### LLM Prompt Pattern

```
System:
You are a research assistant. Review the retrieved context and answer the question.

Format your response as exactly two parts:
Line 1: yes   (if context is sufficient for a complete answer)
        no    (if context is missing key information)
Line 2 onwards: Your best answer based on the context. Always write something.

User:
Question: {{#start_node_id.sys.query#}}

{{#context#}}
```

`{{#context#}}` is injected by the LLM node's `context` block — never use `{{#kr_node_id.result#}}` directly in a prompt.

### Loop Count Guidelines for RAG

| `loop_count` | When to use |
|-------------|-------------|
| 2 | Simple factual KBs; use 2 as a safety net |
| 3 | Most RAG scenarios — best balance of quality and cost |
| 5 | Research-grade Q&A where depth matters more than latency |
| > 5 | Rarely justified — if 5 passes fail, the KB is missing content |

---

## RAG Topology Selection Guide

| Scenario | Topology | Key node(s) |
|----------|----------|-------------|
| One KB, one question per run | **Basic RAG** | `knowledge-retrieval → llm` |
| Short or ambiguous user queries | **RAG + query rewrite** | `llm → knowledge-retrieval → llm` |
| Multiple separate KBs, same question | **Parallel multi-KB RAG** | `N × knowledge-retrieval (parallel) → aggregator → llm` |
| Batch: list of questions against one KB | **Iterative RAG** | `iteration [knowledge-retrieval → llm] → template` |
| High-stakes Q&A, uncertain first-pass quality | **Agentic loop RAG** | `loop [knowledge-retrieval → check llm → assigner] → llm` |

See `skills/dify/agents/knowledge-architect.md` Step 0 for the full decision guide used by the knowledge-architect agent.
