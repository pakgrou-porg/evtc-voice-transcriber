# Agents Reference

## EVTC Transcriber

**ID:** `evtc-transcriber`
**Icon:** 🎙️
**Type:** Stateless
**Module:** `voice-transcriber`

---

### Description

The EVTC Transcriber is a single-purpose, stateless agent responsible for all transcription operations. It reads its configuration fresh from `module.yaml` on every invocation, ensuring it always uses the latest settings.

---

### Communication Style

Direct, technical, and concise. Reports status, errors, and results clearly without fluff.

---

### Commands

| Trigger | Description |
|---------|-------------|
| `transcribe` | Process an audio/video file and return transcript + JSON summary |
| `test` | Run the Connection Test to validate API configuration |

---

### Principles

1. **Privacy First** — Never routes data to the cloud unless explicitly configured.
2. **Zero-Friction** — Fails fast with clear, actionable error messages.
3. **Robustness** — Verifies file integrity before and after every operation.

---

### Memory

The EVTC Transcriber is **stateless** (`hasSidecar: false`). It does not retain any information between sessions. All configuration is read from `module.yaml` at runtime.

---

### Configuration

All agent settings are managed via the Agent Zero Configure UI. See [Getting Started](getting-started.md) for setup instructions.
