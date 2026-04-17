# Workflow Specification: connection-test

**Module:** voice-transcriber
**Status:** Placeholder — To be created via create-workflow workflow
**Created:** 2026-04-17

---

## Workflow Overview

**Goal:** Validate the user's transcription engine configuration before processing real files.

**Description:** Sends a bundled 5-second `test.mp3` file to the configured API endpoint, verifies a successful transcription response is returned, and reports the result (success, latency, engine info, or detailed error message).

**Workflow Type:** Feature

---

## Workflow Structure

### Entry Point

```yaml
---
name: connection-test
description: Validate transcription engine connectivity using a bundled test audio file
web_bundle: true
installed_path: '{project-root}/skills/bmad-voice-transcriber/workflows/connection-test'
---
```

### Mode

- [x] Create-only (steps-c/)
- [ ] Tri-modal (steps-c/, steps-e/, steps-v/)

---

## Planned Steps

| Step | Name | Goal |
|------|------|------|
| 01 | Load Config | Read API URL, port, prefix, and model name from module.yaml |
| 02 | Locate Test File | Confirm bundled `scripts/test.mp3` exists |
| 03 | Submit Request | Send test.mp3 to configured API endpoint |
| 04 | Validate Response | Check for successful transcription text in response |
| 05 | Report | Return success with latency, or detailed error with troubleshooting hints |

---

## Workflow Inputs

### Required Inputs

- None. All config read from `module.yaml`.

### Optional Inputs

- `test_audio_path`: Override the default bundled test file path.

---

## Workflow Outputs

### Output Format

- [ ] Document-producing
- [x] Non-document

### Output Files

- Console/log report: `Connection Successful. Engine: {model_name}. Latency: {ms}ms.` or error details.

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

_Spec created on 2026-04-17 via BMAD Module workflow_
