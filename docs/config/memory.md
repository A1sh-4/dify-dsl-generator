# Conversation Memory Configuration

## Overview

Conversation memory allows an LLM node in a Dify chatflow to automatically include the history of prior messages from the current conversation in its context. Without memory, every user message is processed as if the conversation just started — the model has no knowledge of what was said before. With memory enabled, the model can reference prior questions and answers, maintain continuity across turns, and provide responses that feel coherent and context-aware.

Memory is a chatflow-only feature. Workflow apps process discrete, independent runs with no conversation concept, so memory configuration does not apply to them.

---

## How Memory Works

When a user sends a message to a chatflow, Dify:

1. Looks up the conversation history for the current `conversation_id`
2. Fetches the last `window.size` turns from that history
3. Inserts those turns into the LLM node's context as alternating user/assistant messages, before the current user message
4. Sends the full context (system prompt + history + current message) to the LLM

The model then sees the conversation as a natural multi-turn dialogue. This is transparent to the user — they simply experience a chatbot that remembers what they said.

Memory is scoped to a conversation. Each conversation ID (representing one user's session) has its own independent history. Different users never see each other's conversations, and different conversation IDs are always isolated.

When the conversation ends (session cleared, new conversation started), the history does not carry over. Each new conversation starts fresh.

---

## Memory Configuration in LLM Node DSL

```yaml
nodes:
  - id: chat_llm
    type: llm
    data:
      model:
        provider: anthropic
        name: claude-3-5-sonnet-20241022
        mode: chat
      memory:
        enabled: true
        role_prefix:
          assistant: 'Assistant: '
          user: 'User: '
        window:
          enabled: true
          size: 10
      prompts:
        - role: system
          text: |
            You are a helpful customer support agent for {{#env.company_name#}}.
            Use the conversation history to maintain context across turns.
```

**Field reference:**

| Field | Type | Description |
|---|---|---|
| `memory.enabled` | boolean | Enables or disables memory for this LLM node |
| `memory.role_prefix.assistant` | string | Label prepended to assistant messages in history |
| `memory.role_prefix.user` | string | Label prepended to user messages in history |
| `memory.window.enabled` | boolean | Enables windowing (limiting history length) |
| `memory.window.size` | integer | Number of conversation turns to include (1 turn = 1 user + 1 assistant message pair) |

---

## Memory Disabled Configuration

To explicitly disable memory (stateless LLM node inside a chatflow):

```yaml
memory:
  enabled: false
```

Use this when:
- The LLM node performs a subtask that does not need conversation context (e.g., a classification step, a knowledge retrieval summarization)
- You want each message to be handled independently regardless of history
- You are managing context manually via conversation variables

---

## Window Size Trade-offs

The window size is the primary tuning parameter for memory. It controls how many prior turns are included, which directly affects both the quality of context and the token cost of every request.

A "turn" is defined as one complete exchange: one user message plus one assistant response. Window size 10 means the last 10 user messages and 10 assistant responses are included.

| Window Size | Token Cost | Context Quality | Best For |
|---|---|---|---|
| 0 (or disabled) | None | No history | Stateless processing; each message independent |
| 3–5 | Low | Short context | Simple Q&A; questions that are mostly independent |
| 10 | Medium | Good | Most general-purpose chatbots |
| 20 | High | Full context | Complex multi-step conversations; long troubleshooting sessions |
| 30+ | Very High | Extended context | Research assistants; long-running project conversations |

**General recommendation:** Start with `size: 10`. Reduce to `5` if token costs are a concern or if the conversation topics are largely independent. Increase to `20` only if users frequently reference earlier parts of the conversation by turn number or by referencing specific past answers.

---

## Token Budget Planning

Memory consumes tokens from the model's context window. For every LLM call, the total token count is approximately:

```
total_tokens = system_prompt_tokens
             + history_tokens (window.size × avg_turn_length)
             + current_user_message_tokens
             + reserved_output_tokens (max_tokens setting)
```

This total must not exceed the model's context window limit. If it does, the oldest history messages are truncated first.

**Practical planning example:**

Assuming:
- System prompt: 500 tokens
- Average turn length: 300 tokens (150 user + 150 assistant)
- window.size: 10 → 10 × 300 = 3,000 tokens of history
- Current user message: 200 tokens
- max_tokens: 1,000 (reserved for output)

Total: 500 + 3,000 + 200 + 1,000 = **4,700 tokens per request**

For a model with a 16K context window, this is comfortable. For a model with an 8K context window, window.size 10 with long turns could approach the limit. If conversations involve long messages (e.g., users pasting code snippets), reduce window size or increase the model's context window.

---

## Role Prefix Configuration

Role prefixes are labels injected before each historical message to clarify speaker identity when the history is formatted as a single text block. In most modern API-based models using the chat format, these labels are handled by the message role (`user` vs `assistant`) rather than by text prefixes.

**When to customize role prefixes:**
- When your system prompt references the prefixes by name (e.g., "User:" and "Assistant:" headings)
- When you want history formatted differently for clarity

**Example with custom prefixes for a medical assistant:**
```yaml
memory:
  enabled: true
  role_prefix:
    assistant: 'Medical Assistant: '
    user: 'Patient: '
  window:
    enabled: true
    size: 10
```

For most standard chatbots, the default prefixes work correctly and do not need to be customized.

---

## Memory vs Conversation Variables

Memory and conversation variables are complementary features that serve different purposes. Understanding the distinction helps you design chatflows that use each appropriately.

| Dimension | Memory | Conversation Variables |
|---|---|---|
| What it stores | Full message text from prior turns | Specific named values you define (strings, numbers, booleans, objects) |
| How it's accessed | Automatically injected into LLM context | Via `{{#conversation.variable_name#}}` in prompts or node inputs |
| How it's updated | Automatically after each turn | Explicitly via a variable-assigner node |
| Controlled by | `memory.window.size` setting | Your workflow logic |
| Token impact | Grows with window size and message length | Fixed; only the values you store |
| Persists when | Within the same conversation_id | Within the same conversation_id |
| Reset when | New conversation starts | New conversation starts |
| Best for | General conversation continuity | Tracking application state, user preferences, accumulated data |

**Common pattern — using both together:**

Memory handles the natural conversational flow. Conversation variables track extracted state:

```
Turn 1: User says "I prefer responses in French"
→ Parameter-extractor detects language preference
→ Variable-assigner sets conversation.language = "fr"

Turns 2–10: LLM prompt includes {{#conversation.language#}}
→ System prompt: "Always respond in {{#conversation.language#}}"
→ Memory provides the conversational context
→ Conversation variable provides the extracted preference
```

This is more reliable than relying on the model to remember a preference from conversation history alone, especially after many turns when early messages may have scrolled out of the window.

---

## Common Memory Configurations

### Standard Chatbot

```yaml
memory:
  enabled: true
  role_prefix:
    assistant: 'Assistant: '
    user: 'User: '
  window:
    enabled: true
    size: 10
```

### Customer Support (Longer Context)

```yaml
memory:
  enabled: true
  role_prefix:
    assistant: 'Support Agent: '
    user: 'Customer: '
  window:
    enabled: true
    size: 20
```

### High-Volume / Cost-Constrained

```yaml
memory:
  enabled: true
  role_prefix:
    assistant: 'Assistant: '
    user: 'User: '
  window:
    enabled: true
    size: 5
```

### Stateless Processing Node (inside a chatflow)

For an intermediate LLM node that performs a subtask (e.g., classifying the user's intent) where history is irrelevant:

```yaml
memory:
  enabled: false
```

---

## Limitations and Considerations

**Memory does not persist across conversations.** Each conversation_id gets a clean slate. If a user starts a new conversation, the prior conversation's history is not available to the LLM (though it may be stored in Dify's logs for review).

**Memory is not the same as long-term user knowledge.** Memory contains raw message text, not structured knowledge about the user. For persistent user preferences or facts, use conversation variables (within a session) or an external database queried via an HTTP node (across sessions).

**Very long individual messages reduce effective window size.** If a user pastes a 2,000-word document in a single message, one turn can consume as many tokens as 10 normal turns. Consider adding a pre-processing step that summarizes or truncates unusually long messages before they enter the LLM context.

**Memory and streaming.** Streaming responses are compatible with memory. The completed streamed response is stored as the assistant turn after generation finishes, and will be included in subsequent turn contexts.
