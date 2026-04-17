# Getting Started with EVTC

## Prerequisites

- Agent Zero installed and running.
- A transcription engine available (local or cloud):
  - **Local:** Whisper, WhisperX, or Cohere Transcribe running as a local API server.
  - **Cloud:** An API key for Amazon STT or Turboscribe.ai.
- FFmpeg installed (or the module will manage it automatically).

---

## Installation

```bash
bmad install voice-transcriber
```

During installation, you will be asked:
1. **Engine type** — Select local or cloud provider.
2. **API URL** — The base address of your transcription engine.
3. **Port** — The port your engine is running on.
4. **API prefix** — Usually `/v1`.
5. **Model name** — The exact model identifier your engine uses.
6. **Auto-remove source** — Whether to delete source files after success.

---

## Testing Your Setup

After installation, use the built-in **Connection Test** to verify your setup:

1. Open Agent Zero.
2. Select the **EVTC Transcriber** agent.
3. Type `test` or click **Test Connection**.
4. The module sends a bundled 6.77-second dialog MP3 to your engine.
5. You should receive a confirmation: `Connection Successful. Engine: {model}. Latency: {ms}ms.`

If the test fails, check:
- Is your engine running?
- Is the URL, port, and prefix correct?
- Is the model name exactly as registered in your engine?

---

## Your First Transcription

1. Attach an audio or video file to an Agent Zero conversation.
2. Ask: *"Transcribe this file and give me a meeting summary."*
3. EVTC will automatically:
   - Validate the file format.
   - Transcode to a compatible format (if needed).
   - Split into overlapping chunks.
   - Submit to your configured engine.
   - Stitch the results together.
   - Return a transcript and structured JSON summary.

---

## Supported Formats

| Format | Supported |
|--------|-----------|
| MP3 | ✅ |
| WAV | ✅ |
| MP4 | ✅ |
| M4A | ✅ (via transcode) |
| OGG | ✅ (via transcode) |

---

## Next Steps

- See [Agents Reference](agents.md) to understand the EVTC Transcriber agent.
- See [Workflows Reference](workflows.md) for detailed pipeline documentation.
- See [Examples](examples.md) for real-world use cases.
