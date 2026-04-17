# Workflows Reference

## 1. transcribe-and-analyze (Core)

**Purpose:** End-to-end processing of audio/video files into structured transcripts and JSON summaries.

### Trigger
```
transcribe
```
or attach a media file and ask for transcription.

### Input
- Audio or video file (MP3, WAV, MP4, M4A, OGG)
- Optional: output format (`json` or `text`)

### Pipeline

| Step | Action |
|------|--------|
| 01 | Validate file exists and format is supported |
| 02 | Transcode to engine-compatible format via FFmpeg |
| 03 | Split into 10-15 min chunks with 1-second overlaps |
| 04 | Sequentially submit chunks to configured engine API |
| 05 | Stitch transcript, removing duplicates from 1-sec overlaps |
| 06 | Generate structured JSON summary |
| 07 | Run safe-cleanup (if auto-remove enabled) |
| 08 | Return transcript and summary |

### Output
- `{filename}-transcript.txt` — Full transcript with speaker tags
- `{filename}-summary.json` — Structured summary:
```json
{
  "subject": "...",
  "action_items": [],
  "detailed_topics": [],
  "resourcing": [],
  "commitments": []
}
```

---

## 2. connection-test (Feature)

**Purpose:** Validate your transcription engine configuration.

### Trigger
```
test
```
or click **Test Connection** in the Configure UI.

### Input
- None. Uses bundled `scripts/test.mp3` and reads config from `module.yaml`.

### Pipeline

| Step | Action |
|------|--------|
| 01 | Load API URL, port, prefix, and model name from config |
| 02 | Confirm bundled test file exists |
| 03 | Submit test.mp3 to API endpoint |
| 04 | Validate transcription response is non-empty |
| 05 | Report success with latency, or detailed error |

### Output
```
Connection Successful. Engine: whisper-large. Latency: 840ms.
```
or an error with specific troubleshooting guidance.

---

## 3. safe-cleanup (Utility)

**Purpose:** Safely delete source media files after verified transcription.

**Note:** This workflow runs automatically as the final step of `transcribe-and-analyze` when `source_auto_remove` is enabled. It can also be triggered manually.

### Safety Rules
- Does NOT delete unless HTTP 200 (or equivalent) is received from the engine.
- Does NOT delete unless the output transcript file is non-empty.
- Logs all deletions with timestamp to `cleanup.log`.

### Input
- Source file path
- Transcription success flag
- Output transcript path

### Output
- Log entry in `{output_folder}/logs/cleanup.log`
