# Design — Concept Ideation Front Door for the `/dify` Skill

**Date:** 2026-05-30
**Status:** Approved (design); pending implementation plan

## Problem

When a user invokes `/dify` with a thin prompt (e.g. "bento recipe generator"), the pipeline
currently goes straight into `requirements-analyzer`, which only formalizes whatever the user
typed. A one-line idea produces a thin app. We want the skill to **proactively ideate** — take any
prompt and aggressively expand it into a rich, creative, fully-specified app concept (inputs,
output types, creative features) — and get the user's confirmation before the pipeline runs.

## Decisions (locked during brainstorming)

1. **Always expand aggressively.** The ideation step runs for every prompt and always produces a
   big, rich concept, regardless of how much detail the user gave.
2. **Present one rich concept, editable.** Show a single fully-fleshed-out concept; the user
   approves or requests changes in plain text; revise and re-confirm until approved.
3. **Confirmed concept feeds `requirements-analyzer`, which may still ask genuine technical
   clarifiers.** The analyzer treats the confirmed concept as authoritative scope and only asks
   about genuine technical ambiguity — it does not re-expand scope.
4. **New `concept-ideator` agent + SKILL.md confirmation gate.** A one-shot agent generates the
   proposal; SKILL.md presents it and runs the approve/edit loop (mirrors the existing node-plan
   approval gate).

## Where it slots in the pipeline

A new **Step 2b — Concept Ideation & Confirmation**, inserted between Step 2 (collect free-form
description) and Step 3 (requirements-analyzer). It adds a **second approval gate**:

```
Step 1  Welcome
Step 2  Collect free-form description
Step 2b NEW: Concept Ideation  -> [CONCEPT APPROVAL GATE]
Step 3  requirements-analyzer (receives confirmed concept; may still ask genuine technical clarifiers)
Step 4+ research -> knowledge -> node-planner -> [NODE-PLAN APPROVAL GATE] -> prompt-engineer -> ... -> dsl-generator -> validation
```

- **Concept gate** confirms *what we're building*.
- **Node-plan gate** (existing) confirms *how it's built*.

The reverse-direction mode (explain/review an existing DSL) is unaffected — it still short-circuits
before Step 1, so ideation does not run for explain/review requests.

## Component 1 — New agent `concept-ideator`

**File:** `skills/dify/agents/concept-ideator.md`

**Role:** Take a (possibly one-line) app idea and aggressively expand it into a rich, creative,
fully-specified **App Concept Proposal**. One-shot and non-interactive — it produces a proposal and
never asks the user directly (interactivity lives in SKILL.md). It stays at the *what* level: it
does NOT pick node types, does NOT decide the final app type, and does NOT write YAML — those belong
to `requirements-analyzer`, `node-planner`, and `dsl-generator` respectively.

**Inputs received:**
- The user's raw description, verbatim.
- The full conversation context.
- On a revision pass: the previous App Concept Proposal plus the user's change requests.

**Output — a delimited block** `=== APP CONCEPT PROPOSAL ===` ... `=== END CONCEPT ===` containing:

- **App name** — catchy, derived from the idea.
- **Vision** — one paragraph: what the app does and who it is for, expanded creatively.
- **Interaction style hint** — a light, non-binding note ("feels like a one-shot tool" vs.
  "feels conversational") to inform downstream agents. Not a final app-type decision.
- **Inputs** — a generous list. Each entry: `name · type · required? · why`. `type` is restricted
  to valid Dify start-node input types: `text-input | paragraph | select | number | file |
  file-list`. The agent proactively invents sensible inputs the user never mentioned (e.g. for a
  bento app: budget, allergies, servings, cuisine, prep time).
- **Output types** — multiple distinct outputs/sections the app should produce, each with a
  one-line description (e.g. recipe cards, shopping list with cost, nutrition breakdown, prep
  timeline, substitution tips).
- **Creative features** — optional delightful enhancements, clearly marked optional so they are
  easy to trim (e.g. leftover-aware mode, seasonal suggestions, weekly batch-prep plan).
- **Assumptions made** — the creative leaps the agent took, listed so the user can correct them.

**Constraints:**
- Responds in the user's language (per the skill language rule); variable `name`s stay ASCII.
- Reads `skills/dify/references/config/variables.md` (valid input types) and
  `skills/dify/references/patterns/chatflow-vs-workflow.md` (for the interaction-style hint only).
- Never produces YAML, never designs nodes, never picks the final app type.

## Component 2 — SKILL.md Step 2b (the confirmation gate)

1. Spawn `concept-ideator` with the raw description + conversation context.
2. Receive the App Concept Proposal.
3. Present it to the user in friendly prose (not raw delimiters), explicitly highlighting **the
   inputs it invented, the output types, and the creative features**, and inviting edits:
   *"I've expanded your idea into a fuller concept. Add/remove/change anything — or say 'looks good'
   to continue."*
4. **Gate loop:**
   - If the user requests changes → re-spawn `concept-ideator` with the previous proposal + the
     user's change requests → re-present → repeat.
   - If the user approves (any affirmation, in any language) → store the **confirmed concept** and
     proceed to Step 3.
5. Pass the confirmed concept verbatim to `requirements-analyzer` as the authoritative description
   (in addition to the original raw prompt and conversation context).

This step never generates YAML and never exposes the internal agent name (per existing Hard Rules
8 and 9 — phrase it as "Let me flesh out your idea..." rather than naming the agent).

## Component 3 — Ripple changes

- **`skills/dify/agents/requirements-analyzer.md`** — "What You Receive" gains an item: *a
  user-confirmed App Concept Proposal; treat it as authoritative scope; only ask clarifiers for
  genuine technical ambiguity; do not re-expand or re-propose scope.*
- **`skills/dify/SKILL.md` Hard Rules** — add a rule: *always run concept ideation (Step 2b) and
  obtain explicit concept confirmation before spawning requirements-analyzer.* Add `concept-ideator`
  to the mandatory-agents list (Hard Rule 7).
- **`CLAUDE.md`** — add `concept-ideator` to the Mandatory Agent Pipeline as the first agent
  (always runs, has a confirmation gate); update the agent count 13 -> 14 and the
  `skills/dify/agents/` description.
- **`CHANGELOG.md`** — record the feature under `## [Unreleased]`.
- **`TODO.md`** — record the feature as a completed item with a short description.

## Example — "bento recipe generator"

- **App name:** Bento Box Architect
- **Vision:** designs balanced, budget-aware bento boxes tailored to dietary needs and prep time.
- **Inputs invented:** servings (number), budget per box (number), allergies/restrictions (select),
  cuisine style (select), prep-time available (select), ingredients on hand (paragraph, optional),
  kid-friendly (select yes/no).
- **Output types:** per-item recipe cards; consolidated shopping list with cost estimate; nutrition
  breakdown; prep timeline; substitution tips.
- **Creative features:** leftover-aware mode; seasonal-ingredient suggestions; weekly batch-prep
  plan.
- **Assumptions:** home cooking; single-day box.
- User tweaks ("drop nutrition, add a Japanese-authenticity score") → confirm → into the pipeline.

## Non-goals

- No YAML generation, node selection, or app-type decision in the ideator (those stay downstream).
- No change to the reverse-direction (explain/review) mode.
- No change to the node-plan approval gate.
- Not building a "pick from 2-3 directions" chooser or a per-item toggle UI (we chose the single
  editable concept).

## Testing / acceptance

- Invoking `/dify` with a thin prompt ("build a bento recipe generator") produces an App Concept
  Proposal containing multiple invented inputs (with valid Dify input types), multiple output types,
  and creative features, and pauses for confirmation before any requirements analysis.
- Requesting an edit ("remove X, add Y") produces a revised proposal reflecting the change.
- On approval, the pipeline proceeds and `requirements-analyzer` receives the confirmed concept and
  does not re-ask scope questions already settled by the concept.
- Reverse-direction (explain/review a `.yml`) still bypasses ideation entirely.
