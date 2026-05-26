# TODO — Dify DSL Generator Plugin

Track improvement tasks here. Check items off as they are completed. Add new items at the bottom of each section.

---

## Completed

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

## Medium Priority

- [x] Update `skills/dify/agents/requirements-analyzer.md` — add an output format preference question (table vs card vs prose) so `node-planner` doesn't have to guess the layout type
- [x] Update `skills/dify/SKILL.md` Step 6 (prompt-engineer spawn) — explicitly pass which nodes in the plan are upstream of `template-transform` nodes so `prompt-engineer` knows which specs need the template guidance section
- [x] Update `skills/dify/agents/dsl-validator.md` — add checks for: `template-transform` node presence in chatflows, non-empty `opening_statement` in chatflows, `answer` node referencing `template_node_id.output` (not raw LLM text)
- [x] Update `skills/dify/references/nodes/llm.md` — add `structured_output` / `structured_output_enabled` field documentation with schema example and when-to-use guidance

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

---

## Future Additions (Pending Version Upgrade)

These require Dify node types or features not yet available in the current version being targeted.

- [ ] Add `skills/dify/references/patterns/human-in-the-loop.md` — human approval branching pattern using the Human node (interrupt, review, approve/reject flow); add once the Human node is available in the target Dify version

---

## Notes

- All Python scripts MUST be run via `.venv/Scripts/python` — never the global Python environment
- Ground-truth DSL examples live in `skills/dify/assets/` — the skill uses them as structural references; they must remain valid importable YAML
- Windows encoding: never use em-dash `—` in Python `print()` statements — use ASCII hyphen `-` (causes cp932 UnicodeEncodeError on Windows)
