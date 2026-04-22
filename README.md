# Easy Voice Transcription Caller (EVTC)

Frictionless audio/video transcription plugin for Agent Zero

Privacy-first transcription with local or cloud engines, auto-chunking, and structured summaries

---

## Overview

EVTC is an Agent Zero plugin that accepts audio and video files in multiple formats (MP3, WAV, MP4, M4A, OGG, FLAC, AAC, WebM), automatically transcodes and chunks them for processing, submits them to a configured local or cloud transcription engine, stitches the results into a complete transcript, and returns a structured JSON summary including speakers, action items, topics, and commitments.

Designed for privacy-conscious users, EVTC supports local inference servers (Whisper, Cohere Transcribe) as well as cloud APIs (Amazon STT, Turboscribe.ai, OpenAI) — all configurable via the Agent Zero settings UI without editing any files.

---

## Installation

Install from the Agent Zero Plugin Hub, or clone into your plugins directory:

```bash
cd /a0/usr/plugins
git clone https://github.com/pakgrou-porg/evtc-voice-transcriber.git evtc_voice_transcriber
```

The install hook will automatically check for FFmpeg and attempt to install it if missing.

---

## Quick Start

1. Install the plugin and enable it in **Settings → Plugins**.
2. Open the plugin settings gear to configure your transcription engine.
3. Ask an agent to **test the connection**: *"Test my transcription engine connection."*
4. Attach an audio or video file and ask: *"Transcribe this file and give me a meeting summary."*
5. Receive a full transcript and structured JSON summary.

---

## Tools

| Tool | Description |
|------|-------------|
| `transcribe` | End-to-end audio processing: transcode → chunk → API transcribe → stitch → summarize |
| `test_connection` | Validates engine connectivity using a bundled 7-second test audio clip |

---

## Configuration

All settings are configurable via the plugin settings panel in the Agent Zero UI:

| Setting | Description | Default |
|---------|-------------|--------|
| `engine_type` | Transcription backend | `local-cohere` |
| `transcription_api_url` | Base URL of the transcription API | `http://10.116.2.56:8101` |
| `transcription_api_port` | Optional port number (if not in URL) | _(empty)_ |
| `transcription_api_prefix` | API endpoint prefix | `/v1` |
| `transcription_model_name` | Model identifier string | `CohereLabs/cohere-transcribe-03-2026` |
| `transcription_language` | ISO 639-1 language code | `en` |
| `source_auto_remove` | Delete source file after successful transcription | `true` |

### Supported Engines

| Engine | Type | Notes |
|--------|------|-------|
| Whisper / WhisperX | Local | Self-hosted, full privacy |
| Cohere Transcribe | Local | Self-hosted, full privacy |
| OpenAI API | Cloud | Requires API key |
| Amazon STT | Cloud | Requires API key |
| Turboscribe.ai | Cloud | Requires API key |

---

## Pipeline

The transcription pipeline processes audio in five stages:

1. **Transcode** — FFmpeg converts input to 16kHz mono WAV (required by all engines)
2. **Chunk** — Audio is split into 12-minute segments with 1-second overlaps
3. **Transcribe** — Chunks are submitted sequentially to the configured API
4. **Stitch** — Chunks are reassembled with semantic deduplication of overlap text
5. **Summarize** — (JSON mode) Generates structured summary with subject, action items, topics, commitments

### Output Files

- `{filename}_{timestamp}_transcript.txt` — Full raw transcript
- `{filename}_{timestamp}_summary.json` — Structured JSON summary (JSON mode only)

---

## Plugin Structure

```
evtc_voice_transcriber/
├── plugin.yaml              # A0 runtime manifest
├── default_config.yaml      # Default settings
├── hooks.py                 # Install hook (FFmpeg check)
├── __init__.py              # Package init
├── LICENSE                  # MIT License
├── README.md                # This file
├── .gitignore
├── helpers/                 # Core processing modules
│   ├── __init__.py
│   ├── transcoder.py        # FFmpeg audio conversion
│   ├── chunker.py           # WAV splitting with overlap
│   ├── api_client.py        # API submission + 16kHz conversion
│   ├── stitcher.py          # Chunk deduplication & merge
│   ├── summarizer.py        # Structured JSON summary generation
│   └── test.mp3             # Bundled test audio (7s speech clip)
├── tools/                   # A0 Tool subclasses
│   ├── __init__.py
│   ├── transcribe.py        # TranscribeTool — full pipeline
│   └── test_connection.py   # TestConnectionTool — API validation
├── prompts/                 # Tool discovery prompts
│   ├── agent.system.tool.transcribe.md
│   └── agent.system.tool.test_connection.md
├── webui/                   # Settings UI
│   └── config.html          # Alpine.js settings panel
└── tests/                   # pytest test suite (108 tests)
    ├── __init__.py
    ├── conftest.py
    ├── test_transcoder.py
    ├── test_chunker.py
    ├── test_stitcher.py
    ├── test_api_client.py
    ├── test_summarizer.py
    ├── test_tool_transcribe.py
    ├── test_tool_connection.py
    ├── test_hooks.py
    └── test_integration.py
```

---

## Development

### Prerequisites

- Agent Zero installed and running
- FFmpeg installed (auto-checked on plugin install)
- A transcription engine accessible via HTTP API
- Python 3.10+

### Running Tests

```bash
cd /a0/usr/plugins/evtc_voice_transcriber
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

The test suite includes:
- **92 unit tests** covering all helper modules and tool classes
- **9 integration tests** using real FFmpeg processing with mocked API calls
- **4 hook tests** for install lifecycle
- **3 tool tests** validating A0 framework integration

All external dependencies (API calls, A0 framework classes) are mocked in tests.

### Code Standards

- Every line of code includes an explanatory comment
- All functions return structured dicts with `{'success': bool, 'error': str|None, ...}`
- Error handling is graceful — tools return `Response(message=error)`, never crash
- FFmpeg is the only external binary dependency

---

## Requirements

- **FFmpeg** — Required for audio transcoding (auto-installed via `hooks.py`)
- **requests** — HTTP client for API calls (included in A0 base environment)

---

## Author

Created 2026-04-17

---

## License

MIT License — see [LICENSE](LICENSE) for details.
