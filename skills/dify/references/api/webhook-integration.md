# Webhook Integration in Dify Workflows

This document explains how to receive webhooks from external systems — GitHub, Stripe, Slack, form builders, and any other HTTP-capable service — and process them inside a Dify workflow using the Trigger-Webhook node.

---

## Overview

The general flow is:

```
External system → POST to Dify webhook URL → Trigger-Webhook node fires → Workflow executes
```

A webhook integration turns Dify into a reactive processing engine: instead of a user typing a message, an external event (a GitHub push, a Stripe payment, a form submission) triggers the workflow automatically.

The Trigger-Webhook node replaces the Start node. It receives the incoming HTTP request, extracts the body and headers, and makes them available as variables to all downstream nodes.

---

## Getting the Webhook URL

1. Create a new **Workflow** app in Dify (not a chatflow — see Limitations section).
2. In the canvas, delete the default Start node and add a **Trigger-Webhook** node instead. Or select "Trigger-Webhook" as the app type when creating.
3. Open the Trigger-Webhook node configuration panel.
4. Dify generates a unique webhook URL in this format:

```
https://<your-dify-domain>/v1/workflows/webhook/{workflow_id}/{webhook_path}
```

For this project's instance: `https://app-human04s.tsunagi.ai/v1/workflows/webhook/{workflow_id}/{webhook_path}`

5. Copy this URL and paste it into your external system's webhook configuration screen (GitHub repo settings, Stripe dashboard, Typeform integrations, etc.).

The URL is stable for the lifetime of the workflow. If you need to rotate it (for security reasons), delete the Trigger-Webhook node and add a new one — Dify will generate a new path.

---

## Trigger-Webhook Node Configuration

Inside the node's settings panel you can configure:

- **Method** — `GET` or `POST`. Nearly all webhooks from production systems use `POST`. Use `GET` only for simple ping/health-check integrations or query-parameter-based triggers.
- **Content-Type** — `application/json` (most common) or `application/x-www-form-urlencoded` (some legacy or form-based systems).
- **Custom response body** — Some webhook providers require the receiving endpoint to return a specific body (e.g., a challenge string for Slack's Event API verification handshake). Configure this in the node settings.
- **Variable extraction** — Dify automatically exposes the raw request body, selected headers, and query parameters as node output variables.

---

## What External Systems Send

A typical webhook POST from a system like GitHub looks like this:

```
POST https://<your-dify-domain>/v1/workflows/webhook/{id}/{path}
Content-Type: application/json
X-Hub-Signature-256: sha256=abc123...
X-GitHub-Event: push

{
  "event": "push",
  "repository": {
    "name": "my-repo",
    "full_name": "org/my-repo"
  },
  "head_commit": {
    "message": "Fix critical bug in auth module",
    "author": { "name": "Jane Dev", "email": "jane@example.com" }
  },
  "pusher": { "name": "jane" }
}
```

Dify receives this request and passes the body and relevant headers to the Trigger-Webhook node's output variables.

---

## Accessing Webhook Data in Downstream Nodes

The raw request body is available in downstream nodes as a variable reference pointing to the Trigger-Webhook node's output. Assuming the node ID is `webhook_node_id`:

```
{{#webhook_node_id.body#}}        — The raw request body as a JSON string
{{#webhook_node_id.headers#}}     — Selected request headers (format varies by Dify version)
{{#webhook_node_id.query#}}       — URL query parameters (for GET webhooks)
```

Because the body is a raw string, you must parse it in a Code node before using individual fields.

**Code node — parse a GitHub push webhook:**

```python
def main(raw_body: str) -> dict:
    import json
    data = json.loads(raw_body)
    return {
        "event_type": data.get("event", "push"),
        "repo_name": data.get("repository", {}).get("name", ""),
        "repo_full_name": data.get("repository", {}).get("full_name", ""),
        "commit_message": data.get("head_commit", {}).get("message", ""),
        "pusher_name": data.get("pusher", {}).get("name", "")
    }
```

Wire this Code node's input variable to `{{#webhook_node_id.body#}}`. After the Code node, fields like `{{#code_node_id.commit_message#}}` are available to LLM nodes, HTTP nodes, and If-Else branches.

---

## Security: HMAC Signature Verification

Most production webhook providers sign their payloads with an HMAC secret to prove authenticity. You should always verify this signature before processing the payload. GitHub, Stripe, Twilio, and many others follow this pattern.

The provider sends a header like:
- GitHub: `X-Hub-Signature-256: sha256=<hex_digest>`
- Stripe: `Stripe-Signature: t=<timestamp>,v1=<hex_digest>`
- Twilio: `X-Twilio-Signature: <base64_digest>`

**Step 1 — Store the webhook secret as an environment variable.**

In Workspace Settings → Environment Variables, add `WEBHOOK_SECRET` with the secret value provided by the webhook sender. Never hardcode it in the workflow.

**Step 2 — Add a Code node immediately after the Trigger-Webhook node to verify the signature.**

```python
def main(payload: str, signature_header: str, secret: str) -> dict:
    import hmac
    import hashlib

    # GitHub-style SHA-256 HMAC verification
    expected_sig = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    is_valid = hmac.compare_digest(expected_sig, signature_header)
    return {
        "is_valid": is_valid,
        "payload": payload
    }
```

Wire inputs:
- `payload` → `{{#webhook_node_id.body#}}`
- `signature_header` → `{{#webhook_node_id.headers.x-hub-signature-256#}}` (exact key depends on Dify's header extraction format)
- `secret` → `{{#env.WEBHOOK_SECRET#}}`

Note: `hmac.new` is the correct stdlib call. The Code node sandbox supports `hmac`, `hashlib`, `json`, `base64`, `re`, `datetime`, and other pure-Python standard library modules. It does not support network calls or filesystem access.

**Step 3 — Add an If-Else node after the verification Code node.**

```
Condition: {{#verify_node_id.is_valid#}} == false
  → True branch: End node (return 400 or a rejection message)
  → False branch: Continue to main processing logic
```

This ensures that invalid or spoofed webhook payloads are rejected before any business logic executes.

---

## Webhook Response Behavior

Dify returns `200 OK` immediately when it receives a webhook request. The workflow then runs asynchronously in the background. The external system does not wait for the workflow to complete.

This means:
- The response body the external system sees is the **custom response** configured in the Trigger-Webhook node settings (or a default empty 200).
- Workflow results are NOT returned to the webhook sender in the HTTP response.
- If you need to notify the sender of results, use an HTTP node inside the workflow to call back to the sender's API (e.g., post a GitHub commit status, send a Slack message).

**Exception — Slack Event API challenge:** Slack's Event API sends a `challenge` field during URL verification and expects you to echo it back in the response body. Configure this in the Trigger-Webhook node's custom response settings, returning `{"challenge": "{{#webhook_node_id.challenge#}}"}`.

---

## Common Webhook Integration Patterns

**GitHub — Process push events for automated code review or CI summaries:**
- Trigger on `push` event
- Extract `head_commit.message`, `repository.name`, `pusher.name`
- Send to an LLM node for classification or summarization
- Post result to a Slack channel via HTTP node

**Stripe — Handle payment events for automated fulfillment:**
- Trigger on `payment_intent.succeeded` or `invoice.payment_succeeded`
- Verify Stripe signature
- Extract `amount`, `customer`, `metadata`
- Call internal API to provision service or send confirmation email

**Slack — Handle slash commands or event subscriptions:**
- Trigger on slash command POST (form-encoded body)
- Parse `text`, `user_id`, `channel_id` fields
- Process with LLM or routing logic
- HTTP node to call Slack API (`chat.postMessage`) with the result

**Typeform / Tally — Process form submissions:**
- Trigger on form submission webhook
- Extract field answers from the JSON body
- Route to appropriate processing workflow based on form type
- Store results or trigger follow-up actions

---

## Testing Webhooks

**During development with self-hosted Dify:**

Use [ngrok](https://ngrok.com) to expose your local Dify instance to the internet so external services can reach it:

```bash
ngrok http 3000
```

Ngrok provides a public URL like `https://abc123.ngrok.io`. Construct your webhook URL as:

```
https://abc123.ngrok.io/v1/workflows/webhook/{workflow_id}/{webhook_path}
```

Paste this into your external system's webhook configuration for testing.

**Inspecting raw payloads before building the workflow:**

Use [webhook.site](https://webhook.site) to capture and inspect real webhook payloads from the external system before wiring them into Dify. Point the external system at your webhook.site URL, trigger an event, and examine the exact JSON structure and headers. Use this to design your Code node parsing logic.

**Using Dify's workflow debug mode:**

Dify Cloud and self-hosted instances offer a debug/preview mode where you can manually trigger a workflow run with a simulated input. Paste a sample webhook body as the input variable value to test your parsing and routing logic without needing real external events.

---

## Limitations

- **Workflow-only** — The Trigger-Webhook node is available only in Workflow apps. It is not available in Chatflow apps, Completion apps, or Agent apps. If you need to handle webhook events in a chat context, use a separate webhook-triggered workflow that sends results to your chatflow via the chat-messages API.
- **Asynchronous response only** — Dify immediately returns 200 to the webhook sender. The workflow result cannot be synchronously returned in the webhook HTTP response (except for custom static responses configured in the node). Design integrations assuming fire-and-forget behavior.
- **No direct streaming to webhook senders** — Unlike chatflow streaming for browser clients, webhook-triggered workflows do not stream events back to the caller.
- **Header extraction** — The exact format for accessing specific request headers (e.g., `X-Hub-Signature-256`) from the Trigger-Webhook node may vary by Dify version. Check the node's output variable list in the canvas to confirm the available fields.
- **Published app restrictions** — Trigger-Webhook workflows cannot be published as web apps or MCP servers. They are invocation-only via the webhook URL.
- **Dify Cloud custom responses** — Response body customization in the Trigger-Webhook node may be limited on Dify Cloud plans. Self-hosted instances have full control over this setting.
