# Trigger: Webhook Node

## Overview

The Webhook Trigger node starts a Dify Workflow automatically when an external system sends an HTTP request to a Dify-generated URL. Instead of a human typing a message or clicking a button, the trigger is a machine-to-machine call — a GitHub push event, a Stripe payment confirmation, a form submission from your website, or any other programmatic notification.

The node extracts specific fields from the incoming request (from the body, query string, or headers) and makes them available as variables for the rest of the workflow to use. This makes it straightforward to build event-driven automations that react to real-world activity without any manual intervention.

**Important**: Webhook triggers are available in **Workflows only**. They cannot be used in Chatflows.

## When to Use

Use a Webhook Trigger whenever an external system needs to hand off data to a Dify workflow in real time:

- **GitHub webhooks**: React to push events, pull request openings, issue comments, or CI status changes. Parse the repository name, branch, author, and commit message directly from the GitHub payload.
- **Stripe payment webhooks**: Trigger fulfilment workflows when a `payment_intent.succeeded` event arrives. Extract the customer ID, amount, and currency from the Stripe event body.
- **Form submission notifications**: Connect a Typeform, HubSpot, or custom web form directly to a Dify workflow. Each submission triggers a run with the respondent's answers as variables.
- **Third-party SaaS events**: Zapier, Make (Integromat), and similar platforms can POST to a Dify webhook URL, bridging thousands of SaaS tools to your Dify automations.
- **Internal microservice events**: When a service in your infrastructure emits an event (job completed, error detected, threshold crossed), it can call the Dify webhook to kick off a remediation or notification workflow.
- **IoT and sensor data**: Edge devices or gateways can POST readings to a Dify workflow URL for real-time processing and alerting.

Anywhere you would previously have written a small serverless function to handle an incoming HTTP event, a Dify webhook workflow is a strong alternative — with the added benefit of LLM-powered processing built in.

## Limitations

- **Workflow type only**: Webhook triggers cannot be added to Chatflows. The node type does not appear in the Chatflow node palette.
- **No standalone web app**: A workflow with a webhook trigger cannot be published as a standalone web application (the one-click Share URL feature). It is accessed exclusively via the webhook URL.
- **No MCP server publishing**: Webhook-triggered workflows cannot be exposed as MCP server tools. MCP publishing is reserved for workflows with a Start node.
- **No manual test runs from the UI**: Because the trigger depends on an incoming HTTP request, you cannot click "Run" in the editor the same way you can with a Start-node workflow. You need to send a test HTTP request (e.g., via curl or Postman) to trigger a run during development.

## The Webhook URL

When you save a workflow containing a Webhook Trigger node, Dify generates a unique, stable URL for that workflow:

```
https://<your-dify-domain>/webhooks/{unique_id}
```

For this project's instance: `https://app-human04s.tsunagi.ai/webhooks/{unique_id}`

The `{unique_id}` is a UUID assigned to the workflow. This URL is displayed in the node's configuration panel in the Dify editor. Copy it and paste it into the external system's webhook settings.

The URL does not change unless you delete and recreate the node. This means you can configure the external system once and it will continue to work across workflow edits and republications.

## YAML Configuration

```yaml
- data:
    desc: ''
    selected: false
    title: Webhook Trigger
    type: trigger-webhook
    method: POST           # HTTP method to accept: GET, POST, PUT, PATCH
    variables:             # parameters to extract from the incoming request
      - label: 'Event Type'
        type: string
        variable: event_type
        source: body       # where to extract from: body, query, header
        path: 'event'      # JSON path within the source
        required: true
      - label: 'Repository'
        type: string
        variable: repo_name
        source: body
        path: 'repository.full_name'
        required: false
      - label: 'Signature'
        type: string
        variable: signature
        source: header
        path: 'X-Hub-Signature-256'
        required: true
      - label: 'Ref'
        type: string
        variable: git_ref
        source: query
        path: 'ref'
        required: false
  height: 54
  id: '1732001000001'
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
```

### Top-level fields

| Field | Type | Description |
|---|---|---|
| `type` | string | Always `trigger-webhook` |
| `method` | string | HTTP method to accept: `GET`, `POST`, `PUT`, `PATCH` |
| `variables` | array | List of parameter extraction definitions |

### Variable definition fields

| Field | Type | Description |
|---|---|---|
| `variable` | string | Identifier used to reference this value downstream |
| `label` | string | Human-readable display name |
| `type` | string | Data type: `string`, `number`, `boolean` |
| `source` | string | Where to extract the value: `body`, `query`, `header` |
| `path` | string | Key or dot-notation path within the source |
| `required` | boolean | Whether the workflow should fail if this field is missing |

## Parameter Sources

Dify can extract values from three parts of the incoming HTTP request:

### body

Extracts from the request body. The body is parsed as JSON. Use dot notation for nested fields:

```yaml
source: body
path: 'repository.full_name'   # extracts {"repository": {"full_name": "..."}}
```

Form-encoded bodies are also supported; in that case `path` is the form field name.

### query

Extracts from URL query parameters:

```yaml
source: query
path: 'page'    # extracts ?page=2 from the URL
```

### header

Extracts from HTTP request headers. Header names are case-insensitive:

```yaml
source: header
path: 'X-Hub-Signature-256'   # extracts the GitHub HMAC signature header
```

Use `header` extraction to capture authentication tokens, API keys, or signature headers that external systems send alongside event payloads.

## Security: Signature Verification

Accepting arbitrary HTTP POST requests without validation is a security risk — anyone who discovers your webhook URL could trigger your workflow with fake data. Most webhook providers (GitHub, Stripe, Twilio, etc.) sign their requests with an HMAC-SHA256 signature so the receiver can verify authenticity.

### Verification Pattern

1. Extract the signature header (e.g., `X-Hub-Signature-256`) as a variable on the Webhook Trigger node.
2. Extract the raw request body as another variable.
3. Pass both to a downstream Code node.
4. In the Code node, compute HMAC-SHA256 of the raw body using your shared secret.
5. Compare the computed signature to the received one. If they differ, raise an error or route to a rejection branch.

### Python Example (Code Node)

```python
import hmac
import hashlib

def main(signature_header: str, raw_body: str, webhook_secret: str) -> dict:
    """
    Verify a GitHub-style HMAC-SHA256 webhook signature.
    
    Args:
        signature_header: Value of X-Hub-Signature-256 header, e.g. "sha256=abc123..."
        raw_body: The raw request body string
        webhook_secret: The shared secret configured in GitHub and stored in Dify env vars
    
    Returns:
        dict with 'verified' boolean
    """
    if not signature_header.startswith("sha256="):
        return {"verified": False, "error": "Missing sha256= prefix"}
    
    received_sig = signature_header[len("sha256="):]
    
    computed_sig = hmac.new(
        key=webhook_secret.encode("utf-8"),
        msg=raw_body.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Use compare_digest to prevent timing attacks
    is_valid = hmac.compare_digest(received_sig, computed_sig)
    
    return {
        "verified": is_valid,
        "error": "" if is_valid else "Signature mismatch — request rejected"
    }
```

Store the `webhook_secret` as a Dify Environment Variable (accessible via `{{#env.webhook_secret#}}`) rather than hard-coding it in the workflow.

### Post-verification Routing

Connect the Code node's output to an If-Else node that checks `{{#code_node_id.verified#}}`:
- **True branch**: Continue to the main workflow logic.
- **False branch**: Route to an End node that returns a 401-equivalent error response.

## Custom Response Configuration

By default, Dify responds to the webhook caller with `200 OK` and an empty body as soon as the workflow starts executing (not after it finishes). You can customise this in the node settings:

| Setting | Options | Default |
|---|---|---|
| Status code | Any 2xx or 3xx integer (200–399) | `200` |
| Response body | JSON object or plain text string | Empty |
| Response headers | Key-value pairs | None |

Note that the response is sent synchronously at workflow start, not at completion. If your caller needs the workflow's output, consider using an HTTP Request node at the end of the workflow to POST results back to the caller's callback URL.

## Output Variables

Every variable declared in the `variables` array is available downstream using the standard reference syntax:

```
{{#<node_id>.<variable_name>#}}
```

For example, if the node's `id` is `'1732001000001'` and you declared a variable named `event_type`, reference it as:

```
{{#1732001000001.event_type#}}
```

These references work in LLM prompt templates, Code node inputs, If-Else conditions, HTTP Request body templates, and all other node types that accept variable references.

## Example: GitHub Push Workflow

A complete GitHub push event handler would have this structure:

1. **Webhook Trigger**: Extracts `event_type` (body: `event`), `repo_name` (body: `repository.full_name`), `commit_message` (body: `head_commit.message`), and `signature` (header: `X-Hub-Signature-256`).
2. **Code node**: Verifies the HMAC signature.
3. **If-Else node**: Routes based on `verified` output.
4. **LLM node** (true branch): Summarises the commit and generates a Slack notification message.
5. **HTTP Request node**: POSTs the summary to a Slack incoming webhook URL.
6. **End node** (false branch): Returns a rejection message.
