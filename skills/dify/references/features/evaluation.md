# Evaluation

Dify's evaluation system enables systematic quality assessment of workflows and chatflows. Rather than relying on anecdotal testing, evaluation provides structured, repeatable measurement of output quality using test datasets, annotation tools, and automated scoring.

---

## What Annotation Is

Annotation is the process of applying human judgment to workflow outputs. For each workflow run, a human reviewer can:

- Rate the response quality (good/bad, 1-5 stars, or custom scale).
- Provide a corrected or improved response.
- Mark specific failures (wrong facts, poor tone, incomplete answer, hallucination).
- Add labels or categories to group failure types.

Annotations create a record of human feedback attached to specific inputs and outputs. This data is used to improve prompts, measure quality trends, and build evaluation datasets.

---

## Creating Test Datasets

A test dataset is a curated collection of input-output pairs used to evaluate workflow quality consistently.

**Creating a dataset:**
1. Go to **Evaluation → Datasets** in the Dify sidebar.
2. Click **Create Dataset**.
3. Add test cases manually — each test case has an input (user query or structured inputs) and an expected output (the correct response).
4. Or, import from CSV: columns for `input`, `expected_output`, and optional metadata fields.
5. Or, promote annotated workflow runs to the dataset — any annotated run can be added to a dataset with one click.

**Dataset size recommendations:**
- Minimum 20 cases for meaningful metrics.
- 100+ cases for statistically reliable evaluation.
- Include edge cases, failure modes, and domain-specific queries.

---

## Running Evaluation Runs

An evaluation run executes the workflow against every test case in a dataset and scores the results.

**Steps:**
1. Go to **Evaluation → Runs**.
2. Select the workflow version to evaluate.
3. Select the dataset.
4. Configure scoring metrics (see below).
5. Click **Run Evaluation**. Dify executes each test case in parallel.
6. View results when the run completes.

Evaluation runs are version-stamped, so you can compare results across workflow versions.

---

## Evaluation Metrics

Dify supports both automated LLM-based scoring and human annotation scoring:

### Correctness
Is the answer factually correct relative to the expected output? Scored by comparing the generated response to the `expected_output` in the dataset. LLM-as-judge: an evaluation LLM reads both and outputs a score 0–1.

### Faithfulness
Does the answer stay grounded in the retrieved context (for RAG workflows)? Measures hallucination: a faithful answer makes no claims beyond what the retrieved chunks support. Requires knowledge retrieval output to be accessible.

### Relevance
Is the answer relevant to the input query? Measures whether the response addresses what was asked, even if wording differs. High relevance + low correctness = the model understood the question but got the answer wrong.

### Coherence
Is the response grammatically correct, logically structured, and easy to understand? Coherence scoring is less commonly used but useful for evaluating long-form generation tasks (summarization, creative writing).

---

## Annotation Workflow

1. Open a completed workflow run in the **Logs** view.
2. Click a specific run to open the trace.
3. Use the **thumbs up / thumbs down** or rating widget to score the response.
4. Optionally add a corrected response in the **Annotation** panel.
5. Add labels (e.g., `hallucination`, `off-topic`, `incomplete`).
6. Save. The annotation is attached to this run and contributes to quality metrics.

**Batch annotation:** Export run logs as CSV, annotate externally, and re-import annotations. Useful for large-scale annotation workflows with external annotators.

---

## Annotation-Driven Prompt Iteration

Annotations expose systematic failure patterns:
- If 30% of runs are labeled `hallucination`, the LLM prompt likely does not constrain the model to the context.
- If 20% are labeled `off-topic`, the system prompt may need stronger scope constraints.
- If `incomplete` is common, the max-tokens setting may be too low, or the prompt needs to instruct comprehensive responses.

Use annotation label frequency charts to prioritize prompt changes. After each prompt iteration, run a new evaluation batch and compare scores to the previous version.

---

## Annotation Reply Feature

The annotation reply feature bypasses the LLM for queries where a human-verified response already exists.

**How it works:**
1. When an annotator marks a run as correct and saves a canonical response, Dify stores the (input, canonical_response) pair.
2. When a future user submits the same (or semantically similar) query, Dify detects the match.
3. Instead of calling the LLM, Dify returns the cached human-written response directly.

**Configuration:** Enable in **App Settings → Annotation Reply**. Set a similarity threshold (cosine similarity of embeddings) — queries above the threshold get the cached response; queries below go to the LLM.

This feature is useful for high-traffic queries with known correct answers (FAQ responses, policy statements) where LLM variability is undesirable.

---

## A/B Testing

Compare two workflow versions against the same dataset:

1. Create Version A and Version B of the workflow (different prompts, models, or node configurations).
2. Run evaluation against the same dataset for both versions.
3. Compare metrics side-by-side in the **Evaluation → Compare** view.
4. Select the version with superior metrics for promotion to production.

A/B test dimensions: LLM model selection, system prompt wording, temperature setting, retrieval top-k, reranker usage.

---

## Viewing Results and Trends

The **Evaluation Dashboard** shows:
- Score distribution per metric (histogram).
- Trend lines: how metrics change across evaluation runs over time.
- Failure breakdown: which test cases fail most often (sorted by score, lowest first).
- Per-node analysis: for multi-step workflows, see which node contributes most to failures.

Use the trend view to confirm that prompt changes improve quality and do not regress other metrics.

---

## Using Evaluation Data to Identify Failing Nodes

For multi-node workflows, Dify traces which nodes contributed to a failing output:
- Click any failing evaluation result.
- Open the **Trace** view.
- Inspect intermediate outputs at each node (LLM input/output, retrieval results, code node output).
- Identify the node where the error originates.

Common failure patterns:
- **Retrieval failure:** Knowledge retrieval returns irrelevant chunks — adjust retrieval mode or chunking.
- **Prompt failure:** LLM produces wrong format or ignores instructions — refine system prompt.
- **Code node failure:** Variable transformation logic error — debug the code node.
- **HTTP node failure:** External API returned unexpected data — update JSON extraction logic.
