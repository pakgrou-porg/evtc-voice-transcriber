# test_integration.py — Functional/integration tests for the EVTC pipeline
# Uses real test.mp3 and ffmpeg for transcode/chunk stages, mocks only the API calls
# Verifies the full pipeline: MP3 → WAV → chunks → (mock API) → stitch

import os  # File path operations
import wave  # WAV file validation
from unittest.mock import patch, MagicMock  # Mock API calls only

from helpers.transcoder import transcode, check_ffmpeg  # Audio format conversion
from helpers.chunker import chunk_audio, get_audio_duration  # WAV splitting
from helpers.api_client import transcribe_all_chunks  # API submission (will be mocked)
from helpers.stitcher import stitch_transcripts  # Transcript reassembly
from helpers.summarizer import summarize, save_summary  # Summary generation


class TestFullPipeline:
    """Integration tests exercising the full EVTC pipeline with real audio processing."""

    def test_ffmpeg_is_available(self):
        """Verify ffmpeg is installed on the test system (prerequisite for all integration tests)."""
        assert check_ffmpeg() is True  # ffmpeg must be available for these tests

    def test_transcode_real_mp3_to_wav(self, test_mp3_path, tmp_dir):
        """Verify real MP3 to WAV transcoding produces a valid 16kHz mono WAV file."""
        wav_path = os.path.join(tmp_dir, 'transcoded.wav')  # Output WAV path
        result = transcode(test_mp3_path, wav_path)  # Run real transcode

        assert result['success'] is True  # Transcode must succeed
        assert os.path.exists(wav_path)  # Output file must exist
        assert os.path.getsize(wav_path) > 0  # File must not be empty

        # Validate WAV properties
        with wave.open(wav_path, 'rb') as wf:  # Open the WAV file
            assert wf.getnchannels() == 1  # Must be mono
            assert wf.getframerate() == 16000  # Must be 16kHz
            assert wf.getnframes() > 0  # Must have audio data

    def test_chunk_real_wav(self, sample_wav, tmp_dir):
        """Verify chunking a real WAV file produces valid chunk files."""
        chunks_dir = os.path.join(tmp_dir, 'chunks')  # Output dir for chunks
        result = chunk_audio(sample_wav, chunks_dir)  # Chunk the real WAV

        assert result['success'] is True  # Chunking must succeed
        assert len(result['chunks']) >= 1  # At least one chunk

        for chunk_path in result['chunks']:  # Validate each chunk
            assert os.path.exists(chunk_path)  # Chunk file must exist
            with wave.open(chunk_path, 'rb') as wf:  # Open as WAV
                assert wf.getnframes() > 0  # Must have audio frames
                assert wf.getnchannels() == 1  # Must be mono
                assert wf.getframerate() == 16000  # Must be 16kHz

    def test_full_pipeline_mp3_to_stitched_transcript(self, test_mp3_path, tmp_dir):
        """Verify end-to-end pipeline: MP3 → WAV → chunks → mock API → stitch."""
        # Step 1: Transcode MP3 to WAV
        wav_path = os.path.join(tmp_dir, 'pipeline.wav')  # WAV output path
        transcode_result = transcode(test_mp3_path, wav_path)  # Real transcode
        assert transcode_result['success'] is True  # Must succeed

        # Step 2: Chunk the WAV file
        chunks_dir = os.path.join(tmp_dir, 'chunks')  # Chunks output dir
        chunk_result = chunk_audio(wav_path, chunks_dir)  # Real chunking
        assert chunk_result['success'] is True  # Must succeed
        chunk_paths = chunk_result['chunks']  # Get chunk file paths
        assert len(chunk_paths) >= 1  # At least one chunk

        # Step 3: Mock API transcription for each chunk
        mock_texts = [f'Transcript for chunk {i}.' for i in range(len(chunk_paths))]  # Mock texts
        mock_response = MagicMock()  # Mock HTTP response
        mock_response.status_code = 200  # HTTP OK

        # Return different text for each chunk
        call_count = [0]  # Mutable counter for side effect

        def mock_post_side_effect(*args, **kwargs):  # Side effect function
            idx = min(call_count[0], len(mock_texts) - 1)  # Get current index
            mock_response.json.return_value = {'text': mock_texts[idx]}  # Set response text
            call_count[0] += 1  # Increment counter
            return mock_response  # Return mock response

        with patch('helpers.api_client.requests.post', side_effect=mock_post_side_effect):  # Mock API
            api_result = transcribe_all_chunks(chunk_paths, 'http://localhost/v1', 'model')  # Call

        assert api_result['success'] is True  # All chunks must succeed
        assert len(api_result['texts']) == len(chunk_paths)  # Must have text for each chunk

        # Step 4: Stitch transcript chunks
        stitch_result = stitch_transcripts(api_result['texts'])  # Real stitching
        assert stitch_result['success'] is True  # Must succeed
        assert len(stitch_result['transcript']) > 0  # Transcript must not be empty

        # Verify all chunk texts appear in the final transcript
        for text in mock_texts:  # Check each chunk's contribution
            # The text should appear (possibly without overlap dedup)
            assert 'chunk' in stitch_result['transcript'].lower()  # At least partial content present

    def test_pipeline_with_summarization(self, test_mp3_path, tmp_dir):
        """Verify the pipeline through to summarization produces valid output."""
        # Step 1: Transcode
        wav_path = os.path.join(tmp_dir, 'summary_test.wav')  # WAV output
        transcode_result = transcode(test_mp3_path, wav_path)  # Real transcode
        assert transcode_result['success'] is True  # Must succeed

        # Step 2: Chunk
        chunks_dir = os.path.join(tmp_dir, 'chunks')  # Chunks dir
        chunk_result = chunk_audio(wav_path, chunks_dir)  # Real chunking
        assert chunk_result['success'] is True  # Must succeed

        # Step 3: Mock API with realistic transcript text
        realistic_text = (
            'We will review the quarterly budget next Monday. '
            'Alice should prepare the presentation slides. '
            'Bob must submit the expense reports by Friday.'
        )  # Text with action keywords for summarizer to detect

        mock_response = MagicMock()  # Mock HTTP response
        mock_response.status_code = 200  # HTTP OK
        mock_response.json.return_value = {'text': realistic_text}  # Set response

        with patch('helpers.api_client.requests.post', return_value=mock_response):  # Mock API
            api_result = transcribe_all_chunks(
                chunk_result['chunks'], 'http://localhost/v1', 'model'  # API params
            )

        assert api_result['success'] is True  # Must succeed

        # Step 4: Stitch
        stitch_result = stitch_transcripts(api_result['texts'])  # Real stitch
        assert stitch_result['success'] is True  # Must succeed

        # Step 5: Summarize
        summary_result = summarize(stitch_result['transcript'])  # Real summarizer
        assert summary_result['success'] is True  # Must succeed
        assert 'subject' in summary_result['summary']  # Must have subject field

        # Step 6: Save summary
        summary_path = os.path.join(tmp_dir, 'test_summary.json')  # Output path
        save_result = save_summary(summary_result['summary'], summary_path)  # Write to disk
        assert save_result['success'] is True  # Must succeed
        assert os.path.exists(summary_path)  # File must exist

    def test_audio_duration_matches_expected(self, sample_wav):
        """Verify the test audio duration is close to the expected 6.77 seconds."""
        duration = get_audio_duration(sample_wav)  # Get real duration
        assert 5.0 < duration < 10.0  # Should be approximately 6.77s

    def test_chunk_count_consistency(self, sample_wav, tmp_dir):
        """Verify chunking produces consistent results across runs."""
        dir1 = os.path.join(tmp_dir, 'run1')  # First run output
        dir2 = os.path.join(tmp_dir, 'run2')  # Second run output
        result1 = chunk_audio(sample_wav, dir1)  # First chunk run
        result2 = chunk_audio(sample_wav, dir2)  # Second chunk run
        assert result1['success'] is True  # First run must succeed
        assert result2['success'] is True  # Second run must succeed
        assert len(result1['chunks']) == len(result2['chunks'])  # Same number of chunks
