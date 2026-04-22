# transcribe.py — A0 Tool that orchestrates the full EVTC transcription pipeline
# Accepts an audio/video file path, transcodes, chunks, transcribes via API, stitches, and summarizes
# Part of the EVTC (Easy Voice Transcription Caller) plugin for Agent Zero

import os          # File path operations and existence checks
import tempfile    # Create temporary working directories for intermediate files
import shutil      # Directory cleanup after pipeline completes
import time        # Track total pipeline execution time
from pathlib import Path  # Resolve plugin directory for helper imports

from helpers.tool import Tool, Response  # A0 base Tool class and Response dataclass
from helpers.print_style import PrintStyle  # A0 styled console output for progress logging
from helpers import plugins  # A0 plugin config loader

# Resolve the plugin root directory (one level up from tools/)
PLUGIN_DIR = Path(__file__).resolve().parents[1]  # /path/to/voice-transcriber/

# Import EVTC helper modules from the plugin's helpers/ directory
# Uses sys.path insertion to support both dev (project dir) and installed (usr/plugins) locations
import sys  # System path manipulation for dynamic imports
sys.path.insert(0, str(PLUGIN_DIR))  # Add plugin root so 'helpers' package is importable

from helpers.transcoder import transcode, check_ffmpeg, get_supported_formats  # Audio format conversion
from helpers.chunker import chunk_audio  # WAV splitting into overlapping segments
from helpers.api_client import build_api_url, transcribe_all_chunks  # API URL construction and chunk submission
from helpers.stitcher import stitch_transcripts  # Reassemble transcript chunks with deduplication
from helpers.summarizer import build_summary_prompt, extract_json_from_response, summarize, save_summary  # JSON summary generation


class TranscribeTool(Tool):  # A0 Tool subclass for the transcribe action

    async def execute(self, **kwargs) -> Response:  # Main entry point called by A0 framework
        """Execute the full EVTC transcription pipeline on a given audio/video file."""

        await self.agent.handle_intervention()  # Wait for intervention and handle it, if paused

        # ── Step 0: Read arguments from self.args ──
        audio_file_path = self.args.get("audio_file_path", "").strip()  # Required: path to source media file
        output_format = self.args.get("output_format", "json").strip().lower()  # Optional: 'json' or 'text' (default: json)
        summary_fields_str = self.args.get("summary_fields", "").strip()  # Optional: comma-separated field list

        # Parse summary fields into a list if provided, otherwise use defaults
        summary_fields = None  # None means use all default fields from summarizer.py
        if summary_fields_str:  # Only parse if a non-empty string was provided
            summary_fields = [f.strip() for f in summary_fields_str.split(",") if f.strip()]  # Split CSV into list

        # ── Step 1: Validate required argument ──
        if not audio_file_path:  # audio_file_path is mandatory
            return Response(  # Return error immediately without crashing
                message="Error: 'audio_file_path' argument is required. Provide the absolute path to an audio or video file.",
                break_loop=False  # Allow agent to continue processing
            )

        # ── Step 2: Read plugin configuration ──
        cfg = plugins.get_plugin_config("evtc_voice_transcriber", agent=self.agent) or {}  # Load config or empty dict
        api_url_base = cfg.get("transcription_api_url", "http://127.0.0.1:8101")  # API base URL
        api_port = cfg.get("transcription_api_port", "")  # API port (may be empty if included in URL)
        api_prefix = cfg.get("transcription_api_prefix", "/v1")  # API endpoint prefix
        model_name = cfg.get("transcription_model_name", "")  # Model identifier string
        auto_remove = cfg.get("source_auto_remove", True)  # Whether to delete source file after success

        # ── Step 3: Validate input file exists ──
        if not os.path.exists(audio_file_path):  # Check the source file is on disk
            return Response(
                message=f"Error: Input file not found: {audio_file_path}",
                break_loop=False
            )

        # ── Step 4: Validate file format is supported ──
        file_ext = os.path.splitext(audio_file_path)[1].lower()  # Extract file extension
        supported = get_supported_formats()  # Get list of accepted extensions
        if file_ext not in supported:  # Reject unsupported formats early
            return Response(
                message=f"Error: Unsupported format '{file_ext}'. Supported formats: {supported}",
                break_loop=False
            )

        # ── Step 5: Check ffmpeg dependency ──
        if not check_ffmpeg():  # Verify ffmpeg is available for transcoding
            return Response(
                message="Error: ffmpeg not found on this system. Install ffmpeg to use the transcription tool.",
                break_loop=False
            )

        # ── Step 6: Build API URL ──
        api_url = build_api_url(api_url_base, api_port, api_prefix)  # Construct full API base URL
        PrintStyle(font_color="#1B4F72", bold=True).print(f"EVTC: API endpoint → {api_url}")  # Log target URL

        # ── Step 7: Create temporary working directory ──
        tmp_dir = tempfile.mkdtemp(prefix="evtc_")  # Create temp dir for intermediate files
        PrintStyle(font_color="#1B4F72").print(f"EVTC: Working directory → {tmp_dir}")  # Log temp dir path

        start_time = time.time()  # Record pipeline start time for total duration tracking

        try:
            # ── Step 8: Transcode to 16kHz mono WAV ──
            PrintStyle(font_color="#85C1E9").print("EVTC: [1/5] Transcoding to 16kHz mono WAV...")  # Progress
            wav_path = os.path.join(tmp_dir, "normalized.wav")  # Target WAV file path in temp dir
            transcode_result = transcode(audio_file_path, wav_path)  # Run ffmpeg conversion

            if not transcode_result["success"]:  # Check if transcoding failed
                return Response(
                    message=f"Error during transcoding: {transcode_result['error']}",
                    break_loop=False
                )

            # ── Step 9: Chunk the WAV file ──
            PrintStyle(font_color="#85C1E9").print("EVTC: [2/5] Chunking audio...")  # Progress
            chunks_dir = os.path.join(tmp_dir, "chunks")  # Sub-directory for chunk WAV files
            chunk_result = chunk_audio(wav_path, chunks_dir)  # Split WAV into overlapping segments

            if not chunk_result["success"]:  # Check if chunking failed
                return Response(
                    message=f"Error during chunking: {chunk_result['error']}",
                    break_loop=False
                )

            chunk_paths = chunk_result["chunks"]  # Ordered list of chunk file paths
            PrintStyle(font_color="#85C1E9").print(f"EVTC: Created {len(chunk_paths)} chunk(s)")  # Log chunk count

            # ── Step 10: Transcribe each chunk via API ──
            PrintStyle(font_color="#85C1E9").print("EVTC: [3/5] Sending chunks to transcription API...")  # Progress
            api_result = transcribe_all_chunks(chunk_paths, api_url, model_name)  # Sequential API calls

            if not api_result["success"]:  # Check if any chunk failed transcription
                errors_str = "; ".join(api_result.get("errors", []))  # Join all error messages
                return Response(
                    message=f"Error during transcription: {errors_str}",
                    break_loop=False
                )

            # ── Step 11: Stitch transcript chunks ──
            PrintStyle(font_color="#85C1E9").print("EVTC: [4/5] Stitching transcript...")  # Progress
            stitch_result = stitch_transcripts(api_result["texts"])  # Deduplicate and merge chunks

            if not stitch_result["success"]:  # Check if stitching failed
                return Response(
                    message=f"Error during stitching: {stitch_result['error']}",
                    break_loop=False
                )

            full_transcript = stitch_result["transcript"]  # The complete stitched transcript text

            # ── Step 12: Generate summary if JSON format requested ──
            summary_data = None  # Will hold structured summary dict if generated
            if output_format == "json":  # Only summarize when JSON output is requested
                PrintStyle(font_color="#85C1E9").print("EVTC: [5/5] Generating structured summary...")  # Progress
                summary_result = summarize(full_transcript, fields=summary_fields)  # Rule-based extraction

                if summary_result["success"]:  # Check if summarization succeeded
                    summary_data = summary_result["summary"]  # Store the structured dict
                else:  # Summarization failed but transcript is still valid
                    PrintStyle(font_color="#E74C3C").print(
                        f"EVTC: Summary generation warning: {summary_result['error']}"
                    )  # Log warning but continue
            else:  # Text-only output, skip summarization step
                PrintStyle(font_color="#85C1E9").print("EVTC: [5/5] Skipping summary (text output mode)")  # Progress

            # ── Step 13: Save outputs to disk ──
            # Determine output directory: same directory as the source file
            source_dir = os.path.dirname(audio_file_path)  # Directory containing the source media
            source_name = os.path.splitext(os.path.basename(audio_file_path))[0]  # Source filename without extension
            timestamp = time.strftime("%Y%m%d_%H%M%S")  # Timestamp for unique output filenames

            # Save transcript text file
            transcript_path = os.path.join(source_dir, f"{source_name}_{timestamp}_transcript.txt")  # Output path
            with open(transcript_path, "w", encoding="utf-8") as f:  # Write UTF-8 text file
                f.write(full_transcript)  # Write the full stitched transcript
            PrintStyle(font_color="#27AE60").print(f"EVTC: Transcript saved → {transcript_path}")  # Log output

            # Save JSON summary if generated
            summary_path = None  # Will hold path if summary was saved
            if summary_data:  # Only save if summary was successfully generated
                summary_path = os.path.join(source_dir, f"{source_name}_{timestamp}_summary.json")  # Output path
                save_result = save_summary(summary_data, summary_path)  # Write formatted JSON file
                if save_result["success"]:  # Check if file write succeeded
                    PrintStyle(font_color="#27AE60").print(f"EVTC: Summary saved → {summary_path}")  # Log output
                else:  # File write failed
                    PrintStyle(font_color="#E74C3C").print(
                        f"EVTC: Failed to save summary: {save_result['error']}"
                    )  # Log error but continue

            # ── Step 14: Auto-remove source file if enabled ──
            if auto_remove and os.path.exists(audio_file_path):  # Only if config enables auto-removal
                try:
                    os.remove(audio_file_path)  # Delete the original source media file
                    PrintStyle(font_color="#F39C12").print(
                        f"EVTC: Source file removed → {audio_file_path}"
                    )  # Log deletion
                except OSError as e:  # Handle permission or filesystem errors
                    PrintStyle(font_color="#E74C3C").print(
                        f"EVTC: Could not remove source: {e}"
                    )  # Log warning, not fatal

            # ── Step 15: Calculate total elapsed time ──
            elapsed_ms = int((time.time() - start_time) * 1000)  # Total pipeline time in milliseconds
            api_latency_ms = api_result.get("total_latency_ms", 0)  # Cumulative API call time

            # ── Step 16: Build result message ──
            result_lines = [  # Assemble human-readable result summary
                f"✓ Transcription complete",  # Success header
                f"  Source: {audio_file_path}",  # Input file
                f"  Chunks: {len(chunk_paths)}",  # Number of chunks processed
                f"  API latency: {api_latency_ms}ms",  # API call time
                f"  Total time: {elapsed_ms}ms",  # Full pipeline time
                f"  Transcript: {transcript_path}",  # Output transcript location
            ]

            if summary_path:  # Append summary path if it was generated
                result_lines.append(f"  Summary: {summary_path}")  # Output summary location

            if auto_remove:  # Note if source was removed
                result_lines.append(f"  Source removed: yes")  # Confirm deletion

            # Append a preview of the transcript (first 500 chars)
            preview_len = min(500, len(full_transcript))  # Cap preview length
            result_lines.append(f"\nTranscript preview:\n{full_transcript[:preview_len]}...")  # Preview text

            result_message = "\n".join(result_lines)  # Join all lines into final message

            return Response(message=result_message, break_loop=False)  # Return success result to agent

        except Exception as e:  # Catch any unhandled exceptions in the pipeline
            return Response(
                message=f"Error: Unexpected failure in transcription pipeline: {str(e)}",
                break_loop=False  # Allow agent to continue
            )

        finally:
            # ── Cleanup: Remove temporary working directory ──
            if os.path.exists(tmp_dir):  # Check temp dir still exists
                try:
                    shutil.rmtree(tmp_dir)  # Recursively delete temp dir and all contents
                    PrintStyle(font_color="#1B4F72").print(f"EVTC: Cleaned up {tmp_dir}")  # Log cleanup
                except OSError as e:  # Handle cleanup failure gracefully
                    PrintStyle(font_color="#E74C3C").print(
                        f"EVTC: Warning — could not clean up temp dir: {e}"
                    )  # Log warning, not fatal
