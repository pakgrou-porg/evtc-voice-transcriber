# test_connection.py — A0 Tool that validates connectivity to the transcription API
# Sends the bundled test.mp3 file to the configured endpoint and reports success/failure
# Part of the EVTC (Easy Voice Transcription Caller) plugin for Agent Zero

import os          # File path operations and existence checks
import time        # Measure API response latency
from pathlib import Path  # Resolve plugin directory for locating test audio

from helpers.tool import Tool, Response  # A0 base Tool class and Response dataclass
from helpers.print_style import PrintStyle  # A0 styled console output for progress logging
from helpers import plugins  # A0 plugin config loader

# Resolve the plugin root directory (one level up from tools/)
PLUGIN_DIR = Path(__file__).resolve().parents[1]  # /path/to/voice-transcriber/

# Import EVTC helper modules using A0 plugin import convention
from usr.plugins.evtc_voice_transcriber.helpers.transcoder import check_ffmpeg  # Check ffmpeg availability
from usr.plugins.evtc_voice_transcriber.helpers.api_client import build_api_url, transcribe_chunk  # API URL construction and single chunk transcription


class TestConnectionTool(Tool):  # A0 Tool subclass for the test_connection action

    async def execute(self, **kwargs) -> Response:  # Main entry point called by A0 framework
        """Test connectivity to the transcription API using the bundled test audio file."""

        await self.agent.handle_intervention()  # Wait for intervention and handle it, if paused

        # ── Step 1: Read plugin configuration ──
        cfg = plugins.get_plugin_config("evtc_voice_transcriber", agent=self.agent) or {}  # Load config or empty dict
        api_url_base = cfg.get("transcription_api_url", "http://127.0.0.1:8101")  # API base URL
        api_port = cfg.get("transcription_api_port", "")  # API port (may be empty if included in URL)
        api_prefix = cfg.get("transcription_api_prefix", "/v1")  # API endpoint prefix
        model_name = cfg.get("transcription_model_name", "")  # Model identifier string

        # ── Step 2: Locate the bundled test audio file ──
        test_audio_path = str(PLUGIN_DIR / "helpers" / "test.mp3")  # Path to bundled test file

        if not os.path.exists(test_audio_path):  # Verify the test file is present
            return Response(
                message=f"Error: Bundled test audio not found at: {test_audio_path}",
                break_loop=False  # Allow agent to continue
            )

        # ── Step 3: Check ffmpeg dependency ──
        if not check_ffmpeg():  # Verify ffmpeg is available for transcoding
            return Response(
                message="Error: ffmpeg not found on this system. Install ffmpeg to test the connection.",
                break_loop=False
            )

        # ── Step 4: Build the full API URL ──
        api_url = build_api_url(api_url_base, api_port, api_prefix)  # Construct full API base URL
        PrintStyle(font_color="#1B4F72", bold=True).print(f"EVTC Test: API endpoint → {api_url}")  # Log target

        # ── Step 5: Send test audio to the API ──
        PrintStyle(font_color="#85C1E9").print("EVTC Test: Sending bundled test.mp3 to transcription API...")  # Progress
        start_time = time.time()  # Record start time for latency

        try:
            result = transcribe_chunk(test_audio_path, api_url, model_name)  # Send test file to API
        except Exception as e:  # Catch any unexpected errors during the API call
            return Response(
                message=f"Error: Connection test failed with unexpected error: {str(e)}",
                break_loop=False
            )

        total_ms = int((time.time() - start_time) * 1000)  # Calculate total elapsed time

        # ── Step 6: Report results ──
        if result["success"]:  # API call succeeded and returned transcript text
            transcript_preview = result["text"][:200]  # Show first 200 chars of transcript
            report_lines = [  # Assemble success report
                "✓ Connection test PASSED",  # Success header
                f"  API URL: {api_url}",  # Target endpoint
                f"  Model: {model_name or '(default)'}",  # Model used
                f"  Latency: {result.get('latency_ms', total_ms)}ms",  # API response time
                f"  Total time: {total_ms}ms",  # Including conversion overhead
                f"  Transcript preview: {transcript_preview}",  # Sample of returned text
            ]
            PrintStyle(font_color="#27AE60", bold=True).print("EVTC Test: ✓ PASSED")  # Log success
            return Response(message="\n".join(report_lines), break_loop=False)  # Return success

        else:  # API call failed
            report_lines = [  # Assemble failure report
                "✗ Connection test FAILED",  # Failure header
                f"  API URL: {api_url}",  # Target endpoint
                f"  Model: {model_name or '(default)'}",  # Model attempted
                f"  Error: {result.get('error', 'Unknown error')}",  # Error details
                f"  Total time: {total_ms}ms",  # Time before failure
                "",  # Blank line for readability
                "Troubleshooting:",  # Help section header
                "  1. Verify the transcription engine is running",  # Check server
                "  2. Check API URL, port, and prefix in plugin settings",  # Check config
                "  3. Ensure the model name is correct",  # Check model
                "  4. Check network connectivity to the API host",  # Check network
            ]
            PrintStyle(font_color="#E74C3C", bold=True).print("EVTC Test: ✗ FAILED")  # Log failure
            return Response(message="\n".join(report_lines), break_loop=False)  # Return failure
