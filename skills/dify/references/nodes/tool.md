# Tool Node

## Overview

The tool node invokes an external tool — either a Dify marketplace plugin or a built-in tool — as a step in the workflow. Tools extend what a workflow can do beyond language model inference: they provide web search, web scraping, code execution, data lookup, and integration with external services. The tool node wraps the tool call, passes in parameters, and exposes the tool's output as a variable for downstream nodes.

Tool nodes are how you give Dify workflows access to real-time information, live APIs, and capabilities that LLMs alone cannot provide.

## Tool Types

**Marketplace plugins** are tools published to the Dify plugin marketplace and installed into your workspace. Examples include Brave Search, Firecrawl, Serper, Jina Reader, and DuckDuckGo.

**Built-in tools** are tools bundled with Dify itself, such as the Wikipedia tool, current datetime tool, or math tools.

Both types are invoked using the same tool node structure. The only difference is in the `provider_name` and `tool_name` values.

## Required Configuration

| Field | Description |
|-------|-------------|
| `provider_type` | Either `builtin` or `api` (for marketplace plugins) |
| `provider_id` | The plugin/provider identifier |
| `tool_name` | The specific tool within that provider |
| `tool_parameters` | Key-value pairs of the tool's input parameters |

## Common Marketplace Tools

### Brave Search

Searches the web using Brave's privacy-focused search index. Best for general web search with good freshness.

| Config | Value |
|--------|-------|
| `provider_id` | `brave` |
| `tool_name` | `brave_search` |
| Key parameter | `query` (string) — the search query |

### Firecrawl

Scrapes a URL and returns its content as clean Markdown. Best for extracting full page content from a known URL.

| Config | Value |
|--------|-------|
| `provider_id` | `firecrawl` |
| `tool_name` | `scrape` |
| Key parameter | `url` (string) — the URL to scrape |

### Serper

Google search API wrapper. Returns search results including snippets, links, and knowledge graph data.

| Config | Value |
|--------|-------|
| `provider_id` | `serper` |
| `tool_name` | `serper_search` |
| Key parameter | `q` (string) — the search query |

### Jina Reader

Converts a URL to clean, LLM-friendly text using Jina AI's reader service.

| Config | Value |
|--------|-------|
| `provider_id` | `jina` |
| `tool_name` | `jina_reader` |
| Key parameter | `url` (string) — the URL to read |

### DuckDuckGo Search

Free, no-API-key-required web search. Lower rate limits than Brave or Serper.

| Config | Value |
|--------|-------|
| `provider_id` | `ddg` |
| `tool_name` | `ddg_search` |
| Key parameter | `query` (string) — the search query |

## Authentication

Tool credentials (API keys, tokens) are configured in your Dify workspace under **Settings → Tools**, not in the DSL. When you generate or share a DSL file, credentials are never embedded. This means:

- The DSL is safe to share without exposing secrets
- Credentials must be configured separately in each workspace that runs the DSL
- If a tool's credentials are not configured, the tool node will fail at runtime with an authentication error

## Output Variables

Tool outputs vary by tool. Most tools return either:

- A `text` variable (string) — for search results and web content
- Structured JSON data — for tools that return structured records

Check the tool's documentation in the Dify marketplace for its exact output schema. For search tools, `text` typically contains formatted search results. For scraping tools, `text` contains the page's Markdown content.

Reference output as `{{#tool_node_id.text#}}` for text output, or `{{#tool_node_id.json#}}` for structured output.

## Complete YAML Example: Brave Search

```yaml
- id: web_search
  type: tool
  data:
    title: Search the Web
    provider_type: builtin
    provider_id: brave
    provider_name: Brave Search
    tool_name: brave_search
    tool_label: Brave Search
    tool_parameters:
      query:
        type: mixed
        value: "{{#start.user_query#}}"
    error_strategy: fail-branch
```

## Example: Firecrawl Scrape

```yaml
- id: scrape_page
  type: tool
  data:
    title: Scrape Web Page
    provider_type: builtin
    provider_id: firecrawl
    provider_name: Firecrawl
    tool_name: scrape
    tool_label: Firecrawl Scrape
    tool_parameters:
      url:
        type: mixed
        value: "{{#start.target_url#}}"
    error_strategy: fail-branch
```

## Error Handling

Tools can fail due to network errors, API rate limits, authentication failures, or invalid parameters. Configure the `error_strategy` field to control behavior on failure:

- `fail-branch`: Route to a separate error-handling branch instead of stopping the workflow
- `default-value`: Return a predefined default output value on failure

To use `fail-branch`, add a conditional edge from the tool node's error output port to a recovery path (such as an answer node that says "Search is temporarily unavailable").

```yaml
edges:
  - source: web_search
    target: process_results
    sourceHandle: "true"
  - source: web_search
    target: search_error_handler
    sourceHandle: "false"
```

## Pattern: Web Search → LLM Analysis

```yaml
nodes:
  - id: start
    type: start
    data:
      variables:
        - variable: user_query
          type: string

  - id: web_search
    type: tool
    data:
      provider_id: brave
      tool_name: brave_search
      tool_parameters:
        query:
          type: mixed
          value: "{{#start.user_query#}}"
      error_strategy: fail-branch

  - id: analyze
    type: llm
    data:
      prompt_template:
        - role: user
          text: |
            Based on these search results:
            {{#web_search.text#}}

            Answer: {{#start.user_query#}}
```

## Common Mistakes

1. **Embedding API keys in the DSL.** Never put credentials in the `tool_parameters` or anywhere in the YAML. Configure credentials in the workspace settings. The DSL will not work with hardcoded keys and poses a security risk.

2. **Using the wrong provider_id or tool_name.** These values are case-sensitive and must exactly match the plugin's registered identifiers. Check the tool's marketplace page or installed tool settings for the correct values.

3. **Not enabling fail-branch for unreliable tools.** Web search and scraping tools can fail intermittently. Without `fail-branch`, a single tool failure stops the entire workflow. Always add error handling for external tool calls.

4. **Assuming text output format.** Some tools return JSON objects rather than plain strings. If you pass a JSON output directly to an LLM prompt, the model may receive a raw JSON string. Use a template-transform or code node to extract the fields you need.

5. **Exceeding rate limits without retry logic.** If your workflow runs frequently or in parallel, tool API rate limits can be hit. Consider adding a code node with retry logic or spreading calls with sequential processing instead of parallel iteration.
