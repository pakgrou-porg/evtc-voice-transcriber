# test_tool_transcribe.py — Tests for the TranscribeTool A0 tool class
# Mocks the A0 framework (Tool, Response, PrintStyle, plugins) to test pipeline logic

import os  # File path operations
import sys  # Module path manipulation for mocking
import pytest  # Test framework
from unittest.mock import AsyncMock, MagicMock, patch  # Mocking utilities


# --- Mock A0 framework classes before importing the tool module ---

class MockResponse:  # Replacement for helpers.tool.Response
    """Mock A0 Response dataclass."""
    def __init__(self, message='', break_loop=False):  # Match real signature
        self.message = message  # Store message text
        self.break_loop = break_loop  # Store break_loop flag


class MockTool:  # Replacement for helpers.tool.Tool
    """Mock A0 Tool base class."""
    def __init__(self, args=None, agent=None):  # Constructor with optional args
        self.args = args or {}  # Tool arguments dict
        self.agent = agent or MagicMock()  # Mock agent object
        self.agent.handle_intervention = AsyncMock()  # Async mock for intervention


class MockPrintStyle:  # Replacement for helpers.print_style.PrintStyle
    """Mock A0 PrintStyle — swallows all print calls."""
    def __init__(self, **kwargs):  # Accept any kwargs silently
        pass  # No-op constructor
    def print(self, *args, **kwargs):  # Swallow print calls
        pass  # No-op print


# Create mock module objects for A0 framework
mock_tool_module = MagicMock()  # Mock helpers.tool module
mock_tool_module.Tool = MockTool  # Register MockTool as Tool
mock_tool_module.Response = MockResponse  # Register MockResponse as Response

mock_print_module = MagicMock()  # Mock helpers.print_style module
mock_print_module.PrintStyle = MockPrintStyle  # Register MockPrintStyle

mock_plugins_module = MagicMock()  # Mock helpers.plugins module

# Patch sys.modules so the tool imports resolve to our mocks
sys.modules.setdefault('helpers.tool', mock_tool_module)  # Mock helpers.tool
sys.modules.setdefault('helpers.print_style', mock_print_module)  # Mock helpers.print_style
sys.modules.setdefault('helpers.plugins', mock_plugins_module)  # Mock helpers.plugins

# Now safe to import the tool module
from tools.transcribe import TranscribeTool  # Class under test


@pytest.fixture
def mock_agent():
    """Create a mock A0 agent with async handle_intervention."""
    agent = MagicMock()  # Mock agent object
    agent.handle_intervention = AsyncMock()  # Async intervention handler
    return agent  # Return the mock agent


@pytest.fixture
def make_tool(mock_agent, mock_config):
    """Factory fixture to create TranscribeTool instances with given args."""
    def _make(args=None):  # Inner factory function
        tool = TranscribeTool.__new__(TranscribeTool)  # Create instance without __init__
        tool.args = args or {}  # Set tool arguments
        tool.agent = mock_agent  # Assign mock agent
        return tool  # Return configured tool
    return _make  # Return the factory


class TestTranscribeToolValidation:
    """Tests for input validation in TranscribeTool.execute()."""

    @pytest.mark.asyncio
    async def test_missing_audio_path_returns_error(self, make_tool):
        """Verify error when audio_file_path is not provided."""
        tool = make_tool({'audio_file_path': ''})  # Empty path
        result = await tool.execute()  # Execute the tool
        assert 'audio_file_path' in result.message  # Error mentions missing arg
        assert result.break_loop is False  # Should not break loop

    @pytest.mark.asyncio
    async def test_nonexistent_file_returns_error(self, make_tool):
        """Verify error when audio file does not exist on disk."""
        with patch.object(mock_plugins_module, 'get_plugin_config', return_value={}):  # Mock config
            tool = make_tool({'audio_file_path': '/nonexistent/audio.mp3'})  # Missing file
            result = await tool.execute()  # Execute the tool
        assert 'not found' in result.message.lower()  # Error mentions missing file

    @pytest.mark.asyncio
    async def test_unsupported_format_returns_error(self, make_tool, tmp_dir):
        """Verify error for unsupported file format."""
        bad_file = os.path.join(tmp_dir, 'test.xyz')  # Unsupported extension
        with open(bad_file, 'w') as f:  # Create the file
            f.write('dummy')  # Write content so it exists
        with patch.object(mock_plugins_module, 'get_plugin_config', return_value={}):  # Mock config
            tool = make_tool({'audio_file_path': bad_file})  # Unsupported format
            result = await tool.execute()  # Execute the tool
        assert 'unsupported' in result.message.lower()  # Error mentions unsupported format


class TestTranscribeToolPipeline:
    """Tests for the full pipeline execution in TranscribeTool.execute()."""

    @pytest.mark.asyncio
    async def test_successful_pipeline(self, make_tool, tmp_dir):
        """Verify full pipeline succeeds with mocked API calls."""
        # Generate a synthetic MP3 in tmp_dir for the pipeline
        import subprocess  # For generating test audio
        mp3_path = os.path.join(tmp_dir, 'test_input.mp3')  # Synthetic MP3 path
        subprocess.run(  # Generate 2-second sine wave MP3
            ['ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2',
             '-codec:a', 'libmp3lame', '-b:a', '128k', '-y', mp3_path],
            capture_output=True  # Suppress output
        )

        config = {  # Plugin config
            'transcription_api_url': 'http://127.0.0.1:8101',  # API URL
            'transcription_api_port': '',  # No separate port
            'transcription_api_prefix': '/v1',  # API prefix
            'transcription_model_name': 'test-model',  # Model name
            'source_auto_remove': False,  # Don't delete source
        }

        mock_api_result = {  # Mock API response
            'success': True,  # API succeeded
            'texts': ['Hello world from chunk one.'],  # Transcript text
            'total_latency_ms': 100,  # Mock latency
            'errors': [],  # No errors
        }

        with patch.object(mock_plugins_module, 'get_plugin_config', return_value=config):  # Mock config
            with patch('tools.transcribe.transcribe_all_chunks', return_value=mock_api_result):  # Mock API
                tool = make_tool({'audio_file_path': mp3_path, 'output_format': 'text'})  # Text output
                result = await tool.execute()  # Execute the pipeline

        assert 'complete' in result.message.lower() or 'transcript' in result.message.lower()  # Success

    @pytest.mark.asyncio
    async def test_ffmpeg_missing_returns_error(self, make_tool, tmp_dir):
        """Verify error when ffmpeg is not available."""
        fake_mp3 = os.path.join(tmp_dir, 'test.mp3')  # Create a dummy MP3 file
        with open(fake_mp3, 'w') as f:  # Make it exist on disk
            f.write('dummy')  # Write minimal content
        with patch.object(mock_plugins_module, 'get_plugin_config', return_value={}):  # Mock config
            with patch('tools.transcribe.check_ffmpeg', return_value=False):  # Mock ffmpeg missing
                tool = make_tool({'audio_file_path': fake_mp3})  # Use existing file
                result = await tool.execute()  # Execute the tool
        assert 'ffmpeg' in result.message.lower()  # Error mentions ffmpeg

    @pytest.mark.asyncio
    async def test_transcode_failure_returns_error(self, make_tool, tmp_dir):
        """Verify error when transcoding fails."""
        fake_mp3 = os.path.join(tmp_dir, 'test.mp3')  # Create a dummy MP3 file
        with open(fake_mp3, 'w') as f:  # Make it exist on disk
            f.write('dummy')  # Write minimal content
        mock_transcode = {'success': False, 'output_path': '', 'error': 'ffmpeg crashed'}  # Failed transcode

        with patch.object(mock_plugins_module, 'get_plugin_config', return_value={}):  # Mock config
            with patch('tools.transcribe.transcode', return_value=mock_transcode):  # Mock failure
                tool = make_tool({'audio_file_path': fake_mp3})  # Use existing file
                result = await tool.execute()  # Execute the tool
        assert 'error' in result.message.lower()  # Error in response

    @pytest.mark.asyncio
    async def test_api_failure_returns_error(self, make_tool, tmp_dir):
        """Verify error when API transcription fails."""
        # Generate a synthetic MP3 in tmp_dir for the pipeline
        import subprocess  # For generating test audio
        mp3_path = os.path.join(tmp_dir, 'test_input.mp3')  # Synthetic MP3 path
        subprocess.run(  # Generate 2-second sine wave MP3
            ['ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2',
             '-codec:a', 'libmp3lame', '-b:a', '128k', '-y', mp3_path],
            capture_output=True  # Suppress output
        )

        mock_api_result = {  # Failed API response
            'success': False,  # API failed
            'texts': [],  # No texts
            'total_latency_ms': 0,  # No latency
            'errors': ['Connection refused'],  # Error details
        }

        with patch.object(mock_plugins_module, 'get_plugin_config', return_value={}):  # Mock config
            with patch('tools.transcribe.transcribe_all_chunks', return_value=mock_api_result):  # Mock API failure
                tool = make_tool({'audio_file_path': mp3_path, 'output_format': 'text'})  # Valid file
                result = await tool.execute()  # Execute the tool
        assert 'error' in result.message.lower()  # Error in response

    @pytest.mark.asyncio
    async def test_handle_intervention_called(self, make_tool):
        """Verify handle_intervention is called at the start of execute."""
        with patch.object(mock_plugins_module, 'get_plugin_config', return_value={}):  # Mock config
            tool = make_tool({'audio_file_path': ''})  # Will fail early on validation
            await tool.execute()  # Execute the tool
        tool.agent.handle_intervention.assert_awaited_once()  # Must have been called
