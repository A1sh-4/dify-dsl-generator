# HTTP Request Node

## Overview

The HTTP Request node calls external APIs and web services directly from a Dify workflow. Use it when no Dify plugin exists for the service you need, or when you require fine-grained control over the HTTP request — custom headers, specific authentication schemes, precise body formats, or retry logic.

The HTTP Request node is the standard mechanism for integrating Dify workflows with external systems: REST APIs, webhooks, internal microservices, third-party SaaS platforms, and any endpoint accessible over HTTP or HTTPS.

## When to Use

- Calling REST API endpoints (CRUD operations on external data)
- Sending data to webhooks (Slack, Discord, Teams, Zapier, etc.)
- Querying internal services within your infrastructure
- Fetching data from public APIs (weather, finance, search, etc.)
- Any HTTP endpoint not covered by an existing Dify plugin

If you only need to process or transform the HTTP response (e.g., parse JSON, extract fields), follow the HTTP Request node with a Code node.

## Node Type Reference

From the Dify node type reference:

- **type**: `http-request`
- **Execution Type**: EXECUTABLE
- **Supported methods**: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`
- **Error handling**: supports `error_strategy: fail-branch` or `default-value`
- **Source handles**: `source` (default) or `success-branch` / `fail-branch` (with error strategy)

## Supported Methods

| Method | Typical Use |
|---|---|
| `GET` | Retrieve data; no request body |
| `POST` | Create resources; send data in request body |
| `PUT` | Replace a resource entirely |
| `PATCH` | Partially update a resource |
| `DELETE` | Remove a resource |
| `HEAD` | Check headers without downloading body |

Methods are case-insensitive in Dify but conventionally written in uppercase.

## Complete YAML Example

A POST request to an external API with Bearer token auth, JSON body, custom headers, retry, and timeout:

```yaml
- data:
    authorization:
      config:
        header: 'Authorization'
        type: bearer
        value: '{{#env.openai_api_key#}}'
      type: bearer
    body:
      data:
        - key: model
          type: text
          value: gpt-4
        - key: messages
          type: text
          value: '{{#llm_node.text#}}'
      type: json
    desc: ''
    headers:
      - id: 'header-1'
        key: Content-Type
        type: text
        value: application/json
      - id: 'header-2'
        key: X-Custom-Header
        type: text
        value: '{{#start.correlation_id#}}'
    method: POST
    params: []
    retry_config:
      max_retries: 3
      retry_interval: 2000
    selected: false
    ssl_verify: true
    timeout:
      connect: 10
      max_connect_timeout: 300
      max_read_timeout: 600
      max_write_timeout: 600
      read: 60
      write: 20
    title: Call External API
    type: http-request
    url: 'https://api.example.com/v1/process'
  height: 54
  id: '1732001000020'
  position:
    x: 680
    y: 282
  positionAbsolute:
    x: 680
    y: 282
  selected: false
  sourcePosition: right
  targetPosition: left
  type: custom
  width: 244
```

## URL and Query Parameters

The `url` field accepts a static string or a string with variable injections:

```yaml
url: 'https://api.example.com/v1/users/{{#start.user_id#}}/profile'
```

Query parameters can be embedded directly in the URL string or listed in the `params` array:

```yaml
params:
  - id: 'param-1'
    key: page
    type: text
    value: '1'
  - id: 'param-2'
    key: limit
    type: text
    value: '{{#start.page_size#}}'
```

For GET requests, use `params` instead of a body.

## Authentication Types

### 1. None (no auth)

```yaml
authorization:
  type: no-auth
  config: null
```

Use for public APIs or when auth is handled via custom headers.

### 2. API Key (custom header name)

```yaml
authorization:
  type: api-key
  config:
    type: custom
    header: 'X-API-Key'
    api_key: '{{#env.service_api_key#}}'
```

Sends the key in a custom header. Use when the API expects a non-standard header name.

### 3. Bearer Token

```yaml
authorization:
  type: api-key
  config:
    type: bearer
    api_key: '{{#env.bearer_token#}}'
```

Sends `Authorization: Bearer {token}`. This is the most common auth pattern for modern REST APIs.

### 4. Basic Auth

```yaml
authorization:
  type: api-key
  config:
    type: basic
    api_key: 'username:password'
```

Sends an `Authorization: Basic {base64(username:password)}` header. The `api_key` field contains the credentials as `username:password`. Store credentials in environment variables, never hardcoded.

## Request Headers

Headers are defined as an array of key-value objects:

```yaml
headers:
  - id: 'header-uuid-1'
    key: Content-Type
    type: text
    value: application/json
  - id: 'header-uuid-2'
    key: Accept
    type: text
    value: application/json
  - id: 'header-uuid-3'
    key: X-Request-ID
    type: text
    value: '{{#start.request_id#}}'
```

Each header entry requires a unique `id` string, a `key` (header name), and a `value`. Values support variable injection.

## Body Types

### 1. json

Send a JSON object. Each key-value pair is declared separately:

```yaml
body:
  type: json
  data:
    - key: name
      type: text
      value: '{{#start.user_name#}}'
    - key: action
      type: text
      value: process
```

### 2. form-data (multipart)

For file uploads or multipart forms:

```yaml
body:
  type: form-data
  data:
    - key: file
      type: file
      file:
        - start
        - uploaded_file
    - key: description
      type: text
      value: 'User uploaded document'
```

### 3. x-www-form-urlencoded

URL-encoded form data (classic HTML form submission):

```yaml
body:
  type: x-www-form-urlencoded
  data:
    - key: grant_type
      type: text
      value: client_credentials
    - key: client_id
      type: text
      value: '{{#env.client_id#}}'
```

### 4. raw-text

Send a plain text string body:

```yaml
body:
  type: raw-text
  data:
    - key: ''
      type: text
      value: '{{#start.plain_text_payload#}}'
```

### 5. none

No request body (standard for GET and HEAD):

```yaml
body:
  type: none
  data: []
```

### 6. binary

Send binary data (e.g., a file variable):

```yaml
body:
  type: binary
  data:
    - key: ''
      type: file
      file:
        - start
        - binary_file
```

## Timeout Configuration

```yaml
timeout:
  connect: 10          # seconds to establish connection
  read: 60             # seconds to wait for response data
  write: 20            # seconds to send request data
  max_connect_timeout: 300
  max_read_timeout: 600
  max_write_timeout: 600
```

Set timeouts appropriate to the API's expected latency. For fast internal APIs, use small values (5–10s). For slow external services or large file transfers, increase `read` accordingly.

## Retry Configuration

```yaml
retry_config:
  max_retries: 3        # 0 = no retry; max 10
  retry_interval: 2000  # milliseconds between retries
```

Retries occur on transient failures (network errors, 5xx responses). Use `max_retries: 3` with `retry_interval: 2000` (2 seconds) as a sensible default for production workflows.

## SSL Verification

```yaml
ssl_verify: true    # default — verify SSL certificate (recommended)
ssl_verify: false   # disable only for internal/dev/self-signed endpoints
```

Never disable SSL verification for external production endpoints. Only use `ssl_verify: false` for internal services with self-signed certificates in controlled environments.

## Output Variables

After the HTTP Request node executes, the following variables are available:

| Variable | Type | Description |
|---|---|---|
| `{{#node_id.body#}}` | string | Response body as a raw string |
| `{{#node_id.status_code#}}` | number | HTTP status code (200, 201, 400, 500, etc.) |
| `{{#node_id.headers#}}` | object | Response headers as a key-value object |

Replace `node_id` with the actual `id` of your HTTP Request node.

Note: `body` is always a string, even when the API returns JSON. You must parse it downstream.

## Parsing JSON Responses

The response `body` is a raw string. To extract fields, use a downstream Code node:

```python
def main(response_body: str) -> dict:
    import json
    data = json.loads(response_body)
    return {
        "extracted_field": data["result"]["value"],
        "record_count": len(data.get("items", []))
    }
```

Connect the HTTP Request node's output to this Code node's `response_body` input variable.

## Error Handling

### Fail Branch (recommended for production)

```yaml
error_strategy: fail-branch
```

Creates two source handles: `success-branch` and `fail-branch`. Connect them separately to handle errors gracefully. Error variables available on the fail path:

- `{{#node_id.error_message#}}` — human-readable description of the error
- `{{#node_id.error_type#}}` — error type classification

Typical pattern: success branch continues normal processing; fail branch connects to an LLM node that generates a user-friendly error message, then both branches converge in a variable-aggregator.

### Default Value (simple fallback)

```yaml
error_strategy: default-value
default_value:
  body: '{"error": "service_unavailable"}'
  status_code: 503
```

Returns predefined values on error and continues on the main path. Simpler than fail-branch but less flexible.

### No Error Strategy (abort)

Omit `error_strategy` to let any HTTP error terminate the entire workflow. Use only in development or non-critical paths.

## Security Rules

**NEVER hardcode API keys, passwords, or tokens directly in the YAML.** Always use environment variable references:

```yaml
# CORRECT
value: '{{#env.openai_api_key#}}'

# WRONG — never do this
value: 'sk-abc123...'
```

Environment variables are configured in the Dify workspace settings under "Environment Variables" and referenced with the `{{#env.variable_name#}}` syntax. This keeps secrets out of workflow DSL files and version control.

Store all secrets — API keys, bearer tokens, basic auth credentials, webhook secrets — as environment variables.

## Common Mistakes

- **Parsing the body in the same node**: The HTTP Request node does not parse JSON automatically. Always add a Code node downstream for JSON extraction.
- **Hardcoding credentials**: API keys in the YAML are visible to anyone who can export the workflow. Use `{{#env.key_name#}}` always.
- **Wrong Content-Type for JSON**: When sending a JSON body, ensure `Content-Type: application/json` is in the headers, or the API may reject the request.
- **Forgetting `error_strategy` in production**: Without it, a single API failure crashes the whole workflow. Add `fail-branch` for any external service call.
- **Timeouts too short**: Default timeouts may be too short for slow external APIs. Set `read` to at least 30–60 seconds for services with variable latency.
- **Using GET with a body**: Many servers ignore or reject GET requests with a body. Use `params` for GET query parameters instead.
- **Not checking status_code**: A 200 response does not always mean success at the application level. Use a downstream if-else node to check `status_code` before processing the body.
