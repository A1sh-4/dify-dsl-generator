# Knowledge Retrieval Node

## Overview

The knowledge-retrieval node queries a Dify knowledge base using semantic, full-text, or hybrid search. It is the core building block for Retrieval-Augmented Generation (RAG) workflows — given a user query, it finds the most relevant document chunks from a pre-indexed knowledge base and returns them for use in an LLM prompt.

This node replaces the need to pass entire documents to the LLM. Instead of feeding the model a full corpus, the knowledge-retrieval node retrieves only the chunks most likely to contain the answer, keeping prompts focused and within context limits.

## When to Use

Use knowledge-retrieval when:

- You have a pre-built knowledge base in Dify containing indexed documents
- You want to answer questions grounded in specific source material
- You need source attribution (which document a passage came from)
- You are building a Q&A assistant, documentation search, or research tool

Do not use knowledge-retrieval to process a single document uploaded at runtime — use the doc-extractor node for that purpose. Knowledge-retrieval is for querying a persistent, indexed collection.

## Required Configuration

| Field | Description |
|-------|-------------|
| `dataset_id` | The ID of the knowledge base to query. Found in the knowledge base settings URL. |
| `query` | The search query string. Usually the user's input from the start node. |

## Retrieval Modes

| Mode | Description | Best for |
|------|-------------|----------|
| `semantic_search` | Embedding-based vector similarity search | Questions where phrasing varies |
| `full_text_search` | Keyword-based BM25 search | Exact term lookup, code, SKU numbers |
| `hybrid_search` | Combines semantic and full-text scores | General purpose — best default choice |

## Search Parameters

| Parameter | Type | Range | Description |
|-----------|------|--------|-------------|
| `top_k` | integer | 1–20 | Number of chunks to return |
| `score_threshold` | float | 0.0–1.0 | Minimum relevance score; chunks below this are excluded |
| `score_threshold_enabled` | boolean | — | Whether to enforce the score threshold |

A `top_k` of 3–5 is typical for focused answers. Use a higher `top_k` (8–10) when the answer may span multiple sections. Set `score_threshold` to 0.5–0.7 to filter out clearly irrelevant chunks.

## Reranking

Reranking applies a cross-encoder model to re-score the initial retrieval results for higher precision. It is slower but produces better-ranked results.

```yaml
reranking_mode: reranking_model
reranking_model:
  provider: cohere
  model: rerank-english-v3.0
```

Set `reranking_mode: disabled` to skip reranking (default, faster).

## Multiple Datasets

You can query multiple knowledge bases in a single node by listing multiple entries in the `dataset_ids` array. Results are merged and ranked together.

## Output Variable

The node produces a single output variable: `result`

| Variable | Type | Description |
|----------|------|-------------|
| `result` | array of objects | Ranked list of retrieved document chunks |

Each object in the `result` array contains:

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | The text content of the retrieved chunk |
| `score` | float | Relevance score (0.0–1.0) |
| `title` | string | Document title |
| `url` | string | Source URL or file path |
| `segment_id` | string | Internal identifier for the chunk segment |

Reference individual fields downstream as `{{#knowledge_retrieval_node_id.result[0].content#}}` or pass the full array to template-transform for formatting.

## How to Pass Results to an LLM

**Method 1: Context variable (recommended)**

In the LLM node's context section, add the `result` array directly. The LLM node will automatically format the chunks into the prompt.

```yaml
- id: llm_answer
  type: llm
  data:
    context:
      enabled: true
      variable_selector:
        - knowledge_retrieval
        - result
```

**Method 2: Format with template-transform**

Use a template-transform node to build a custom context string, then inject it into the LLM prompt as a regular variable:

```jinja2
{% for chunk in results %}
Source: {{ chunk.title }}
{{ chunk.content }}
---
{% endfor %}
```

## Complete YAML Example

```yaml
nodes:
  - id: start
    type: start
    data:
      variables:
        - variable: user_query
          type: string
          label: Your question
          required: true

  - id: knowledge_retrieval
    type: knowledge-retrieval
    data:
      title: Search Knowledge Base
      query_variable_selector:
        - start
        - user_query
      dataset_ids:
        - your-dataset-id-here
      retrieval_mode: hybrid_search
      single_retrieval_config:
        model:
          provider: openai
          name: text-embedding-3-small
          mode: embedding
      top_k: 5
      score_threshold_enabled: true
      score_threshold: 0.5
      reranking_mode: disabled

  - id: llm_answer
    type: llm
    data:
      title: Answer Question
      model:
        provider: openai
        name: gpt-4o
        mode: chat
      context:
        enabled: true
        variable_selector:
          - knowledge_retrieval
          - result
      prompt_template:
        - role: system
          text: >
            You are a helpful assistant. Answer the user's question using only
            the provided context. If the context does not contain the answer,
            say so clearly.
        - role: user
          text: "{{#start.user_query#}}"

  - id: end
    type: end
    data:
      outputs:
        - variable: answer
          value_selector:
            - llm_answer
            - text

edges:
  - source: start
    target: knowledge_retrieval
  - source: knowledge_retrieval
    target: llm_answer
  - source: llm_answer
    target: end
```

## Pattern: Start → Knowledge-Retrieval → LLM → Answer

This is the standard RAG chatflow pattern. The start node captures the user's query, knowledge-retrieval finds relevant chunks, the LLM synthesizes an answer grounded in those chunks, and the answer node streams the result back to the user.

## Common Mistakes

1. **Using a wrong or placeholder dataset_id.** The `dataset_id` must exactly match the knowledge base ID shown in your Dify workspace. A wrong ID causes a silent failure with empty results.

2. **Setting top_k too low for multi-part questions.** If the answer spans several sections of a document, a top_k of 1 or 2 may miss critical chunks. Start with 5 and adjust based on result quality.

3. **Setting score_threshold too high.** A threshold of 0.9 may filter out genuinely relevant chunks that score 0.75–0.85. Start without a threshold and add one after reviewing actual scores.

4. **Forgetting that result is an array.** If you reference `{{#knowledge_retrieval.result#}}` in a template expecting a string, you get a serialized array representation. Always iterate over the array or use the LLM context feature.

5. **Not connecting knowledge-retrieval to the LLM context.** A common mistake is to retrieve results but forget to wire them into the LLM node's context or prompt. The retrieval has no effect if the LLM doesn't receive the results.
