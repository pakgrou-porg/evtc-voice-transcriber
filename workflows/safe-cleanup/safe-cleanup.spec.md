# Workflow Specification: safe-cleanup

**Module:** voice-transcriber
**Status:** Placeholder — To be created via create-workflow workflow
**Created:** 2026-04-17

---

## Workflow Overview

**Goal:** Safely delete source media files after verifying successful transcription.

**Description:** Checks for a verified success code from the transcription engine AND the presence of non-empty transcript text before deleting the original media file. Logs the deletion. Only runs if `source_auto_remove` is enabled in config.

**Workflow Type:** Utility (invoked internally by transcribe-and-analyze)

---

## Workflow Structure

### Entry Point

```yaml
---
name: safe-cleanup
description: Safely delete source audio/video files after verified successful transcription
web_bundle: true
installed_path: '{project-root}/skills/evtc_voice_transcriber/workflows/safe-cleanup'
---
```

### Mode

- [x] Create-only (steps-c/)
- [ ] Tri-modal (steps-c/, steps-e/, steps-v/)

---

## Planned Steps

| Step | Name | Goal |
|------|------|------|
| 01 | Check Config | Verify `source_auto_remove` is enabled; abort if not |
| 02 | Verify Success Code | Confirm the transcription engine returned HTTP 200 or equivalent success |
| 03 | Verify Transcript Content | Confirm the output transcript file is non-empty and valid |
| 04 | Delete Source | Delete the original media file from disk |
| 05 | Log Action | Write deletion record to log with timestamp and file name |

---

## Safety Rules

- **Rule 1:** NEVER delete the source file unless the engine returned a verified HTTP 200 success code.
- **Rule 2:** NEVER delete the source file unless the output transcript is confirmed non-empty.
- **Rule 3:** ALWAYS log every deletion with timestamp, filename, and engine response code.
- **Rule 4:** If either check fails, abort cleanup silently and preserve the source file intact.

---

## Workflow Inputs

### Required Inputs

- `source_file_path`: Path to the original media file to potentially delete.
- `transcription_success`: Boolean flag from the transcribe-and-analyze workflow.
- `transcript_output_path`: Path to the generated transcript file for validation.

### Optional Inputs

None.

---

## Workflow Outputs

### Output Format

- [ ] Document-producing
- [x] Non-document

### Output Files

- Log entry: `{output_folder}/logs/cleanup.log` — records each deleted file with timestamp.

---

## Agent Integration

### Primary Agent

EVTC Transcriber (`evtc-transcriber`)

### Other Agents

None.

---

## Implementation Notes

**Use the create-workflow workflow to build this workflow.**

**Safety Rule:** Never delete source unless BOTH success code AND non-empty transcript are confirmed.

---

_Spec created 2026-04-17_
