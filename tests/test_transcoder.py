# test_transcoder.py — Unit tests for the EVTC transcoder helper module
# Tests: check_ffmpeg, get_supported_formats, transcode

import os  # File path operations for test assertions
from unittest.mock import patch  # Mock external dependencies

from helpers.transcoder import check_ffmpeg, get_supported_formats, transcode  # Functions under test


class TestCheckFfmpeg:
    """Tests for the check_ffmpeg() function."""

    def test_check_ffmpeg_returns_bool(self):
        """Verify check_ffmpeg returns a boolean type."""
        result = check_ffmpeg()  # Call the function on the live system
        assert isinstance(result, bool)  # Must return True or False

    def test_check_ffmpeg_returns_true_when_present(self):
        """Verify check_ffmpeg returns True when ffmpeg is in PATH."""
        with patch('helpers.transcoder.shutil.which', return_value='/usr/bin/ffmpeg'):  # Mock ffmpeg found
            assert check_ffmpeg() is True  # Should return True

    def test_check_ffmpeg_returns_false_when_missing(self):
        """Verify check_ffmpeg returns False when ffmpeg is not in PATH."""
        with patch('helpers.transcoder.shutil.which', return_value=None):  # Mock ffmpeg not found
            assert check_ffmpeg() is False  # Should return False


class TestGetSupportedFormats:
    """Tests for the get_supported_formats() function."""

    def test_returns_list(self):
        """Verify get_supported_formats returns a list."""
        result = get_supported_formats()  # Call the function
        assert isinstance(result, list)  # Must be a list

    def test_contains_expected_formats(self):
        """Verify the supported formats list contains all expected extensions."""
        expected = ['.mp3', '.wav', '.mp4', '.m4a', '.ogg', '.flac', '.aac', '.webm']  # All expected
        result = get_supported_formats()  # Get the actual list
        assert result == expected  # Must match exactly in order

    def test_all_entries_start_with_dot(self):
        """Verify every format entry starts with a dot."""
        for fmt in get_supported_formats():  # Iterate each format
            assert fmt.startswith('.')  # Must start with a period


class TestTranscode:
    """Tests for the transcode() function."""

    def test_missing_input_file_returns_error(self, tmp_dir):
        """Verify transcode returns error dict when input file does not exist."""
        result = transcode('/nonexistent/file.mp3', os.path.join(tmp_dir, 'out.wav'))  # Missing input
        assert result['success'] is False  # Must fail
        assert 'not found' in result['error']  # Error message should mention missing file

    def test_unsupported_format_returns_error(self, tmp_dir):
        """Verify transcode returns error for unsupported file extensions."""
        fake_file = os.path.join(tmp_dir, 'test.xyz')  # Unsupported extension
        with open(fake_file, 'w') as f:  # Create a dummy file so it exists
            f.write('dummy')  # Write minimal content
        result = transcode(fake_file, os.path.join(tmp_dir, 'out.wav'))  # Attempt transcode
        assert result['success'] is False  # Must fail
        assert 'Unsupported format' in result['error']  # Error should mention unsupported format

    def test_ffmpeg_not_found_returns_error(self, tmp_dir):
        """Verify transcode returns error when ffmpeg is not available."""
        fake_file = os.path.join(tmp_dir, 'test.mp3')  # Create a dummy MP3 file
        with open(fake_file, 'w') as f:  # Make the file exist
            f.write('dummy')  # Write minimal content
        with patch('helpers.transcoder.check_ffmpeg', return_value=False):  # Mock ffmpeg missing
            result = transcode(fake_file, os.path.join(tmp_dir, 'out.wav'))  # Attempt transcode
        assert result['success'] is False  # Must fail
        assert 'ffmpeg not found' in result['error']  # Error should mention ffmpeg

    def test_successful_transcode_with_real_mp3(self, tmp_dir):
        """Verify transcode succeeds with a real MP3 file and ffmpeg."""
        # Generate a synthetic MP3 in tmp_dir using ffmpeg sine wave generator
        import subprocess  # For generating test audio
        mp3_path = os.path.join(tmp_dir, 'test_input.mp3')  # Synthetic MP3 path
        subprocess.run(  # Generate 2-second sine wave MP3
            ['ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2',
             '-codec:a', 'libmp3lame', '-b:a', '128k', '-y', mp3_path],
            capture_output=True  # Suppress output
        )
        output_path = os.path.join(tmp_dir, 'output.wav')  # Target WAV path
        result = transcode(mp3_path, output_path)  # Run real transcode
        assert result['success'] is True  # Must succeed
        assert result['output_path'] == output_path  # Output path must match
        assert os.path.exists(output_path)  # Output file must exist on disk
        assert os.path.getsize(output_path) > 0  # Output file must not be empty

    def test_result_dict_structure(self, tmp_dir):
        """Verify transcode always returns dict with expected keys."""
        result = transcode('/nonexistent/file.mp3', os.path.join(tmp_dir, 'out.wav'))  # Any call
        assert 'success' in result  # Must have success key
        assert 'output_path' in result  # Must have output_path key
        assert 'error' in result  # Must have error key

    def test_ffmpeg_process_failure(self, tmp_dir):
        """Verify transcode handles ffmpeg subprocess failure gracefully."""
        fake_mp3 = os.path.join(tmp_dir, 'test.mp3')  # Create a dummy MP3 file
        with open(fake_mp3, 'w') as f:  # Make the file exist on disk
            f.write('dummy')  # Write minimal content so os.path.exists passes
        output_path = os.path.join(tmp_dir, 'output.wav')  # Target WAV path
        mock_proc = type('MockProc', (), {'returncode': 1, 'stderr': 'mock error'})()  # Fake failed proc
        with patch('helpers.transcoder.subprocess.run', return_value=mock_proc):  # Mock ffmpeg failure
            result = transcode(fake_mp3, output_path)  # Attempt transcode
        assert result['success'] is False  # Must fail
        assert 'ffmpeg failed' in result['error']  # Error should mention ffmpeg failure

    def test_transcode_timeout(self, tmp_dir):
        """Verify transcode handles subprocess timeout gracefully."""
        import subprocess  # Import for TimeoutExpired exception
        fake_mp3 = os.path.join(tmp_dir, 'test.mp3')  # Create a dummy MP3 file
        with open(fake_mp3, 'w') as f:  # Make the file exist on disk
            f.write('dummy')  # Write minimal content so os.path.exists passes
        output_path = os.path.join(tmp_dir, 'output.wav')  # Target WAV path
        with patch('helpers.transcoder.subprocess.run',  # Mock subprocess.run to raise timeout
                   side_effect=subprocess.TimeoutExpired(cmd='ffmpeg', timeout=300)):
            result = transcode(fake_mp3, output_path)  # Attempt transcode
        assert result['success'] is False  # Must fail
        assert 'timed out' in result['error']  # Error should mention timeout
