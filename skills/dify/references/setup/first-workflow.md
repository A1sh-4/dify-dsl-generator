# Building Your First Workflow

This is a complete end-to-end walkthrough: from invoking the `/dify` skill to having a running, published application in your Dify instance. Follow each step in order.

---

## Prerequisites

Before starting, confirm you have:

- This plugin installed and working (see `docs/setup/installation.md`)
- A Dify instance running — Cloud or self-hosted (see `docs/setup/dify-setup.md`)
- At least one LLM model provider configured in Dify (see `docs/setup/model-configuration.md`)
- Claude Code open in a terminal or the desktop app
- If your workflow uses a knowledge base: the knowledge base created and indexed (see `docs/setup/knowledge-base-setup.md`)

---

## The Example Use Case

This walkthrough builds a **product support chatbot** that:
- Answers user questions using a product documentation knowledge base
- Cites the document sources it retrieved
- Runs as a chatflow (multi-turn conversation)

You will follow this same sequence for any workflow you build — only your description and answers to clarifying questions change.

---

## Step 1: Invoke the Skill

Open Claude Code. Type:

```
/dify
```

The `/dify` skill loads and greets you. You will see a message similar to:

```
Welcome to the Dify DSL Generator. What would you like to build?
Describe your application in plain language — what it does, who uses it,
and any external services or knowledge bases it needs.
```

---

## Step 2: Describe Your Use Case

Type a natural language description. Be specific about:

- **What the application does** at a high level
- **Whether it's conversational** (multi-turn chatbot) or a **one-shot pipeline** (process input → produce output)
- **External services** it needs (Slack notifications, web search, weather data, etc.)
- **Knowledge bases** it should retrieve from (product docs, FAQ, internal wiki, etc.)
- **Any outputs** that go somewhere specific (email, Notion, webhook, etc.)

Example input for this walkthrough:

```
I want a chatbot that answers questions about our product using a knowledge base.
It should cite the sources it used in its answer so users know where the
information comes from. The app should remember the conversation context
so users can ask follow-up questions.
```

Providing more detail upfront reduces the number of clarifying questions and produces a more accurate node plan.

---

## Step 3: Answer Clarifying Questions

The **requirements-analyzer** agent processes your description. If anything is ambiguous, it will ask 1–3 focused questions. Answer them concisely.

Common clarifying questions and good answers:

| Question | Example answer |
|---|---|
| "What retrieval mode do you prefer — semantic, full-text, or hybrid?" | "Hybrid is fine." |
| "How many document chunks should be retrieved per query?" | "Top 5." |
| "Should the bot escalate to a human if it can't answer?" | "No, just say it doesn't know." |
| "What LLM model should power the answer generation?" | "Claude Sonnet." |

After your answers, the requirements-analyzer produces a structured requirements document that all subsequent agents use.

---

## Step 4: Review the Node Graph Plan

The **node-planner** agent produces a complete node graph plan and presents it to you before any YAML is generated. For the product support chatbot, it will look similar to:

```
NODE GRAPH PLAN — Product Support Chatbot (Chatflow)

Nodes:
  Node 1: start            "User Input"         at (80, 282)
  Node 2: knowledge-retrieval  "Search Docs"    at (380, 282)
  Node 3: llm              "Generate Answer"    at (680, 282)
  Node 4: answer           "Stream to User"     at (980, 282)

Edges:
  start → knowledge-retrieval   (user question passed as query)
  knowledge-retrieval → llm     (retrieved chunks passed as context)
  llm → answer                  (LLM output streamed to user)

Variables:
  sys.query → knowledge-retrieval.query
  knowledge-retrieval.result → llm context (injected into system prompt)
  llm.text → answer.answer
```

**This is your opportunity to request changes.** Common adjustments:

- "Add a question classification node before retrieval to handle off-topic questions."
- "Add a fallback branch if no chunks score above the threshold."
- "Add an answer node that formats the sources as a numbered list."

If the plan looks correct, type:

```
approve
```

The pipeline will not proceed until you explicitly approve the plan. If you request changes, node-planner will revise and re-present the plan for another round of approval.

---

## Step 5: Wait for Generation

Once you approve the plan, the remaining agents run automatically in sequence:

1. **prompt-engineer** — writes system and user prompt templates for every LLM node
2. **error-strategy** — (skipped in this example since there are no HTTP nodes)
3. **dsl-generator** — assembles all inputs into the complete DSL YAML file

This process takes approximately 30–60 seconds depending on the complexity of the workflow. You will see status messages as each agent completes its work.

---

## Step 6: Review the Generated YAML

When generation is complete, the skill displays the full YAML in a code block. Take a moment to review it. Key things to check:

- The top-level `app.mode` is `chat` (for a chatflow) or `workflow` (for a pipeline)
- All node IDs are unique UUIDs
- The knowledge retrieval node references your actual dataset UUID (you may need to update this after import)
- LLM node prompts look sensible and use correct Jinja2 variable syntax (`{{#node_id.variable_name#}}`)
- No hardcoded API keys or secrets are present — all sensitive values should use `{{env.VARIABLE_NAME}}`

---

## Step 7: The YAML File is Saved Automatically

The **dsl-generator** writes the YAML file to the `output/` directory (e.g., `output/product-support-chatbot.yml`). Immediately after the file is written, the **dsl-validator** hook fires automatically and runs `scripts/validate_workflow.py`.

Validation checks for:
- Required top-level fields (`version`, `kind`, `app`, `graph`)
- Required fields on every node type
- Edge references pointing to valid node IDs
- Correct variable reference syntax

If validation passes, you will see: `Validation passed — YAML is ready to import.`

If validation fails, the errors are shown with the specific field or node that caused the problem. The dsl-validator agent will attempt to fix the issues automatically and re-validate.

---

## Step 8: Import Into Dify

1. Open your Dify workspace in a browser.
2. Click **Studio** (or **Apps**) in the left sidebar.
3. Click **Create App** in the top right.
4. Select **Import DSL File** from the options.
5. Click **Upload** and select your `.yml` file from the `output/` directory.
6. Click **Import**.

Dify parses the YAML and creates the app with all nodes placed on the canvas. If import succeeds, you will be taken directly to the app's canvas view.

---

## Step 9: Configure Dependencies After Import

Dify may show warning banners after import if any dependencies are not yet connected:

**Missing knowledge base:**
Click on the knowledge retrieval node on the canvas → update the dataset ID to match your actual knowledge base. This is expected if the generated YAML used a placeholder UUID.

**Missing plugin:**
If the workflow uses a plugin node, go to **Plugin → Marketplace**, install the required plugin, then return to the canvas. The node will resolve automatically.

**Missing environment variables:**
If any node uses `{{env.VARIABLE_NAME}}`, set those variables in the app settings: **App Settings → Environment Variables → Add Variable**.

**Missing model:**
If the LLM node references a model not yet configured in your workspace, add the provider in **Settings → Model Provider** and then update the LLM node on the canvas.

---

## Step 10: Test the Workflow

1. Click **Preview** in the top bar of the canvas editor.
2. A chat panel opens on the right (for chatflows) or an input panel (for workflows).
3. Enter a test query, for example: "What are the system requirements for your product?"
4. Verify the response is accurate, cites sources correctly, and does not include hallucinated information.
5. Ask a follow-up question to verify conversation memory works as expected.

**If something fails:**
Click the **Logs** tab to see execution details for each node. The logs show the input each node received, the output it produced, and any error messages. This is the fastest way to identify which node is failing and why.

Common causes of test failures:
- Knowledge base not linked (retrieval node returns empty results)
- LLM prompt has a broken variable reference (the node receives `undefined` instead of context)
- Model provider credentials are invalid or rate-limited

---

## Step 11: Publish

When you are satisfied with the test results:

1. Click **Publish** in the top bar.
2. Choose how to expose the application:
   - **Web App** — generates a public URL your users can visit in a browser
   - **API** — generates an API key and endpoint for programmatic access
   - **MCP Server** — exposes the app as a Model Context Protocol server for AI agent integration
3. Copy the URL or API key and share it with your users.

The app is now live. Any changes you make in the canvas editor require clicking **Publish** again to take effect.

---

## Common Import Errors and Fixes

| Error message | Cause | Fix |
|---|---|---|
| "Invalid DSL version" | The `version` field value is unrecognized | Set `version: 0.1.3` in the YAML |
| "Unknown node type" | A node's `type` string does not match a known Dify node type | Check `docs/nodes/` for the correct type string |
| "Missing required field" | A node is missing a field that Dify requires | Review the error details — it names the node and field |
| "Dataset not found" | The knowledge base UUID in the YAML does not exist in this workspace | Create the knowledge base or update the UUID |
| "Plugin not installed" | A plugin node references a plugin not installed in the workspace | Install the plugin from the Dify marketplace |
| YAML parse error | Indentation or syntax error in the YAML file | Check the line number in the error; YAML requires consistent spaces (not tabs) |
| "Node reference error" | An edge references a node ID that does not exist | Re-run dsl-validator to identify and fix broken references |

---

## Iterating and Improving

**Small changes (moving nodes, adjusting prompts):**
Edit directly in the Dify canvas drag-and-drop editor. Changes take effect immediately in Preview.

**Structural changes (adding nodes, changing flow logic):**
Run `/dify` again, describe what you want to change, and regenerate. The new YAML can be imported over the existing app (Dify will ask whether to replace or create a new app).

**Debugging retrieval quality:**
Go to **Knowledge → [Your Knowledge Base] → Retrieval Test** and enter the queries that are failing. Adjust `top_k` and `score_threshold` in the knowledge retrieval node on the canvas.

**Viewing execution history:**
Go to **Logs** in the left sidebar of the app to see all historical runs with full node-by-node traces. This is useful for identifying patterns in failures after the app is in production.
