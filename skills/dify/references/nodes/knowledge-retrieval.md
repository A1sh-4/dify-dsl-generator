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

Do not use knowledge-retrieval to process a single document uploaded at runtime — use the document-extractor node for that purpose. Knowledge-retrieval is for querying a persistent, indexed collection.

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

In the LLM node's `context` block, point `variable_selector` to the `result` output of the knowledge-retrieval node. Then use `{{#context#}}` in the user prompt — Dify expands this to the retrieved chunks at runtime.

```yaml
context:
  enabled: true
  variable_selector:
    - '[knowledge_retrieval_node_id]'   # actual 13-digit node ID
    - result
```

In the prompt template user turn:

```yaml
- edition_type: basic
  id: '[uuid]'
  role: user
  text: '{{#context#}}'
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

The following matches the real structure exported from Dify. Note:

- `retrieval_mode: multiple` is the standard mode Dify uses when you configure weighted hybrid retrieval
- `query_variable_selector` uses `[start_node_id, sys.query]` — the start node's system query variable
- `query_attachment_selector: []` is always present
- The LLM node uses `{{#context#}}` in the user prompt to receive the retrieved chunks

```yaml
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
    - '[start_node_id]'   # 13-digit ID of the start node
    - sys.query
    retrieval_mode: multiple
    selected: false
    title: Knowledge Retrieval
    type: knowledge-retrieval
  height: 92
  id: '[knowledge_retrieval_node_id]'
  position:
    x: 376
    y: 303
  positionAbsolute:
    x: 376
    y: 303
  sourcePosition: right
  targetPosition: left
  type: custom
  width: 243
```

**Downstream LLM node — how to consume the retrieved context:**

```yaml
- data:
    context:
      enabled: true
      variable_selector:
      - '[knowledge_retrieval_node_id]'
      - result
    prompt_template:
    - edition_type: basic
      id: '[uuid]'
      role: system
      text: 'Answer only from the provided context. Cite your sources.'
    - edition_type: basic
      id: '[uuid]'
      role: user
      text: '{{#context#}}'   # expands to retrieved document chunks at runtime
    ...
```

**Ground-truth config reference:** `skills/dify/assets/chatflows/rag-chatflow.yml` — complete working RAG chatflow exported from a real Dify instance showing the full knowledge-retrieval node config and downstream LLM wiring.

## Pattern: Start → Knowledge-Retrieval → LLM → Answer

This is the standard RAG chatflow pattern. The start node captures the user's query, knowledge-retrieval finds relevant chunks, the LLM synthesizes an answer grounded in those chunks, and the answer node streams the result back to the user.

## Post-Import: Connecting the Knowledge Base on the Canvas

When a DSL is imported, the knowledge-retrieval node contains a placeholder `dataset_id` (`YOUR_DATASET_ID_HERE`). The node will be visible on the canvas but will show no dataset connected. You must connect it manually after import — this cannot be done through the YAML alone.

**Steps to connect:**

1. Open the imported app in the Dify canvas
2. Click the **Knowledge Retrieval** node (or whatever name was given to it) to open its settings panel
3. In the **Datasets** section, click the **+** (Add) button
4. A modal appears listing all knowledge bases in your workspace — select the one you created for this app
5. The node now shows the dataset name — close the panel

**Before doing this, the knowledge base must already exist and be fully indexed.** Always complete the knowledge base setup (upload, index, wait for "Completed" status on all documents) before importing the DSL and connecting the node.

**Order of operations:**

1. Create and index the knowledge base in the Knowledge tab
2. Import the DSL
3. Connect the knowledge base to the node on the canvas
4. Test the app

## Common Mistakes

1. **Using a wrong or placeholder dataset_id.** The `dataset_id` must exactly match the knowledge base ID shown in your Dify workspace. A wrong ID causes a silent failure with empty results.

2. **Setting top_k too low for multi-part questions.** If the answer spans several sections of a document, a top_k of 1 or 2 may miss critical chunks. Start with 5 and adjust based on result quality.

3. **Setting score_threshold too high.** A threshold of 0.9 may filter out genuinely relevant chunks that score 0.75–0.85. Start without a threshold and add one after reviewing actual scores.

4. **Forgetting that result is an array.** If you reference `{{#knowledge_retrieval.result#}}` in a template expecting a string, you get a serialized array representation. Always iterate over the array or use the LLM context feature.

5. **Not connecting knowledge-retrieval to the LLM context.** A common mistake is to retrieve results but forget to wire them into the LLM node's context or prompt. The retrieval has no effect if the LLM doesn't receive the results.
