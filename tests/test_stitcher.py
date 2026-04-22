# test_stitcher.py — Unit tests for the EVTC stitcher helper module
# Tests: normalize_text, find_overlap, stitch_transcripts, stitch_from_files

import os  # File path operations for writing test chunk files

from helpers.stitcher import normalize_text, find_overlap, stitch_transcripts, stitch_from_files  # Functions under test


class TestNormalizeText:
    """Tests for the normalize_text() function."""

    def test_collapses_multiple_spaces(self):
        """Verify multiple spaces are collapsed to a single space."""
        result = normalize_text('hello    world')  # Multiple spaces between words
        assert result == 'hello world'  # Should be single space

    def test_collapses_newlines_and_tabs(self):
        """Verify newlines and tabs are collapsed to single spaces."""
        result = normalize_text('hello\n\tworld\n\n  end')  # Mixed whitespace
        assert result == 'hello world end'  # All whitespace normalized

    def test_strips_leading_trailing_whitespace(self):
        """Verify leading and trailing whitespace is removed."""
        result = normalize_text('  hello world  ')  # Leading/trailing spaces
        assert result == 'hello world'  # Must be stripped

    def test_empty_string(self):
        """Verify empty string returns empty string."""
        result = normalize_text('')  # Empty input
        assert result == ''  # Must return empty

    def test_single_word(self):
        """Verify single word passes through unchanged."""
        result = normalize_text('hello')  # Single word
        assert result == 'hello'  # Must be unchanged


class TestFindOverlap:
    """Tests for the find_overlap() function."""

    def test_finds_exact_overlap(self):
        """Verify find_overlap detects known overlapping text."""
        tail = 'The quick brown fox jumps over the lazy dog.'  # End of previous chunk
        head = 'over the lazy dog. The rain in Spain.'  # Start of current chunk
        overlap = find_overlap(tail, head)  # Should find 'over the lazy dog.'
        assert overlap > 0  # Must detect some overlap

    def test_returns_zero_for_no_overlap(self):
        """Verify find_overlap returns 0 when there is no matching text."""
        tail = 'completely different text here'  # No shared words
        head = 'nothing in common at all today'  # No shared words
        overlap = find_overlap(tail, head)  # No overlap expected
        assert overlap == 0  # Must return 0

    def test_returns_zero_for_short_overlap(self):
        """Verify find_overlap ignores overlaps shorter than min_overlap_words."""
        tail = 'hello world foo'  # Only 3 words in tail
        head = 'foo bar baz'  # Only 1 word overlaps
        overlap = find_overlap(tail, head, min_overlap_words=4)  # Min 4 words required
        assert overlap == 0  # Too short to count as overlap

    def test_overlap_with_min_words_met(self):
        """Verify find_overlap works when exactly min_overlap_words match."""
        tail = 'one two three four five'  # 5 words
        head = 'two three four five six seven'  # First 4 words overlap with tail
        overlap = find_overlap(tail, head, min_overlap_words=4)  # Exactly 4 words match
        assert overlap > 0  # Must detect the 4-word overlap

    def test_empty_tail(self):
        """Verify find_overlap handles empty tail gracefully."""
        overlap = find_overlap('', 'some text here')  # Empty tail
        assert overlap == 0  # No overlap possible

    def test_empty_head(self):
        """Verify find_overlap handles empty head gracefully."""
        overlap = find_overlap('some text here', '')  # Empty head
        assert overlap == 0  # No overlap possible


class TestStitchTranscripts:
    """Tests for the stitch_transcripts() function."""

    def test_empty_list_returns_error(self):
        """Verify stitch_transcripts returns error for empty chunk list."""
        result = stitch_transcripts([])  # Empty list
        assert result['success'] is False  # Must fail
        assert 'No transcript chunks' in result['error']  # Error should mention empty list

    def test_single_chunk_returns_it(self):
        """Verify stitch_transcripts returns the single chunk unchanged."""
        text = 'Hello world this is a test.'  # Single chunk text
        result = stitch_transcripts([text])  # Single element list
        assert result['success'] is True  # Must succeed
        assert result['transcript'] == text  # Must return the text unchanged

    def test_two_chunks_no_overlap(self):
        """Verify two chunks with no overlap are concatenated with a space."""
        chunks = ['First chunk text.', 'Second chunk text.']  # No overlap
        result = stitch_transcripts(chunks)  # Stitch them
        assert result['success'] is True  # Must succeed
        assert 'First chunk text.' in result['transcript']  # First chunk present
        assert 'Second chunk text.' in result['transcript']  # Second chunk present

    def test_overlapping_chunks_are_deduplicated(self, sample_chunks_text):
        """Verify overlapping text between chunks is removed during stitching."""
        result = stitch_transcripts(sample_chunks_text)  # Stitch overlapping chunks
        assert result['success'] is True  # Must succeed
        transcript = result['transcript']  # Get stitched result
        # The final text should not have duplicate phrases
        # Count occurrences of a phrase that appears in the overlap
        assert transcript.count('lazy dog') <= 1  # Should appear at most once after dedup

    def test_result_dict_structure(self):
        """Verify stitch_transcripts returns dict with expected keys."""
        result = stitch_transcripts([])  # Any call
        assert 'success' in result  # Must have success key
        assert 'transcript' in result  # Must have transcript key
        assert 'error' in result  # Must have error key

    def test_empty_chunks_are_skipped(self):
        """Verify empty string chunks in the list are skipped."""
        chunks = ['Hello world.', '', 'Goodbye world.']  # Middle chunk is empty
        result = stitch_transcripts(chunks)  # Stitch with empty chunk
        assert result['success'] is True  # Must succeed
        assert 'Hello world.' in result['transcript']  # First chunk present
        assert 'Goodbye world.' in result['transcript']  # Third chunk present


class TestStitchFromFiles:
    """Tests for the stitch_from_files() function."""

    def test_missing_file_returns_error(self):
        """Verify stitch_from_files returns error when a chunk file is missing."""
        result = stitch_from_files(['/nonexistent/chunk.txt'])  # Missing file
        assert result['success'] is False  # Must fail
        assert 'not found' in result['error']  # Error should mention missing file

    def test_reads_and_stitches_files(self, tmp_dir):
        """Verify stitch_from_files reads text files and stitches them."""
        # Create two chunk text files
        file1 = os.path.join(tmp_dir, 'chunk_000.txt')  # First chunk file
        file2 = os.path.join(tmp_dir, 'chunk_001.txt')  # Second chunk file
        with open(file1, 'w', encoding='utf-8') as f:  # Write first chunk
            f.write('Hello from chunk zero.')  # Chunk 0 content
        with open(file2, 'w', encoding='utf-8') as f:  # Write second chunk
            f.write('Hello from chunk one.')  # Chunk 1 content
        result = stitch_from_files([file1, file2])  # Stitch from files
        assert result['success'] is True  # Must succeed
        assert 'chunk zero' in result['transcript']  # First file content present
        assert 'chunk one' in result['transcript']  # Second file content present

    def test_partial_missing_file_fails_fast(self, tmp_dir):
        """Verify stitch_from_files fails on the first missing file."""
        file1 = os.path.join(tmp_dir, 'chunk_000.txt')  # First chunk exists
        with open(file1, 'w', encoding='utf-8') as f:  # Write it
            f.write('Chunk zero.')  # Content
        result = stitch_from_files([file1, '/nonexistent/chunk.txt'])  # Second file missing
        assert result['success'] is False  # Must fail
        assert 'not found' in result['error']  # Error mentions missing file
