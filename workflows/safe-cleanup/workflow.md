# Safe Cleanup

_Safely delete source audio/video files after verifying successful transcription. Invoked automatically by Transcribe & Analyze when auto-remove is enabled, or manually by the user._

**⚠️ LLM EXECUTION RULES (MANDATORY):**
- Execute ALL steps in EXACT ORDER
- HALT immediately if any safety check fails — do NOT delete the source file
- Log every action including successful deletions and aborted attempts
- NEVER delete unless BOTH success checks pass

---

## Step 1 — Check Auto-Remove Configuration

- **Action:** Read `source_auto_remove` value from `module.yaml`
- **IF `source_auto_remove` is false/disabled:** Report `Auto-remove is disabled. Source file preserved.` and EXIT (no deletion)
- **IF `source_auto_remove` is true:** Continue to Step 2
- **Report:** `Auto-remove enabled. Proceeding with safety checks...`

## Step 2 — Verify Transcription Success Code

- **Check:** Was the transcription API call completed with HTTP 200 or equivalent success status?
- **IF NOT:** Report `Safety check failed: No verified success code from engine. Source file PRESERVED.` and EXIT
- **Report:** `✅ Safety check 1/2: API returned verified success code`

## Step 3 — Verify Transcript Content

- **Check:** Does the output transcript file exist at `{transcript_output_path}`?
- **Check:** Is the output transcript file non-empty (size > 0 bytes)?
- **IF NOT:** Report `Safety check failed: Transcript file is missing or empty. Source file PRESERVED.` and EXIT
- **Report:** `✅ Safety check 2/2: Transcript file confirmed non-empty`

## Step 4 — Delete Source File

- **Action:** Delete the source media file at `{source_file_path}`
- **IF DELETION FAILS:** Report `Deletion failed: {os_error}. Manual cleanup may be needed.` and EXIT
- **Report:** `🗑️ Source file deleted: {source_filename}`

## Step 5 — Log Deletion

- **Action:** Append a log entry to `{output_folder}/logs/cleanup.log`
- **Log format:** `[{timestamp}] DELETED: {source_filename} | Success code: {status_code} | Transcript: {transcript_filename} ({size} bytes)`
- **Create log directory** if it does not exist
- **Report:** `Cleanup logged to cleanup.log`

## Step 6 — Return Result

**On Success:**
```
✅ Safe Cleanup Complete
Deleted: {source_filename}
Transcript preserved: {transcript_path}
Log entry written: {output_folder}/logs/cleanup.log
```

**On Any Safety Failure:**
```
⚠️ Cleanup Aborted — Source File Safe
Reason: {specific_safety_check_that_failed}
Source file: {source_filepath} [PRESERVED]
```
