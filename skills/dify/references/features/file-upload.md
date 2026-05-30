# File Upload

Dify supports file upload in chatflows and workflows, enabling users to submit documents and images for processing. Files can be analyzed by vision-capable LLMs, extracted by document-extractor nodes, or used in list-processing patterns.

---

## Enabling File Upload in DSL

File upload configuration lives in the `features.file_upload` block of the DSL YAML. This block controls which file types are accepted, how many files are allowed, and how they are transferred.

### Image Upload Configuration

```yaml
features:
  file_upload:
    image:
      enabled: true
      number_limits: 5
      transfer_methods:
        - local_file
        - remote_url
```

Fields:
- `enabled` (boolean) — set `true` to allow image uploads.
- `number_limits` (integer) — maximum number of image files per submission. Range: 1–10.
- `transfer_methods` (array) — controls how images reach Dify:
  - `local_file` — user uploads directly from their device.
  - `remote_url` — user provides an HTTPS URL to an image.

For the **minimum image upload config** (local upload only, 3 images):
```yaml
features:
  file_upload:
    image:
      enabled: true
      number_limits: 3
      transfer_methods:
        - local_file
```

For **disabled image upload** (default state):
```yaml
features:
  file_upload:
    image:
      enabled: false
      number_limits: 3
      transfer_methods:
        - local_file
        - remote_url
```

---

## Supported File Types

### Image Types (for Vision LLM)
The following image formats are supported for vision processing:
- `jpg` / `jpeg`
- `png`
- `gif` (static frame only for most vision models)
- `webp`
- `svg`

### Document Types (for Text Extraction)
The following document formats are supported via the document-extractor node:
- `pdf` — PDF documents (text layer extracted; scanned PDFs may require OCR)
- `docx` / `doc` — Microsoft Word documents
- `xls` / `xlsx` — Microsoft Excel spreadsheets
- `ppt` / `pptx` — Microsoft PowerPoint presentations
- `txt` — plain text files
- `md` — Markdown files
- `html` — HTML files (tags stripped, text content extracted)
- `csv` — comma-separated values

---

## File Size Limits

- **Per file:** 15 MB maximum by default.
- **Total per submission:** 100 MB maximum across all uploaded files.
- Self-hosted Dify instances can adjust these limits in environment configuration (`FILE_UPLOAD_SIZE_LIMIT`).

---

## How Uploaded Files Appear as Variables

### Start Node File Variables

When file upload is enabled, uploaded files are available in the workflow as a variable on the Start node.

**Correct variable reference:**
```
{{#start.files#}}
```

This is an array of file objects. Each file object contains:
- `type` — MIME type (e.g., `image/png`, `application/pdf`).
- `url` — temporary access URL for the file.
- `name` — original filename.
- `size` — file size in bytes.
- `extension` — file extension (e.g., `pdf`, `jpg`).
- `transfer_method` — `local_file` or `remote_url`.

### `{{#start.sys.files#}}` vs `{{#start.files#}}`

These two variables are distinct:

- `{{#start.files#}}` — **the correct variable** for user-uploaded files in a workflow with file upload enabled via the `features.file_upload` block.
- `{{#start.sys.files#}}` — the system-provided files variable, used in some internal contexts. In most workflow designs, use `{{#start.files#}}`.

**Use `{{#start.files#}}`** when referencing uploaded files in node variable selectors.

---

## Passing Files to an LLM Node for Vision

To analyze images with a vision-capable LLM (GPT-4o, Claude 3.x, Gemini Vision, etc.):

1. **Enable vision** in the LLM node configuration (`vision.enabled: true`).
2. **Configure the vision input** to reference the uploaded file variable.

In the LLM node DSL:
```yaml
vision:
  enabled: true
  configs:
    detail: high
    variable_selector:
      - start
      - files
```

The LLM node receives the image alongside the text prompt and generates a response that incorporates visual analysis.

**Requirements:**
- The selected LLM model must support vision (check model capabilities in workspace model settings).
- The file must be an image type (see supported image types above).
- If the user uploads multiple images, the LLM node can process all of them in a single call (up to model limits).

---

## Passing Files to Doc-Extractor Node

For text extraction from documents (PDF, DOCX, etc.), use the **document-extractor** node:

```yaml
- data:
    type: document-extractor
    title: Extract Document Text
    variable_selector:
      - start
      - files
  id: doc_extractor_1
  type: document-extractor
```

**Output:** `{{#doc_extractor_1.text#}}` — the extracted plain text content of the document.

This text can be passed to an LLM node for summarization, analysis, or Q&A.

---

## List File Processing Pattern

When users upload multiple files and each must be processed individually, use this pattern:

```
Start Node (file-list input)
    ↓
List Operator Node (filter by type)
    ↓
Iteration Node
    ↓
  Doc-Extractor Node (extracts text from each file)
    ↓
  LLM Node (processes each file's text)
    ↓
End / Answer Node (aggregated results)
```

**Step-by-step DSL pattern:**

1. **Start node** — `files` input of type `array[file]`.
2. **List Operator node** — filter `{{#start.files#}}` by `extension` to separate PDFs from images if needed.
3. **Iteration node** — iterate over the filtered file list. Inside the iteration, the current file is accessed as `{{item}}` (no `{{# #}}` delimiters — iteration item variable uses plain `{{item}}` syntax).
4. **Doc-Extractor node** — inside the iteration, extract text from `{{item}}`.
5. **LLM node** — inside the iteration, process `{{#doc_extractor.text#}}`.
6. **Collect results** using a variable aggregator or string template after the iteration completes.

**Critical syntax note:** Inside iteration containers, the item variable is `{{item}}`, not `{{#item#}}`. This is a unique syntax exception — do not wrap it in `{{# #}}` delimiters.

---

## Number of Files Configuration

Configure how many files a user can upload per submission:

```yaml
features:
  file_upload:
    image:
      enabled: true
      number_limits: 5   # 1 to 10, inclusive
```

If a user attempts to upload more than `number_limits` files, the web app interface prevents the upload before submission.

---

## Transfer Methods

### `local_file`
User uploads a file from their device. The file is uploaded to Dify's storage and a temporary URL is generated. This URL is included in the file object and is accessible during the workflow run.

### `remote_url`
User provides an HTTPS URL pointing to a file. Dify fetches the file from the URL and processes it. Useful for workflows where files are already hosted (e.g., attachments from a CRM, files in an S3 bucket with a public/signed URL).

Configure which transfer methods are allowed:
```yaml
transfer_methods:
  - local_file    # allow direct upload
  - remote_url    # allow URL input
```

Both can be enabled simultaneously to give users the choice.

---

## Related Documentation

- See `skills/dify/references/nodes/document-extractor.md` for the document-extractor node full configuration reference.
- See `skills/dify/references/nodes/list-operator.md` for filtering and sorting file arrays before iteration.
- See `skills/dify/references/nodes/iteration.md` for the iteration node, including the `{{item}}` variable syntax.
- See `skills/dify/references/features/chatflow-features.md` for the complete `features` block DSL reference.
