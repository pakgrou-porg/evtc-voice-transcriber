# api_client.py — Sends audio chunks to the configured transcription API and returns text
# Part of the EVTC (Easy Voice Transcription Caller) module for Agent Zero
# Supports local (Whisper, Cohere) and cloud (OpenAI, Amazon STT, Turboscribe) endpoints
# IMPORTANT: All audio is converted to 16kHz mono WAV before sending to the transcription service

import requests   # HTTP library for sending multipart audio file requests to the API
import os         # Used for file path operations and checking file existence
import time       # Used for measuring API latency and implementing retry delays
import tempfile   # Used to create a temporary directory for WAV conversion before upload
import shutil     # Used to check if ffmpeg is available for audio conversion


# Default timeout for API requests in seconds (5 minutes for large chunks)
DEFAULT_TIMEOUT = 300

# Number of times to retry a failed request before giving up
MAX_RETRIES = 3

# Seconds to wait between retry attempts (increases with each attempt)
RETRY_DELAY = 2

# Target sample rate for all audio sent to the transcription service
TARGET_SAMPLE_RATE = 16000  # 16kHz mono WAV is required by all supported transcription engines


def build_api_url(base_url: str, port: str, prefix: str) -> str:
    # Construct the full API base URL from its three components
    # base_url: e.g., 'http://127.0.0.1'
    # port: e.g., '8080' or '' for cloud URLs using standard ports
    # prefix: e.g., '/v1' or '' for root

    url = base_url.rstrip('/')  # Remove any trailing slash from the base URL for clean joining

    if port and not base_url.startswith('https://'):  # Only append port for non-HTTPS URLs with a port set
        url = f'{url}:{port}'  # Append port number to the URL

    if prefix:  # Only append prefix if one is configured
        url = f'{url}{prefix}'  # Append the API prefix path

    return url  # Return the fully constructed base URL


def ensure_wav_16khz_mono(audio_path: str, tmp_dir: str) -> str:
    # Convert any audio file to 16kHz mono WAV format required by the transcription service
    # ALL audio must be in 16kHz mono WAV format before being sent to the transcription API
    # audio_path: absolute path to the source audio file (any supported format)
    # tmp_dir: temporary directory to write the converted WAV file into
    # Returns the path to the converted WAV file

    # Build the output WAV path in the temporary directory
    base_name = os.path.splitext(os.path.basename(audio_path))[0]  # Strip original extension
    wav_path = os.path.join(tmp_dir, f'{base_name}_16khz_mono.wav')  # Target WAV filename

    # If the file is already a WAV, verify it still meets the 16kHz mono requirement via ffmpeg
    # We always re-encode to guarantee the correct format regardless of source specification
    import subprocess  # Import here to keep module-level imports clean

    # Build ffmpeg command to normalize audio to 16kHz mono WAV
    cmd = [
        'ffmpeg',            # Call ffmpeg binary for format conversion
        '-i', audio_path,    # Input: source audio file
        '-ac', '1',          # Force mono channel (required by transcription engines)
        '-ar', str(TARGET_SAMPLE_RATE),  # Force 16kHz sample rate (required by transcription engines)
        '-y',                # Overwrite output file without prompting
        wav_path             # Output: normalized WAV file
    ]

    # Execute the conversion, suppressing stdout/stderr for clean pipeline logging
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5-minute timeout

    if proc.returncode != 0:  # Check if ffmpeg conversion failed
        raise RuntimeError(f'WAV conversion failed: {proc.stderr}')  # Raise with ffmpeg error details

    if not os.path.exists(wav_path):  # Verify the output file was actually created
        raise RuntimeError(f'WAV output file not found after conversion: {wav_path}')  # Unexpected failure

    return wav_path  # Return path to the 16kHz mono WAV file ready for upload


def transcribe_chunk(chunk_path: str, api_url: str, model_name: str, api_key: str = None) -> dict:
    # Send a single audio chunk to the transcription API and return the transcript text
    # NOTE: Audio is automatically converted to 16kHz mono WAV before sending to the API
    # chunk_path: absolute path to the audio chunk file to transcribe (any supported format)
    # api_url: full base URL including port and prefix (from build_api_url)
    # model_name: exact model identifier string expected by the API
    # api_key: optional API key for cloud services (None for local engines)
    # Returns dict with 'success' bool, 'text' str, 'latency_ms' int, and 'error' str if failed

    result = {'success': False, 'text': '', 'latency_ms': 0, 'error': None}  # Initialize result

    # Verify the chunk file exists before attempting to convert and upload it
    if not os.path.exists(chunk_path):
        result['error'] = f'Chunk file not found: {chunk_path}'  # Report missing file
        return result  # Return failure early

    # Build the full transcription endpoint URL (OpenAI-compatible /audio/transcriptions)
    endpoint = f'{api_url}/audio/transcriptions'  # Standard endpoint path for Whisper-compatible APIs

    # Build request headers — include Authorization only if an API key is provided
    headers = {}  # Start with empty headers dict
    if api_key:  # Only add Authorization header if an API key was provided
        headers['Authorization'] = f'Bearer {api_key}'  # Standard Bearer token format

    attempt = 0  # Track which retry attempt we are on

    # Use a temporary directory for WAV conversion — auto-cleaned when the block exits
    with tempfile.TemporaryDirectory() as tmp_dir:  # Create a temp dir that auto-deletes on exit

        try:
            # Convert the audio chunk to 16kHz mono WAV before sending to the transcription service
            # This ensures compatibility with all supported engines regardless of source format
            wav_path = ensure_wav_16khz_mono(chunk_path, tmp_dir)  # Convert to required WAV format

        except Exception as e:
            # Conversion failed — cannot proceed without valid 16kHz mono WAV
            result['error'] = f'Audio conversion to 16kHz mono WAV failed: {str(e)}'  # Report conversion error
            return result  # Return failure early

        while attempt < MAX_RETRIES:  # Retry loop up to MAX_RETRIES times
            attempt += 1  # Increment attempt counter
            start_time = time.time()  # Record start time for latency calculation

            try:
                # Open the converted WAV file in binary mode for upload
                with open(wav_path, 'rb') as audio_file:  # Open 16kHz mono WAV as binary stream
                    files = {'file': (os.path.basename(wav_path), audio_file, 'audio/wav')}  # Multipart WAV upload
                    data = {'model': model_name} if model_name else {}  # Include model name if provided

                    # Send the POST request with the WAV audio file
                    response = requests.post(
                        endpoint,          # Full endpoint URL
                        headers=headers,   # Auth headers (may be empty for local)
                        files=files,       # Multipart 16kHz mono WAV file upload
                        data=data,         # Model name parameter
                        timeout=DEFAULT_TIMEOUT  # Apply timeout to prevent hanging indefinitely
                    )

                latency_ms = int((time.time() - start_time) * 1000)  # Calculate elapsed time in ms
                result['latency_ms'] = latency_ms  # Store latency in result

                # Check for HTTP error status codes (4xx and 5xx)
                if response.status_code != 200:
                    result['error'] = f'API returned HTTP {response.status_code}: {response.text}'  # Include body
                    if attempt < MAX_RETRIES:  # Only sleep and retry if we have attempts remaining
                        time.sleep(RETRY_DELAY * attempt)  # Exponential backoff between retries
                    continue  # Try again

                # Parse the JSON response body
                response_json = response.json()  # Deserialize the JSON response

                # Extract transcript text — handle both 'text' and 'transcript' key formats
                text = response_json.get('text') or response_json.get('transcript', '')  # Try both key names

                if not text:  # If the API returned no text, treat as a failed transcription
                    result['error'] = f'API returned empty transcript for chunk: {chunk_path}'  # Empty result
                    return result  # Return failure

                result['success'] = True  # Mark request as successful
                result['text'] = text.strip()  # Store cleaned transcript text
                return result  # Return success result

            except requests.exceptions.Timeout:
                # Handle requests that exceed the timeout duration
                result['error'] = f'Request timed out after {DEFAULT_TIMEOUT}s (attempt {attempt})'  # Timeout
                if attempt < MAX_RETRIES:  # Retry if attempts remain
                    time.sleep(RETRY_DELAY * attempt)  # Wait before retrying

            except requests.exceptions.ConnectionError as e:
                # Handle network connectivity errors (engine not running, wrong port, etc.)
                result['error'] = f'Connection failed: {str(e)} (attempt {attempt})'  # Include error details
                if attempt < MAX_RETRIES:  # Retry if attempts remain
                    time.sleep(RETRY_DELAY * attempt)  # Wait before retrying

            except Exception as e:
                # Catch any other unexpected errors
                result['error'] = f'Unexpected error: {str(e)}'  # General error handler
                return result  # Do not retry on unexpected errors

    return result  # Return after exhausting all retry attempts


def transcribe_all_chunks(chunk_paths: list, api_url: str, model_name: str, api_key: str = None) -> dict:
    # Transcribe a list of audio chunks sequentially and return all results
    # NOTE: Each chunk is automatically converted to 16kHz mono WAV before sending to the API
    # chunk_paths: ordered list of chunk file paths (from chunker.py)
    # Returns dict with 'success' bool, 'texts' list of str, 'errors' list, and 'total_latency_ms' int

    result = {'success': False, 'texts': [], 'errors': [], 'total_latency_ms': 0}  # Initialize result

    for i, chunk_path in enumerate(chunk_paths):  # Iterate over each chunk in order
        print(f'Transcribing chunk {i+1}/{len(chunk_paths)}: {os.path.basename(chunk_path)} [converting to 16kHz mono WAV...]')  # Progress

        chunk_result = transcribe_chunk(chunk_path, api_url, model_name, api_key)  # Transcode + submit

        result['total_latency_ms'] += chunk_result.get('latency_ms', 0)  # Accumulate total latency

        if not chunk_result['success']:  # If this chunk failed, record the error and stop
            result['errors'].append(f'Chunk {i}: {chunk_result["error"]}')  # Log the failure
            return result  # Fail fast — do not continue if a chunk fails

        result['texts'].append(chunk_result['text'])  # Append successful transcript text to list

    result['success'] = True  # All chunks transcribed successfully
    return result  # Return complete result with all texts
