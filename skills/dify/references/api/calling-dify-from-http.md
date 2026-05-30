# Calling Dify from an HTTP Node (Meta-Workflows)

This document explains how to use an HTTP node inside a Dify workflow to call Dify's own API — either to invoke another Dify app, query a knowledge base, or chain workflows together. This pattern is sometimes called a "meta-workflow" or parent-child workflow composition.

The HTTP node in Dify can call any external API. This document focuses on the Dify-to-Dify case, which is the most common meta-workflow scenario.

---

## Why Call Dify from Inside Dify?

There are several practical use cases for this pattern:

**Trigger a child workflow from a chatflow** — A chatflow handles a user conversation but needs to run a long, multi-step background process (e.g., generating a report, processing a document). The chatflow fires a workflow run via the API and either waits for the result or hands back a run ID the user can check later.

**Route to specialized sub-apps** — A master orchestration workflow classifies incoming requests and routes them to different specialized Dify apps, each optimized for a specific task (customer support, code generation, data analysis). The master uses HTTP nodes to dispatch and collect results.

**Query the knowledge base API programmatically** — Instead of using the built-in Knowledge Retrieval node, a workflow calls `POST /datasets/{id}/retrieve` to implement custom retrieval logic — for example, querying multiple datasets and merging results.

**Spawn parallel child runs** — Dify does not natively support dynamic parallelism, but a workflow can fire multiple HTTP requests to the workflow run endpoint in sequence (or via branching), passing different inputs to each, then aggregate the results.

**Poll for completion of a long-running run** — Fire a workflow with `response_mode: "blocking"` and a generous timeout. If that is insufficient, fire with a short-timeout call, store the `workflow_run_id`, and poll `GET /workflows/run/{id}` from a subsequent HTTP node.

---

## Security: Storing and Referencing the API Key

Never put a raw API key in an HTTP node's authorization field or header value. Instead:

1. Go to **Workspace Settings → Environment Variables**.
2. Add a variable named `DIFY_APP_API_KEY` with the App API Key of the target Dify app.
3. In the HTTP node, reference it as `{{#env.DIFY_APP_API_KEY#}}`.

If you are calling multiple different Dify apps from the same workflow, create one environment variable per app key, with descriptive names like `DIFY_REPORT_APP_KEY`, `DIFY_SUPPORT_APP_KEY`, etc.

---

## Example: HTTP Node That Runs a Child Workflow

The following YAML block shows a complete HTTP node configuration for calling a child workflow app in blocking mode:

```yaml
- id: "1718000000002"
  type: http-request
  data:
    title: "Run Child Workflow"
    method: POST
    url: "{{#env.DIFY_BASE_URL#}}/workflows/run"
    authorization:
      type: bearer
      config:
        token: "{{#env.DIFY_APP_API_KEY#}}"
    headers:
      - id: "h1"
        name: "Content-Type"
        value: "application/json"
    body:
      type: json
      data: |
        {
          "inputs": {"user_query": "{{#start.query#}}"},
          "response_mode": "blocking",
          "user": "workflow-caller"
        }
    timeout:
      connect: 10
      read: 60
      write: 10
    error_strategy: fail-branch
    retry_config:
      max_retries: 2
      retry_interval: 2000
```

Key points about this configuration:

- `url` points directly to the Dify API endpoint for running workflows. Replace this with the correct app's endpoint if the target is a chatflow (`/chat-messages`) or completion app (`/completion-messages`).
- `authorization.type: bearer` tells the HTTP node to add the `Authorization: Bearer ...` header automatically. The `token` value uses the env variable reference.
- `{{#start.query#}}` is a Dify DSL variable reference — it injects the value of the `query` field from the Start node into the JSON body at runtime. Adjust node ID and field name to match your workflow.
- `response_mode: "blocking"` is mandatory when consuming the response inside the same workflow. Streaming (SSE) responses cannot be parsed by the HTTP node or subsequent Code nodes.
- `timeout.read: 60` gives the child workflow up to 60 seconds to complete. Increase this for computationally intensive child workflows.
- `error_strategy: fail-branch` routes execution to the error branch if the HTTP request fails (non-2xx response or timeout). Connect this to an If-Else or End node that returns a meaningful error to the user.
- `retry_config` automatically retries the request up to 2 times with a 2-second delay between attempts on transient failures.

---

## Example: Calling a Chatflow App from Inside a Workflow

To send a message to a chatflow (e.g., to use it as a sub-agent), call the chat-messages endpoint:

```yaml
body:
  type: json
  data: |
    {
      "query": "{{#llm_node.text#}}",
      "conversation_id": "",
      "user": "parent-workflow",
      "inputs": {},
      "response_mode": "blocking"
    }
```

Set `conversation_id` to an empty string `""` to always start a fresh conversation (stateless call). To maintain multi-turn state across workflow runs, store the returned `conversation_id` and pass it back on subsequent calls.

---

## Parsing the HTTP Node Response in a Code Node

The HTTP node stores the response body as a raw string. You must use a Code node immediately after the HTTP node to parse it.

The HTTP node output variable is typically named `body` and accessed as `{{#http_node_id.body#}}`.

**Code node — extract workflow outputs:**

```python
def main(response_body: str) -> dict:
    import json
    data = json.loads(response_body)
    # For workflow/run blocking response:
    outputs = data.get("data", {}).get("outputs", {})
    return {
        "output_text": outputs.get("result", ""),
        "run_id": data.get("workflow_run_id", ""),
        "status": data.get("data", {}).get("status", "")
    }
```

**Code node — extract chat-messages blocking response:**

```python
def main(response_body: str) -> dict:
    import json
    data = json.loads(response_body)
    return {
        "answer": data.get("answer", ""),
        "conversation_id": data.get("conversation_id", ""),
        "message_id": data.get("id", "")
    }
```

Wire the Code node's input variable to `{{#http_node_id.body#}}`. The returned dict fields become variables accessible to downstream nodes as `{{#code_node_id.output_text#}}`, etc.

---

## Polling Pattern for Long-Running Workflows

If a child workflow may take longer than 60–90 seconds, use a two-phase approach:

**Phase 1 — Fire and get the run ID:**

Send the initial `POST /workflows/run` request with a short timeout. Even if the workflow is still running, you will receive the `workflow_run_id` in the response immediately (the API accepts the request synchronously before the run completes).

Extract `workflow_run_id` in a Code node.

**Phase 2 — Poll for completion:**

Add a second HTTP node that calls:

```
GET {{#env.DIFY_BASE_URL#}}/workflows/run/{{#code_node_id.run_id#}}
```

With `Authorization: Bearer {{#env.DIFY_APP_API_KEY#}}` (no body needed for GET).

Add a Code node to check `data.status`. If `status == "running"`, you could use an If-Else to loop back (limited by Dify's node graph structure) or simply accept that the result is not yet available and return a "check back later" message to the user.

---

## Checking HTTP Node Status Code

The HTTP node also outputs `status_code` (integer) and `headers` (string). You can check the status code in an If-Else node:

```
If {{#http_node_id.status_code#}} != 200 → route to error handler
```

This allows you to distinguish between a successful call, a rate limit (429), and an auth failure (401) and handle each case differently.

---

## Important Limitations and Notes

- **No streaming inside HTTP nodes** — The Dify HTTP node reads the full response body as a string. SSE streams cannot be consumed. Always use `"response_mode": "blocking"` when calling Dify from inside a workflow.
- **Response body is always a string** — Even if the API returns JSON, the HTTP node stores it as a raw string. Always parse it with a Code node before using the data.
- **Code node sandbox restrictions** — Code nodes have no network access. They can parse JSON, do string manipulation, compute HMAC, encode/decode base64, and use Python standard library modules that do not require network or filesystem access. They cannot make HTTP requests themselves.
- **Rate limits apply to internal calls** — API calls from within a workflow consume rate limit quota just like external calls. If your workflow fires many child runs, ensure your plan supports the throughput.
- **Environment variable naming** — Use descriptive names when you have multiple app keys. Document which key maps to which app in the workflow description or a comment node.
- **Timeouts are per-attempt** — With `max_retries: 2` and `read: 60`, a single node could block for up to 180 seconds in the worst case. Size timeouts carefully.
