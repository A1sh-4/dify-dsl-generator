# TODO — Dify DSL Generator Plugin

Track improvement tasks here. Check items off as they are completed. Add new items at the bottom of each section.

---

## Completed

- [x] Initial plugin build — all 40 tasks (phases 0–15) complete
- [x] Set up `.venv` virtual environment at project root; updated `.gitignore` to exclude it
- [x] Rewrote `scripts/validate_workflow.py` with 14 validation checks covering all known Dify import requirements
- [x] Created 91-test pytest suite in `tests/test_validate_workflow.py` for full coverage of all 14 checks
- [x] Created `scripts/fix_assets.py` — batch-fixed 7/10 asset YAML files (LLM prompt IDs, code node format)
- [x] Fixed critical skill bug: dummy data questions were never asked because subagents can't be interactive — moved all question-asking into `skills/dify.md` Step 4b
- [x] Updated `agents/node-planner.md`: added `template-transform` as near-mandatory rule, Step 2b (output presentation design), Step 2c (conversation opener HTML), `CONVERSATION SETUP` + `OUTPUT PRESENTATION` blocks in plan output format
- [x] Updated `agents/dsl-generator.md`: rich HTML `opening_statement` template for chatflows, full `template-transform` node YAML block, `structured_output_enabled` guidance, updated delivery checklist
- [x] Updated `agents/prompt-engineer.md`: Step 7 (proactive structured output decision), Step 8 (template-transform content spec), updated output format and hard constraints

---

## High Priority

- [x] Update `assets/templates/starter-chatflow.yml` — rich HTML placeholder with card layout, pill tags, full interactive options reference (buttons, forms, all input types, all variants)
- [x] Update `docs/nodes/template-transform.md` — full rewrite: blank-line rendering rule, complete Jinja2 feature set (filters, groupby, set blocks, section accumulation), all output formats (HTML tables, details/summary accordion, mixed markdown+HTML), interactive forms/buttons in output, complete YAML structure, 4 practical examples
- [x] Update `assets/chatflows/*.yml` example files — add `template-transform` nodes and rich HTML `opening_statement` values to model the new patterns for `dsl-generator`

---

## Medium Priority

- [x] Update `agents/requirements-analyzer.md` — add an output format preference question (table vs card vs prose) so `node-planner` doesn't have to guess the layout type
- [x] Update `skills/dify.md` Step 6 (prompt-engineer spawn) — explicitly pass which nodes in the plan are upstream of `template-transform` nodes so `prompt-engineer` knows which specs need the template guidance section
- [ ] Update `agents/dsl-validator.md` — add checks for: `template-transform` node presence in chatflows, non-empty `opening_statement` in chatflows, `answer` node referencing `template_node_id.output` (not raw LLM text)
- [x] Update `docs/nodes/llm.md` — add `structured_output` / `structured_output_enabled` field documentation with schema example and when-to-use guidance

---

## Low Priority

- [ ] Publish to Claude Code plugin marketplace
- [ ] Add more asset YAML examples for complex patterns (parallel branches, iteration over file lists, multi-classifier routing)
- [ ] Add more node type docs if Dify releases new node types
- [ ] Review all `docs/nodes/*.md` files against the reference DSL analysis to catch any field documentation gaps
- [ ] Add a `knowledge/README.md` explaining the folder purpose and upload instructions for Dify

---

## Notes

- All Python scripts MUST be run via `.venv/Scripts/python` — never the global Python environment
- The `reference_dsls/` folder contains real working DSL files for reference only — the skill must NOT depend on them at runtime
- Windows encoding: never use em-dash `—` in Python `print()` statements — use ASCII hyphen `-` (causes cp932 UnicodeEncodeError on Windows)
