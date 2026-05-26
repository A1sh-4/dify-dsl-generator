# API Extensions

API extensions allow you to connect Dify to external HTTP endpoints that extend platform behavior with custom logic. Unlike HTTP nodes (which are part of the workflow graph and run during node execution), API extensions are registered at the workspace level and are invoked by Dify at specific lifecycle points — for example, before processing user input (moderation) or when fetching dynamic data (external data tool).

---

## What API Extensions Are

An API extension is an external HTTPS endpoint that you own and deploy. You register its URL in the Dify workspace. When Dify reaches a point in processing where the extension is needed, it calls your endpoint with a JSON payload and uses the response to continue processing.

API extensions are managed in **Settings → API Extensions**.

---

## The Two Extension Types

### 1. Moderation Extension

A moderation extension sits between user input / LLM output and Dify's response pipeline. Dify sends the text to your endpoint, and your endpoint decides whether to allow or block it.

**Use cases:**
- Custom profanity or hate speech filter using your own blocklist.
- Domain-specific content restriction (e.g., block non-business-related queries in a corporate chatbot).
- PII detection — block inputs or outputs containing email addresses, phone numbers, or SSNs.
- Regulatory compliance — ensure outputs never mention competitor products.

**How Dify calls your moderation endpoint:**

Dify sends a POST request to your registered URL with the following JSON body:

```json
{
  "point": "app.external_data_tool.query",
  "params": {
    "app_id": "abc123",
    "tool_variable": "moderation_check",
    "inputs": {
      "query": "User's input text here"
    },
    "query": "User's input text here"
  }
}
```

For output moderation, the `point` field changes to indicate it is the LLM's output being checked:
```json
{
  "point": "app.moderation.output",
  "params": {
    "app_id": "abc123",
    "text": "LLM output text here",
    "query": "original user query"
  }
}
```

**Your endpoint must return:**

```json
{
  "flagged": false,
  "action": "direct_output",
  "preset_response": ""
}
```

Fields:
- `flagged` (boolean) — `true` if the text should be blocked, `false` if allowed.
- `action` — one of:
  - `"direct_output"` — return the `preset_response` to the user instead of continuing.
  - `"overridden"` — replace the input/output with the `preset_response` and continue the workflow with the replacement text.
- `preset_response` (string) — the replacement text to use when `flagged: true`. Example: `"I'm sorry, I can't help with that request."`

If `flagged: false`, the `action` and `preset_response` fields are ignored.

---

### 2. External Data Tool

An external data tool extension lets Dify fetch data from your endpoint during workflow execution. From the workflow's perspective, the external data tool behaves like a data source — it is queried with the current inputs, and the result is injected as a variable.

**Use cases:**
- CRM data lookup — fetch customer tier, account status, or history from Salesforce during chatflow execution.
- Real-time product pricing — query your pricing service to inject current prices into LLM prompts.
- Internal knowledge graph — retrieve structured company data that is not suitable for a document-based knowledge base.
- Dynamic system prompt injection — fetch user-specific configuration from your database to personalize the system prompt.

**How Dify calls your external data tool endpoint:**

Dify sends a POST request:

```json
{
  "point": "app.external_data_tool.query",
  "params": {
    "app_id": "abc123",
    "tool_variable": "customer_data",
    "inputs": {
      "user_id": "user-456",
      "query": "What is my account balance?"
    },
    "query": "What is my account balance?"
  }
}
```

Fields:
- `point` — always `"app.external_data_tool.query"` for external data tool extensions.
- `params.app_id` — the Dify app ID making the request.
- `params.tool_variable` — the name of the external data tool variable (as configured in workspace settings).
- `params.inputs` — all current workflow input variables, keyed by variable name.
- `params.query` — the user's current query string.

**Your endpoint must return:**

```json
{
  "result": "Account balance: $1,234.56. Status: Active. Tier: Premium."
}
```

The `result` field (string) is injected into the workflow as the value of the external data tool variable. This value can be referenced in prompts using standard Dify variable syntax.

---

## Health Check

When you register an API extension in Dify, the platform immediately sends a **health check ping** to verify the endpoint is reachable:

```json
{
  "point": "ping"
}
```

Your endpoint must respond with:
```json
{
  "result": "pong"
}
```

If the health check fails (non-200 status, wrong response, timeout), Dify will not save the extension configuration. Fix the endpoint and retry.

**Important:** The health check uses the same URL and authentication headers as live requests. Ensure your endpoint handles the `"ping"` point without error.

---

## Authentication

Dify sends an API key header with every extension request for security:

```
Authorization: Bearer <your-extension-api-key>
```

You define this key when registering the extension in Dify. Your endpoint should validate this header and reject requests with invalid or missing keys.

---

## Setting Up Locally with Ngrok for Development

To test API extensions during development before deploying to production, use Ngrok to expose your local server:

1. Start your local extension server (e.g., on port 5000).
2. Run: `ngrok http 5000`
3. Ngrok provides a public HTTPS URL like `https://abc123.ngrok.io`.
4. Register this URL in Dify as the extension endpoint.
5. Dify will route requests through Ngrok to your local server.

**Note:** Ngrok free tier URLs change on restart. Use a fixed ngrok domain (paid plan) for stable development.

---

## Production Deployment

Any HTTPS endpoint works for production. Recommended platforms:

- **Cloudflare Workers** — runs at the edge globally, low latency, free tier available. Deploy a Worker that validates the Dify API key and handles the `ping`, moderation, and data tool points.
- **AWS Lambda / Azure Functions / Google Cloud Functions** — serverless functions behind API Gateway with HTTPS.
- **Any standard web server** (FastAPI, Express, Flask) deployed behind HTTPS (Nginx, Caddy, or a managed platform like Railway or Render).

**Requirements:**
- HTTPS only (HTTP endpoints are rejected by Dify).
- Response time under 5 seconds (Dify times out extension calls at 5s).
- Return JSON with the correct schema.

---

## Example: Simple Cloudflare Worker Moderation Extension

```javascript
export default {
  async fetch(request, env) {
    const auth = request.headers.get('Authorization');
    if (auth !== `Bearer ${env.DIFY_EXTENSION_KEY}`) {
      return new Response('Unauthorized', { status: 401 });
    }

    const body = await request.json();

    if (body.point === 'ping') {
      return Response.json({ result: 'pong' });
    }

    const text = body.params?.query || body.params?.text || '';
    const blocked = /badword1|badword2/i.test(text);

    return Response.json({
      flagged: blocked,
      action: blocked ? 'direct_output' : 'direct_output',
      preset_response: blocked ? "I can't help with that." : ''
    });
  }
};
```

---

## Related Documentation

- See `skills/dify/references/nodes/http.md` for HTTP nodes (in-graph API calls, as opposed to workspace-level extensions).
- See `skills/dify/references/features/plugins-marketplace.md` for marketplace plugins (preferred over HTTP nodes and extensions when available).
