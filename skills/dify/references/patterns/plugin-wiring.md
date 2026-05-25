# Plugin Wiring Pattern: Marketplace Plugins in DSL

## Overview

Dify's plugin marketplace provides pre-built integrations for common services — web search, web scraping, image generation, code execution, and more. Using a plugin tool node is the correct approach whenever a marketplace plugin exists for the required service. Plugins are officially maintained, handle authentication at the workspace level (no credentials in YAML), and expose a clean, standardized parameter interface.

This document covers the complete process of wiring a marketplace plugin into a DSL file: finding the plugin, configuring the dependencies block, wiring the tool node, and handling its output.

**Always check for a marketplace plugin before building an HTTP node.** The plugin-finder agent performs this check automatically. Only fall back to an HTTP node when no plugin exists.

See also: `docs/features/plugins-marketplace.md` for the plugin catalog and credential configuration.

---

## Step-by-Step Wiring Process

### Step 1: Find the Plugin

Browse `marketplace.dify.ai` or refer to `docs/features/plugins-marketplace.md`. Identify:
- **author** — the plugin's namespace prefix (typically `langgenius`)
- **plugin-name** — the plugin's unique slug (e.g., `brave`, `firecrawl`, `stability`)
- **version** — the installed version (e.g., `0.0.3`)
- **tool_name** — the specific callable action within the plugin (e.g., `brave_search`, `firecrawl_crawl`, `text2image`)

The `provider_id` field in node YAML uses the pattern `langgenius/<plugin-name>`.

### Step 2: Install the Plugin in the Workspace

Before importing any DSL that uses a plugin, the plugin must be installed in the target workspace:
1. In the Dify sidebar, go to **Plugins**.
2. Search for the plugin by name.
3. Click **Install**.
4. Go to **Settings → Plugin Credentials** and enter the required API key or token.

Credentials are stored encrypted at the workspace level. They are **never** referenced in DSL YAML.

### Step 3: Add the `dependencies` Block

Every DSL file that uses a marketplace plugin must declare that dependency at the top level:

```yaml
dependencies:
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/brave:0.0.3/brave"
```

The `marketplace_plugin_unique_identifier` format is: `author/plugin-name:version/plugin-name`.

For multiple plugins, add one entry per plugin:

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

Dify uses this block to warn importers when a required plugin is not installed.

### Step 4: Add the Tool Node

The tool node has `type: tool` and references the plugin through `provider_id`, `provider_name`, `provider_type`, `tool_name`, and `tool_parameters`:

```yaml
- data:
    desc: "Search the web for current information."
    provider_id: langgenius/brave/brave
    provider_name: Brave Search
    provider_type: builtin
    title: Web Search
    tool_configurations:
      count: 5
    tool_name: brave_search
    tool_parameters:
      query:
        type: mixed
        value: "{{#1718000000001.query#}}"
    type: tool
  height: 90
  id: "1718000000002"
  position:
    x: 380
    y: 282
  positionAbsolute:
    x: 380
    y: 282
  selected: false
  sourcePosition: right
  targetPosition: left
  type: custom
  width: 244
```

**Key fields:**
- `provider_id`: `author/plugin-name/plugin-name` — the trailing plugin name segment is repeated (e.g., `langgenius/brave/brave`).
- `provider_type`: always `builtin` for marketplace plugins.
- `tool_parameters`: each parameter has a `type` and `value`. Use `type: mixed` with a variable reference when the value comes from an upstream node. Use `type: mixed` with a literal string for static values.
- `tool_configurations`: static configuration options that don't change per-run (e.g., `count: 5` for search result count).

### Step 5: Wire the Output

Tool nodes output a `text` variable (for most tools) or a `files` variable (for image generation tools). Reference the output using:

```
{{#tool_node_id.text#}}
```

or

```
{{#tool_node_id.files#}}
```

Always confirm the output field name from `docs/features/plugins-marketplace.md` before wiring.

### Step 6: Handle "Plugin Not Installed" Errors

When a DSL is imported to a workspace where the plugin is not installed, Dify displays an import warning. The workflow can be imported but will fail at runtime when the tool node executes.

**Resolution:**
1. Install the plugin in the workspace.
2. Configure credentials in **Settings → Plugin Credentials**.
3. Re-run the workflow — no re-import needed once the plugin is installed.

---

## Plugin Pattern 1: Web Search (Brave Search)

**Use case:** Start with a user query, search the web for current information, summarize the results with an LLM, and return the summary.

**Node graph:**
```
start → tool (brave_search) → llm (summarize) → end
```

**Node IDs:** `"1718100000001"`, `"1718100000002"`, `"1718100000003"`, `"1718100000004"`

```yaml
app:
  description: "Searches the web using Brave Search and returns an LLM-synthesized summary."
  icon: "\U0001F50D"
  icon_background: "#E3F2FD"
  mode: workflow
  name: Web Search Summary
dependencies:
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/brave:0.0.3/brave"
features: {}
kind: app
version: "0.1.3"
workflow:
  conversation_variables: []
  environment_variables: []
  graph:
    edges:
      - data:
          isInIteration: false
          sourceType: start
          targetType: tool
        id: "1718100000001-source-1718100000002-target"
        source: "1718100000001"
        sourceHandle: source
        target: "1718100000002"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: tool
          targetType: llm
        id: "1718100000002-source-1718100000003-target"
        source: "1718100000002"
        sourceHandle: source
        target: "1718100000003"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: llm
          targetType: end
        id: "1718100000003-source-1718100000004-target"
        source: "1718100000003"
        sourceHandle: source
        target: "1718100000004"
        targetHandle: target
        type: custom
        zIndex: 0
    nodes:
      - data:
          desc: ""
          title: Start
          type: start
          variables:
            - label: Search Query
              max_length: 500
              options: []
              required: true
              type: text-input
              variable: query
        height: 54
        id: "1718100000001"
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

      - data:
          desc: "Search the web for current information using Brave Search."
          provider_id: langgenius/brave/brave
          provider_name: Brave Search
          provider_type: builtin
          title: Web Search
          tool_configurations:
            count: 5
          tool_name: brave_search
          tool_parameters:
            query:
              type: mixed
              value: "{{#1718100000001.query#}}"
          type: tool
        height: 90
        id: "1718100000002"
        position:
          x: 380
          y: 282
        positionAbsolute:
          x: 380
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          desc: "Synthesize the search results into a concise, accurate summary."
          model:
            completion_params:
              max_tokens: 1024
              temperature: 0.3
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: search-system
              role: system
              text: |
                You are a research assistant. Synthesize the web search results below into a concise, accurate answer.

                Search results:
                {{#1718100000002.text#}}

                Rules:
                - Answer the user's question directly using the search results
                - Cite the source URLs where relevant
                - If the results are insufficient, say so clearly
            - id: search-user
              role: user
              text: "{{#1718100000001.query#}}"
          title: Summarize Results
          type: llm
          vision:
            enabled: false
        height: 98
        id: "1718100000003"
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

      - data:
          desc: ""
          outputs:
            - label: Summary
              name: summary
              type: string
              value_selector:
                - "1718100000003"
                - text
          title: End
          type: end
        height: 54
        id: "1718100000004"
        position:
          x: 980
          y: 282
        positionAbsolute:
          x: 980
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
```

**Output variable:** `{{#1718100000002.text#}}` — the raw search result text containing titles, URLs, and snippets from Brave Search.

---

## Plugin Pattern 2: Web Scraping (Firecrawl)

**Use case:** Accept a URL as input, scrape its full content using Firecrawl, extract structured information using an LLM, and return the extraction.

**Node graph:**
```
start → tool (firecrawl_crawl) → llm (extract info) → end
```

**Node IDs:** `"1718200000001"`, `"1718200000002"`, `"1718200000003"`, `"1718200000004"`

```yaml
app:
  description: "Scrapes a web page using Firecrawl and extracts structured information with an LLM."
  icon: "\U0001F578"
  icon_background: "#FFF3E0"
  mode: workflow
  name: Web Page Extractor
dependencies:
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/firecrawl:0.0.8/firecrawl"
features: {}
kind: app
version: "0.1.3"
workflow:
  conversation_variables: []
  environment_variables: []
  graph:
    edges:
      - data:
          isInIteration: false
          sourceType: start
          targetType: tool
        id: "1718200000001-source-1718200000002-target"
        source: "1718200000001"
        sourceHandle: source
        target: "1718200000002"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: tool
          targetType: llm
        id: "1718200000002-source-1718200000003-target"
        source: "1718200000002"
        sourceHandle: source
        target: "1718200000003"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: llm
          targetType: end
        id: "1718200000003-source-1718200000004-target"
        source: "1718200000003"
        sourceHandle: source
        target: "1718200000004"
        targetHandle: target
        type: custom
        zIndex: 0
    nodes:
      - data:
          desc: ""
          title: Start
          type: start
          variables:
            - label: URL to Scrape
              max_length: 2048
              options: []
              required: true
              type: text-input
              variable: url
            - label: What to Extract
              max_length: 500
              options: []
              required: true
              type: text-input
              variable: extraction_goal
        height: 90
        id: "1718200000001"
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

      - data:
          desc: "Extract full text content from the URL as clean Markdown."
          provider_id: langgenius/firecrawl/firecrawl
          provider_name: Firecrawl
          provider_type: builtin
          title: Scrape Page
          tool_configurations: {}
          tool_name: firecrawl_crawl
          tool_parameters:
            url:
              type: mixed
              value: "{{#1718200000001.url#}}"
          type: tool
        height: 90
        id: "1718200000002"
        position:
          x: 380
          y: 282
        positionAbsolute:
          x: 380
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          desc: "Extract the requested information from the scraped page content."
          model:
            completion_params:
              max_tokens: 2048
              temperature: 0.2
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: extract-system
              role: system
              text: |
                You are a precise data extraction assistant. Extract the requested information from the web page content below.

                Extraction goal: {{#1718200000001.extraction_goal#}}

                Web page content:
                {{#1718200000002.text#}}

                Instructions:
                - Extract only what was requested
                - Preserve the original wording where important
                - If the requested information is not present, say "Not found on this page."
                - Format your output clearly — use bullet points or structured sections as appropriate
            - id: extract-user
              role: user
              text: "Extract the following from the page: {{#1718200000001.extraction_goal#}}"
          title: Extract Information
          type: llm
          vision:
            enabled: false
        height: 98
        id: "1718200000003"
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

      - data:
          desc: ""
          outputs:
            - label: Extracted Data
              name: extracted_data
              type: string
              value_selector:
                - "1718200000003"
                - text
          title: End
          type: end
        height: 54
        id: "1718200000004"
        position:
          x: 980
          y: 282
        positionAbsolute:
          x: 980
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
```

**Output variable:** `{{#1718200000002.text#}}` — clean Markdown-formatted content of the scraped page.

---

## Plugin Pattern 3: Image Generation (Stability AI)

**Use case:** Accept a brief description, enhance it into a detailed image prompt using an LLM, generate the image using Stability AI's text-to-image tool, and return the image file.

**Node graph:**
```
start → llm (enhance prompt) → tool (stability text2image) → end
```

**Node IDs:** `"1718300000001"`, `"1718300000002"`, `"1718300000003"`, `"1718300000004"`

**Important:** The Stability AI tool outputs `files` (an array of image file objects), not `text`. The end node must declare the output as type `array[file]`.

```yaml
app:
  description: "Enhances a user description into a detailed image prompt, then generates the image using Stability AI."
  icon: "\U0001F3A8"
  icon_background: "#F3E5F5"
  mode: workflow
  name: AI Image Generator
dependencies:
  - current_identifier: null
    type: marketplace
    value:
      marketplace_plugin_unique_identifier: "langgenius/stability:0.0.2/stability"
features: {}
kind: app
version: "0.1.3"
workflow:
  conversation_variables: []
  environment_variables: []
  graph:
    edges:
      - data:
          isInIteration: false
          sourceType: start
          targetType: llm
        id: "1718300000001-source-1718300000002-target"
        source: "1718300000001"
        sourceHandle: source
        target: "1718300000002"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: llm
          targetType: tool
        id: "1718300000002-source-1718300000003-target"
        source: "1718300000002"
        sourceHandle: source
        target: "1718300000003"
        targetHandle: target
        type: custom
        zIndex: 0
      - data:
          isInIteration: false
          sourceType: tool
          targetType: end
        id: "1718300000003-source-1718300000004-target"
        source: "1718300000003"
        sourceHandle: source
        target: "1718300000004"
        targetHandle: target
        type: custom
        zIndex: 0
    nodes:
      - data:
          desc: ""
          title: Start
          type: start
          variables:
            - label: Image Description
              max_length: 1000
              options: []
              required: true
              type: text-input
              variable: description
            - label: Art Style
              max_length: 100
              options:
                - photorealistic
                - digital art
                - oil painting
                - watercolor
                - anime
              required: false
              type: select
              variable: style
        height: 90
        id: "1718300000001"
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

      - data:
          desc: "Rewrite the user's description into a detailed, high-quality image generation prompt."
          model:
            completion_params:
              max_tokens: 512
              temperature: 0.7
            mode: chat
            name: gpt-4o-mini
            provider: openai
          prompt_template:
            - id: prompt-enhance-system
              role: system
              text: |
                You are a professional image prompt engineer. Convert the user's brief description into a detailed, high-quality image generation prompt optimized for Stable Diffusion.

                Style requested: {{#1718300000001.style#}}

                Rules:
                - Include lighting conditions, camera angle, mood, and atmospheric details
                - Add technical quality terms: "8K", "highly detailed", "sharp focus", "professional photography"
                - Include the art style prominently
                - Output ONLY the prompt — no explanation, no quotes
                - Keep the prompt under 200 words
            - id: prompt-enhance-user
              role: user
              text: "Convert this description into an image prompt: {{#1718300000001.description#}}"
          title: Enhance Prompt
          type: llm
          vision:
            enabled: false
        height: 98
        id: "1718300000002"
        position:
          x: 380
          y: 282
        positionAbsolute:
          x: 380
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244

      - data:
          desc: "Generate the image from the enhanced prompt using Stability AI."
          provider_id: langgenius/stability/stability
          provider_name: Stability AI
          provider_type: builtin
          title: Generate Image
          tool_configurations: {}
          tool_name: text2image
          tool_parameters:
            prompt:
              type: mixed
              value: "{{#1718300000002.text#}}"
          type: tool
        height: 90
        id: "1718300000003"
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

      - data:
          desc: ""
          outputs:
            - label: Generated Image
              name: image
              type: array[file]
              value_selector:
                - "1718300000003"
                - files
          title: End
          type: end
        height: 54
        id: "1718300000004"
        position:
          x: 980
          y: 282
        positionAbsolute:
          x: 980
          y: 282
        selected: false
        sourcePosition: right
        targetPosition: left
        type: custom
        width: 244
```

**Output variable:** `{{#1718300000003.files#}}` — array of generated image file objects. The end node's output type is `array[file]` to match this.

---

## Plugin vs HTTP Node Decision Matrix

Use this matrix to determine whether to use a plugin tool node or a raw HTTP node:

| Scenario | Recommended Approach |
|---|---|
| Plugin exists in Dify marketplace for the service | Plugin tool node |
| Custom or private internal API | HTTP node |
| Plugin exists but does not expose needed parameters | HTTP node to the same API |
| Need custom authentication flow (OAuth PKCE, multi-step) | HTTP node |
| Need custom request headers or non-standard body format | HTTP node |
| Standard services: search, scraping, image gen, code exec | Plugin tool node |
| Prototype speed matters more than maintenance | Plugin tool node |
| Full control over retry, timeout, and header logic required | HTTP node |

**Rule:** When in doubt, use a plugin. Plugins eliminate credential management from YAML, are maintained by the Dify team, and produce more readable DSL. HTTP nodes are appropriate when plugins do not exist or cannot satisfy the specific API requirements.

See also: `docs/nodes/http.md` for HTTP node configuration when no plugin exists.

---

## Common Mistakes

### Using the wrong `provider_id` format

**Wrong:** `provider_id: brave` or `provider_id: langgenius/brave`
**Correct:** `provider_id: langgenius/brave/brave`

The `provider_id` always uses the three-segment format: `author/plugin-name/plugin-name`. The plugin name is repeated in the third segment.

### Using `provider_type: plugin` instead of `builtin`

**Wrong:** `provider_type: plugin`
**Correct:** `provider_type: builtin`

All marketplace plugins use `provider_type: builtin` in tool node YAML, regardless of their installation source.

### Referencing the wrong output field

Different plugins have different output fields:
- Most tool plugins output `text` — reference as `{{#node_id.text#}}`
- Stability AI and image tools output `files` — reference as `{{#node_id.files#}}`
- Some tools output `json` — reference the specific field path

Always verify the output field name in `docs/features/plugins-marketplace.md` before wiring.

### Omitting the `dependencies` block

A DSL file that uses plugins but omits the `dependencies` block will import without errors but will not warn the importer about missing plugins. Always include the `dependencies` block for every marketplace plugin referenced in the DSL.

### Embedding credentials in YAML

**Wrong:** Setting an API key in `tool_configurations` or `tool_parameters`
**Correct:** Credentials are configured in workspace **Settings → Plugin Credentials** and never appear in DSL YAML

Plugin authentication is entirely workspace-managed. DSL files are credential-free by design.

---

## Multi-Plugin Wiring Example

When a workflow uses more than one plugin, list all plugins in the `dependencies` block and add one tool node per plugin. See `docs/patterns/parallel-execution.md` for an example that runs Brave Search and Jina Reader in parallel, and `docs/patterns/agentic-pattern.md` for an agent node that can call multiple plugins autonomously based on LLM decisions.

See also:
- `docs/features/plugins-marketplace.md` — complete plugin catalog with provider IDs, tool names, and output fields
- `docs/nodes/tool.md` — full tool node DSL field reference
- `docs/patterns/agentic-pattern.md` — wiring plugins into agent nodes for dynamic tool selection
- `docs/patterns/error-handling.md` — adding fail-branch to tool nodes when plugin availability matters
