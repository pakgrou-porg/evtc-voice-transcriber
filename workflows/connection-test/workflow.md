# Connection Test

_Validate the EVTC transcription engine configuration using the bundled dialog test audio file._

**⚠️ LLM EXECUTION RULES (MANDATORY):**
- Execute ALL steps in EXACT ORDER
- DO NOT skip steps
- HALT and report clearly if any step fails — do not proceed past a failure
- Report latency and engine info on success

**📋 AUDIO PROCESSING NOTE:**
All audio is converted to **16kHz mono WAV** format before being sent to the transcription service.
This is mandatory for compatibility with all supported engines regardless of source format.

---

## Step 1 — Load Configuration

- **Action:** Read `module.yaml` from `{project-root}/skills/bmad-voice-transcriber/module.yaml`
- **Extract:** `transcription_api_url`, `transcription_api_port`, `transcription_api_prefix`, `transcription_model_name`, `transcription_language`
- **Build:** Full API URL using `api_client.build_api_url(url, port, prefix)`
- **Report:** `Testing connection to: {full_api_url}` with model name

## Step 2 — Locate Test Audio File

- **Action:** Verify the bundled test file exists at `{project-root}/skills/bmad-voice-transcriber/scripts/test.mp3`
- **IF NOT FOUND:** Report error: `Test file missing. Expected: scripts/test.mp3` and HALT
- **Report:** `Test file found: test.mp3 (~7s dialog audio)`

## Step 3 — Convert to 16kHz Mono WAV

- **Action:** Call `api_client.ensure_wav_16khz_mono(test_mp3_path, tmp_dir)` to convert the test file
- **This converts:** Source MP3 → 16kHz mono WAV (required format for all transcription engines)
- **IF FAIL:** Report `Audio conversion failed: {error}. Is ffmpeg installed?` and HALT
- **Report:** `Audio converted to 16kHz mono WAV for submission`

## Step 4 — Submit Test Request

- **Action:** Call `api_client.transcribe_chunk(test_mp3_path, api_url, model_name)` (WAV conversion is automatic)
- **Action:** Record start time before call, end time after response
- **Calculate:** Latency in milliseconds

## Step 5 — Validate Response

- **Check:** HTTP 200 received from engine
- **Check:** Response contains non-empty `text` or `transcript` field
- **IF FAIL:** Report specific error with troubleshooting hints:
  - HTTP 400 (Invalid audio) → Audio format issue — check ffmpeg is installed and working
  - HTTP 404 → Check API prefix (e.g., `/v1` vs `/api`)
  - HTTP 401/403 → Check API key configuration
  - Connection refused → Verify engine is running and port is correct
  - Empty transcript → Check model name matches engine registration
- **IF SUCCESS:** Proceed to Step 6

## Step 6 — Report Result

**On Success:**
```
✅ Connection Successful
Engine: {model_name}
URL: {full_api_url}
Latency: {latency_ms}ms
Audio format: 16kHz mono WAV (converted from MP3)
Test transcript preview: "{first_50_chars_of_text}..."
Ready to transcribe.
```

**On Failure:**
```
❌ Connection Failed
Error: {specific_error}
Troubleshooting: {hint}
```
