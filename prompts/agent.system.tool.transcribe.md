## Tool: transcribe
Transcribe an audio or video file and generate a structured summary.

Pipeline: transcode → chunk → API transcribe → stitch → summarize.
All audio is automatically converted to 16kHz mono WAV before submission.

### Args
- **audio_file_path** (required): Absolute path to the media file to transcribe.
  Supported formats: .mp3, .wav, .mp4, .m4a, .ogg, .flac, .aac, .webm
- **output_format** (optional): `"json"` (default) or `"text"`.
  JSON mode generates a structured meeting summary alongside the transcript.
  Text mode returns only the raw transcript.
- **summary_fields** (optional): Comma-separated list of summary fields to include.
  Available fields: subject, action_items, detailed_topics, resourcing, commitments.
  Default: all fields.

### Output
- Saves `{filename}_{timestamp}_transcript.txt` alongside the source file.
- If JSON mode, also saves `{filename}_{timestamp}_summary.json`.
- If `source_auto_remove` is enabled in config, deletes the source file after success.
- Returns a status report with chunk count, latency, output paths, and transcript preview.

### Requirements
- ffmpeg must be installed on the system.
- Transcription API must be running and configured in plugin settings.
