# Workflow Specification: transcribe-and-analyze

**Module:** voice-transcriber
**Status:** Placeholder — To be created via create-workflow workflow
**Created:** 2026-04-17

---

## Workflow Overview

**Goal:** End-to-end processing of audio/video files into structured transcripts and summaries.

**Description:** Accepts a media file (MP3, WAV, MP4), transcodes it if needed, splits it into overlapping chunks, sequentially submits chunks to the configured transcription engine, stitches the results into a full transcript, then returns a structured JSON summary with speaker tags, action items, and topics.

**Workflow Type:** Core

---

## Workflow Structure

### Entry Point

```yaml
---
name: transcribe-and-analyze
description: Process audio/video files into structured transcripts and JSON summaries
web_bundle: true
installed_path: '{project-root}/skills/evtc_voice_transcriber/workflows/transcribe-and-analyze'
---
```

### Mode

- [x] Create-only (steps-c/)
- [ ] Tri-modal (steps-c/, steps-e/, steps-v/)

---

## Planned Steps

| Step | Name | Goal |
|------|------|------|
| 01 | Validate Input | Check file exists, format is supported (MP3/WAV/MP4), and config is loaded |
| 02 | Transcode | Use FFmpeg to normalize audio format for the engine |
| 03 | Chunk | Split into segments with 1-second overlaps to ensure continuity |
| 04 | Transcribe | Sequentially submit chunks to the configured engine API |
| 05 | Stitch | Reassemble chunks, remove duplicate text from 1-sec overlaps |
| 06 | Summarize | Generate structured JSON with subject, action items, topics, commitments |
| 07 | Cleanup | If auto-remove enabled and success verified, delete source file |
| 08 | Output | Return final transcript and JSON summary to caller |

---

## Workflow Inputs

### Required Inputs

- `audio_file_path`: Absolute path to the media file to process.

### Optional Inputs

- `output_format`: `json` (default) or `text`.
- `summary_fields`: List of fields to include in the JSON summary (default: all).

---

## Workflow Outputs

### Output Format

- [x] Document-producing
- [ ] Non-document

### Output Files

- `{output_folder}/transcripts/{filename}-transcript.txt`: Full raw transcript with speaker tags.
- `{output_folder}/transcripts/{filename}-summary.json`: Structured JSON summary.

---

## Agent Integration

### Primary Agent

EVTC Transcriber (`evtc-transcriber`)

### Other Agents

None.

---

## Implementation Notes

**Use the create-workflow workflow to build this workflow.**

---

_Spec created 2026-04-17_
