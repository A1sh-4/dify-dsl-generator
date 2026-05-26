# Plugin Installation Guide

This document covers how to install the Dify DSL Generator plugin for Claude Code, verify the installation, and keep the plugin updated.

## Prerequisites

Before installing, make sure you have the following:

- **Claude Code CLI** installed. Install it with:
  ```bash
  npm install -g @anthropic-ai/claude-code
  ```
  Alternatively, use the Claude Code desktop app which includes the CLI.
- **Access to a Dify instance** — either Dify Cloud (app.dify.ai) or a self-hosted Dify deployment. See `skills/dify/references/setup/dify-setup.md` for instructions on getting Dify running.
- **Python 3.8 or later** — required to run the validation and utility scripts in the `scripts/` directory. Verify your Python version with:
  ```bash
  python --version
  # or
  python3 --version
  ```

---

## Installation Methods

There are three ways to install this plugin depending on your setup and workflow.

### Method 1: Claude Code Plugin Marketplace (Recommended when available)

Once the plugin is published to the Claude Code marketplace, this is the easiest installation path.

```bash
# Search for the plugin in the marketplace
claude /plugin search dify

# Install it
claude /plugin install dify
```

After installation, the plugin is globally available in all Claude Code sessions. No path configuration is needed.

### Method 2: Local Development Install

Use this method if you have cloned the repository locally and want to load it as a plugin without publishing it. You point Claude Code at the plugin directory directly.

```bash
# Point Claude Code at the plugin directory
claude --plugin-dir /path/to/DIFY_DSL_Generator

# Or set the environment variable and then launch Claude normally
export CLAUDE_PLUGIN_DIR=/path/to/DIFY_DSL_Generator
claude
```

On Windows (PowerShell):
```powershell
$env:CLAUDE_PLUGIN_DIR = "C:\path\to\DIFY_DSL_Generator"
claude
```

When Claude Code starts with a plugin directory specified, it reads the `plugin.json` manifest from `.claude-plugin/plugin.json` and registers all skills, agents, and hooks defined there.

### Method 3: Direct Project Use

The simplest approach for immediate use: clone the repository and open it as a Claude Code project. Claude Code automatically loads `CLAUDE.md` from the project root, which contains the full plugin instructions.

```bash
git clone https://github.com/your-org/dify-plugin
cd dify-plugin
claude .
```

When you run `claude .` from the plugin directory, the `CLAUDE.md` file is automatically read and the `/dify` skill becomes available for the duration of that session. This method requires no installation step and is ideal for trying the plugin before committing to a permanent install.

---

## Verifying the Installation

After installing with any of the three methods above, open Claude Code and type:

```
/dify
```

You should see a welcome message asking what kind of Dify application you want to build. If the skill loads correctly, it will greet you and prompt you to describe your use case in natural language.

If the skill does not respond, work through the troubleshooting section below.

---

## Updating the Plugin

Keep the plugin current to get the latest node type support, schema updates, and bug fixes.

- **Method 1 (marketplace):**
  ```bash
  claude /plugin update dify
  ```

- **Methods 2 and 3 (local clone):**
  ```bash
  git pull
  ```
  Pull from the repository root. If you are using `--plugin-dir`, restart Claude Code after pulling so the updated files are reloaded.

---

## Uninstalling the Plugin

- **Method 1 (marketplace):**
  ```bash
  claude /plugin remove dify
  ```

- **Method 2 (environment variable or flag):** Remove the `CLAUDE_PLUGIN_DIR` environment variable or stop passing `--plugin-dir` when launching Claude Code. The plugin files remain on disk but are no longer loaded.

- **Method 3 (direct project use):** Simply stop opening Claude Code from the plugin directory. If you want to remove the files entirely, delete the cloned repository folder.

---

## Troubleshooting

**Plugin not found when searching the marketplace**
The plugin may not yet be published. Use Method 2 or 3 instead.

**`/dify` command is not recognized**
- Verify `skills/dify.md` exists in the plugin directory.
- Verify `.claude-plugin/plugin.json` exists and contains a valid skills entry for `dify`.
- If using `--plugin-dir`, confirm the path points to the directory that contains `.claude-plugin/`, not to `.claude-plugin/` itself.

**Permission errors when running**
Open `settings.json` in the plugin root and confirm the `permissions` block includes the required allowances for Bash tool calls and file writes. Refer to the `settings.json` file in the repository root for the reference permissions configuration.

**Python script errors (validate_workflow.py, generate_id.py, format_yaml.py)**
- Run `python --version` or `python3 --version` to confirm Python 3.8+ is installed.
- If `python` points to Python 2, update your PATH or use `python3` explicitly.
- The scripts have no external dependencies beyond the Python standard library, so no `pip install` step is required.

**CLAUDE.md not being read (Method 3)**
Make sure you launch Claude Code from the plugin directory root (`claude .`), not from a subdirectory. The `CLAUDE.md` file must be at the top level of the directory Claude Code opens.
