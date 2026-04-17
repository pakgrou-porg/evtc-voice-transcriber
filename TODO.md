# TODO: Easy Voice Transcription Caller (EVTC)

Development roadmap for voice-transcriber module.

---

## Agents to Build

- [ ] EVTC Transcriber (Transcription Specialist)
  - Use: `bmad:bmb:agents:agent-builder`
  - Spec: `agents/evtc-transcriber.spec.md`

---

## Workflows to Build

- [ ] transcribe-and-analyze
  - Use: `bmad:bmb:workflows:workflow` or `/workflow`
  - Spec: `workflows/transcribe-and-analyze/transcribe-and-analyze.spec.md`
- [ ] connection-test
  - Use: `bmad:bmb:workflows:workflow` or `/workflow`
  - Spec: `workflows/connection-test/connection-test.spec.md`
- [ ] safe-cleanup
  - Use: `bmad:bmb:workflows:workflow` or `/workflow`
  - Spec: `workflows/safe-cleanup/safe-cleanup.spec.md`

---

## Scripts to Create

- [ ] `scripts/transcoder.py` — FFmpeg wrapper for normalizing audio formats
- [ ] `scripts/chunker.py` — Splits audio into overlapping chunks
- [ ] `scripts/stitcher.py` — Reassembles chunks, removes 1-sec overlap duplicates
- [ ] `scripts/api_client.py` — Sends chunks to configured transcription API
- [ ] `scripts/summarizer.py` — Generates structured JSON summary from transcript
- [ ] `scripts/test.mp3` — Bundled 5-second test audio file

---

## Installation Testing

- [ ] Test installation with `bmad install`
- [ ] Verify module.yaml prompts work correctly in A0 Configure UI
- [ ] Verify `Test Connection` sends test.mp3 and returns response
- [ ] Verify all agents and workflows are discoverable
- [ ] Verify auto-remove only triggers on verified success

---

## Documentation

- [ ] Complete `docs/getting-started.md` with setup walkthrough
- [ ] Complete `docs/agents.md` with EVTC Transcriber reference
- [ ] Complete `docs/workflows.md` with all 3 workflow guides
- [ ] Complete `docs/examples.md` with real-world usage examples
- [ ] Add troubleshooting section to docs
- [ ] Document all configuration options with examples

---

## Quality & Testing

- [ ] Unit tests for chunker (verify overlap logic)
- [ ] Unit tests for stitcher (verify deduplication)
- [ ] Unit tests for api_client (verify retry/error handling)
- [ ] Integration test: full pipeline with local Whisper
- [ ] Integration test: full pipeline with cloud API
- [ ] Test with MP3, WAV, and MP4 formats
- [ ] Test with files under 10 min and over 60 min

---

## Next Steps

1. Build agents using create-agent workflow
2. Build workflows using create-workflow workflow
3. Create scripts with line-by-line comments
4. Test installation and pipeline functionality
5. Iterate based on community feedback

---

_Last updated: 2026-04-17_
