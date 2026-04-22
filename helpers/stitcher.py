# stitcher.py — Reassembles transcript chunks into a single coherent document
# Part of the EVTC (Easy Voice Transcription Caller) module for Agent Zero
# Handles removal of duplicate text introduced by the 1-second overlap between chunks

import re       # Regular expressions for detecting and removing duplicate sentence fragments
import os       # Used for file path operations


def normalize_text(text: str) -> str:
    # Normalize whitespace in a string to make comparison reliable
    return re.sub(r'\s+', ' ', text.strip())  # Replace multiple spaces/newlines with a single space


def find_overlap(tail: str, head: str, min_overlap_words: int = 4) -> int:
    # Find how many characters of 'tail' duplicate the start of 'head'
    # tail: the end of the previous chunk's transcript text
    # head: the beginning of the current chunk's transcript text
    # min_overlap_words: minimum word count to consider a valid overlap match
    # Returns the number of characters to strip from the start of 'head'

    tail_words = tail.split()        # Split the tail text into individual words
    head_words = head.split()        # Split the head text into individual words

    # Try progressively smaller candidate overlap windows from the tail
    for window in range(min(len(tail_words), 30), min_overlap_words - 1, -1):  # Start with up to 30 words
        candidate = ' '.join(tail_words[-window:])   # Take the last 'window' words of the tail
        candidate_norm = normalize_text(candidate)   # Normalize for comparison
        head_norm = normalize_text(head)             # Normalize the head for comparison

        # Check if the head text starts with this candidate overlap
        if head_norm.startswith(candidate_norm):     # Exact match at the beginning
            return len(candidate) + 1  # Return the character count to strip (plus space separator)

    return 0  # No overlap detected — return 0 to keep the full head text


def stitch_transcripts(chunks: list, overlap_window_chars: int = 200) -> dict:
    # Combine a list of transcript text strings into one clean document
    # chunks: ordered list of transcript strings (one per audio chunk)
    # overlap_window_chars: how many characters from the end of each chunk to inspect for duplicates
    # Returns a dict with 'success' bool, 'transcript' str, and 'error' str if failed

    result = {'success': False, 'transcript': '', 'error': None}  # Initialize result dict

    # Validate that we received at least one chunk to stitch
    if not chunks:
        result['error'] = 'No transcript chunks provided'  # Nothing to stitch
        return result  # Return failure early

    # Start with the first chunk as the base — no deduplication needed for chunk 0
    stitched = chunks[0].strip()  # Strip leading/trailing whitespace from first chunk

    for i in range(1, len(chunks)):  # Iterate over all subsequent chunks starting at index 1
        current = chunks[i].strip()  # Strip whitespace from current chunk text

        if not current:              # Skip any empty chunks (e.g., silence segments)
            continue                  # Move to the next chunk without appending anything

        # Extract the tail of the stitched text (the last N chars) as the overlap search window
        tail = stitched[-overlap_window_chars:] if len(stitched) > overlap_window_chars else stitched

        # Detect how many characters at the start of 'current' duplicate the tail
        overlap_len = find_overlap(tail, current)  # Returns 0 if no overlap detected

        # Remove the overlapping prefix from the current chunk before appending
        deduped = current[overlap_len:].strip()  # Strip any leading space after overlap removal

        if deduped:  # Only append if there is non-empty content remaining after deduplication
            stitched += ' ' + deduped  # Join with a space to maintain sentence flow

    result['success'] = True         # Mark stitching as successful
    result['transcript'] = stitched  # Store the final stitched transcript
    return result                    # Return success result


def stitch_from_files(chunk_text_files: list, overlap_window_chars: int = 200) -> dict:
    # Convenience function to stitch transcripts read from text files on disk
    # chunk_text_files: ordered list of file paths containing chunk transcript text
    # Returns a dict with 'success' bool, 'transcript' str, and 'error' str if failed

    chunks = []  # List to hold the text content of each chunk file

    for path in chunk_text_files:  # Iterate over each chunk text file path in order
        if not os.path.exists(path):  # Check that the chunk file exists
            return {'success': False, 'transcript': '', 'error': f'Chunk file not found: {path}'}  # Fail fast
        with open(path, 'r', encoding='utf-8') as f:  # Open file with UTF-8 encoding
            chunks.append(f.read())  # Append the file content to the chunks list

    return stitch_transcripts(chunks, overlap_window_chars)  # Delegate to the main stitch function
