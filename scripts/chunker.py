# chunker.py — Splits a WAV audio file into overlapping segments for sequential transcription
# Part of the EVTC (Easy Voice Transcription Caller) module for Agent Zero
# Requires: wave (standard library), math (standard library)

import wave    # Standard library module for reading and writing WAV files
import math    # Standard library module for ceiling division on chunk counts
import os      # Used for building output file paths and creating directories


def get_audio_duration(wav_path: str) -> float:
    # Return the total duration of a WAV file in seconds
    with wave.open(wav_path, 'rb') as wf:  # Open the WAV file in read-binary mode
        frames = wf.getnframes()            # Get the total number of audio frames
        rate = wf.getframerate()            # Get the sample rate (frames per second)
    return frames / float(rate)             # Duration = total frames divided by frame rate


def chunk_audio(wav_path: str, output_dir: str, chunk_minutes: int = 12, overlap_seconds: int = 1) -> dict:
    # Split a WAV file into overlapping chunks for sequential API submission
    # wav_path: path to the normalized WAV file produced by transcoder.py
    # output_dir: directory where chunk files will be written
    # chunk_minutes: target length of each chunk in minutes (default 12 min)
    # overlap_seconds: seconds of audio to repeat at the start of each subsequent chunk (default 1 sec)
    # Returns a dict with 'success' bool, 'chunks' list of paths, and 'error' str if failed

    result = {'success': False, 'chunks': [], 'error': None}  # Initialize result dict

    # Verify the input WAV file exists before opening it
    if not os.path.exists(wav_path):
        result['error'] = f'WAV file not found: {wav_path}'  # Report missing input
        return result  # Return failure early

    # Create the output directory if it does not already exist
    os.makedirs(output_dir, exist_ok=True)  # exist_ok=True prevents error if dir already exists

    try:
        with wave.open(wav_path, 'rb') as wf:  # Open the source WAV file for reading
            n_channels = wf.getnchannels()      # Number of audio channels (should be 1 for mono)
            sample_width = wf.getsampwidth()    # Bytes per sample (e.g., 2 for 16-bit audio)
            frame_rate = wf.getframerate()      # Frames (samples) per second
            n_frames = wf.getnframes()          # Total number of audio frames in the file

            # Calculate frame counts for chunk size and overlap
            chunk_frames = chunk_minutes * 60 * frame_rate   # Convert chunk duration to frame count
            overlap_frames = overlap_seconds * frame_rate     # Convert overlap seconds to frame count

            # Calculate the step size between chunk start positions (chunk minus overlap)
            step_frames = chunk_frames - overlap_frames  # Each chunk starts overlap_frames before the previous chunk ended

            # Calculate the total number of chunks needed to cover the entire file
            n_chunks = math.ceil((n_frames - overlap_frames) / step_frames)  # Round up to include the final partial chunk

            chunk_paths = []  # List to accumulate paths of created chunk files

            for i in range(n_chunks):  # Iterate over each chunk index
                start_frame = i * step_frames  # Calculate this chunk's starting frame position
                end_frame = min(start_frame + chunk_frames, n_frames)  # Clamp end to file boundary

                wf.setpos(start_frame)  # Seek the reader to the start of this chunk
                frames_to_read = end_frame - start_frame  # Calculate how many frames to read
                chunk_data = wf.readframes(frames_to_read)  # Read the raw audio bytes for this chunk

                # Build the output path for this chunk file
                chunk_filename = f'chunk_{i:03d}.wav'         # Zero-padded name for correct sort order
                chunk_path = os.path.join(output_dir, chunk_filename)  # Full absolute path

                # Write the chunk as a new WAV file with the same audio parameters
                with wave.open(chunk_path, 'wb') as out_wf:  # Open chunk file for writing
                    out_wf.setnchannels(n_channels)           # Preserve channel count
                    out_wf.setsampwidth(sample_width)         # Preserve sample width
                    out_wf.setframerate(frame_rate)           # Preserve frame rate
                    out_wf.writeframes(chunk_data)            # Write the raw audio data

                chunk_paths.append(chunk_path)  # Add completed chunk path to the list

        result['success'] = True      # Mark chunking as successful
        result['chunks'] = chunk_paths  # Return list of all chunk file paths in order
        return result  # Return success result

    except Exception as e:
        # Catch any unexpected errors during file I/O or wave processing
        result['error'] = f'Chunking failed: {str(e)}'  # Include error message for debugging
        return result  # Return failure result
