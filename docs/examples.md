# Examples

## Example 1: Transcribe a Short Meeting (MP3)

**Scenario:** Alex has a 30-minute team standup recorded as `standup-2026-04-17.mp3`.

**Step 1:** Attach the file in Agent Zero and type:
```
Transcribe this file and give me a meeting summary.
```

**Step 2:** EVTC processes and returns:

`standup-2026-04-17-transcript.txt`
```
[Speaker 1 - 00:00]: Good morning everyone. Today's priorities are...
[Speaker 2 - 00:45]: I finished the API integration yesterday...
...
```

`standup-2026-04-17-summary.json`
```json
{
  "subject": "Daily Standup – April 17, 2026",
  "action_items": [
    "Alice to complete PR review by EOD",
    "Bob to update staging environment"
  ],
  "detailed_topics": [
    "API integration status",
    "Staging environment blocker",
    "Sprint velocity update"
  ],
  "resourcing": [],
  "commitments": [
    "Team committed to sprint goal delivery by Friday"
  ]
}
```

---

## Example 2: Long Meeting with Multiple Speakers (MP4)

**Scenario:** Sarah needs to process a 90-minute board meeting recorded as `board-meeting-q2.mp4`.

**What happens behind the scenes:**
1. EVTC validates the MP4 format.
2. FFmpeg transcodes audio to a normalized WAV.
3. The file is split into 7 chunks (~13 min each) with 1-second overlaps.
4. Each chunk is sent sequentially to the local Whisper engine.
5. Responses are stitched back together, removing duplicate text from the overlaps.
6. The full transcript (with speaker labels) is passed to A0 for summary generation.

**Result:** A clean 90-minute transcript and structured JSON summary — no memory crashes, no cut-off sentences.

---

## Example 3: Switch from Local to Cloud Engine

**Scenario:** Alex's local Whisper model is struggling with heavy accents.

**Step 1:** Go to Agent Zero Configure → EVTC → Change `engine_type` to `Cloud Turboscribe.ai`.
**Step 2:** Enter the Turboscribe API key.
**Step 3:** Click **Test Connection** — success confirmed.
**Step 4:** Re-run the same transcription workflow without any code changes.

**Result:** Turboscribe handles the accent with higher accuracy. Alex switches back to local when the accent issue is resolved — just one dropdown change.

---

## Example 4: Manual Cleanup (Override Auto-Remove)

**Scenario:** The `source_auto_remove` setting is enabled, but Alex wants to keep a specific file.

Simply disable `source_auto_remove` in the Configure UI before processing that file. Re-enable it afterward.

---

## Example 5: Validate Before Processing

**Scenario:** Alex installed EVTC on a new server and wants to confirm it's working before processing real meetings.

```
test
```

EVTC sends the bundled `test.mp3` to the configured engine and reports:
```
Connection Successful. Engine: whisper-large. Latency: 840ms.
Ready to transcribe.
```
