# Doc Extractor Node

## Overview

The doc-extractor node converts uploaded documents into plain text. It accepts a file variable — either uploaded by the user through the start node or received from an iteration over a file list — and returns the full extracted text content as a single string. This text can then be passed to an LLM for summarization, analysis, classification, or any other language task.

Supported file formats include PDF, DOCX, TXT, MD (Markdown), HTML, CSV, and XLSX. The node handles parsing, character encoding, and basic structure extraction automatically.

## When to Use

Use doc-extractor when:

- A user uploads a single document and you need to read its content
- You are iterating over a list of files and processing each one inside an iteration node
- You need the full document text before passing it to an LLM (as opposed to searching for relevant chunks)
- You are building a document summarization, review, or analysis workflow

### Doc-Extractor vs Knowledge Retrieval

This is an important architectural decision:

| Scenario | Use |
|----------|-----|
| User uploads one document to analyze or summarize | doc-extractor |
| Searching across many pre-indexed documents | knowledge-retrieval |
| Processing a batch of documents in a loop | doc-extractor inside iteration |
| RAG over a persistent knowledge base | knowledge-retrieval |

Doc-extractor processes the document at runtime, in the workflow. Knowledge-retrieval queries a pre-built index. Use doc-extractor when the document is dynamic (uploaded by the user); use knowledge-retrieval when the documents are static and pre-loaded into a knowledge base.

## Input

| Field | Type | Description |
|-------|------|-------------|
| `variable` | file | A file-type variable from an upstream node |

The input must be a file variable, not a string path. Typically this comes from `{{#start.file_variable_name#}}` when the user uploads a file through the application interface, or from `{{item}}` when iterating over a file array.

## Output Variables

| Variable | Type | Description |
|----------|------|-------------|
| `text` | string | The full plain-text content extracted from the document |

Reference this downstream as `{{#doc_extractor_node_id.text#}}`.

## Limitation: No OCR for Scanned PDFs

The doc-extractor node cannot perform optical character recognition (OCR). If a PDF consists entirely of scanned images (a common case with older documents or digitized paper), the node will return an empty string or minimal content. Only PDFs with embedded text layers can be read.

If your workflow needs to handle scanned documents, you must route the file through an external OCR tool node (such as a Firecrawl or custom API call) before passing the result to your LLM.

## Complete YAML Example

```yaml
- id: extract_document
  type: document-extractor
  data:
    title: Extract Document Text
    variable_selector:
      - start
      - uploaded_file
```

The node does not require additional configuration beyond the source variable. All parsing is handled internally.

## Pattern: File Upload → Doc-Extractor → LLM

This is the standard document analysis pipeline:

```yaml
nodes:
  - id: start
    type: start
    data:
      variables:
        - variable: uploaded_file
          type: file
          label: Upload a document
          required: true

  - id: extract_document
    type: document-extractor
    data:
      title: Extract Document Text
      variable_selector:
        - start
        - uploaded_file

  - id: summarize
    type: llm
    data:
      title: Summarize Document
      model:
        provider: openai
        name: gpt-4o
        mode: chat
      prompt_template:
        - role: system
          text: You are a document analyst. Provide a clear, structured summary.
        - role: user
          text: |
            Please summarize the following document:

            {{#extract_document.text#}}

edges:
  - source: start
    target: extract_document
  - source: extract_document
    target: summarize
```

## Pattern: Iterate Over Multiple Files

When a user uploads multiple files, combine iteration with doc-extractor to process each one:

```yaml
- id: process_each_file
  type: iteration
  data:
    title: Process Each Uploaded File
    iterator_selector:
      - start
      - file_list
    output_selector:
      - extract_each
      - text
    nodes:
      - id: extract_each
        type: document-extractor
        data:
          variable_selector:
            - iteration_start
            - item
```

## Common Mistakes

1. **Passing a string path instead of a file variable.** The node requires a proper file-type variable. You cannot pass a URL string or filename string — it must be an actual file variable from the start node or iteration context.

2. **Expecting OCR output from scanned PDFs.** If users may upload image-only PDFs, add a check or inform users in the app's UI that scanned documents are not supported.

3. **Passing the entire extracted text to a model with a small context window.** Large documents can produce very long text strings. Consider using the list-operator or template-transform to slice or truncate before passing to an LLM, or use knowledge-retrieval with chunking instead.

4. **Using doc-extractor when you need semantic search.** If you need to find relevant sections within a large document rather than process it all, index it in a knowledge base and use knowledge-retrieval instead.

5. **Not handling empty output.** If the file format is unsupported or the document is image-only, `text` will be empty. Add an if-else node downstream to check for empty output and handle the failure gracefully.
