# Dify DSL Generator Plugin

## Purpose

This is a Claude Code plugin that generates Dify DSL YAML files — specifically chatflows and workflows — that are ready to import directly into a Dify instance. Rather than requiring users to understand the full Dify YAML schema, the plugin uses a conversational, multi-agent pipeline to gather requirements, research integrations, plan node graphs, craft LLM prompts, and assemble production-ready YAML output.

The plugin is designed for developers, product managers, and AI practitioners who want to build Dify applications quickly without manually authoring complex DSL files. It handles the full lifecycle: from understanding what the user wants to build, through research and planning, to generating validated, importable YAML.

## How to Use

Invoke the plugin by typing `/dify` in Claude Code and describing what you want to build in natural language. For example:

- `/dify` — "Build a customer support chatbot that searches our product FAQ knowledge base and escalates to a human agent via Slack when it can't answer."
- `/dify` — "Create a document summarization workflow that accepts a PDF, extracts key points, and posts a summary to Notion."

The `/dify` skill will guide you through a structured conversation, asking clarifying questions where needed, and then spawn a series of specialized sub-agents to handle each phase of the generation process. At the end, you will receive a complete YAML file ready to import into Dify.

## Mandatory Agent Pipeline

CRITICAL: When executing the /dify skill, Claude MUST always spawn agents in this EXACT sequence. No steps may be skipped unless the condition for that agent is explicitly not met (see conditions below):

1. **concept-ideator** — always first, for every forward-direction request. Aggressively expands the user's idea (however thin) into a rich **App Concept Proposal**: vision, a generous set of inputs (with valid Dify input types), multiple output types, and optional creative features. MUST be shown to the user, who confirms or edits it, BEFORE the pipeline continues. Does not run for reverse-direction (explain/review) requests.

2. **requirements-analyzer** — runs after the confirmed concept; determines app type (chatflow vs workflow), identifies required integrations, knowledge bases, and error handling needs. Produces a structured requirements document that all subsequent agents consume.

3. **plugin-finder** — runs if any external service is mentioned (e.g., Slack, Notion, GitHub, SendGrid). Searches the Dify marketplace for an existing plugin before any API research is done. If a plugin exists, it is used instead of a raw HTTP integration.

4. **api-researcher** — runs only if no Dify marketplace plugin was found for a required external service. Researches the external API: authentication method, relevant endpoints, request/response shapes, and rate limits.

5. **integration-builder** — runs only if api-researcher was used. Translates the API research into Dify HTTP node configurations, including headers, body templates, and variable mappings.

6. **knowledge-architect** — runs if the requirements include a knowledge base or RAG (Retrieval-Augmented Generation) component. Designs the knowledge retrieval strategy: dataset selection, retrieval mode, top-k settings, and score threshold.

7. **node-planner** — always runs. Produces a complete node graph plan: node types, names, connections, variable passing, and branching logic. MUST show this plan to the user and WAIT FOR EXPLICIT APPROVAL before proceeding. Do not continue to the next step until the user confirms the plan.

8. **prompt-engineer** — always runs. For every LLM node identified in the approved plan, crafts a system prompt and user prompt template following Dify prompt best practices. Prompts are context-aware and use Jinja2 variable syntax for dynamic inputs.

9. **error-strategy** — runs if the plan contains any HTTP nodes, tool nodes, or external API calls. Designs error handling: retry logic, fallback branches, user-facing error messages, and logging strategy.

10. **dsl-generator** — always runs. This is the only agent that produces YAML output. It assembles all inputs from previous agents into a complete, valid Dify DSL YAML file following the current schema. It generates unique node IDs, sets correct node positions for the canvas, and structures the file for immediate import.

11. **dsl-validator** — fires automatically via the post-write hook whenever a YAML file is written to the `output/` directory, but is also invoked manually if validation fails or the user requests re-validation. Runs `skills/dify/scripts/validate_workflow.py` and reports any schema errors, missing required fields, or broken node references.

**Reverse-direction agents** — run instead of the forward pipeline when the user provides an existing DSL file to explain or review:

- **dsl-explainer** (`skills/dify/agents/dsl-explainer.md`) — reads an existing DSL YAML and produces a plain-language walkthrough, a Visual Flow Diagram (Mermaid), and a node-by-node explanation. Triggered when the user says "explain", "what does this do", "walk me through", etc.
- **dsl-reviewer** (`skills/dify/agents/dsl-reviewer.md`) — audits an existing DSL YAML for security, reliability, prompt quality, and design anti-patterns. Triggered when the user says "review", "audit", "what's wrong with", etc.

## Rules

- NEVER generate YAML directly inside the `/dify` skill itself — the dsl-generator agent is solely responsible for all YAML output. Generating YAML outside this agent breaks the validation pipeline and produces inconsistent results.
- ALWAYS show the node plan (produced by node-planner) to the user before generating any YAML, and WAIT for the user to explicitly approve it. The user may request changes, which cause node-planner to revise and re-present the plan.
- ALWAYS check for Dify marketplace plugins (via plugin-finder) before researching external APIs. Plugins are preferred because they are officially maintained, use standardized auth, and avoid raw HTTP node complexity.
- NEVER embed API keys, secrets, or credentials in generated YAML. All sensitive values must reference environment variables using the `{{env.VARIABLE_NAME}}` syntax supported by Dify.
- ALWAYS use the `skills/dify/scripts/generate_id.py` utility when creating node IDs to ensure they conform to the required format and are collision-free.
- ALWAYS run `skills/dify/scripts/format_yaml.py` on the output before presenting it to the user to ensure consistent indentation and field ordering.
- ALWAYS run ALL Python scripts using the project virtual environment — never the global Python installation. The venv is at `.venv/` in this directory. Correct invocation: `.venv/Scripts/python skills/dify/scripts/validate_workflow.py [args]`. Never use `python` or `python3` bare commands.
- ALWAYS update `CHANGELOG.md` under the `## [Unreleased]` section after making any change to agent files, reference docs, scripts, hooks, or skill configuration. Use Keep-a-Changelog format: Added / Changed / Fixed / Removed sub-sections.

## Project Structure

- `skills/dify/` — contains the `/dify` skill entry point (`SKILL.md`), all reference documentation (`references/`), ground-truth YAML examples (`assets/`), agent definitions (`agents/`), Python utility scripts (`scripts/`), post-write hooks (`hooks/`), and test suite (`tests/`). This is the fully self-contained skill folder that follows the agentskills.io standard.
- `skills/dify/agents/` — contains 14 specialized agent definition files. Forward-pipeline agents: concept-ideator, requirements-analyzer, plugin-finder, api-researcher, integration-builder, knowledge-architect, dummy-data-generator, node-planner, prompt-engineer, error-strategy, dsl-generator, dsl-validator. Reverse-direction agents (run when the user provides an existing DSL file): dsl-explainer, dsl-reviewer.
- `skills/dify/hooks/` — contains the post-write hook that auto-triggers dsl-validator whenever a YAML file is saved to `output/`. Ensures no invalid DSL is silently produced.
- `skills/dify/scripts/` — Python utility scripts: `generate_id.py` (UUID generation in Dify node format), `validate_workflow.py` (schema and reference validation), `format_yaml.py` (YAML normalization and formatting), `preview_graph.py` (Mermaid flowchart preview from a DSL file), `fix_assets.py` (batch-fix common structural issues in YAML asset files). Always run via `.venv/Scripts/python`.
- `skills/dify/references/` — reference documentation organized by category: node types, LLM configuration, DSL schema, common patterns, and Dify marketplace plugin information. Agents consult these docs during generation.
- `skills/dify/assets/` — example YAML files and templates organized into `chatflows/`, `workflows/`, and `templates/` subdirectories. These serve as ground-truth examples that dsl-generator uses as structural references.
- `docs/` — implementation plans and design specs. `docs/plans/` holds pre-implementation plans for multi-file features (write a plan here before starting any complex multi-file change; delete the plan file once the work is fully done). `docs/superpowers/` holds design specs generated by Superpowers skill sessions.
- `.venv/` — project-local Python virtual environment. All Python execution must use `.venv/Scripts/python`. Run `python -m venv .venv` to recreate if missing, then `pip install pyyaml pytest` to install dependencies.
- `TODO.md` — tracked improvement tasks for the plugin. Check this file to see what's pending and mark items complete as work is done.
- `CHANGELOG.md` — record of all changes to the plugin. Always update this after making any change to agent files, reference docs, scripts, hooks, or skill configuration.

## Documentation Reference

- Node types: `skills/dify/references/nodes/` — one file per node type covering required fields, optional fields, and configuration examples.
- LLM configuration: `skills/dify/references/config/llm-settings.md` — covers model selection, temperature, max tokens, context window, and vision settings.
- Schema reference: `skills/dify/references/schema/` — the authoritative DSL schema for both chatflow and workflow formats, including top-level fields and node-level fields.
- Common patterns: `skills/dify/references/patterns/` — reusable design patterns such as RAG pipelines, tool-use loops, human-in-the-loop branching, and multi-step classification.
- Plugin info: `skills/dify/references/features/plugins-marketplace.md` — how to discover, reference, and configure Dify marketplace plugins within a DSL file.

## Sources

- Official Dify documentation: https://docs.dify.ai
- Ground-truth YAML examples that reflect actual importable DSL structure: `skills/dify/assets/workflows/` and `skills/dify/assets/chatflows/`
- When documentation is insufficient or outdated, agents may use WebFetch to retrieve current documentation from docs.dify.ai or raw.githubusercontent.com.
