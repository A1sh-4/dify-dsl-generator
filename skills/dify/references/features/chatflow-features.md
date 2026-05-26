# Chatflow Features Block

The `features` block in a chatflow DSL YAML controls the conversational capabilities exposed to end users via the web app interface. It is a top-level field in the DSL, adjacent to `graph`, `model`, and `app`. It has no equivalent in workflow DSL files — workflow YAML does not include a `features` block (or includes only a minimal subset).

---

## Position in DSL

The `features` block appears at the top level of the chatflow DSL:

```yaml
app:
  description: ""
  icon: "🤖"
  icon_background: "#FFEAD5"
  mode: advanced-chat
  name: "My Chatflow"
  use_icon_as_answer_icon: false
features:
  file_upload: ...
  opening_statement: ...
  retriever_resource: ...
  sensitive_word_avoidance: ...
  speech_to_text: ...
  suggested_questions: ...
  suggested_questions_after_answer: ...
  text_to_speech: ...
graph:
  edges: ...
  nodes: ...
```

---

## Complete Features Block Reference

```yaml
features:
  file_upload:
    image:
      enabled: false
      number_limits: 3
      transfer_methods:
        - local_file
        - remote_url
  opening_statement: "Hello! How can I help you today?"
  retriever_resource:
    enabled: true
  sensitive_word_avoidance:
    enabled: false
  speech_to_text:
    enabled: false
  suggested_questions:
    - "What can you help me with?"
    - "How does this work?"
  suggested_questions_after_answer:
    enabled: true
  text_to_speech:
    enabled: false
    language: ""
    voice: ""
```

---

## Field-by-Field Reference

### `opening_statement`

**Type:** string

The greeting message displayed when the chatflow web app is opened by a user. This text appears in the chat window before the user sends their first message. It is not sent to the LLM — it is a static UI element only.

**Variable injection:** The `opening_statement` supports Jinja2-style variable injection using the syntax `{{variable_name}}` (without the `{{# #}}` DSL delimiters). These variables are resolved from the chatflow's configured input variables (defined on the start node or app settings).

Example with variable:
```yaml
opening_statement: "Hello, {{user_name}}! I'm here to help with your {{department}} questions."
```

**Important:** This uses `{{variable_name}}` (Jinja2) NOT `{{#node_id.field#}}` (DSL variable reference syntax). These are different syntaxes serving different purposes.

If `opening_statement` is empty string (`""`), no greeting is shown — the chat opens with an empty input area.

---

### `suggested_questions`

**Type:** array of strings

A static list of suggested prompt buttons shown to the user before they send their first message. These appear as clickable chips or buttons below the opening statement. Clicking one fills the input field with that text.

```yaml
suggested_questions:
  - "What can you help me with?"
  - "How does this work?"
  - "Tell me about pricing"
```

**Characteristics:**
- Static — the same suggestions are shown to all users regardless of context.
- Shown only before the first message is sent.
- Disappear after the user starts the conversation.
- Maximum recommended: 4-6 suggestions. More than 6 may clutter the UI.
- Empty array (`[]`) disables suggested questions.

**Distinction from `suggested_questions_after_answer`:** This field is a static, pre-conversation list. The `after_answer` variant is dynamic and AI-generated.

---

### `suggested_questions_after_answer`

**Type:** object with `enabled` boolean

When enabled, Dify uses AI to generate contextually relevant follow-up question suggestions after each assistant response. These appear as clickable chips below the assistant's answer, helping users discover related queries they might not have thought to ask.

```yaml
suggested_questions_after_answer:
  enabled: true
```

**Characteristics:**
- Dynamic — questions are generated fresh for each answer based on the conversation context.
- Uses a small, fast LLM call in the background to generate 2-3 suggestions.
- Adds slight latency per response (the suggestions appear shortly after the main answer).
- Effective for discoverability in knowledge-base chatflows (users see follow-up questions related to retrieved content).
- Works best with factual, structured content. Less effective for open-ended creative chatflows.

To disable:
```yaml
suggested_questions_after_answer:
  enabled: false
```

---

### `retriever_resource`

**Type:** object with `enabled` boolean

Controls whether document source citations are displayed in the web app UI after answers that used knowledge retrieval.

```yaml
retriever_resource:
  enabled: true
```

**When enabled:**
- After each answer that involved a knowledge retrieval node, the sources panel shows the document names, chunk content previews, and relevance scores of the chunks used.
- Users can see exactly which documents and sections grounded the answer.
- The citation panel appears below the answer text.

**When disabled:**
- No source attribution is shown, even if the workflow used knowledge retrieval internally.

**Critical:** For RAG chatflows that retrieve from knowledge bases, `retriever_resource.enabled: true` is **required** for citation display. Setting it to `false` hides all source information from users, which may reduce trust in factual responses.

This setting does not affect retrieval behavior — chunks are still retrieved and used regardless of this setting. It only controls whether the UI shows them.

---

### `sensitive_word_avoidance`

**Type:** object with `enabled` boolean

Enables Dify's built-in sensitive word filtering. When enabled, Dify checks both user inputs and LLM outputs against a configured word list. Matching content is blocked or replaced.

```yaml
sensitive_word_avoidance:
  enabled: false
```

**Configuration:** The word list is not stored in the DSL YAML — it is configured in **Workspace Settings → Content Moderation → Sensitive Words**. Enabling this in the features block activates checking; the word list management is separate.

**Behavior:**
- Input check: if user input contains a sensitive word, Dify returns a configurable rejection message without running the workflow.
- Output check: if the LLM's output contains a sensitive word, it is replaced with `***` or a custom replacement string.

For more sophisticated moderation (regex patterns, ML classifiers, custom logic), use an API Extension moderation endpoint instead. See `skills/dify/references/features/api-extensions.md`.

---

### `speech_to_text`

**Type:** object with `enabled` boolean

Enables voice input in the chatflow web app. Users can click a microphone button and speak instead of type. The audio is transcribed to text and processed as `sys.query`.

```yaml
speech_to_text:
  enabled: false
```

See `skills/dify/references/features/speech.md` for full details on STT model selection, language support, and limitations.

**Chatflow-only.** Web app interface only. API mode does not support STT.

---

### `text_to_speech`

**Type:** object with `enabled`, `language`, and `voice` fields

Converts the chatflow's text answer into spoken audio played in the web app.

```yaml
text_to_speech:
  enabled: false
  language: ""
  voice: ""
```

When enabled:
```yaml
text_to_speech:
  enabled: true
  language: "en-US"
  voice: "alloy"
```

- `language` — BCP-47 language code (e.g., `"en-US"`, `"zh-CN"`, `"ja-JP"`). Controls pronunciation and language model selection.
- `voice` — voice identifier specific to the TTS model. For OpenAI TTS: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`.

See `skills/dify/references/features/speech.md` for full details on TTS model selection and voice options.

**Chatflow-only.** Web app interface only.

---

### `file_upload`

**Type:** nested object

Controls image and document file upload capability in the chatflow web app.

```yaml
file_upload:
  image:
    enabled: false
    number_limits: 3
    transfer_methods:
      - local_file
      - remote_url
```

See `skills/dify/references/features/file-upload.md` for the complete file upload reference including supported types, size limits, and how to reference uploaded files in the workflow graph.

---

## Conversation Memory Configuration

Conversation memory (maintaining context across turns in a chatflow) is **not** configured in the `features` block. It is configured in the chatflow graph settings or the LLM node:

- In the LLM node, set `memory.enabled: true` and `memory.window.enabled: true` with a `window_size` (number of previous turns to include).
- Or configure a dedicated **Memory node** in the graph to use external storage (Redis, database) for long-term memory.

The `features` block only controls UI-level capabilities; conversation memory is a graph-level concern.

---

## Features Block: Chatflow vs Workflow

Chatflow (`mode: advanced-chat`) has a rich `features` block as documented above.

Workflow (`mode: workflow`) has no `features` block or a minimal version. If a `features` block appears in a workflow DSL, only `file_upload` may be relevant (for workflows that accept file inputs via the start node). All conversational features (`opening_statement`, `suggested_questions`, `speech_to_text`, `text_to_speech`, `retriever_resource`) are chatflow-only.

---

## Common Feature Combinations

### RAG Knowledge Base Chatflow
```yaml
features:
  file_upload:
    image:
      enabled: false
      number_limits: 3
      transfer_methods:
        - local_file
        - remote_url
  opening_statement: "Ask me anything about our product documentation."
  retriever_resource:
    enabled: true        # Show document citations
  sensitive_word_avoidance:
    enabled: false
  speech_to_text:
    enabled: false
  suggested_questions:
    - "What are the system requirements?"
    - "How do I reset my password?"
    - "What's new in version 3.0?"
  suggested_questions_after_answer:
    enabled: true        # AI-generated follow-ups based on retrieved content
  text_to_speech:
    enabled: false
    language: ""
    voice: ""
```

### Customer Service Chatflow
```yaml
features:
  file_upload:
    image:
      enabled: true      # Allow screenshots/photos for troubleshooting
      number_limits: 3
      transfer_methods:
        - local_file
        - remote_url
  opening_statement: "Hello! I'm here to help. Please describe your issue."
  retriever_resource:
    enabled: true
  sensitive_word_avoidance:
    enabled: true        # Block profanity and abuse
  speech_to_text:
    enabled: false
  suggested_questions:
    - "I need help with billing"
    - "My account isn't working"
    - "I want to cancel my subscription"
  suggested_questions_after_answer:
    enabled: false       # Keep conversation focused, not exploratory
  text_to_speech:
    enabled: false
    language: ""
    voice: ""
```

### Voice-Enabled Creative Writing Assistant
```yaml
features:
  file_upload:
    image:
      enabled: false
      number_limits: 3
      transfer_methods:
        - local_file
        - remote_url
  opening_statement: "Welcome! Tell me what you'd like to write today."
  retriever_resource:
    enabled: false       # No knowledge base — no citations needed
  sensitive_word_avoidance:
    enabled: false
  speech_to_text:
    enabled: true        # Voice input
  suggested_questions:
    - "Write a short story about space"
    - "Help me brainstorm blog ideas"
  suggested_questions_after_answer:
    enabled: true
  text_to_speech:
    enabled: true        # Read the creative output aloud
    language: "en-US"
    voice: "fable"       # Storytelling voice
```

---

## Related Documentation

- See `skills/dify/references/features/speech.md` for STT/TTS model configuration.
- See `skills/dify/references/features/file-upload.md` for file upload node patterns.
- See `skills/dify/references/schema/chatflow-schema.md` for the complete chatflow DSL structure.
- See `skills/dify/references/features/knowledge-base.md` for setting up the retrieval that `retriever_resource` cites.
