# Speech (STT and TTS)

Dify supports voice interaction through two complementary features: Speech to Text (STT) for voice input and Text to Speech (TTS) for audio output. Both are chatflow-only features and operate at the input/output layer of the application, not within the workflow node graph.

---

## Chatflow-Only Restriction

Speech features (both STT and TTS) are available **only for chatflows** (`mode: advanced-chat`). They are not available for standard workflows (`mode: workflow`). Additionally, both features only function in the **web app** publishing mode — the chat UI renders the microphone input button (STT) and audio playback (TTS). When calling the chatflow via API, STT/TTS is not applied; the API receives and returns text only.

---

## Features Block Configuration

Both STT and TTS are controlled via the `features` block in the chatflow DSL YAML:

```yaml
features:
  speech_to_text:
    enabled: true
  text_to_speech:
    enabled: true
    language: "en-US"
    voice: "alloy"
```

To disable both (default state):
```yaml
features:
  speech_to_text:
    enabled: false
  text_to_speech:
    enabled: false
    language: ""
    voice: ""
```

---

## Speech to Text (STT)

### What It Does

STT converts the user's spoken audio into text. In the web app, when STT is enabled, a microphone icon appears in the chat input area. The user clicks the microphone, speaks, and Dify transcribes the audio to text. The transcribed text is injected into `sys.query` — exactly as if the user had typed it — and the workflow runs normally.

STT operates entirely at the **input layer**. No special handling is required within the workflow graph. The workflow receives the transcribed text as the user's query and processes it identically to typed text.

### Enabling STT

```yaml
features:
  speech_to_text:
    enabled: true
```

### Model Selection

The STT model is configured in **Workspace Settings → Model Provider**, not in the DSL YAML. Available models depend on which model providers are configured in the workspace:

- **OpenAI Whisper** (`whisper-1`) — high-quality multilingual transcription. Supports 99 languages. Best overall STT model for production.
- **Azure Cognitive Services Speech** — enterprise-grade STT via Azure. Requires Azure Speech service credentials.
- **Local Whisper** (self-hosted Dify) — run Whisper locally via faster-whisper or whisper.cpp. No API cost, but requires GPU for acceptable latency.
- Other STT-capable model providers configured in workspace settings.

### Language Support

Whisper supports automatic language detection by default. To force a specific language, configure the language setting in workspace STT model settings. Supported languages include all major world languages (English, Spanish, Chinese, French, German, Japanese, Portuguese, Arabic, and 90+ others).

### Audio Format

The Dify web app records audio in WebM format (Opus codec) from the browser microphone and sends it to the STT model for transcription. No client-side configuration is required.

### Integration Flow

```
User speaks into microphone (web app)
    ↓
Audio recorded in browser
    ↓
Audio sent to Dify STT endpoint
    ↓
STT model transcribes audio to text
    ↓
Text injected as sys.query
    ↓
Chatflow runs with transcribed text
    ↓
Answer node generates response
```

---

## Text to Speech (TTS)

### What It Does

TTS converts the chatflow's text answer into spoken audio. When TTS is enabled, the web app plays the generated audio response automatically or provides a play button after each assistant message.

TTS operates at the **output layer**. The text from the `answer` node is passed to the TTS model, which generates an audio stream. No changes to the workflow graph are required.

### Enabling TTS

```yaml
features:
  text_to_speech:
    enabled: true
    language: "en-US"
    voice: "alloy"
```

### Model Selection

TTS model is selected in Workspace Settings → Model Provider. Available options:

- **OpenAI TTS** — models `tts-1` (fast, lower quality) and `tts-1-hd` (slower, higher quality). Six voices available: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`.
- **Azure Cognitive Services TTS** — wide range of voices, including neural voices and custom voice cloning. Enterprise-grade.
- **ElevenLabs** (via plugin) — ultra-realistic voice synthesis with voice cloning. Requires ElevenLabs plugin.
- Other configured TTS providers.

### Voice Selection

The `voice` field in the DSL specifies which voice to use for TTS output. Available voices depend on the selected TTS model:

**OpenAI TTS voices:**
- `alloy` — neutral, balanced
- `echo` — male, slightly deeper
- `fable` — storytelling, expressive
- `onyx` — deep, authoritative
- `nova` — bright, energetic (female)
- `shimmer` — warm, friendly (female)

### Language Configuration

The `language` field (BCP-47 format, e.g., `"en-US"`, `"zh-CN"`, `"es-ES"`) tells the TTS model the expected language of the text. Some models auto-detect language; others require this hint for correct pronunciation.

```yaml
text_to_speech:
  enabled: true
  language: "zh-CN"
  voice: "nova"
```

### Integration Flow

```
Chatflow executes
    ↓
Answer node produces text response
    ↓
TTS model converts text to audio
    ↓
Audio streamed to web app
    ↓
User hears spoken response (with play/pause controls)
```

---

## Combined STT + TTS Configuration

A fully voice-enabled chatflow:
```yaml
features:
  speech_to_text:
    enabled: true
  text_to_speech:
    enabled: true
    language: "en-US"
    voice: "nova"
```

This creates a voice-in, voice-out experience in the web app. Users can interact entirely without typing.

---

## Limitations Summary

| Limitation | Details |
|---|---|
| Chatflow only | STT/TTS not available in workflow mode |
| Web app only | No audio in API mode; API sends/receives text |
| No in-graph control | STT/TTS run at I/O layer, not inside the node graph |
| Model must be configured | STT/TTS model must be set up in workspace model settings |
| Language set in DSL | `language` and `voice` in the YAML control TTS output language/voice |

---

## Related Documentation

- See `docs/features/chatflow-features.md` for the complete `features` block reference.
- See `docs/schema/chatflow-schema.md` for the full DSL structure including the `features` block position.
