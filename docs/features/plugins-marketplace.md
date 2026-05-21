# Plugins Marketplace

Dify's plugin marketplace provides a curated catalog of integrations that extend Dify's capabilities without requiring raw HTTP node configuration. Plugins handle authentication, request formatting, and error handling — making them significantly simpler to use than custom HTTP nodes.

Marketplace URL: https://marketplace.dify.ai — 120+ plugins available as of 2025.

---

## Plugin Types

There are 5 distinct plugin types, each serving a different purpose in the Dify ecosystem:

### 1. Model Plugins
Add new LLM providers or embedding model providers to the workspace. Once installed, the provider's models appear in node model dropdowns and workspace model settings. Example: adding Mistral AI, Groq, or Ollama as a local model provider.

### 2. Tool Plugins
The most common plugin type. Tool plugins expose one or more callable tools that can be used in **Tool nodes** and **Agent nodes**. Each tool has defined input parameters and output fields. Examples: Brave Search, Firecrawl, Serper, GitHub, Slack, Notion.

### 3. Agent Strategy Plugins
Custom reasoning strategies for agent nodes. Instead of the built-in ReAct or Function Calling loops, an agent strategy plugin defines a custom iterative planning and execution pattern. Advanced use case — typically used for specialized multi-step reasoning tasks.

### 4. Extension Plugins
Data tools and moderation extensions. These integrate with Dify's **API Extension** system to provide custom moderation logic, external data lookups, or other pre/post-processing. Installed extension plugins appear in workspace extension settings.

### 5. Trigger Plugins
Webhook and schedule-based triggers that initiate workflow execution. A trigger plugin registers an endpoint that Dify exposes, or a cron-like schedule, so workflows can be launched from external systems without calling the Dify API directly.

---

## Finding and Installing Plugins

### Discovery
Browse https://marketplace.dify.ai or use the **Plugins** section in the Dify workspace sidebar. Filter by type, category, or search by name.

### Installation via UI
1. Go to **Workspace → Plugins** in the Dify sidebar.
2. Click **Discover Plugins** or browse the marketplace tab.
3. Click **Install** on the desired plugin.
4. The plugin installs to the workspace. All workspace members can use it.
5. After installation, configure credentials in **Settings → Plugin Credentials**.

### Installation via CLI (self-hosted Dify)
```bash
dify plugin install langgenius/brave
```
Or by uploading a `.difypkg` file directly through the **Install Local Plugin** option.

### Before Importing a DSL That Uses Plugins
If you import a DSL YAML that references marketplace plugins, those plugins **must already be installed** in the target workspace. If a plugin is missing, the workflow will fail at runtime with a "plugin not found" error. Always install required plugins before importing DSL files.

---

## How Tool Plugins Appear in DSL YAML

A Tool node that uses a marketplace plugin references the plugin's provider and tool identifier. The node `type` is `tool` and the `provider_id` follows the pattern `langgenius/<plugin-name>`.

---

## Plugin DSL Configurations

### Brave Search
Performs web search via the Brave Search API.

```yaml
- data:
    desc: "Search the web using Brave"
    provider_id: langgenius/brave
    provider_name: brave
    provider_type: plugin
    tool_configurations: {}
    tool_label: Brave Search
    tool_name: brave_search
    tool_parameters:
      query:
        type: mixed
        value: "{{#start.query#}}"
  height: 82
  id: tool_brave_search
  position:
    x: 400
    y: 200
  selected: false
  sourcePosition: right
  targetPosition: left
  type: tool
  width: 244
```

**Input parameters:**
- `query` (string, required) — the search query to send to Brave.

**Output:** `text` — raw search result text including titles, URLs, and snippets.

---

### Firecrawl
Crawls and extracts content from web pages as clean Markdown.

```yaml
- data:
    desc: "Extract web page content using Firecrawl"
    provider_id: langgenius/firecrawl
    provider_name: firecrawl
    provider_type: plugin
    tool_configurations: {}
    tool_label: Firecrawl Crawl
    tool_name: firecrawl_crawl
    tool_parameters:
      url:
        type: mixed
        value: "{{#start.url#}}"
  height: 82
  id: tool_firecrawl
  position:
    x: 400
    y: 300
  selected: false
  sourcePosition: right
  targetPosition: left
  type: tool
  width: 244
```

**Input parameters:**
- `url` (string, required) — the URL of the page to crawl and extract.

**Output:** `text` — Markdown-formatted page content.

---

### Serper
Google search results via the Serper API.

```yaml
- data:
    desc: "Search Google via Serper"
    provider_id: langgenius/serper
    provider_name: serper
    provider_type: plugin
    tool_configurations: {}
    tool_label: Serper Search
    tool_name: serper_search
    tool_parameters:
      query:
        type: mixed
        value: "{{#start.query#}}"
  height: 82
  id: tool_serper
  position:
    x: 400
    y: 200
  selected: false
  sourcePosition: right
  targetPosition: left
  type: tool
  width: 244
```

**Input parameters:**
- `query` (string, required) — the Google search query.

**Output:** `text` — structured search results including organic results, knowledge graph, and answer boxes.

---

### Jina AI (Jina Reader)
Fetches and converts any URL to clean, LLM-friendly text.

```yaml
- data:
    desc: "Read URL content via Jina Reader"
    provider_id: langgenius/jina
    provider_name: jina
    provider_type: plugin
    tool_configurations: {}
    tool_label: Jina Reader
    tool_name: jina_reader
    tool_parameters:
      url:
        type: mixed
        value: "{{#start.url#}}"
  height: 82
  id: tool_jina
  position:
    x: 400
    y: 200
  selected: false
  sourcePosition: right
  targetPosition: left
  type: tool
  width: 244
```

**Input parameters:**
- `url` (string, required) — URL to read and convert to text.

**Output:** `text` — clean Markdown or plain text content.

---

### Stability AI
Generates images from text prompts using Stability AI's image generation API.

```yaml
- data:
    desc: "Generate image from text prompt"
    provider_id: langgenius/stability
    provider_name: stability
    provider_type: plugin
    tool_configurations: {}
    tool_label: Text to Image
    tool_name: text2image
    tool_parameters:
      prompt:
        type: mixed
        value: "{{#llm_node.text#}}"
  height: 82
  id: tool_stability
  position:
    x: 600
    y: 200
  selected: false
  sourcePosition: right
  targetPosition: left
  type: tool
  width: 244
```

**Input parameters:**
- `prompt` (string, required) — text description of the image to generate.

**Output:** `files` — array of generated image file objects.

---

### GitHub
Retrieves repository information from GitHub.

```yaml
- data:
    desc: "Get GitHub repository details"
    provider_id: langgenius/github
    provider_name: github
    provider_type: plugin
    tool_configurations: {}
    tool_label: GitHub Get Repo
    tool_name: github_get_repo
    tool_parameters:
      repo:
        type: mixed
        value: "{{#start.repo#}}"
  height: 82
  id: tool_github
  position:
    x: 400
    y: 200
  selected: false
  sourcePosition: right
  targetPosition: left
  type: tool
  width: 244
```

**Input parameters:**
- `repo` (string, required) — repository in `owner/repo` format (e.g., `langgenius/dify`).

**Output:** `text` — repository metadata including description, stars, language, and recent activity.

---

## Plugin vs HTTP Node: When to Use Each

| Scenario | Use Plugin | Use HTTP Node |
|---|---|---|
| Service has a marketplace plugin | Yes | No |
| Auth is OAuth or API key (standard) | Yes (plugin handles it) | Possible but complex |
| Custom internal API | No | Yes |
| API not in marketplace | No | Yes |
| Need full control over request headers/body | No | Yes |
| Production reliability + maintained integration | Yes | Riskier (self-maintained) |

**Rule:** Always check the Dify marketplace (via the plugin-finder agent) before building an HTTP node integration. Plugins are officially maintained, use standardized auth, and reduce DSL complexity significantly.

---

## The `dependencies` Block in DSL YAML

Any DSL file that uses marketplace plugins must include a `dependencies` block at the top level. This block declares which plugins the workflow requires. It is used by Dify to warn users if required plugins are not installed before import.

```yaml
dependencies:
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/brave:0.0.3/brave"
```

**Fields:**
- `current_identifier` — set to `null` for marketplace plugins (used for local/custom plugins).
- `type` — always `marketplace` for marketplace plugins.
- `value.marketplace_plugin_unique_identifier` — the fully qualified plugin identifier in the format `author/plugin-name:version/plugin-name`. The version segment (`0.0.3`) reflects the installed version at DSL generation time.

**Multiple plugins:**
```yaml
dependencies:
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/brave:0.0.3/brave"
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/firecrawl:0.0.8/firecrawl"
```

If a DSL uses no plugins, the `dependencies` block can be omitted or set to an empty list (`dependencies: []`).

---

## Plugin Credentials

Plugin API keys and credentials are **never stored in DSL YAML**. They are configured at the workspace level:

1. Go to **Settings → Plugin Credentials** (or **Integrations → Plugins**).
2. Select the installed plugin.
3. Enter API keys, tokens, or OAuth credentials.
4. Credentials are stored encrypted in the workspace and applied automatically when the plugin is called.

This means DSL files are safe to share — they contain no secrets. The DSL references the plugin tool, and the runtime supplies credentials from workspace settings.

**NEVER embed API keys in DSL YAML.** Use `{{#env.VARIABLE_NAME#}}` for HTTP nodes if secrets must be referenced. For plugin nodes, no credential reference is needed — the workspace credential is applied automatically.

---

## Related Documentation

- See `docs/nodes/tool.md` for the full tool node DSL schema.
- See `docs/features/api-extensions.md` for custom API endpoints (alternative to plugins for proprietary APIs).
- See `docs/nodes/http.md` for HTTP node configuration when no plugin exists.
