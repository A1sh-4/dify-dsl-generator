# Dify API Reference

This document covers the Dify REST API surface — base URL, authentication, endpoint categories, request/response formats, error codes, and rate limiting. Use this as a reference when configuring HTTP nodes that call Dify from external systems, or when building tooling that manages Dify apps programmatically.

---

## Base URL and Authentication

```
Base URL:       https://api.dify.ai/v1
Auth header:    Authorization: Bearer {APP_API_KEY}
Content-Type:   application/json
```

All requests require an `Authorization` header carrying a Bearer token. The token type depends on what you are doing — see **API Key Types** below.

### API Key Types

Dify has two distinct API key types with different scopes:

| Type | Where to find it | Used for |
|---|---|---|
| **App API Key** | App settings → API Access page | Chat, workflow run, completion, file upload endpoints |
| **Workspace API Key** | Workspace settings → API Keys | Dataset / knowledge base management endpoints |

Using the wrong key type results in a `401 Unauthorized` error. Never embed either key directly in YAML or code. All keys must reference environment variables using `{{#env.VARIABLE_NAME#}}` syntax.

---

## Endpoint Categories

### 1. Chat Messages (chatflow apps)

These endpoints apply to apps of type `chatflow`. They manage multi-turn conversations.

**`POST /chat-messages`** — Send a message to a chatflow and receive a response.

Request body parameters:
- `query` (string, required) — The user's message text.
- `conversation_id` (string, optional) — Omit to start a new conversation. Pass an existing ID to continue.
- `user` (string, required) — A stable identifier for the end user. Used for conversation isolation and rate limiting.
- `inputs` (object, optional) — Key-value pairs matching the app's declared input variables.
- `response_mode` (string, required) — Either `"blocking"` (wait for full response) or `"streaming"` (SSE stream).
- `files` (array, optional) — List of `{type, transfer_method, url | upload_file_id}` objects for vision or document inputs.

**`GET /messages`** — List messages in a conversation.

Query parameters: `conversation_id`, `user`, `limit`, `first_id` (cursor for pagination).

**`GET /conversations`** — List all conversations for a user.

Query parameters: `user`, `limit`, `last_id` (cursor).

**`DELETE /conversations/{conversation_id}`** — Permanently delete a conversation and its messages.

Query parameters: `user` (required to scope the deletion).

**`POST /messages/{message_id}/feedbacks`** — Submit thumbs-up or thumbs-down feedback on a message.

Body: `{ "rating": "like" | "dislike" | null, "user": "..." }`

---

### 2. Workflow (workflow apps)

These endpoints apply to apps of type `workflow`. Workflows are stateless — there is no conversation history.

**`POST /workflows/run`** — Execute a workflow run.

Request body parameters:
- `inputs` (object, required) — Key-value pairs matching the Start node's variable definitions exactly.
- `response_mode` (string, required) — `"blocking"` or `"streaming"`.
- `user` (string, required) — Caller identifier.

**`GET /workflows/run/{workflow_run_id}`** — Retrieve the status and final outputs of a completed (or in-progress) workflow run.

Returns: `status` (`running`, `succeeded`, `failed`, `stopped`), `outputs` (dict), `error` (if failed), `elapsed_time`, `total_tokens`.

**`GET /workflows/run/{workflow_run_id}/steps`** — Get detailed per-node execution logs for a run. Useful for debugging failed runs.

---

### 3. Files

**`POST /files/upload`** — Upload a file using `multipart/form-data`.

Form fields: `file` (the binary), `user` (string).

Returns a JSON object containing `id` (the `file_id`). Pass this `file_id` in the `files` array of subsequent `/chat-messages` or `/workflows/run` requests using `transfer_method: "local_file"`.

---

### 4. Knowledge Base / Dataset (workspace API key required)

These endpoints manage datasets and documents. They use the **Workspace API Key**, not the App API Key.

**`POST /datasets`** — Create a new dataset (knowledge base).

Body: `{ "name": "...", "permission": "only_me" | "all_team_members" }`

**`POST /datasets/{dataset_id}/document/create_by_text`** — Add a plain-text document to a dataset.

Body: `{ "name": "...", "text": "...", "indexing_technique": "high_quality" | "economy", "process_rule": { "mode": "automatic" } }`

**`POST /datasets/{dataset_id}/document/create_by_file`** — Upload a file (PDF, DOCX, TXT, etc.) to a dataset using `multipart/form-data`.

**`POST /datasets/{dataset_id}/retrieve`** — Test retrieval against a dataset. Send a query and get back matched document chunks.

Body: `{ "query": "...", "retrieval_model": { "search_method": "semantic_search", "top_k": 5, "score_threshold": 0.5 } }`

**`GET /datasets/{dataset_id}/documents`** — List all documents in a dataset with their indexing status.

---

### 5. Text Generation / Completion (completion apps)

**`POST /completion-messages`** — Single-turn text generation. No conversation history is maintained.

Body: `{ "inputs": {}, "query": "...", "response_mode": "blocking" | "streaming", "user": "..." }`

---

### 6. Speech

**`POST /audio-to-text`** — Transcribe audio to text. Send as `multipart/form-data` with a `file` field containing an audio file (MP3, WAV, M4A, etc.).

Returns: `{ "text": "transcribed content" }`

**`POST /text-to-audio`** — Convert text to speech audio.

Body: `{ "message_id": "..." }` or `{ "text": "...", "voice": "...", "streaming": false }`

---

### 7. App Info and Metadata

**`GET /info`** — Returns app metadata: `name`, `description`, `tags`.

**`GET /parameters`** — Returns the app's declared input variables (used to know which `inputs` keys are expected by `/chat-messages` or `/workflows/run`). Also includes opening statement and suggested questions.

**`GET /meta`** — Returns tool icons and metadata for tools configured in the app.

---

## Response Formats

### Blocking Mode Response (`response_mode: "blocking"`)

```json
{
  "event": "message",
  "task_id": "abc123",
  "id": "msg_xyz",
  "answer": "The response text",
  "conversation_id": "conv_abc",
  "created_at": 1718000000
}
```

For workflow runs in blocking mode, the response is wrapped under `data`:
```json
{
  "workflow_run_id": "run_abc",
  "task_id": "task_xyz",
  "data": {
    "id": "run_abc",
    "status": "succeeded",
    "outputs": { "result": "..." },
    "elapsed_time": 3.21,
    "total_tokens": 512
  }
}
```

### Streaming Mode Response (SSE — `response_mode: "streaming"`)

Response uses `Content-Type: text/event-stream`. Each line is a Server-Sent Event:

```
data: {"event": "message", "task_id": "...", "answer": "Hello"}
data: {"event": "message", "task_id": "...", "answer": " world"}
data: {"event": "message_end", "task_id": "...", "metadata": {"usage": {"total_tokens": 45}}}
```

For workflows, events include `workflow_started`, `node_started`, `node_finished`, `workflow_finished`.

The HTTP node inside Dify **cannot consume streaming responses** — always use `"blocking"` when one Dify workflow calls another.

---

## Error Codes

| Status Code | Meaning |
|---|---|
| `400` | Bad request — invalid or missing parameters. Check `code` and `message` fields in the response body. |
| `401` | Unauthorized — invalid or missing API key, or wrong key type. |
| `404` | Not found — wrong app ID, endpoint path, or resource does not exist. |
| `429` | Rate limit exceeded — slow down requests. Check rate limit headers. |
| `500` | Internal server error — Dify-side issue. Retry with backoff. |

---

## Rate Limiting

Rate limit information is returned in response headers:

| Header | Description |
|---|---|
| `X-RateLimit-Limit` | Maximum requests allowed per window |
| `X-RateLimit-Remaining` | Requests remaining in the current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |

- **Dify Cloud**: rate limits vary by subscription plan. Check your plan in workspace settings.
- **Self-hosted**: limits are configurable in the server environment. Default may be very high or unlimited.

When a `429` is returned, wait until `X-RateLimit-Reset` before retrying, or implement exponential backoff. The HTTP node's built-in `retry_config` handles this automatically for transient errors.

---

## Security Notes

- Never hardcode API keys in DSL YAML, code nodes, or HTTP node configurations.
- Store keys as Dify environment variables (workspace settings → Environment Variables).
- Reference them in HTTP nodes using `{{#env.VARIABLE_NAME#}}` in authorization config or header values.
- App API Keys are scoped to a single app — compromise of one key does not expose other apps.
- Rotate keys immediately if they are accidentally exposed in logs or version control.
