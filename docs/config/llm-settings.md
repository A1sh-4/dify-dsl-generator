# LLM Settings Configuration

## Overview

LLM sampling parameters control how a language model generates text. Adjusting these parameters shifts the model's behavior along axes of creativity, determinism, verbosity, and diversity. Understanding each parameter — and how they interact — allows you to produce outputs that are reliably suited to your specific use case, whether that is deterministic data extraction or open-ended creative writing.

This document covers every sampling parameter available in Dify's LLM nodes, with ranges, effects, practical guidance, and ready-to-use presets.

---

## Parameters Reference

| Parameter | Type | Range | Default | Effect |
|---|---|---|---|---|
| temperature | float | 0.0–2.0 | 0.7 | Controls randomness. 0 = deterministic, 2 = very random |
| top_p | float | 0.0–1.0 | 1.0 | Nucleus sampling. Lower = fewer token choices |
| top_k | integer | 1–100 | varies by model | Top-k sampling. Limits vocabulary at each step |
| max_tokens | integer | 1–model limit | 2000 | Maximum output length in tokens |
| presence_penalty | float | -2.0–2.0 | 0 | Penalizes repeated topics. Positive = more variety |
| frequency_penalty | float | -2.0–2.0 | 0 | Penalizes repeated tokens. Positive = less repetition |
| stop | array[string] | any strings | [] | Stop generation when any listed string is encountered |

---

## Parameter Explanations

### temperature

Temperature is the most impactful sampling parameter. It scales the probability distribution over the vocabulary before sampling. At `0.0`, the model always selects the single highest-probability token, making outputs fully deterministic and reproducible. As temperature rises toward `1.0`, lower-probability tokens become increasingly likely, producing more varied and sometimes surprising responses. Values above `1.0` push into territory where unusual and potentially incoherent tokens can surface — useful for maximally creative tasks but risky for factual ones.

**When to increase:** Creative writing, brainstorming, ideation, generating multiple diverse alternatives.  
**When to decrease:** Code generation, data extraction, classification, structured output, factual Q&A.  
**Practical rule:** Start at `0.7` for general tasks. Move to `0.1–0.3` for deterministic tasks. Move to `1.0–1.2` for creative tasks.

### top_p (Nucleus Sampling)

`top_p` defines a probability mass cutoff. The model considers only the smallest set of tokens whose cumulative probability reaches `top_p`. Setting `top_p: 0.9` means the model samples from the 90% most likely tokens at each step, discarding long-tail vocabulary. Unlike temperature, top_p adapts dynamically — when one token is very dominant, the nucleus is small; when probabilities are more spread, the nucleus is larger.

**When to decrease:** When you want more conservative, on-topic outputs without making the model fully deterministic.  
**When to leave at 1.0:** When temperature alone is your primary control knob.  
**Avoid:** Setting both `top_p` below `0.9` and `temperature` high simultaneously. They compound and can produce erratic results.

### top_k

`top_k` limits the token vocabulary at each generation step to the `k` most probable candidates, then samples from those. For example, `top_k: 40` means only the 40 highest-scoring tokens are eligible at each step, regardless of their probability values. This is a hard cutoff, unlike top_p's adaptive approach.

**When to use:** Some models (notably Gemini and some open-source models via Ollama) respond well to top_k. OpenAI and Anthropic models typically perform better without it.  
**Recommended value:** `40–80` if used. Leave unset or at maximum to effectively disable it.

### max_tokens

`max_tokens` caps how many tokens the model may generate in a single response. One token is approximately 0.75 words in English. Setting this too low will truncate responses mid-sentence; setting it too high on simple tasks wastes API budget.

**Guidelines by task type:**
- Classification / short answers: `50–200`
- Q&A, summarization: `500–1500`
- Code generation: `1000–4000`
- Long-form writing: `2000–8000` (model limit permitting)

### presence_penalty

Presence penalty applies a one-time penalty to any token that has already appeared in the output, regardless of how often. A positive value discourages the model from revisiting topics or concepts it already introduced, promoting variety and breadth. A negative value encourages the model to stay on the same topics.

**When to increase:** Chatbots where you want responses to feel fresh and not circular; brainstorming outputs where you want diverse ideas.  
**When to leave at 0:** Data extraction, code generation, any task where exact repetition is correct (e.g., returning a field name the model already mentioned).

### frequency_penalty

Frequency penalty applies a cumulative penalty proportional to how many times a token has already appeared. Unlike presence_penalty's one-shot penalty, this grows with each repetition. A positive value strongly discourages repetitive phrasing, common in verbose model outputs. Too high a value can cause the model to avoid reasonable repeated words like "the" or "is."

**When to increase:** Long-form writing where you want the model to vary sentence structure and vocabulary.  
**When to leave at 0:** Structured data extraction, code generation, short outputs.  
**Practical cap:** Values above `0.5` often produce unnatural text. Stay in the `0.1–0.3` range for most use cases.

### stop

Stop sequences immediately halt generation when the model produces any string in the list. Useful for constraining output to a specific section or preventing the model from continuing past a delimiter.

**Common uses:**
```yaml
stop:
  - "\n\n"      # Stop at first blank line
  - "###"       # Stop at markdown header
  - "</answer>" # Stop at closing XML tag
  - "Human:"    # Stop before simulated user turn
```

---

## How Parameters Interact

**Do not use top_p and top_k together.** Both are vocabulary-limiting mechanisms applied at the same step. Stacking them compounds the restriction unpredictably. Choose one.

**temperature and top_p are complementary.** A common professional approach: tune temperature first, keep top_p at `1.0`. If results are still too wide-ranging, lower top_p slightly (e.g., to `0.95`). Do not aggressively lower both simultaneously.

**presence_penalty and frequency_penalty compound.** Both apply to tokens already in the output. Setting both to `0.3` effectively discourages repetition as much as setting one to `0.5`–`0.6`. If you use both, keep values modest (≤`0.2` each).

**max_tokens is a hard limit, not a target.** The model stops at the natural end of its answer or at max_tokens, whichever comes first. Setting `max_tokens: 4000` on a task that needs 200 tokens does not cause verbosity — but it does cost latency budget if rate limits apply.

---

## Recommended Presets

### Deterministic (Coding, Data Extraction, Classification)

For tasks where correctness matters more than creativity. The model should follow instructions precisely and produce repeatable output.

```yaml
temperature: 0.1
top_p: 0.9
max_tokens: 2000
frequency_penalty: 0
presence_penalty: 0
```

**Rationale:** Very low temperature keeps the model on the most probable path. A slight top_p cutoff avoids extreme long-tail tokens without sacrificing coherence. No penalties needed since repetition is often correct in structured tasks.

---

### Balanced (General Q&A, Summarization, RAG)

The workhorse preset for most Dify workflows. Produces reliable, readable, and moderately varied responses.

```yaml
temperature: 0.5
top_p: 1.0
max_tokens: 2000
frequency_penalty: 0
presence_penalty: 0
```

**Rationale:** Mid-range temperature gives sensible, non-robotic answers while maintaining accuracy. top_p at `1.0` avoids over-constraining. No penalties preserves factual repetition when it is correct.

---

### Conversational (Chatbots, Customer Support)

Optimized for dialogue that feels natural, engaging, and non-repetitive over multi-turn conversations.

```yaml
temperature: 0.7
top_p: 1.0
max_tokens: 1000
frequency_penalty: 0.1
presence_penalty: 0.1
```

**Rationale:** Higher temperature produces warmer, more human-feeling responses. Modest penalties discourage the conversational tendency to circle back to the same phrasing. Lower max_tokens keeps replies appropriately concise.

---

### Creative (Writing, Brainstorming, Ideation)

For tasks where originality and surprise are desirable, and occasional imperfection is acceptable.

```yaml
temperature: 1.1
top_p: 0.95
max_tokens: 4000
frequency_penalty: 0.3
presence_penalty: 0.3
```

**Rationale:** Temperature above `1.0` meaningfully expands the vocabulary distribution. A slight top_p cutoff (0.95) prevents the very lowest-probability tokens from appearing. Higher penalties push the model to generate a broader range of ideas rather than elaborating the same concept repeatedly. Higher max_tokens gives room for expansive output.

---

## Per-Model Notes

### OpenAI o1 / o3 (Reasoning Models)
- `temperature` is fixed at `1` internally and cannot be changed
- `top_p`, `presence_penalty`, `frequency_penalty` are ignored
- `max_tokens` maps to `max_completion_tokens` and includes reasoning tokens
- These models do not support system prompts in the standard way

### Anthropic Claude
- `temperature` range `0.0–1.0` is the effective range; values above `1.0` are accepted by the API but not recommended and may produce unstable outputs
- `top_k` is supported natively; other providers may not pass it through
- No `frequency_penalty` or `presence_penalty` equivalents in the native API — Dify may simulate these

### Google Gemini
- `top_k` is supported and recommended for fine-grained control alongside `top_p`
- `temperature` and `top_p` behave similarly to OpenAI
- Very long context windows (up to 2M tokens for Gemini 1.5 Pro) make `max_tokens` less of a constraint

### Local Models via Ollama
- Parameter support varies by model and version
- Most llama-based models support temperature, top_p, top_k, and stop
- Some smaller models are sensitive to high temperature values and may produce incoherent output above `0.8`
