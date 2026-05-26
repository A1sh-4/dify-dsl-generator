# Knowledge Base

Dify's knowledge base feature provides Retrieval-Augmented Generation (RAG) capabilities. Agents and workflows query one or more knowledge bases to retrieve relevant document chunks, which are then passed to an LLM node for grounded, citation-backed responses.

---

## Creating a Knowledge Base

Navigate to **Knowledge** in the Dify sidebar, then click **Create Knowledge Base**. Three ingestion methods are available:

### 1. File Upload
Upload documents from your local machine. Supported file types:
- **Text:** TXT, MD, HTML
- **Office:** PDF, DOCX, CSV, XLSX
- **Code/Markup:** JSON, YAML (treated as text)
- **Integrations:** Notion pages (via OAuth)

Files are chunked, embedded, and indexed automatically after upload.

### 2. Website Sync
Provide a URL and Dify will crawl and sync the page (or site) on a schedule. Useful for keeping documentation knowledge bases current. Requires enabling the Jina Reader or Firecrawl plugin for content extraction.

### 3. API Ingestion
POST documents programmatically via the Dify Knowledge Base API. Use this to build automated pipelines that push content from your CMS, database, or other systems into Dify on a schedule.

---

## Chunking Strategies

Chunking splits documents into segments before embedding. The strategy significantly impacts retrieval precision.

### Fixed-Size Chunking
Splits text into chunks of a fixed character count, with optional overlap.

- **Long PDFs (reports, manuals):** chunk size `500`, overlap `50`
- **Short articles / blog posts:** chunk size `200`, overlap `20`
- Overlap ensures context is not lost at chunk boundaries.

### Paragraph-Based Chunking
Splits on paragraph breaks (double newlines). Good for narrative documents and most general-purpose use. This is the recommended default for most ingestion jobs.

### Sentence-Based Chunking
Splits on sentence boundaries. Produces smaller, more precise chunks. Recommended when retrieval precision matters more than breadth (e.g., Q&A over legal or medical text).

### Structured Data (CSV/XLSX)
Use **paragraph split** mode. Each row or record becomes a chunk. Do not use fixed-size chunking on tabular data as it will split rows arbitrarily.

---

## Embedding Model Selection

The embedding model converts text chunks into vector representations. Model choice directly affects retrieval quality.

- **Production:** Use a high-quality embedding model such as `text-embedding-3-large` (OpenAI), `embed-english-v3.0` (Cohere), or `bge-large-en` (open-source). These produce dense, semantically rich embeddings.
- **Development/Cost-saving:** `text-embedding-3-small` or `bge-small-en` are cheaper and faster, but retrieval quality is lower.
- **Rule:** Once a knowledge base is indexed with a specific embedding model, you cannot change the model without re-indexing. Choose carefully before ingestion.
- The embedding model must be available in your Dify workspace (configured under **Settings → Model Providers**).

---

## Indexing Modes

### High Quality (Embedding-Based)
Uses the configured embedding model to vectorize all chunks. Enables semantic search and hybrid search. Costs tokens on ingestion. Required for production RAG.

### Economy (Keyword Only)
No embedding is performed. Uses BM25 keyword index only. Zero ingestion cost. Suitable for exact-match use cases or when budget is a constraint. Full-text search only — no semantic retrieval.

---

## Retrieval Modes

When a knowledge retrieval node queries a knowledge base, it can use one of three retrieval modes:

### Semantic Search
Uses cosine similarity between the query embedding and chunk embeddings. Best for natural-language questions where the wording may differ from document text. Requires high-quality indexing mode.

### Full-Text Search (BM25)
Keyword-based retrieval using BM25 scoring. Best for queries that use exact terminology found in documents (product codes, error codes, names). Works with economy indexing mode.

### Hybrid Search
Combines semantic and full-text search scores. Weights are configurable. Generally produces the best retrieval results. Requires high-quality indexing. Recommended for most production deployments.

---

## Reranking

Reranking applies a cross-encoder model to re-score retrieved chunks after initial retrieval. The reranker reads the full query and each chunk together, producing a more accurate relevance score.

- **When to enable:** When retrieval precision is critical (customer support, legal Q&A, technical docs).
- **Supported reranker models:** Cohere Rerank, BGE Reranker, Jina Reranker, and others configured in workspace model settings.
- **Tradeoff:** Adds latency and cost per query. Top-k chunks are passed to the reranker; only top-N (configurable) are forwarded to the LLM.
- **Typical setup:** Retrieve top-20 chunks → rerank → pass top-5 to LLM.

---

## Parent-Child Hierarchical Retrieval

Standard chunking retrieves small, precise chunks but loses surrounding context. Parent-child retrieval solves this:

- **Child chunks:** Small, semantically precise units used for retrieval matching.
- **Parent chunks:** Larger surrounding context returned to the LLM.

**How it works:** A child chunk matches the query. Dify returns the parent chunk (e.g., the full paragraph or section) to the LLM instead of just the small match.

**Use case:** When precise matching is needed but the LLM requires broader context to generate a coherent answer. Enable in the knowledge base indexing settings.

---

## Metadata Filtering

Documents in a knowledge base can have metadata fields attached (e.g., `department`, `product_version`, `date`, `document_type`).

**Adding metadata:**
1. Upload documents.
2. In the knowledge base document list, click a document and add key-value metadata.
3. Or, pass metadata via the API during programmatic ingestion.

**Using metadata filters in retrieval:**
In the knowledge retrieval node, configure filter conditions such as:
```
department = "engineering"
product_version >= "3.0"
```

Only chunks from documents matching the filter are retrieved. This is essential for multi-tenant deployments where different users should only access their own data partition.

---

## Keeping Knowledge Bases Updated

### Manual Re-upload
Delete outdated documents and re-upload updated versions. Simple but requires manual effort.

### Sync Scheduling (Website Sync)
For URL-synced knowledge bases, configure a sync schedule (daily, weekly) so content stays current automatically.

### API Pipeline
Build an ingestion job that queries your source system and pushes updates via the Knowledge Base API. Supports upsert (update existing documents by ID) and bulk add.

---

## External Knowledge Base Connection

Dify supports connecting to an external knowledge base via a custom API endpoint. Instead of Dify managing the vector store, your system hosts the retrieval logic and Dify calls your endpoint at query time.

**Setup:**
1. Implement an HTTP endpoint that accepts a query and returns ranked chunks.
2. Register the endpoint in **Settings → Knowledge → External Knowledge Base**.
3. Reference the external knowledge base in retrieval nodes like any internal knowledge base.

This is useful when the organization already has a vector database (Pinecone, Weaviate, Chroma) and wants to use it without re-indexing in Dify.

---

## Quality Testing

Before deploying a workflow that uses a knowledge base, test retrieval quality using the **Retrieval Test** interface:

1. Open the knowledge base in the Dify UI.
2. Click **Retrieval Test**.
3. Enter representative user queries.
4. Review which chunks are returned, their scores, and their relevance.
5. Adjust chunk size, retrieval mode, top-k, and score threshold based on results.

Always run retrieval tests before deploying to production.

---

## Knowledge Base ID in DSL YAML

When a knowledge base is referenced in a DSL YAML file, its ID appears as a placeholder. The actual knowledge base UUID is assigned at runtime when the DSL is imported into a Dify instance.

In generated YAML, knowledge base references look like:
```yaml
dataset_ids:
  - "<knowledge-base-uuid>"
```

The plugin generates placeholder UUIDs during DSL generation. Users must replace these with actual knowledge base IDs from their Dify workspace after import, or configure the correct IDs before import.

---

## Output Variable Structure

The knowledge retrieval node outputs a variable named `result`. This is an array of retrieved chunk objects.

Each chunk object contains:
```
result[i].content       — The text content of the chunk
result[i].score         — Relevance score (0.0 to 1.0)
result[i].document      — Parent document metadata (title, source URL)
result[i].segment_id    — Unique ID of the chunk within the knowledge base
```

**Accessing in DSL variable syntax:**
```
{{#knowledge_node_id.result#}}
```

---

## The Context Variable Pattern (RAG)

To implement RAG, pass the knowledge retrieval result to an LLM node using the context input type. The standard pattern:

1. **Knowledge Retrieval node** — queries knowledge base, outputs `result`.
2. **LLM node** — receives the retrieval output as a `context` input variable.

In the LLM node system prompt, reference the context like this (Jinja2 in the prompt template):
```
You are a helpful assistant. Answer based only on the following context:

{% for item in context %}
Source: {{ item.document.name }}
{{ item.content }}
{% endfor %}
```

In the DSL, the LLM node's context input maps to:
```yaml
context:
  enabled: true
  variable_selector:
    - knowledge_node_id
    - result
```

See `skills/dify/references/nodes/knowledge-retrieval.md` for the full node configuration reference and `skills/dify/references/patterns/rag-pipeline.md` for end-to-end RAG workflow examples.
