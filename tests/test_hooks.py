# test_hooks.py — Unit tests for the EVTC hooks.py module
# Tests: install() function with ffmpeg present and missing scenarios

from unittest.mock import patch, MagicMock  # Mock external dependencies

from hooks import install  # Function under test


class TestInstallHook:
    """Tests for the install() lifecycle hook."""

    def test_ffmpeg_already_present(self, capsys):
        """Verify install() reports success when ffmpeg is already available."""
        with patch('hooks.shutil.which', return_value='/usr/bin/ffmpeg'):  # Mock ffmpeg found
            install()  # Run the install hook
        captured = capsys.readouterr()  # Capture printed output
        assert 'ffmpeg found' in captured.out  # Should report ffmpeg was found

    def test_ffmpeg_missing_install_succeeds(self, capsys):
        """Verify install() attempts apt-get install when ffmpeg is missing and succeeds."""
        mock_proc = MagicMock()  # Mock subprocess result
        mock_proc.returncode = 0  # Simulate successful apt-get
        mock_proc.stderr = ''  # No error output

        with patch('hooks.shutil.which', return_value=None):  # Mock ffmpeg not found
            with patch('hooks.subprocess.run', return_value=mock_proc) as mock_run:  # Mock apt-get
                install()  # Run the install hook

        # Verify apt-get was called with correct arguments
        mock_run.assert_called_once()  # Must be called exactly once
        call_args = mock_run.call_args[0][0]  # Get the command list
        assert 'apt-get' in call_args  # Must call apt-get
        assert 'ffmpeg' in call_args  # Must install ffmpeg

        captured = capsys.readouterr()  # Capture printed output
        assert 'installed successfully' in captured.out  # Should report success

    def test_ffmpeg_missing_install_fails(self, capsys):
        """Verify install() reports failure when apt-get install fails."""
        mock_proc = MagicMock()  # Mock subprocess result
        mock_proc.returncode = 1  # Simulate failed apt-get
        mock_proc.stderr = 'E: Unable to locate package ffmpeg'  # Error output

        with patch('hooks.shutil.which', return_value=None):  # Mock ffmpeg not found
            with patch('hooks.subprocess.run', return_value=mock_proc):  # Mock apt-get failure
                install()  # Run the install hook

        captured = capsys.readouterr()  # Capture printed output
        assert 'installation failed' in captured.out  # Should report failure
        assert 'manually' in captured.out.lower()  # Should suggest manual install

    def test_install_prints_checking_message(self, capsys):
        """Verify install() always prints the initial checking message."""
        with patch('hooks.shutil.which', return_value='/usr/bin/ffmpeg'):  # Mock ffmpeg found
            install()  # Run the install hook
        captured = capsys.readouterr()  # Capture printed output
        assert 'Checking dependencies' in captured.out  # Must print checking message
