# Transcribe & Analyze

_End-to-end processing of audio/video files into full transcripts and structured JSON meeting summaries._

**⚠️ LLM EXECUTION RULES (MANDATORY):**
- Execute ALL steps in EXACT ORDER
- DO NOT skip steps
- HALT and report clearly if any step fails — do not proceed past a failure
- Report progress at each step so the user knows the pipeline is running
- Log chunk count and estimated completion before submitting to API

---

## Step 1 — Validate Input

- **Action:** Confirm an audio or video file was provided (attached or path given)
- **Check:** File extension is one of: `.mp3`, `.wav`, `.mp4`, `.m4a`, `.ogg`, `.flac`, `.aac`, `.webm`
- **Check:** File exists and is not zero bytes
- **IF FAIL:** Report `Unsupported or missing file. Accepted formats: MP3, WAV, MP4, M4A, OGG, FLAC` and HALT
- **Report:** `Input validated: {filename} ({size}MB)`

## Step 2 — Load Configuration

- **Action:** Read configuration from `module.yaml` (API URL, port, prefix, model name, auto-remove setting)
- **Build:** Full API connection string using `api_client.build_api_url(url, port, prefix)`
- **Report:** `Engine: {model_name} @ {api_url}`

## Step 3 — Transcode Audio

- **Action:** Call `transcoder.transcode(input_path, output_wav_path, sample_rate=16000)`
- **This converts:** Any format → mono 16kHz WAV (optimal for all supported engines)
- **IF FAIL:** Report `Transcoding failed: {error}. Is ffmpeg installed?` and HALT
- **Report:** `Transcoded to WAV: {duration}s`

## Step 4 — Chunk Audio

- **Action:** Call `chunker.chunk_audio(wav_path, chunk_dir, chunk_minutes=12, overlap_seconds=1)`
- **This splits:** Long files into 12-minute segments with 1-second overlaps for continuity
- **IF 1 chunk only:** Note that file is short enough to process in a single pass
- **Report:** `Split into {n} chunk(s) with 1-second overlaps`

## Step 5 — Transcribe Chunks

- **Action:** Call `api_client.transcribe_all_chunks(chunk_paths, api_url, model_name)`
- **This submits:** Each chunk sequentially to the configured transcription engine
- **Report progress:** `Transcribing chunk {n}/{total}...` for each chunk
- **IF ANY CHUNK FAILS:** Report `Chunk {n} failed: {error}` and HALT (do not partial-save)
- **Report:** `All {n} chunks transcribed successfully. Total latency: {ms}ms`

## Step 6 — Stitch Transcript

- **Action:** Call `stitcher.stitch_transcripts(chunk_texts)`
- **This removes:** Duplicate phrases introduced by the 1-second overlaps
- **Result:** One clean, continuous transcript text
- **Report:** `Transcript stitched: {word_count} words`

## Step 7 — Generate Summary

- **Action:** Call `summarizer.build_summary_prompt(transcript)` and send to the active LLM
- **Extract:** `subject`, `action_items`, `detailed_topics`, `resourcing`, `commitments`
- **Parse:** JSON response using `summarizer.extract_json_from_response(llm_response)`
- **Save transcript:** `{output_folder}/transcripts/{filename}-transcript.txt`
- **Save summary:** `{output_folder}/transcripts/{filename}-summary.json`

## Step 8 — Safe Cleanup (Conditional)

- **Check:** Is `source_auto_remove` enabled in config?
- **IF YES:** Load and execute `{project-root}/skills/bmad-voice-transcriber/workflows/safe-cleanup/workflow.md`
  - Pass: source file path, transcription success=true, transcript output path
- **IF NO:** Skip cleanup, notify user: `Source file preserved (auto-remove disabled)`

## Step 9 — Return Results

**On Success:**
```
✅ Transcription Complete
File: {original_filename}
Duration: {audio_duration}s
Chunks processed: {n}
Total API latency: {ms}ms

Transcript saved: {transcript_path}
Summary saved:    {summary_path}

Meeting Summary Preview:
  Subject: {subject}
  Action Items: {count}
  Topics: {count}
```

**On Failure:**
```
❌ Transcription Failed at Step {n}
Error: {specific_error}
Source file: PRESERVED (not deleted)
```
