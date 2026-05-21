# Knowledge Base Setup

Dify knowledge bases provide the document storage and retrieval layer for RAG (Retrieval-Augmented Generation) workflows. This guide covers creating a knowledge base, uploading and chunking documents, selecting embedding models, and testing retrieval quality before connecting a knowledge base to a workflow.

---

## Creating a Knowledge Base

1. Open your Dify instance and click the **Knowledge** tab in the left sidebar.
2. Click **Create Knowledge Base**.
3. Enter a name and optional description. Use a name that clearly identifies the content (e.g., "Product FAQ", "Support Docs v2", "Internal Policy").
4. Choose a creation method:
   - **Upload File** — upload documents from your local machine
   - **Sync from Website** — provide a URL; Dify crawls and indexes the page(s)
   - **Create via API** — use the datasets API to create and populate programmatically

Click **Create** to proceed to the document upload and chunking configuration screen.

---

## Supported Document Types

The following file formats can be uploaded directly:

| Format | Notes |
|---|---|
| PDF | Text extraction; scanned PDFs (image-only) may require OCR |
| DOCX | Microsoft Word documents |
| TXT | Plain text |
| MD | Markdown files |
| HTML | Web pages; HTML tags are stripped during processing |
| CSV | Each row is treated as a chunk when using the paragraph splitter |
| XLSX | Excel files; sheet data is extracted as text |
| PPTX | PowerPoint; slide text is extracted |

You can also paste text directly into the text input field if you don't have a file to upload.

---

## Chunking Strategy

Chunking controls how Dify splits documents into retrievable pieces. Choosing the right strategy significantly affects retrieval quality. Select chunking settings on the document upload screen.

### Recommended Settings by Document Type

| Document Type | Chunk Size | Overlap | Split By |
|---|---|---|---|
| Long PDFs (books, annual reports) | 500 tokens | 50 tokens | Paragraph |
| Technical documentation | 300 tokens | 30 tokens | Paragraph |
| Short blog posts or articles | 200 tokens | 20 tokens | Paragraph |
| FAQ documents (Q&A pairs) | 150 tokens | 10 tokens | Line |
| CSV / structured data | — | — | Paragraph (per row) |

**Chunk size** controls the maximum number of tokens per chunk. Smaller chunks retrieve more precisely but may lack enough context for the LLM to generate a complete answer. Larger chunks give the LLM more context but may include irrelevant content that degrades answer quality.

**Overlap** ensures that the end of one chunk and the beginning of the next share some text. This prevents important sentences from being cut off mid-thought at a chunk boundary. An overlap of 10–15% of the chunk size is a good default.

**Custom separators:** For documents with consistent structure (e.g., headers, numbered sections), you can add custom separator strings. Dify splits on those strings first before applying the token limit.

---

## Embedding Model Selection

The embedding model converts text chunks into vector representations used for semantic search. You must configure an embedding model before indexing.

**Key rule:** The embedding model used during indexing must match the embedding model used during retrieval. Changing the embedding model after indexing requires re-indexing all documents.

| Model | Provider | Quality | Cost |
|---|---|---|---|
| `text-embedding-3-large` | OpenAI | Highest | Higher |
| `voyage-2` | Voyager AI | High | Moderate |
| `text-embedding-3-small` | OpenAI | Good | Low |
| `text-embedding-ada-002` | OpenAI | Good | Low |
| `nomic-embed-text` | Ollama (local) | Good | Free |
| `mxbai-embed-large` | Ollama (local) | Good | Free |

For most production knowledge bases, `text-embedding-3-small` provides a good quality-to-cost balance. For highest accuracy in complex retrieval scenarios, use `text-embedding-3-large` or `voyage-2`.

For development and testing, or for workflows where data cannot leave your infrastructure, use an Ollama embedding model running locally.

---

## Indexing Modes

Choose the indexing mode on the document upload screen:

**High Quality (recommended):**
Creates vector embeddings for every chunk. Enables semantic search, hybrid search, and reranking. Costs embedding tokens. Required for any retrieval mode other than full-text search.

**Economy:**
Keyword-based indexing only (BM25 algorithm). No embedding cost. Only supports full-text search (exact and fuzzy keyword matching). Appropriate when semantic search is not needed and cost is a concern.

For most knowledge-intensive applications, use High Quality. Economy mode misses semantically related content that doesn't share exact keywords with the query.

---

## Retrieval Modes

Once a knowledge base is indexed and connected to a knowledge retrieval node, you configure the retrieval mode in the node settings:

| Mode | Description | Requires |
|---|---|---|
| Semantic search | Pure vector similarity search | High quality indexing |
| Full-text search | BM25 keyword search | Either indexing mode |
| Hybrid search | Combines semantic + keyword results | High quality indexing |

Hybrid search with reranking generally produces the best results. It catches both semantically similar chunks (that don't share keywords) and exact keyword matches.

**Reranking:** After initial retrieval, a reranking model re-scores the candidates and returns the most relevant subset. Enable reranking in the knowledge retrieval node settings. A reranking model must be configured in Settings → Model Provider → System Model Settings.

---

## Testing Retrieval Quality

Before connecting a knowledge base to a production workflow, test its retrieval accuracy:

1. Open the knowledge base in Dify.
2. Click **Retrieval Test** (in the top bar or sidebar).
3. Enter queries that represent actual user questions your workflow will handle.
4. Review the returned chunks:
   - Are the most relevant chunks appearing in the top 5 results?
   - Is the score (similarity) reasonably high (above 0.5 for semantic search)?
   - Are irrelevant chunks appearing in the top results?

**Tuning tips:**
- If too many irrelevant chunks appear: increase the `score_threshold` (e.g., from 0.3 to 0.5). This filters out low-confidence matches.
- If relevant content is missing from results: lower the `score_threshold`, increase `top_k`, or check that the document was fully indexed.
- If chunks lack context: increase chunk size or overlap.
- If retrieval is imprecise: switch from full-text to semantic or hybrid mode.

---

## Finding the Knowledge Base ID for DSL YAML

When the `dsl-generator` agent builds a workflow that includes a knowledge retrieval node, it needs the knowledge base's UUID. Find it in the URL when you have the knowledge base open:

```
https://app.dify.ai/datasets/{dataset_id}/documents
```

Copy the `dataset_id` UUID from the URL. This is the value that goes into the DSL YAML:

```yaml
# Knowledge retrieval node configuration
type: knowledge-retrieval
dataset_ids:
  - "your-dataset-uuid-here"
retrieval_mode: hybrid_search
top_k: 5
score_threshold: 0.5
reranking_enable: true
```

If you are using a self-hosted Dify instance, the URL format is the same but with your instance's hostname instead of `app.dify.ai`.

---

## Adding More Documents to an Existing Knowledge Base

You can add documents to a knowledge base at any time without affecting existing indexed content:

1. Open the knowledge base.
2. Click **Add File**.
3. Upload the new document(s).
4. Choose the same chunking strategy as the original documents (for consistency).
5. Click **Save and Process**.

New documents are indexed in the background. Once indexing completes (status changes to "Available"), they are immediately searchable.

---

## Keeping the Knowledge Base Up to Date

**For website-synced knowledge bases:**
Enable **Automatic Sync** in the knowledge base settings. Dify will re-crawl the source URL on a schedule and update changed content.

**For file-based knowledge bases:**
Re-upload updated documents manually. If a document has changed significantly, delete the old version first (to avoid duplicate chunks appearing in retrieval results) and upload the new version.

**Via API:**
Use the Dify datasets API to add, update, or delete documents programmatically. This is useful for integrating knowledge base updates into a CI/CD pipeline or a content management workflow.

```bash
# Example: upload a new document via API
curl -X POST https://app.dify.ai/v1/datasets/{dataset_id}/document/create_by_file \
  -H "Authorization: Bearer {api_key}" \
  -F "file=@./updated-docs.pdf" \
  -F "data={\"indexing_technique\":\"high_quality\",\"process_rule\":{\"mode\":\"automatic\"}}"
```

---

## Permissions and Sharing

By default, a knowledge base is only accessible within the workspace where it was created. There is no cross-workspace sharing in the current version of Dify.

All apps within the same workspace can use the same knowledge base. When you link a knowledge base to a knowledge retrieval node in a DSL file, the dataset UUID must belong to the same workspace where the DSL is imported.
