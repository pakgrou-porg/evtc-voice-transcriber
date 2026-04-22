## Tool: test_connection
Test the transcription engine connection using a bundled test audio file.

Sends a short (~7 second) dialog clip to the configured transcription API
and reports success/failure with latency metrics.

### Args
No arguments required. Reads all configuration from plugin settings.

### Output
- On success: API URL, model name, response latency, and a preview of the transcribed text.
- On failure: Error details and troubleshooting steps.

### Requirements
- ffmpeg must be installed on the system.
- Transcription API must be running and reachable.
