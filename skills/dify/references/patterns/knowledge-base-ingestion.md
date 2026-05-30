# Pattern: Knowledge Base Ingestion (Writing to a KB from a Workflow)

## What this pattern is

Dify has **no native "write to knowledge base" node**. To create, update, or upsert documents and
segments in a Knowledge Base from inside a workflow, you call the **Dify Dataset API** from
`http-request` nodes and shape the request payloads in `code` nodes. This turns a workflow into an
**ingestion pipeline**: take a file or payload in, transform it, and write it into a KB so other
apps can later retrieve from it.

This is the inverse of RAG. `rag-pattern.md` covers reading *from* a KB; this pattern covers
writing *into* one. Reach for it whenever the job is "load / sync / update content **into** a
knowledge base," for example:

- A monthly report file → append each record to the right document in a KB
- A CMS or database export → push documents on a schedule
- A user-uploaded file → parse it and store it as structured segments
- A scheduled job that keeps a KB in sync with an external source

> **This is one family of designs, not a fixed recipe.** The example asset uses parent-child
> chunking and an upsert loop, but that is *an* example. Choose the chunking mode, the delimiters,
> and the topology from the actual data and requirements every time. The sections below give you
> the decision framework — use it to think, don't copy one shape blindly.

---

## Prerequisite: the KB exists first, with a deliberately chosen chunking mode

The target Knowledge Base must already exist in Dify (created in the UI, or via the
`POST /datasets` create-dataset API) **before** the ingestion workflow runs. A common pattern is to
seed it once with a small amount of representative/dummy data so the mode and field structure are
locked in, then let the workflow ingest real data into that pre-configured KB.

The KB is created with one **chunking / index mode**, and a document's `doc_form` must match it.
You must pick this deliberately — **do not default to any single mode.**

---

## Step 1 — Choose the chunking / index mode (reason about the data)

| Data shape | Mode | `doc_form` | When it's right |
| --- | --- | --- | --- |
| Flat, self-contained units: articles, manual sections, rows of a table, log/record lines, prose | **General / Standard** | `text_model` | Each chunk stands alone and is both what you match *and* what you return. The default for most content. |
| Each record has a short identity/header **plus** detailed sub-items, and you want precise matching on the detail but want the *whole record* returned as context | **Parent-child / Hierarchical** | `hierarchical_model` | The match unit and the context unit differ — e.g., per-company timelines, per-product spec sheets, sectioned policies. |
| Content is genuinely question→answer shaped (FAQ, support macros, exam banks) | **Q&A** | `qa_model` | Retrieval should match a *question* and return its *answer*. Dify can also auto-generate Q&A pairs from source text. |

**Ask yourself:**
- Is the thing the user's query should *match* the same as the thing the LLM should *read*? If
  yes → **General**. If the match unit is smaller than the useful context unit → **Parent-child**.
- Is the source naturally Q→A? → **Q&A**.
- Is the data tabular/record-oriented with one logical entity per row or group? Parent-child often
  fits (entity = parent, each row/period = child), but General is fine if each row is self-contained.

Whatever you choose, **state the reasoning** in the plan so the user can confirm it matches intent.

---

## Step 2 — Choose the delimiters (derive them from the extracted text)

This is the most important and most-overlooked decision. **There is no universal default.** After
the document is extracted to text, *inspect its structure* and pick delimiters from the boundaries
that actually exist in it.

### General mode
One `separator`, placed at the natural record/section boundary, with `max_tokens` sized to one unit.

| Source structure | `separator` | Notes |
| --- | --- | --- |
| Paragraphed prose | `\n\n` | Each paragraph = one chunk |
| One record per line / tabular rows | `\n` | Each row = one chunk; keep `max_tokens` generous |
| Records separated by an explicit marker | that marker (e.g. `\n---\n`, `###`) | Most reliable when you control the upstream text |

### Parent-child mode
Two separators. The mental model:

> **Parent separator = the boundary between the units you want RETURNED as context.**
> **Child separator = the boundary between the smallest units you want the query to MATCH.**
>
> Parent = "what the LLM should read." Child = "what the query should hit."

| Source structure | Parent `separator` | Child `subchunk_segmentation.separator` |
| --- | --- | --- |
| One entity with a multi-line timeline/detail per entity | a marker between entities, e.g. `###\n` | `\n` (one fact/line per child) |
| Markdown with `#`/`##` headed sections | the heading boundary (e.g. `\n# `) | `\n\n` (paragraphs within the section) |
| JSON/record objects rendered to text, one block per record | `\n###\n` between blocks | `\n` per field-line |
| Long article | `\n\n` (paragraph = parent) | `. ` / sentence boundary (sentence = child) |

When you control the upstream `code` node that builds the text (as in the example asset), the
clean move is to **insert your own explicit parent marker** (e.g. join records with `\n###\n`) so
the parent separator is unambiguous, and let a within-record newline be the child separator.

### Q&A mode
A separator between Q&A pairs; set `doc_language` (e.g. `English`, `Japanese`). If you provide raw
text instead of pre-formed pairs, Dify's Q&A indexing generates the pairs for you.

**Principle:** pick delimiters by looking at the post-extraction text, not by habit. If you can't
name *why* a separator matches the data's structure, you haven't chosen the right one yet.

---

## Step 3 — The KB write API surface

All calls use `Authorization: Bearer <dataset-api-key>` and target a dataset by id in the URL path.
Base URL is your instance (`https://<your-dify-domain>/v1`). See
`skills/dify/references/api/dify-api-reference.md` for the full endpoint reference and
`skills/dify/references/api/calling-dify-from-http.md` for the HTTP-node wiring.

| Operation | Method + path |
| --- | --- |
| List documents in a dataset (find/avoid duplicates) | `GET /datasets/{dataset_id}/documents?limit=100` |
| Create a document from text | `POST /datasets/{dataset_id}/document/create-by-text` |
| Create a document from an uploaded file | `POST /datasets/{dataset_id}/document/create-by-file` |
| List a document's segments (parents) — paginate on `has_more` | `GET /datasets/{dataset_id}/documents/{document_id}/segments?status=completed&page=N&limit=100` |
| Create new segment(s) | `POST /datasets/{dataset_id}/documents/{document_id}/segments` |
| Update one segment | `POST /datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}` |

### `create-by-text` payload — the `doc_form` + `process_rule` shape

The payload differs by mode. Build it in a `code` node with `json.dumps(..., ensure_ascii=False)`
and POST the resulting string. Key fields:

```jsonc
{
  "name": "<document name>",
  "text": "<the compiled text, using your chosen delimiters>",
  "indexing_technique": "high_quality",          // or "economy" (keyword-only, no embeddings)
  "doc_form": "hierarchical_model",              // text_model | hierarchical_model | qa_model
  "doc_language": "English",                     // required for qa_model
  "process_rule": {
    "mode": "hierarchical",                      // "custom" for text_model; "hierarchical" for parent-child
    "rules": {
      "pre_processing_rules": [
        {"id": "remove_extra_spaces", "enabled": true},
        {"id": "remove_urls_emails", "enabled": false}
      ],
      "parent_mode": "paragraph",                // hierarchical only: "paragraph" | "full-doc"
      "segmentation":        {"separator": "###\n", "max_tokens": 4000, "chunk_overlap": 0},  // PARENT
      "subchunk_segmentation": {"separator": "\n",  "max_tokens": 500,  "chunk_overlap": 0}   // CHILD (hierarchical only)
    }
  },
  "retrieval_model": {
    "search_method": "hybrid_search",
    "reranking_enable": false,
    "top_k": 3,
    "score_threshold_enabled": false,
    "weights": {"weight_type": "keyword_first"}
  },
  "embedding_model": "<embedding-model-name>",
  "embedding_model_provider": "<provider>"
}
```

For **General** mode: `doc_form: text_model`, `process_rule.mode: custom`, and a single
`segmentation` block (no `subchunk_segmentation`, no `parent_mode`). For **Q&A**: `doc_form:
qa_model` and set `doc_language`.

### Segment create / update payloads

```jsonc
// Create parent segment(s) — POST .../segments
{"segments": [{"content": "<parent text>", "keywords": ["<optional keyword>"]}]}

// Update one parent segment — POST .../segments/{segment_id}
{"segment": {"content": "<new parent text>"}}
```

Updating a parent segment's `content` in hierarchical mode triggers re-generation of its child
chunks on re-index.

---

## Step 4 — The idempotent upsert topology

The example asset implements a **safe re-runnable** ingestion: running the same file twice must not
duplicate data. The shape:

```text
start (file/payload)
  → code  (validate input: format, naming, required fields)
  → if-else (valid?) ──no──> end (return error)
  → document-extractor (file → text)        [only when input is a file]
  → code  (parse text → structured records, choosing/inserting delimiters)
  → http  GET documents   (does the target document already exist?)
  → if-else (exists? / error?)
       ├─ error           → end (return error)
       ├─ does NOT exist  → code (build create-by-text payload) → http POST create-by-text → end
       └─ exists          → http GET segments (paginate) 
                            → code "traffic cop": diff incoming records vs existing segments
                                 • already present (same period/key) → skip   (idempotency)
                                 • present but stale                 → update list
                                 • new                               → create list
                            → iteration over update list → http POST .../segments/{id}
                            → iteration over create list → http POST .../segments
                            → end
```

Notes:
- **Validate before writing.** A leading `code` + `if-else` guard prevents malformed input from
  polluting the KB.
- **Check existence first** (`GET /documents`) to decide create-vs-update — never blind-create.
- **Diff against existing segments** so re-ingesting the same period is a no-op (the "traffic cop"
  code node). This is what makes the pipeline idempotent.
- **Paginate** segment reads on `has_more` — Dify caps `limit` at 100.
- Use `iteration` nodes to fan the per-record create/update calls; give each HTTP node a
  `retry_config` since network writes can fail transiently.

---

## Step 5 — Environment variables & auth

KB ingestion needs, at minimum, two secrets plus the base URL. Declare them as
`environment_variables` (type `secret`) in the workflow so nothing is hardcoded:

| Env var (suggested) | Holds | Used in |
| --- | --- | --- |
| `KB_API` | the **dataset API key** (`dataset-...`) | `Authorization: Bearer {{#env.KB_API#}}` header, and passed into `code` nodes as a variable |
| `DB_ID` | the **dataset (KB) UUID** | the URL path: `/datasets/{{#env.DB_ID#}}/...` |
| `DIFY_BASE_URL` *(optional but recommended)* | `https://<your-dify-domain>/v1` | HTTP node URL prefix; avoids hardcoding the domain inside `code` nodes |

In `code` nodes the secrets are passed as input variables (`value_selector: [env, KB_API]`,
`value_type: secret`). In `http-request` nodes they are referenced inline as `{{#env.KB_API#}}` /
`{{#env.DB_ID#}}`. Never embed the literal key or id — see the project rule on `{{env.*}}`.

---

## Step 6 — Building and delivering the flow (env vars + SETUP.md)

When `dsl-generator` builds an ingestion flow:

1. **Declare the env vars with placeholder values** (`value: ""`, `value_type: secret`) so Dify
   prompts for them on import — never bake in real keys or ids.
2. **The SETUP.md must explain how to obtain and wire each value**, because these are not
   guessable. Include steps like:
   - **Dataset API key** — in Dify, open the target Knowledge Base → **API Access** (or
     **Settings → API Keys** for datasets) → create/copy a key (starts with `dataset-`). Paste it
     into the `KB_API` environment variable.
   - **Dataset (KB) ID** — open the Knowledge Base; the id is in the URL
     `.../datasets/<COPY THIS>/documents`. Paste it into `DB_ID`.
   - **Base URL** — confirm your instance base URL (`https://<your-dify-domain>/v1`); set
     `DIFY_BASE_URL` and/or replace the placeholder domain in any `code` node that builds a URL.
   - **Chunking mode must already match** — the document `doc_form` the workflow sends must match
     how the KB was created; note the chosen mode and that a mismatch causes ingestion to fail.
3. **Re-run safety** — tell the user the flow is idempotent (safe to re-run the same file) only if
   the diff/skip logic is present; if it isn't, warn that re-running may duplicate data.

---

## Reference asset

`skills/dify/assets/workflows/knowledge-base-ingestion.yml` — a real, sanitized Dify export that
ingests a monthly report into a parent-child KB (validate → parse → check existence → create or
upsert via segment APIs, with two `iteration` fan-outs). **Use it for the exact API call and
payload syntax** (`create-by-text` body, segment create/update bodies, pagination loop,
hierarchical `process_rule`). It is *one* worked example — the chunking mode, delimiters, and
topology for a new flow must still be chosen from that flow's own data per Steps 1–4.

## Related references

- `skills/dify/references/features/knowledge-base.md` — KB concepts, chunking strategies, the
  Dataset write-API section
- `skills/dify/references/patterns/rag-pattern.md` — the read side (retrieval) of the same KB
- `skills/dify/references/api/dify-api-reference.md` — full Dataset API endpoint reference
- `skills/dify/references/api/calling-dify-from-http.md` — HTTP-node wiring for Dify's own API
- `skills/dify/references/nodes/iteration.md` — fanning per-record create/update calls
