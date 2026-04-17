# transcoder.py — Converts audio/video files to a normalized WAV format for transcription
# Part of the EVTC (Easy Voice Transcription Caller) module for Agent Zero
# Requires: ffmpeg installed on the system (auto-checked at runtime)

import subprocess  # Used to call ffmpeg as a system process
import os          # Used for file path operations and existence checks
import shutil      # Used to check if ffmpeg binary is available in PATH


def check_ffmpeg() -> bool:
    # Verify that ffmpeg is available on the system before attempting transcoding
    return shutil.which('ffmpeg') is not None  # Returns True if ffmpeg is found in PATH


def get_supported_formats() -> list:
    # Return the list of audio/video formats that EVTC accepts as input
    return ['.mp3', '.wav', '.mp4', '.m4a', '.ogg', '.flac', '.aac', '.webm']  # Common meeting recording formats


def transcode(input_path: str, output_path: str, sample_rate: int = 16000) -> dict:
    # Convert any supported audio/video file to a mono 16kHz WAV file for the transcription engine
    # input_path: absolute path to the source media file
    # output_path: absolute path where the normalized WAV will be written
    # sample_rate: target sample rate in Hz (16000 is optimal for Whisper-based models)
    # Returns a dict with 'success' bool, 'output_path' str, and 'error' str if failed

    result = {'success': False, 'output_path': output_path, 'error': None}  # Initialize result dict

    # Check that ffmpeg is available before proceeding
    if not check_ffmpeg():
        result['error'] = 'ffmpeg not found. Install ffmpeg or add it to PATH.'  # User-friendly error message
        return result  # Return early with failure state

    # Check that the input file actually exists on disk
    if not os.path.exists(input_path):
        result['error'] = f'Input file not found: {input_path}'  # Report the missing file path
        return result  # Return early with failure state

    # Get the file extension to verify the format is supported
    ext = os.path.splitext(input_path)[1].lower()  # Extract and normalize the file extension
    if ext not in get_supported_formats():  # Check against the supported format list
        result['error'] = f'Unsupported format: {ext}. Supported: {get_supported_formats()}'  # List valid options
        return result  # Return early with failure state

    # Build the ffmpeg command to normalize the audio
    # -i: input file
    # -ac 1: convert to mono (single channel, reduces API payload size)
    # -ar: set audio sample rate to target Hz
    # -y: overwrite output file without asking
    cmd = [
        'ffmpeg',          # Call ffmpeg binary
        '-i', input_path,  # Specify input file path
        '-ac', '1',        # Force mono audio channel
        '-ar', str(sample_rate),  # Set sample rate (default 16000 Hz)
        '-y',              # Overwrite output without prompt
        output_path        # Write result to this path
    ]

    try:
        # Execute the ffmpeg command as a subprocess, capturing stdout and stderr
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5-minute timeout for large files

        # Check if ffmpeg exited with a non-zero return code (indicates failure)
        if proc.returncode != 0:
            result['error'] = f'ffmpeg failed: {proc.stderr}'  # Include ffmpeg stderr for debugging
            return result  # Return failure result

        # Verify the output file was actually created
        if not os.path.exists(output_path):
            result['error'] = 'ffmpeg completed but output file not found'  # Unexpected state
            return result  # Return failure result

        # All checks passed — mark transcoding as successful
        result['success'] = True  # Set success flag
        return result  # Return success result with output path

    except subprocess.TimeoutExpired:
        # Handle case where ffmpeg takes longer than 5 minutes
        result['error'] = 'Transcoding timed out after 300 seconds'  # Report timeout
        return result  # Return failure result

    except Exception as e:
        # Catch any unexpected errors and include the message for debugging
        result['error'] = f'Unexpected error during transcoding: {str(e)}'  # General error handler
        return result  # Return failure result
