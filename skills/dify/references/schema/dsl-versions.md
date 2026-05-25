# Dify DSL Version Reference

## Overview

Dify DSL files include a `version` field that controls which features are available and how the file is parsed. The version must always be a **quoted string** in YAML — never an unquoted number. The `kind: app` field is also required and must always be exactly `app`.

---

## Version History

### v0.1 — Early Version

- Basic workflow support
- Limited node types (LLM, code, HTTP, end)
- Simple edge structure without extended metadata
- No plugin dependency system
- Primarily used for simple linear workflows

### v0.3 — Stable Baseline

- Used by many existing workflows in the wild
- Supports most standard node types
- Basic plugin system support
- Stable enough for production workflows without advanced features
- Compatible with a wide range of self-hosted Dify deployments

### v0.6 — Current Recommended Version

- Full plugin dependency system (`dependencies` block) for declaring marketplace plugins
- Extended trigger node types: webhook and schedule triggers
- Structured output support for LLM nodes
- Parallel iteration mode (run iteration body steps concurrently)
- Full conversation variable system with variable-assigner node support
- Human input node support for human-in-the-loop workflows
- Recommended for all new workflows

---

## Compatibility Notes

- Always use `version: '0.1'` as the quoted string value in the YAML header — even for workflows that use v0.6 features. Verify this against your reference YAML files, as the version field value in the file header may differ from the feature set version designation.
- The `kind: app` field is required and must always be exactly the string `app`.
- Dify Cloud always runs the latest available version and supports all features.
- Self-hosted deployments: check your installed Dify version to ensure the features you use are supported. Deploying a DSL that uses v0.6 features (e.g. the `dependencies` block or parallel iteration) on an older self-hosted instance will cause import errors.

---

## Recommended YAML Header

Every Dify DSL file should begin with this header structure:

```yaml
app:
  description: ''
  icon: '🤖'
  icon_background: '#FFEAD5'
  mode: advanced-chat   # or: workflow
  name: 'My App'
  use_icon_as_answer_icon: false
kind: app
version: '0.1'
```

### Field notes

| Field | Required | Notes |
|---|---|---|
| `app.description` | No | Short human-readable description of the app |
| `app.icon` | No | Emoji character used as the app icon |
| `app.icon_background` | No | Hex color string for the icon background |
| `app.mode` | Yes | Either `advanced-chat` (chatflow) or `workflow` |
| `app.name` | Yes | Display name of the app |
| `app.use_icon_as_answer_icon` | No | Whether to show the icon in chat responses |
| `kind` | Yes | Always `app` — never change this |
| `version` | Yes | Always a quoted string, e.g. `'0.1'` |

---

## The `dependencies` Block

Used in v0.6+ workflows for declaring required marketplace plugins. This block appears at the top level of the DSL file alongside `kind` and `version`.

```yaml
dependencies:
  - current_identifier: ''
    type: marketplace
    value:
      author: langgenius
      name: brave_search
      version: 0.0.1
```

### Field notes for each dependency entry

| Field | Description |
|---|---|
| `current_identifier` | Internal identifier string; leave as empty string `''` if not assigned |
| `type` | Always `marketplace` for Dify marketplace plugins |
| `value.author` | The plugin author's handle on the Dify marketplace |
| `value.name` | The plugin's slug name on the marketplace |
| `value.version` | The exact semantic version string of the plugin to use |

Multiple dependencies are listed as additional array entries under `dependencies`. If a workflow uses no plugins, the `dependencies` block can be omitted entirely.
