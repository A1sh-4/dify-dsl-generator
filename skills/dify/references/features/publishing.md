# Publishing

Dify applications can be published and accessed through multiple channels. Each publishing mode suits different use cases, from internal team tools to public-facing products to developer API integrations.

---

## Development Mode vs Published App

Before any publishing mode is activated, workflows and chatflows run in **development mode** — accessible only to workspace members through the Dify editor. Publishing creates a stable, versioned snapshot of the application.

**Versioning:**
- Click **Publish** (top-right in the editor) to publish the current state as a new version.
- Previous versions remain accessible under **Version History**.
- The published app URL always serves the latest published version.
- Rolling back: publish a previous version to replace the current one.

---

## 1. Web App (Sharing URL)

The simplest publishing mode. Dify generates a public-facing web application with a chat or workflow interface.

### URL Format
```
https://cloud.dify.ai/chat/<app-id>
```
For self-hosted instances:
```
https://your-dify-instance.com/chat/<app-id>
```

### Access Control
- **Public:** Anyone with the URL can access the app. No login required.
- **Password protection:** Set a password in **Settings → Publish → Web App**. Users must enter the password before accessing.
- **Login required:** Restrict access to signed-in Dify workspace members only (team/enterprise plans).

### Customization
Customize the web app appearance under **Settings → Publish → Web App Customization**:
- **App name:** Display name shown in browser tab and header.
- **App icon:** Upload a logo or icon image.
- **Brand color:** Primary color applied to buttons and accents.
- **Opening message:** The greeting shown when the chatflow loads (also controlled by `features.opening_statement` in DSL).
- **Copyright text:** Footer attribution text.

---

## 2. API

Integrate the Dify workflow or chatflow programmatically via REST API.

### API Key
Each published app has its own **App API Key**. This is distinct from the workspace-level API key.

To get the App API Key:
1. Go to **Settings → API Access**.
2. Click **Create API Key**.
3. Copy the key. Store securely — it will not be shown again.

The App API Key grants access only to this specific app, not the entire workspace.

### Endpoint URL
```
https://api.dify.ai/v1
```
Self-hosted:
```
https://your-dify-instance.com/v1
```

### Key API Endpoints

**Chatflow — send message:**
```
POST /chat-messages
Authorization: Bearer <app-api-key>
Content-Type: application/json

{
  "query": "user message here",
  "conversation_id": "optional-existing-conversation-id",
  "user": "user-identifier",
  "inputs": {}
}
```

**Workflow — run:**
```
POST /workflows/run
Authorization: Bearer <app-api-key>
Content-Type: application/json

{
  "inputs": { "variable_name": "value" },
  "user": "user-identifier"
}
```

### Blocking vs Streaming Mode
- **Blocking:** Add `"response_mode": "blocking"` to the request body. The HTTP response waits until the workflow completes, then returns the full output. Simple to implement but increases response time.
- **Streaming:** Add `"response_mode": "streaming"`. The response uses Server-Sent Events (SSE). Tokens stream as they are generated. Required for chatflows with long responses to avoid client timeout.

### Rate Limits
- Dify Cloud: 60 requests per minute per API key by default. Contact support to increase.
- Self-hosted: Rate limits are configurable in the Dify environment configuration.

---

## 3. MCP Server

Dify can expose a workflow as an **MCP (Model Context Protocol) server**, making it callable as a tool by MCP clients (Claude Desktop, other MCP-compatible AI agents).

### CRITICAL LIMITATION
MCP server publishing is **only available for workflows that use the Start node with User Input type**. Specifically:
- The workflow must be of type **workflow** (not chatflow).
- The Start node must have its trigger type set to **User Input** (manually initiated by a user).
- MCP server publishing is **NOT available** for workflows triggered by webhooks, schedules, or other trigger-based start nodes.
- MCP is also not available for chatflows.

If the workflow uses a trigger-based start node (webhook, cron, etc.), the MCP Server option will be grayed out in the publishing panel.

### Enabling MCP Server
1. Ensure the workflow uses a Start node with User Input type.
2. Go to **Settings → Publish**.
3. Click **MCP Server** tab.
4. Click **Enable**.
5. Copy the MCP server URL and API key.
6. Add to your MCP client configuration (e.g., Claude Desktop `config.json`).

The workflow's start node input variables become the MCP tool's input parameters. The end node output becomes the tool's return value.

---

## 4. Marketplace Publishing

Publish your Dify application to the Dify Marketplace so other users can discover and install it.

### Requirements
- App must be fully functional and tested.
- Must include documentation (description, usage instructions, screenshots).
- No hardcoded API keys or personal credentials.
- Must comply with Dify content policies.

### Process
1. Go to **Settings → Publish → Marketplace**.
2. Complete the submission form: name, description, category, screenshots.
3. Submit for review.
4. Dify team reviews the submission (typically 2-5 business days).
5. Once approved, the app appears in the marketplace.

Marketplace apps are packaged as `.difypkg` files that users can install to their own workspace.

---

## 5. Embedded Widget

Embed the Dify chatflow directly into any web page using an iframe or JavaScript snippet.

### iframe Embed
```html
<iframe
  src="https://cloud.dify.ai/chat/<app-id>?embed=true"
  style="width: 100%; height: 600px; border: none;"
  allow="microphone">
</iframe>
```

The `embed=true` parameter hides the Dify header for cleaner embedding.

### JavaScript Widget
Dify provides a JavaScript chat widget that can be injected into any web page:
```html
<script>
  window.difyChatbotConfig = {
    token: '<app-api-key>',
    baseUrl: 'https://api.dify.ai'
  }
</script>
<script src="https://cloud.dify.ai/embed.min.js" defer></script>
```

The widget renders a floating chat bubble on the page. Clicking it opens the chat interface.

**Customization:**
- `isDraggable`: allow users to drag the bubble.
- `defaultOpen`: start with the chat panel open.
- `width` / `height`: override the default panel dimensions.

---

## How the App API Key Differs from the Workspace API Key

| Feature | App API Key | Workspace API Key |
|---|---|---|
| Scope | Single app only | All workspace resources |
| Used for | Calling a specific published app | Managing workspace (create apps, manage knowledge bases) |
| Found in | App → Settings → API Access | Account → Settings → API Keys |
| Risk if leaked | Only that app is exposed | Entire workspace exposed |

Always use the App API Key for application integrations. Reserve the workspace API key for administrative automation.
