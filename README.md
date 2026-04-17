# Easy Voice Transcription Caller (EVTC)

Frictionless audio/video transcription engine for Agent Zero

Privacy-first transcription with local or cloud engines, auto-chunking, and structured summaries

---

## Overview

EVTC is a standalone Agent Zero module that accepts audio and video files in multiple formats (MP3, WAV, MP4), automatically transcodes and chunks them for processing, submits them to a configured local or cloud transcription engine, stitches the results into a complete transcript, and returns a structured JSON summary including speakers, action items, topics, and commitments.

Designed for privacy-conscious users, EVTC supports local inference servers (Whisper, Cohere Transcribe) as well as cloud APIs (Amazon STT, Turboscribe.ai, OpenAI) — all configurable via the Agent Zero settings UI without editing any files.

---

## Installation

```bash
bmad install voice-transcriber
```

During installation you will be prompted to configure:
- Transcription engine type (local or cloud)
- API URL, port, and prefix
- Model name
- Auto-remove source files on success

---

## Quick Start

1. Install the module and complete the configuration wizard.
2. Click **Test Connection** to validate your setup using the bundled `test.mp3`.
3. Attach an audio or video file to an Agent Zero conversation.
4. Ask: *"Transcribe this file and give me a meeting summary."*
5. Receive a full transcript and structured JSON summary.

**For detailed documentation, see [docs/](docs/).**

---

## Components

### Agents

- **EVTC Transcriber** — Stateless transcription specialist. Handles all audio processing, API calls, and output formatting.

### Workflows

| Workflow | Type | Description |
|----------|------|-------------|
| `transcribe-and-analyze` | Core | End-to-end audio processing and structured summarization |
| `connection-test` | Feature | Validates engine connectivity using bundled test file |
| `safe-cleanup` | Utility | Safely removes source files after verified transcription |

---

## Configuration

The module supports these configuration options (set during installation via the A0 Configure UI):

| Variable | Description | Default |
|----------|-------------|----------|
| `engine_type` | Transcription backend (local or cloud) | `local-whisper` |
| `transcription_api_url` | Base URL of the transcription API | `http://127.0.0.1` |
| `transcription_api_port` | Port number for the API | `8080` |
| `transcription_api_prefix` | API endpoint prefix | `/v1` |
| `transcription_model_name` | Model name to use | `whisper-large` |
| `source_auto_remove` | Delete source file after success | `true` |
| `test_audio_path` | Path to bundled test audio file | `scripts/test.mp3` |

---

## Module Structure

```
voice-transcriber/
├── module.yaml
├── README.md
├── TODO.md
├── docs/
│   ├── getting-started.md
│   ├── agents.md
│   ├── workflows.md
│   └── examples.md
├── agents/
│   └── evtc-transcriber.spec.md
├── scripts/
│   └── test.mp3
└── workflows/
    ├── transcribe-and-analyze/
    ├── connection-test/
    └── safe-cleanup/
```

---

## Documentation

For detailed user guides and documentation, see the **[docs/](docs/)** folder:
- [Getting Started](docs/getting-started.md)
- [Agents Reference](docs/agents.md)
- [Workflows Reference](docs/workflows.md)
- [Examples](docs/examples.md)

---

## Development Status

This module is currently in development. The following components are planned:

- [ ] Agents: 1 agent (EVTC Transcriber)
- [ ] Workflows: 3 workflows

See TODO.md for detailed status.

---

## Author

Created via BMAD Module workflow

---

## License

Part of the BMAD framework. MIT License.
