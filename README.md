# Dify DSL Generator

A Claude Code plugin that generates production-ready Dify DSL YAML files through a conversational, multi-agent pipeline. Describe what you want to build — the plugin handles requirements analysis, integration research, node planning, prompt engineering, and YAML generation, producing a file you can import directly into Dify.

---

## What It Does

Dify applications are defined by YAML DSL files that describe node graphs, LLM configurations, integrations, and conversation logic. Authoring these files by hand requires deep knowledge of the schema, node types, and Dify-specific conventions.

This plugin eliminates that barrier. You describe your use case conversationally, and a pipeline of specialized agents handles every step:

- Analyzes your requirements and determines whether to build a chatflow or workflow
- Searches the Dify marketplace for existing plugins before resorting to raw API integration
- Researches external APIs when no plugin is available and builds HTTP node configurations
- Designs knowledge base retrieval strategies for RAG use cases
- Plans the full node graph and presents it for your approval before generating anything
- Engineers system and user prompts for every LLM node
- Designs error handling and fallback logic for external calls
- Generates a complete, validated YAML file ready for immediate import

---

## Installation

### Method 1: Claude Code Marketplace

Search for "dify" in the Claude Code plugin marketplace and install directly. The plugin is available under the name `dify-dsl-generator`.

### Method 2: Local Development Install

Clone this repository and add it as a local plugin:

```bash
git clone https://github.com/dify-plugin/dify-dsl-generator.git
cd dify-dsl-generator
claude plugin install --local .
```

### Method 3: Project Clone

Copy the plugin into your project's `.claude/plugins/` directory to make it available only within that project:

```bash
cd your-project
git clone https://github.com/dify-plugin/dify-dsl-generator.git .claude/plugins/dify-dsl-generator
```

---

## Quick Start

1. Open Claude Code in any project directory.
2. Type `/dify` and press Enter.
3. Describe what you want to build:

```
/dify

I want to build a customer support chatbot that:
- Searches our product documentation knowledge base
- Answers questions using GPT-4o
- Escalates unresolved issues to our Slack #support channel
- Logs all conversations to a Notion database
```

4. The pipeline will ask any clarifying questions, then present a node plan for your approval.
5. After you approve, it generates the YAML and saves it to `output/`.
6. Import the file into Dify via Settings > DSL Import.

---

## Agent Pipeline

The plugin executes a fixed 10-step pipeline for every generation request:

```
User: /dify "build a support chatbot with Slack escalation"
       |
       v
[1] requirements-analyzer
       Determines: chatflow, needs Slack plugin, needs knowledge base
       |
       v
[2] plugin-finder
       Finds: official Slack plugin on Dify marketplace
       |
       v (no plugin found path)
[3] api-researcher ---------> [4] integration-builder
       Research external API        Build HTTP node config
       |
       v
[5] knowledge-architect
       Designs: RAG retrieval strategy, top-k, score threshold
       |
       v
[6] node-planner
       Produces node graph plan --> SHOWS TO USER --> WAITS FOR APPROVAL
       |
       v (after user approves)
[7] prompt-engineer
       Writes system + user prompts for every LLM node
       |
       v
[8] error-strategy
       Designs retry logic, fallback branches, error messages
       |
       v
[9] dsl-generator
       Assembles complete YAML DSL file --> writes to output/
       |
       v
[10] dsl-validator (auto-triggered by hook)
       Validates schema, node references, required fields
       |
       v
    output/your_chatbot_YYYYMMDD_HHMMSS.yaml
    (ready to import into Dify)
```

Steps 3, 4, 5, and 8 are conditional — they only run when the relevant components are present in your requirements. Steps 1, 6, 7, 9, and 10 always run.

---

## Directory Structure

```
dify-dsl-generator/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest (name, version, author, license)
├── skills/
│   └── dify/
│       ├── SKILL.md             # /dify skill entry point (with YAML frontmatter)
│       ├── references/          # Reference documentation for agents
│       │   ├── nodes/           # Per-node-type reference docs (20 files)
│       │   ├── config/          # LLM and app configuration
│       │   ├── schema/          # DSL schema reference
│       │   ├── patterns/        # Reusable design patterns
│       │   ├── features/        # Plugins, tools, knowledge bases
│       │   ├── api/             # Dify API reference
│       │   └── setup/           # Setup and installation guides
│       └── assets/              # Ground-truth YAML examples
│           ├── chatflows/       # Example chatflow YAML files
│           ├── workflows/       # Example workflow YAML files
│           └── templates/       # Minimal starter templates
├── agents/
│   ├── requirements-analyzer.md
│   ├── plugin-finder.md
│   ├── api-researcher.md
│   ├── integration-builder.md
│   ├── knowledge-architect.md
│   ├── node-planner.md
│   ├── prompt-engineer.md
│   ├── error-strategy.md
│   ├── dsl-generator.md
│   └── dsl-validator.md
├── hooks/
│   └── post-write-validate.sh   # Auto-validation hook
├── scripts/
│   ├── generate_id.py           # Node ID generation
│   ├── validate_workflow.py     # Schema validation
│   └── format_yaml.py           # YAML normalization
├── tests/                       # Pytest suite (91 tests)
├── settings.json                # Plugin permissions
├── CLAUDE.md                    # Agent instructions and rules
├── LICENSE                      # MIT
├── README.md                    # This file
└── CHANGELOG.md                 # Version history
```

---

## Requirements

- **Claude Code** — version 1.0 or later, with plugin support enabled
- **Dify instance** — self-hosted or Dify Cloud account for importing and running the generated YAML files
- **Python 3.8+** — required for the validation and utility scripts (`scripts/`)
- **Internet access** — the plugin fetches current documentation from docs.dify.ai when needed and searches the Dify marketplace for plugins

---

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request for significant changes. See `skills/dify/references/` for the reference materials agents use during generation — improving these docs directly improves generation quality.

---

## License

MIT
