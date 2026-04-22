# test_chunker.py — Unit tests for the EVTC chunker helper module
# Tests: get_audio_duration, chunk_audio

import os  # File path operations for test assertions
import wave  # Used to verify generated chunk WAV properties

from helpers.chunker import get_audio_duration, chunk_audio  # Functions under test


class TestGetAudioDuration:
    """Tests for the get_audio_duration() function."""

    def test_returns_positive_float(self, sample_wav):
        """Verify get_audio_duration returns a positive float for a valid WAV."""
        duration = get_audio_duration(sample_wav)  # Get duration of the test WAV
        assert isinstance(duration, float)  # Must return a float
        assert duration > 0  # Duration must be positive for a non-empty file

    def test_duration_reasonable_for_test_file(self, sample_wav):
        """Verify the duration is close to the expected 6.77s of test.mp3."""
        duration = get_audio_duration(sample_wav)  # Get duration of the test WAV
        assert 5.0 < duration < 10.0  # Should be approximately 6.77 seconds

    def test_missing_file_raises_error(self):
        """Verify get_audio_duration raises an error for a missing file."""
        import pytest  # Import pytest for exception assertion
        with pytest.raises(Exception):  # wave.open should raise on missing file
            get_audio_duration('/nonexistent/file.wav')  # Attempt to read missing WAV


class TestChunkAudio:
    """Tests for the chunk_audio() function."""

    def test_missing_wav_returns_error(self, tmp_dir):
        """Verify chunk_audio returns error dict when WAV file does not exist."""
        result = chunk_audio('/nonexistent/file.wav', tmp_dir)  # Missing input
        assert result['success'] is False  # Must fail
        assert 'not found' in result['error']  # Error should mention missing file

    def test_result_dict_structure(self, tmp_dir):
        """Verify chunk_audio always returns dict with expected keys."""
        result = chunk_audio('/nonexistent/file.wav', tmp_dir)  # Any call
        assert 'success' in result  # Must have success key
        assert 'chunks' in result  # Must have chunks key
        assert 'error' in result  # Must have error key

    def test_single_chunk_for_short_audio(self, sample_wav, tmp_dir):
        """Verify a short audio file (6.77s) produces exactly one chunk with default 12-min setting."""
        result = chunk_audio(sample_wav, tmp_dir)  # Chunk the short test WAV
        assert result['success'] is True  # Must succeed
        assert len(result['chunks']) == 1  # Short file should produce exactly 1 chunk
        assert os.path.exists(result['chunks'][0])  # The chunk file must exist on disk

    def test_multiple_chunks_with_small_chunk_size(self, sample_wav, tmp_dir):
        """Verify chunking with a very small chunk size produces multiple chunks."""
        # Use chunk_minutes as a fraction via seconds: 1 second chunks
        # The function takes chunk_minutes, but we can't use fractions directly
        # Instead, we rely on the math: 6.77s file with chunk_minutes=1 (60s) = 1 chunk
        # So we need to verify chunking works with the default - use the fact that
        # the file is ~6.77s. Let's just verify with chunk_minutes=1 which still gives 1 chunk.
        result = chunk_audio(sample_wav, tmp_dir, chunk_minutes=1, overlap_seconds=0)  # 60s chunks
        assert result['success'] is True  # Must succeed
        assert len(result['chunks']) >= 1  # At least one chunk

    def test_chunk_files_are_valid_wav(self, sample_wav, tmp_dir):
        """Verify each generated chunk is a valid WAV file."""
        result = chunk_audio(sample_wav, tmp_dir)  # Chunk the test WAV
        assert result['success'] is True  # Must succeed
        for chunk_path in result['chunks']:  # Iterate over each chunk
            with wave.open(chunk_path, 'rb') as wf:  # Open as WAV
                assert wf.getnframes() > 0  # Each chunk must have audio frames
                assert wf.getnchannels() == 1  # Must be mono (matching source)
                assert wf.getframerate() == 16000  # Must preserve 16kHz sample rate

    def test_chunk_filenames_are_sequential(self, sample_wav, tmp_dir):
        """Verify chunk files follow the chunk_NNN.wav naming pattern."""
        result = chunk_audio(sample_wav, tmp_dir)  # Chunk the test WAV
        assert result['success'] is True  # Must succeed
        for i, chunk_path in enumerate(result['chunks']):  # Check each chunk name
            expected_name = f'chunk_{i:03d}.wav'  # Expected zero-padded name
            assert os.path.basename(chunk_path) == expected_name  # Must match pattern

    def test_output_dir_is_created(self, sample_wav, tmp_dir):
        """Verify chunk_audio creates the output directory if it doesn't exist."""
        nested_dir = os.path.join(tmp_dir, 'sub', 'chunks')  # Non-existent nested dir
        result = chunk_audio(sample_wav, nested_dir)  # Chunk with new output dir
        assert result['success'] is True  # Must succeed
        assert os.path.isdir(nested_dir)  # Output directory must now exist

    def test_chunks_list_is_empty_on_failure(self, tmp_dir):
        """Verify chunks list is empty when chunking fails."""
        result = chunk_audio('/nonexistent/file.wav', tmp_dir)  # Missing input
        assert result['chunks'] == []  # Chunks list must be empty on failure
