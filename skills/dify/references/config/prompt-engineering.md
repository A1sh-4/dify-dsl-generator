# Prompt Engineering for Dify LLM Nodes

## Overview

Prompt quality is the single biggest determinant of LLM node output quality. A well-engineered prompt is specific, structured, and instructs the model on what to do, what format to use, and what to avoid. This document covers how to write effective prompts for Dify workflows, how variable injection works, which patterns to use for common tasks, and the key pitfalls to avoid.

---

## Variable Injection in Prompts

Dify uses a proprietary reference syntax to inject dynamic values into prompt text at runtime. This syntax resolves node outputs, start node inputs, environment variables, system variables, and conversation variables into the prompt before sending it to the LLM.

**Syntax:**
```
{{#node_id.field_name#}}
```

Every reference has two parts separated by a dot: the source identifier (node ID, `env`, `sys`, or `conversation`) and the specific field name on that source.

**Complete example system prompt:**
```
You are a customer support assistant for {{#env.company_name#}}.

Today's date is {{#sys.timestamp#}}.

The user has submitted the following question:
{{#start.user_query#}}

Relevant documentation retrieved from the knowledge base:
{{#knowledge_retrieval_1.result#}}

Instructions:
- Answer clearly and concisely based on the documentation above.
- If the answer is not in the documentation, say: "I don't have specific information about that. Please contact our support team."
- Do not speculate or invent information not present in the documentation.
- Respond in the same language as the user's question.
```

**Reference types:**

| Prefix | Source | Example |
|---|---|---|
| `start` | Start node input variables | `{{#start.user_query#}}` |
| `node_id` | Any upstream node's output | `{{#llm_1.text#}}` |
| `env` | Workspace environment variables | `{{#env.company_name#}}` |
| `sys` | System built-in variables | `{{#sys.user_id#}}` |
| `conversation` | Conversation variables (chatflow only) | `{{#conversation.language_preference#}}` |

---

## Prompt Structure Best Practices

### System Prompt Components

A well-structured system prompt follows this order. Each component serves a distinct purpose and together they give the model complete, unambiguous instructions.

**1. Role Definition**

Be specific. Generic role definitions ("You are a helpful assistant") give the model no useful context and allow it to make assumptions that may not match your intent.

- Weak: `You are a helpful assistant.`
- Strong: `You are a technical support specialist for Acme SaaS, helping customers troubleshoot integration errors with the REST API.`

**2. Context / Background**

Tell the model what situation it is operating in. What is the application? Who is the user? What is the overall goal of the interaction?

```
This application helps software developers diagnose API errors by analyzing error logs and matching them against known failure patterns.
```

**3. Task Instructions**

State explicitly what the model should do with the input it receives. Use numbered steps for multi-step processes.

```
Your task:
1. Read the error log provided by the user.
2. Identify the root cause of the error.
3. Provide a specific fix with code examples where applicable.
```

**4. Output Format Specification**

Specify the exact format of the response. Do not leave format to the model's discretion. If you need JSON, say so. If you need a bullet list, say so. If you need a specific number of items, say so.

```
Return your response in this exact format:
**Root Cause:** [one sentence]
**Fix:** [step-by-step instructions]
**Code Example:** [only if applicable]
```

**5. Constraints**

Define what the model must NOT do. Negative constraints are as important as positive instructions because they prevent the most common failure modes.

```
Constraints:
- Do not suggest solutions that require downgrading the API version below v3.
- Do not speculate about causes not evident in the log.
- Do not respond to questions unrelated to API integration.
```

**6. Examples (Few-Shot, if needed)**

For tasks where format or reasoning style is hard to express in words alone, include one or two examples. Keep examples concise — they consume tokens.

```
Example:
Input: "Error 401: Invalid API key on endpoint /v4/users"
Root Cause: The API key provided does not have permission for the v4 endpoint.
Fix: Generate a new key with v4 scope in your account dashboard under Settings → API Keys.
```

---

## Anti-Patterns to Avoid

### Never Write

**"You are a helpful assistant."**  
This is the worst possible role definition. It tells the model nothing about domain, audience, tone, or constraints. Replace with a specific role.

**"Do your best."**  
Unmeasurable and meaningless to the model. Replace with concrete success criteria.

**"Answer the user's question."**  
Obvious and redundant. Use the instruction space to specify format, constraints, and reasoning approach instead.

**Instructions buried in the middle of a long prompt.**  
Models exhibit primacy and recency bias — they weight instructions at the beginning and end more heavily. Put critical instructions at both locations.

**Assuming the model knows your business context.**  
The model has no knowledge of your specific product, company, users, or data unless you provide it explicitly.

### Always Write

**Specific role with domain and context:**
```
You are a billing specialist for {{#env.company_name#}}, responsible for helping business customers understand their invoices and resolve billing disputes.
```

**Explicit output format in the system prompt:**
```
Return ONLY a JSON object. Do not include any text before or after the JSON.
```

**Explicit handling of edge cases:**
```
If the user's question is unrelated to billing, respond with: {"error": "out_of_scope", "message": "I can only help with billing questions."}
```

---

## Prompt Patterns for Common Tasks

### RAG Answer Pattern

Use when the LLM node receives retrieved knowledge base context and must answer from it.

```
System:
You are a {{#env.domain#}} expert assistant. Answer questions using ONLY the provided context.

Rules:
- If the answer is fully contained in the context, answer directly.
- If the answer is partially in the context, answer what you can and note what is missing.
- If the answer is not in the context, respond: "I don't have information about that in the available documentation."
- Always cite the relevant section title when referencing specific content.

Context:
{{#knowledge_retrieval_1.result#}}

User question:
{{#start.user_query#}}
```

---

### Chain-of-Thought Pattern

Use for reasoning tasks where intermediate steps improve accuracy.

```
System:
Solve the following problem step by step.

Process:
1. Identify all relevant information given in the input.
2. State any assumptions you need to make.
3. Work through the reasoning step by step, showing your work.
4. State your final conclusion on a new line beginning with "Conclusion:".

Do not skip to the conclusion without showing your reasoning.
```

---

### Extraction Pattern

Use when you need to extract structured fields from unstructured text. Pair with structured output when possible.

```
System:
Extract the specified fields from the provided text. Return a JSON object only.
Do not include any explanatory text before or after the JSON.
If a field cannot be found, use null for its value.

Required fields:
{
  "customer_name": "<full name or null>",
  "order_id": "<order ID string or null>",
  "issue_type": "<one of: billing, shipping, product, other, or null>",
  "urgency": "<one of: high, medium, low or null>",
  "contact_email": "<email address or null>"
}

Text to analyze:
{{#start.input_text#}}
```

---

### Classification Pattern

Use when you need to assign an input to one of a fixed set of categories.

```
System:
Classify the following text into exactly one of these categories:
- BILLING: Questions about charges, invoices, payments, refunds
- TECHNICAL: Questions about bugs, errors, functionality, API
- ACCOUNT: Questions about login, password, permissions, settings
- GENERAL: All other inquiries

Return ONLY the category name in uppercase. No explanation. No punctuation.

Text:
{{#start.user_message#}}
```

---

### Summarization Pattern

Use for condensing long documents or conversation histories.

```
System:
Summarize the following content.

Requirements:
- Maximum {{#start.max_sentences#}} sentences
- Use plain language accessible to a non-expert audience
- Focus on: key decisions made, action items identified, and unresolved questions
- Do not include filler phrases like "The document discusses..." — begin directly with the content

Content to summarize:
{{#start.document_text#}}
```

---

## Jinja2 vs DSL Variable Syntax

Dify uses two distinct templating systems in different contexts. Mixing them up is a common source of silent failures.

| Context | Syntax | Example |
|---|---|---|
| LLM node prompts | `{{#node_id.field#}}` (DSL) | `{{#start.query#}}` |
| Template-transform node | `{{ variable }}` (Jinja2) | `{{ input_text }}` |
| Code node (Python) | Direct variable access | `inputs["user_query"]` |

**Rules:**
- In any LLM node's system prompt, user prompt, or assistant prefix fields: use DSL syntax `{{#...#}}`
- In Template-transform node content: use Jinja2 `{{ }}` syntax with variables passed from connected nodes
- Never use Jinja2 syntax inside an LLM node's prompt fields — it will be passed as literal text to the model
- Never use DSL syntax inside a Template-transform node — it is not resolved there

---

## Token Efficiency Tips

Every token in the system prompt reduces the budget available for user input and model output. Optimizing prompts for efficiency matters at scale.

**Remove redundant instructions.** If you say "Be concise" and "Keep responses under 3 sentences," one instruction is enough.

**Use bullet points over paragraphs for instructions.** Lists are easier for models to parse and consume fewer tokens than prose explanations.

**Exploit primacy and recency effect.** The model weights the beginning and end of its context most heavily. Put your most critical instruction at the very start of the system prompt and repeat the single most important constraint at the very end.

**Avoid preamble.** Remove phrases like "Your role is to..." or "In this application...". Go directly to the instruction.

**Use the user prompt field for content, system prompt for instructions.** LLM nodes have separate system and user prompt fields. Put all instructions in the system prompt. Put dynamic content (user queries, retrieved text, documents) in the user prompt via variable references. This improves caching efficiency on providers that support prompt caching.
