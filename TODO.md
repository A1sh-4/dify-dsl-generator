# TODO — Dify DSL Generator Plugin

Track improvement tasks here. Check items off as they are completed. Add new items at the bottom of each section.

---

## Completed

- [x] Add **Concept Ideation front door** — `concept-ideator` agent + SKILL.md Step 2b confirmation gate; expands any prompt into a rich App Concept Proposal (inputs/outputs/creative features) and confirms with the user before the pipeline runs. Wired into requirements-analyzer, SKILL.md Hard Rules, and CLAUDE.md (13 → 14 agents). See `docs/superpowers/specs/2026-05-30-concept-ideation-front-door-design.md`.
- [x] Initial plugin build — all 40 tasks (phases 0–15) complete
- [x] Set up `.venv` virtual environment at project root; updated `.gitignore` to exclude it
- [x] Rewrote `skills/dify/scripts/validate_workflow.py` with 14 validation checks covering all known Dify import requirements
- [x] Created 91-test pytest suite in `skills/dify/tests/test_validate_workflow.py` for full coverage of all 14 checks
- [x] Created `skills/dify/scripts/fix_assets.py` — batch-fixed 7/10 asset YAML files (LLM prompt IDs, code node format)
- [x] Fixed critical skill bug: dummy data questions were never asked because subagents can't be interactive — moved all question-asking into `skills/dify/SKILL.md` Step 4b
- [x] Updated `skills/dify/agents/node-planner.md`: added `template-transform` as near-mandatory rule, Step 2b (output presentation design), Step 2c (conversation opener HTML), `CONVERSATION SETUP` + `OUTPUT PRESENTATION` blocks in plan output format
- [x] Updated `skills/dify/agents/dsl-generator.md`: rich HTML `opening_statement` template for chatflows, full `template-transform` node YAML block, `structured_output_enabled` guidance, updated delivery checklist
- [x] Updated `skills/dify/agents/prompt-engineer.md`: Step 7 (proactive structured output decision), Step 8 (template-transform content spec), updated output format and hard constraints

---

## High Priority

- [x] Add `skills/dify/agents/dsl-explainer.md` and `skills/dify/agents/dsl-reviewer.md` — reverse-direction agents: explainer produces a plain-language walkthrough of an existing DSL; reviewer audits it for security, reliability, prompt quality, and design anti-patterns. Both wired into SKILL.md via a reverse-direction detection block.
- [x] Update `assets/templates/starter-chatflow.yml` — rich HTML placeholder with card layout, pill tags, full interactive options reference (buttons, forms, all input types, all variants)
- [x] Update `skills/dify/references/nodes/template-transform.md` — full rewrite: blank-line rendering rule, complete Jinja2 feature set (filters, groupby, set blocks, section accumulation), all output formats (HTML tables, details/summary accordion, mixed markdown+HTML), interactive forms/buttons in output, complete YAML structure, 4 practical examples
- [x] Update `assets/chatflows/*.yml` example files — add `template-transform` nodes and rich HTML `opening_statement` values to model the new patterns for `dsl-generator`

---

## Next Up — Logic Flow Diagram Feature

**Full implementation plan:** [`docs/plans/logic-flow-diagram.md`](docs/plans/logic-flow-diagram.md)
**Read that file first** — it contains everything needed to implement this feature without re-deriving anything.

### Why

When users approve the node graph plan at Step 5, the plan is dense and technical (node types,
variable references, edge handles). Users cannot easily tell if the logic matches what they
described. A plain-language Mermaid flowchart — showing what the app *does*, not what nodes it
uses — lets them confirm "yes, this is what I asked for" before YAML is generated.
Same visual is added to the reverse-mode explainer so "explain this DSL" also produces a chart.

### What changes (3 files, no new scripts)

- [x] **`skills/dify/agents/node-planner.md`** — Add `Step 8b: Generate the logic flow diagram`
  (Mermaid generation rules from the micro-step list) + add `LOGIC FLOW DIAGRAM` block to the
  output format section + change approval prompt text to "Does this flow match what you had in mind?"
  See `docs/plans/logic-flow-diagram.md` → Change 1 for the exact text to add.

- [x] **`skills/dify/agents/dsl-explainer.md`** — Add `Visual Flow Diagram` section to the output
  format, immediately after "How It Works — Step by Step" and before "Nodes — What Each One Does".
  Rules: derive labels from `data.title` in YAML, use diamond for if-else/question-classifier, use
  class names and condition descriptions as branch labels.
  See `docs/plans/logic-flow-diagram.md` → Change 2 for the exact text to add.

- [x] **`skills/dify/SKILL.md`** — One additional sentence in Step 5b after "SHOW THE PLAN TO THE USER":
  "The plan includes a `LOGIC FLOW DIAGRAM` section near the bottom — draw the user's attention
  to this chart and ask them to confirm the flow makes sense before approving."
  See `docs/plans/logic-flow-diagram.md` → Change 3 for the exact location.

### Verification

After all 3 edits: run `/dify Build a customer support chatbot that answers billing and technical
support questions` and confirm the Step 5 plan output contains a `LOGIC FLOW DIAGRAM` Mermaid
block with plain-language labels (no "llm", no "template-transform", no `{{#...#}}` syntax).

---

## Asset Ground-Truth Validation

Each item below requires building the workflow in Dify, exporting the DSL, and providing the file path so the asset can be corrected and the skill updated to match.

**Already done:**

- [x] `assets/workflows/simple-llm.yml` — Start → LLM → End
- [x] `assets/workflows/conditional-routing.yml` — Start → IF/ELSE → 2 LLM branches → Variable Aggregator → End

**Remaining workflows to build and export:**

- [ ] **`assets/workflows/rag-pipeline.yml`** — RAG workflow
  - Nodes: Start (paragraph input `user_question`) → Knowledge Retrieval (pick any dataset) → LLM (context enabled, `{{#context#}}` in user prompt) → End (output `text` from LLM)
  - Key things to validate: `single_retrieval_config` structure, `context.variable_selector` format, knowledge retrieval node fields

- [x] **`assets/workflows/error-handling.yml`** — HTTP node with error branch
  - Nodes: Start (paragraph input `user_input`) → HTTP Request (any dummy URL, e.g. `https://httpbin.org/post`) → [success branch] LLM → End; [fail branch] LLM (error message generator) → End
  - Key things to validate: HTTP node field structure, fail-branch edge `sourceHandle`, error variable references

- [x] **`assets/workflows/schedule-triggered.yml`** — Schedule Trigger → LLM → End (new asset, ground-truth export confirmed `trigger-schedule` node type, `cron_expression`+`mode`+`timezone`+`config` block structure)

- [ ] **`assets/workflows/webhook-triggered.yml`** — Webhook Trigger + Code node + LLM
  - Nodes: Webhook Trigger (extract `payload` from body) → Code (parse payload) → LLM → End
  - **NOTE:** Dify v1.10.0+ has a real `trigger-webhook` node type — do NOT use Start node. Build using Webhook Trigger node from the canvas.
  - Key things to validate: `trigger-webhook` node DSL structure, how extracted body variables are declared, how they're referenced downstream

**Templates to verify (export a minimal version and compare):**

- [x] **`assets/templates/starter-workflow.yml`** — corrected from simple-llm.yml ground truth: Start variable type paragraph, height 111, removed desc from End node
- [x] **`assets/templates/starter-chatflow.yml`** — corrected from rag-chatflow.yml ground truth: added isInIteration to edge 1, Start height 75/width 243, LLM memory template includes sys.files, Template Transform variables structure fixed (value_type: string, correct indentation), Answer height 105/width 243, added dependencies plugin block, removed all desc fields

---

## Medium Priority

- [x] Update `skills/dify/agents/requirements-analyzer.md` — add an output format preference question (table vs card vs prose) so `node-planner` doesn't have to guess the layout type
- [x] Update `skills/dify/SKILL.md` Step 6 (prompt-engineer spawn) — explicitly pass which nodes in the plan are upstream of `template-transform` nodes so `prompt-engineer` knows which specs need the template guidance section
- [x] Update `skills/dify/agents/dsl-validator.md` — add checks for: `template-transform` node presence in chatflows, non-empty `opening_statement` in chatflows, `answer` node referencing `template_node_id.output` (not raw LLM text)
- [x] Update `skills/dify/references/nodes/llm.md` — add `structured_output` / `structured_output_enabled` field documentation with schema example and when-to-use guidance

### Audit Findings — Medium Priority (from 2026-05-26 skill audit)

- [x] **M1 — Expand SKILL.md description for reliable triggering** (`skills/dify/SKILL.md` frontmatter)
  - **What**: The skill description is too short and vague ("Generates Dify DSL YAML chatflows and workflows"). Skill descriptions are the primary triggering mechanism; if the user says "build a Dify app" or "I need a chatbot" the skill may not fire.
  - **Fix**: Rewrite the `description:` field to include trigger phrases: "build a Dify app", "create a chatflow", "I need a workflow that...", "generate DSL", "make a Dify chatbot", "automate X in Dify". Per skill-creator guidelines, descriptions should be slightly "pushy" — e.g. "Use this skill whenever the user wants to build, generate, or create anything in Dify, even if they don't say 'DSL' or 'YAML' explicitly."
  - **Why it matters**: Without rich trigger phrases, the skill under-fires. Users who type "build me a Dify FAQ bot" expect the skill to activate automatically.

- [x] **M2 — Align node-planner.md "What You Receive" with SKILL.md Step 5b inputs** (`skills/dify/agents/node-planner.md`)
  - **What**: `node-planner.md` lists only "requirements brief" in its "What You Receive" section. But `SKILL.md` Step 5b actually passes 7 items to node-planner: the requirements brief, flow decomposition answers, plugin configs (from plugin-finder), integration configs (from integration-builder), RAG design (from knowledge-architect), API brief, and the user's original description. The agent doesn't know it receives these extra inputs and may ignore them.
  - **Fix**: Update the "What You Receive" section in `node-planner.md` to list all 7 inputs and explain how each one should influence the graph design (e.g., "if plugin config is present, use `tool` nodes not `http-request` nodes for that integration").
  - **Why it matters**: When plugin-finder or knowledge-architect runs, their outputs should directly shape the graph plan. If node-planner doesn't know to look for them, it may design a less optimal graph.

- [x] **M3 — Tighten reverse-direction detection in SKILL.md** (`skills/dify/SKILL.md` reverse-direction block)
  - **What**: The reverse-direction detection triggers when the user's message contains a `.yml`/`.yaml` file OR contains the word "review". This is too broad. If the user says "let me review my requirements and build the chatflow", the skill incorrectly routes to dsl-reviewer instead of the forward-generation pipeline.
  - **Fix**: Change the condition to require BOTH: a `.yml`/`.yaml` attachment/path AND explicit review/audit intent words ("review", "audit", "explain", "what does this do", "critique"). A `.yml` file alone is not enough; a single word "review" without a YAML file is not enough.
  - **Why it matters**: False positives send users into the reverse pipeline when they wanted forward generation, causing confusion and wasted turns.

- [x] **M0 — Document custom Dify instance URL throughout the skill**
  - **What**: The Dify instance we are building for does NOT use the default cloud URL (`https://api.dify.ai/v1`). The actual base URL is `https://app-human04s.tsunagi.ai/v1` (self-hosted / private deployment). Any place in the skill, reference docs, or generated YAML that hardcodes or suggests `api.dify.ai` is wrong for this project.
  - **Fix**: Audit all reference docs and agent files for mentions of `api.dify.ai`. Update examples, setup checklists (e.g., knowledge-architect Step 8), and any HTTP node examples to use a placeholder like `https://<your-dify-domain>/v1` instead of the cloud URL. Add a note in `SKILL.md` or a new `references/config/instance-url.md` that the base URL must be confirmed before deploying any generated DSL that calls the Dify API directly.
  - **Why it matters**: If an agent or generated DSL hardcodes `api.dify.ai`, it will silently fail when imported into the `app-human04s.tsunagi.ai` instance. The URL difference also affects authentication headers and environment variable examples.

- [ ] **M4 — Align empty-retrieval handling between error-strategy and dsl-reviewer** (`skills/dify/agents/error-strategy.md` and `skills/dify/agents/dsl-reviewer.md`)
  - **What**: `error-strategy.md` says knowledge-retrieval nodes use `default-value` strategy and empty results are handled via the downstream LLM's system prompt. `dsl-reviewer.md` rule R5 flags it as HIGH severity if there is no `if-else` node after knowledge-retrieval to handle empty results. These two agents give contradictory guidance.
  - **Fix**: Pick one approach and update both files consistently. The recommended approach is the `if-else` node (aligns with dsl-reviewer): after every knowledge-retrieval node, add an `if-else` node that checks `result` length — if empty, route to a "no results" answer branch; if non-empty, route to the LLM. Update `error-strategy.md` to reflect this: knowledge-retrieval nodes use `if-else` branching, not `default-value`.
  - **Why it matters**: Inconsistent guidance causes dsl-generator to produce one pattern while dsl-reviewer flags it as a bug, creating a contradictory review loop.

- [x] **M5 — Fix CLAUDE.md agent count** (`CLAUDE.md`)
  - **What**: `CLAUDE.md` states "10 specialized agent definition files" in the project structure description. The actual count is 13: requirements-analyzer, plugin-finder, api-researcher, integration-builder, knowledge-architect, dummy-data-generator, node-planner, prompt-engineer, error-strategy, dsl-generator, dsl-validator, dsl-explainer, dsl-reviewer.
  - **Fix**: Change "10 specialized agent definition files" to "13 specialized agent definition files" and update the agent list in Step 9 of the Mandatory Agent Pipeline section to also mention dsl-explainer and dsl-reviewer (they are currently listed in SKILL.md but not in the CLAUDE.md pipeline summary).
  - **Why it matters**: Documentation accuracy; future sessions that read CLAUDE.md to understand the pipeline will have a correct mental model.

- [x] **M6 — Fix CONVERSATION SETUP template in node-planner.md to match Step 2c instructions** (`skills/dify/agents/node-planner.md`)
  - **What**: `node-planner.md` Step 2c describes rich card-style HTML with icons, pill tags, section headers, and interactive elements for the `opening_statement`. But the `CONVERSATION SETUP` block in the output format section shows only basic `<h2>/<ul>` HTML that doesn't match the rich layout. There is a disconnect between the instructions and the template.
  - **Fix**: Replace the basic HTML template in the `CONVERSATION SETUP` output block with a real example that matches Step 2c's card HTML pattern — including a header badge, icon row, capability list with icons, and a suggested first question prompt. The example in `assets/templates/starter-chatflow.yml` can serve as reference for the correct structure.
  - **Why it matters**: dsl-generator copies the `opening_statement` HTML from the plan. If the plan template is basic `<h2>` instead of rich card HTML, the generated chatflow will have a plain opening statement even though the intent was a rich one.

- [x] **M7 — Create evals for the /dify skill** (`skills/dify/evals/evals.json` — new file)
  - **What**: No formal evals exist. The skill has never been tested end-to-end via the skill-creator eval framework. There is no `evals/evals.json`, no workspace, no benchmark.
  - **Fix**: Create `evals/evals.json` with at least 3 test cases covering the core use cases:
    1. Simple chatflow: "Build a customer support chatbot that searches our FAQ knowledge base"
    2. Workflow with external integration: "Create a document summarization workflow that emails a summary via SendGrid"
    3. Reverse direction: provide an existing asset YAML and ask "explain this workflow"
  - Each eval should have an `expected_output` description and assertions checking: YAML file is written to `output/`, YAML passes `validate_workflow.py`, correct app type (chatflow vs workflow), presence of expected node types.
  - **Why it matters**: Without evals, there is no way to verify that changes to the skill don't break existing functionality. Any future improvement iteration is blind.

- [ ] **M8 — Wire in `trigger-webhook.md` and resolve the node-planner "always start" entry-node contradiction** (`skills/dify/agents/node-planner.md`, `skills/dify/agents/dsl-generator.md`)
  - **What**: During the references audit (2026-05-30), `references/nodes/trigger-schedule.md` was wired into node-planner and dsl-generator as an alternate workflow entry node, but `trigger-webhook.md` was intentionally left for later. More importantly, `node-planner.md` Step 1 still hardcodes the trigger node as "always `start`" (see the "Confirm app type" step), which contradicts the existence of `trigger-webhook` and `trigger-schedule` as valid workflow entry nodes documented in `references/schema/workflow-schema.md` and `references/patterns/chatflow-vs-workflow.md`. There is also a `webhook-triggered.yml` asset still pending ground-truth export (see Asset Ground-Truth Validation section).
  - **Fix**:
    1. Add `references/nodes/trigger-webhook.md` to the node read lists in `node-planner.md` and `dsl-generator.md` (conditional: "if the workflow is webhook-triggered").
    2. Rework node-planner Step 1 entry-node logic: the entry node is `start` by default, but `trigger-schedule` for schedule/cron-triggered workflows and `trigger-webhook` for webhook-triggered workflows. Replace the "always `start`" wording with a decision rule keyed off the requirements brief (trigger type).
    3. Ensure requirements-analyzer surfaces the trigger type (manual / scheduled / webhook) so node-planner can pick the right entry node.
  - **Why it matters**: Today, a workflow that should be webhook- or schedule-triggered will be planned with a `start` node, producing DSL that does not auto-trigger. The reference docs and schema already describe the correct trigger nodes; the planning logic just needs to use them. (trigger-schedule is partially handled as of the references audit; this item closes the loop for both trigger types.)

### Ground-Truth Discrepancies (from `DX_Suite_KB.yml` real export, 2026-05-30)

A real, freshly-exported Dify workflow (the user's KB-ingestion app, saved sanitized as
`assets/workflows/knowledge-base-ingestion.yml`) surfaced two mismatches between the skill's
assumptions and current Dify output. Both need verification against ground truth before fixing.

- [x] **G1 — node type string corrected to `document-extractor`** (was the hyphenated `doc-extractor`)
  - **What**: The skill's valid-node-type lists used `doc-extractor`, but the real Dify export uses `type: document-extractor` (confirmed by the user as ground truth). The YAML *examples* in the reference docs were already correct (`document-extractor`); only the type-lists, the edge-types table, the reference filename, and prose were wrong.
  - **Done (2026-05-30)**: Renamed `references/nodes/doc-extractor.md` → `document-extractor.md`; replaced every hyphenated `doc-extractor` (21 occurrences across 7 files) with `document-extractor` — valid-type lists in `node-planner.md` + `requirements-analyzer.md`, the `edge-types.md` sourceHandle table, path references in `dsl-generator.md` / `node-planner.md` / `file-upload.md`, and prose in `document-extractor.md` / `knowledge-retrieval.md`. Example node IDs using the underscore form (`doc_extractor_1`) were left as-is (arbitrary IDs, not type strings). `validate_workflow.py` carries no node-type allowlist, so no validator change was needed.

- [x] **G2 — code-node `outputs` switched to the dict format (dict-only)**
  - **What**: The validator required code-node `outputs` in **list** form, but real Dify exports use the **dict/mapping** form `outputs: {var_name: {type: string, children: null}}`. Confirmed against two unrelated ground-truth exports (`DX_Suite_KB.yml`, `Search.yml`) — 12/12 code nodes use the dict form, `children` always `null` (even for `array[object]`). The user confirmed dict is the only correct form, so we went dict-only (not "accept both").
  - **Done (2026-05-30)**: `validate_workflow.py` now requires the dict form (valid `type` from the 7 types + a `children` key) and rejects the list form (end-node list outputs left intact); fixed the cp932 em-dash crash via UTF-8 stdout; broadened the entry-node check to accept `trigger-schedule`/`trigger-webhook` (this fixed a separate pre-existing failure where ground-truth `schedule-triggered.yml` was rejected — a partial step toward M8). `code.md` + `dsl-generator.md` rewritten to the dict form + the "always return every declared output on every path" rule. `fix_assets.py` migration reversed (list→dict). `webhook-triggered.yml` converted; pytest cases added. **All 13 assets validate; suite 97/97 green.**

---

## Low Priority

- [x] Add `skills/dify/references/nodes/agent.md` — agent node field reference (was referenced in agentic-pattern.md but missing)
- [x] Add `skills/dify/references/patterns/conversation-memory.md` — stateful chatflow pattern: conversation variables, variable-assigner, multi-turn state tracking, 4 patterns with complete YAML
- [x] Add `skills/dify/scripts/preview_graph.py` — generate Mermaid flowchart from a DSL YAML file; usage: `.venv/Scripts/python skills/dify/scripts/preview_graph.py <path>`
- [x] Add Step 10b to `requirements-analyzer.md` — preliminary flow sketch with `[PARALLEL GROUP]` markers so node-planner receives a parallelism hint in the brief
- [x] Add Step 1c to `node-planner.md` — parallelism analysis: identify parallel-eligible groups, `[P: GroupName]` markers, fan-out rule, parallel position lookup table, verification checks 12–13, `PARALLELISM ANALYSIS` plan block
- [x] Fix `parallel-execution.md` — corrected wrong "every fan-out needs variable-aggregator" rule; added convergence strategy decision table; added "Parallel Multi-Section Extraction" pattern with YAML wiring guide
- [ ] Publish to Claude Code plugin marketplace
- [ ] Add more asset YAML examples for complex patterns (parallel branches, iteration over file lists, multi-classifier routing)
- [ ] Add more node type docs if Dify releases new node types
- [ ] Review all `skills/dify/references/nodes/*.md` files against the reference DSL analysis to catch any field documentation gaps

### Audit Findings — Low Priority (from 2026-05-26 skill audit)

- [ ] **L1 — Document or remove version 0.6.0 support in validator** (`skills/dify/scripts/validate_workflow.py` and `skills/dify/agents/dsl-validator.md`)
  - **What**: `validate_workflow.py` accepts both `version: 0.5.0` and `version: 0.6.0`, but no agent in the pipeline ever writes `0.6.0`. The validator silently accepts files with `0.6.0` while the generator always produces `0.5.0`. This creates an undocumented gap.
  - **Fix (option A — document it)**: Add a comment in `validate_workflow.py` and a note in `dsl-validator.md` that `0.6.0` is accepted for forward compatibility with future Dify versions, and that `dsl-generator` currently targets `0.5.0`.
  - **Fix (option B — remove it)**: If Dify 0.6.0 is not yet released or targeted, remove `0.6.0` from the accepted versions list in `validate_workflow.py` so the validator rejects files with unknown versions rather than silently passing them.
  - **Why it matters**: Low risk but causes confusion — if a user imports a third-party `0.6.0` YAML, the validator passes it even if the generator would never produce that version.

- [ ] **L2 — Fix error handler prompt variable references for retry-only LLM nodes** (`skills/dify/agents/error-strategy.md`)
  - **What**: The error handler prompt template in Step 4 references `{{#[failed_node_id].error_message#}}` and `{{#[failed_node_id].error_type#}}`. This is correct for HTTP nodes (which have a fail-branch). But for LLM nodes that use `retry` strategy (no fail-branch), these variables don't exist — LLM nodes on retry-only strategy exhaust retries and stop; they never route to an error handler node. The instruction is internally inconsistent.
  - **Fix**: Add a note in Step 4 clarifying: error handler prompt variable injection (`error_message`, `error_type`) applies ONLY to nodes with a `fail-branch`. For retry-only LLM nodes, no error handler node is created at all, so this section does not apply. Consider adding a table mapping strategy → whether an error handler node is created.
  - **Why it matters**: dsl-generator following Step 4 literally for an LLM retry node would create an error handler that references non-existent variables, causing a runtime error in the workflow.

- [ ] **L3 — Add multilingual welcome example to SKILL.md** (`skills/dify/SKILL.md` welcome message / Step 1)
  - **What**: The welcome message and usage examples in SKILL.md are English-only. The skill's language rule says Claude should respond in the user's language from the first message, but the examples don't demonstrate this and a new user in Japan, France, etc. might not realize the skill supports their language.
  - **Fix**: Add a brief note after the English examples: "This skill responds in your language — describe what you want to build in any language." Optionally add one Japanese example (since the README is bilingual Japanese/English) to make it concrete.
  - **Why it matters**: Cosmetic, but improves first impression for non-English users and aligns the skill's welcome with its stated language behavior.

- [ ] **L4 — Clean up pre-existing MD lint warnings across agent files** (multiple files)
  - **What**: Several agent markdown files have pre-existing lint warnings: MD031 (fenced code block should be surrounded by blank lines), MD032 (lists should be surrounded by blank lines), MD040 (fenced code blocks should have a language specifier), MD060. These don't affect functionality but cause IDE noise.
  - **Affected files** (confirmed by PostToolUse hook output): `dsl-generator.md`, `node-planner.md`, `prompt-engineer.md`, `dsl-reviewer.md`, `error-strategy.md`, `knowledge-architect.md`, `requirements-analyzer.md`
  - **Fix**: Add blank lines before/after all fenced code blocks and lists in these files; add language specifiers (e.g., ` ```yaml `, ` ```text `, ` ```json `) to all bare ` ``` ` fences.
  - **Why it matters**: Purely cosmetic. Does not affect skill behavior. Safe to batch all files in one session.

---

## Future Additions (Pending Version Upgrade)

These require Dify node types or features not yet available in the current version being targeted.

- [ ] Add `skills/dify/references/patterns/human-in-the-loop.md` — human approval branching pattern using the Human node (interrupt, review, approve/reject flow); add once the Human node is available in the target Dify version

---

## Notes

- All Python scripts MUST be run via `.venv/Scripts/python` — never the global Python environment
- Ground-truth DSL examples live in `skills/dify/assets/` — the skill uses them as structural references; they must remain valid importable YAML
- Windows encoding: never use em-dash `—` in Python `print()` statements — use ASCII hyphen `-` (causes cp932 UnicodeEncodeError on Windows)
