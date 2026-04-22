# test_tool_connection.py — Tests for the TestConnectionTool A0 tool class
# Mocks the A0 framework (Tool, Response, PrintStyle, plugins) to test connection testing logic

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
from tools.test_connection import TestConnectionTool  # Class under test


@pytest.fixture
def mock_agent():
    """Create a mock A0 agent with async handle_intervention."""
    agent = MagicMock()  # Mock agent object
    agent.handle_intervention = AsyncMock()  # Async intervention handler
    return agent  # Return the mock agent


@pytest.fixture
def make_tool(mock_agent):
    """Factory fixture to create TestConnectionTool instances."""
    def _make(args=None):  # Inner factory function
        tool = TestConnectionTool.__new__(TestConnectionTool)  # Create instance without __init__
        tool.args = args or {}  # Set tool arguments
        tool.agent = mock_agent  # Assign mock agent
        return tool  # Return configured tool
    return _make  # Return the factory


class TestConnectionToolValidation:
    """Tests for input validation in TestConnectionTool.execute()."""

    @pytest.mark.asyncio
    async def test_missing_test_audio_returns_error(self, make_tool):
        """Verify error when bundled test.mp3 is not found."""
        config = {  # Plugin config
            'transcription_api_url': 'http://127.0.0.1:8101',  # API URL
            'transcription_api_port': '',  # No port
            'transcription_api_prefix': '/v1',  # Prefix
            'transcription_model_name': 'test-model',  # Model
        }
        with patch.object(mock_plugins_module, 'get_plugin_config', return_value=config):  # Mock config
            with patch('tools.test_connection.os.path.exists', return_value=False):  # Mock file missing
                tool = make_tool()  # Create tool
                result = await tool.execute()  # Execute
        assert 'not found' in result.message.lower()  # Error mentions missing file

    @pytest.mark.asyncio
    async def test_ffmpeg_missing_returns_error(self, make_tool):
        """Verify error when ffmpeg is not available."""
        config = {  # Plugin config
            'transcription_api_url': 'http://127.0.0.1:8101',  # API URL
            'transcription_api_port': '',  # No port
            'transcription_api_prefix': '/v1',  # Prefix
            'transcription_model_name': 'test-model',  # Model
        }
        with patch.object(mock_plugins_module, 'get_plugin_config', return_value=config):  # Mock config
            with patch('tools.test_connection.os.path.exists', return_value=True):  # File exists
                with patch('tools.test_connection.check_ffmpeg', return_value=False):  # ffmpeg missing
                    tool = make_tool()  # Create tool
                    result = await tool.execute()  # Execute
        assert 'ffmpeg' in result.message.lower()  # Error mentions ffmpeg


class TestConnectionToolExecution:
    """Tests for connection test execution."""

    @pytest.mark.asyncio
    async def test_successful_connection(self, make_tool):
        """Verify successful connection test with mocked API response."""
        config = {  # Plugin config
            'transcription_api_url': 'http://127.0.0.1:8101',  # API URL
            'transcription_api_port': '',  # No port
            'transcription_api_prefix': '/v1',  # Prefix
            'transcription_model_name': 'test-model',  # Model
        }
        mock_result = {  # Successful transcription result
            'success': True,  # API call succeeded
            'text': 'Test transcription output text.',  # Transcript
            'latency_ms': 150,  # Latency
            'error': None,  # No error
        }
        with patch.object(mock_plugins_module, 'get_plugin_config', return_value=config):  # Mock config
            with patch('tools.test_connection.os.path.exists', return_value=True):  # File exists
                with patch('tools.test_connection.check_ffmpeg', return_value=True):  # ffmpeg available
                    with patch('tools.test_connection.transcribe_chunk', return_value=mock_result):  # Mock API
                        tool = make_tool()  # Create tool
                        result = await tool.execute()  # Execute
        assert 'passed' in result.message.lower()  # Success message
        assert result.break_loop is False  # Should not break loop

    @pytest.mark.asyncio
    async def test_failed_connection(self, make_tool):
        """Verify failed connection test reports error details."""
        config = {  # Plugin config
            'transcription_api_url': 'http://127.0.0.1:8101',  # API URL
            'transcription_api_port': '',  # No port
            'transcription_api_prefix': '/v1',  # Prefix
            'transcription_model_name': 'test-model',  # Model
        }
        mock_result = {  # Failed transcription result
            'success': False,  # API call failed
            'text': '',  # No text
            'latency_ms': 0,  # No latency
            'error': 'Connection refused',  # Error message
        }
        with patch.object(mock_plugins_module, 'get_plugin_config', return_value=config):  # Mock config
            with patch('tools.test_connection.os.path.exists', return_value=True):  # File exists
                with patch('tools.test_connection.check_ffmpeg', return_value=True):  # ffmpeg available
                    with patch('tools.test_connection.transcribe_chunk', return_value=mock_result):  # Mock API
                        tool = make_tool()  # Create tool
                        result = await tool.execute()  # Execute
        assert 'failed' in result.message.lower()  # Failure message
        assert result.break_loop is False  # Should not break loop

    @pytest.mark.asyncio
    async def test_unexpected_exception_returns_error(self, make_tool):
        """Verify unexpected exceptions during API call are caught."""
        config = {  # Plugin config
            'transcription_api_url': 'http://127.0.0.1:8101',  # API URL
            'transcription_api_port': '',  # No port
            'transcription_api_prefix': '/v1',  # Prefix
            'transcription_model_name': 'test-model',  # Model
        }
        with patch.object(mock_plugins_module, 'get_plugin_config', return_value=config):  # Mock config
            with patch('tools.test_connection.os.path.exists', return_value=True):  # File exists
                with patch('tools.test_connection.check_ffmpeg', return_value=True):  # ffmpeg available
                    with patch('tools.test_connection.transcribe_chunk',  # Mock raises exception
                               side_effect=RuntimeError('Unexpected crash')):
                        tool = make_tool()  # Create tool
                        result = await tool.execute()  # Execute
        assert 'error' in result.message.lower()  # Error in response

    @pytest.mark.asyncio
    async def test_handle_intervention_called(self, make_tool):
        """Verify handle_intervention is called at the start of execute."""
        config = {  # Plugin config
            'transcription_api_url': 'http://127.0.0.1:8101',  # API URL
            'transcription_api_port': '',  # No port
            'transcription_api_prefix': '/v1',  # Prefix
            'transcription_model_name': 'test-model',  # Model
        }
        with patch.object(mock_plugins_module, 'get_plugin_config', return_value=config):  # Mock config
            with patch('tools.test_connection.os.path.exists', return_value=False):  # Will fail early
                tool = make_tool()  # Create tool
                await tool.execute()  # Execute
        tool.agent.handle_intervention.assert_awaited_once()  # Must have been called
