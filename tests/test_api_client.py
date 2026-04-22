# test_api_client.py — Unit tests for the EVTC api_client helper module
# Tests: build_api_url, transcribe_chunk, transcribe_all_chunks
# All HTTP requests are mocked — no real API calls are made

import os  # File path operations for creating test fixtures
import json  # JSON serialization for mock response bodies
from unittest.mock import patch, MagicMock  # Mock external HTTP calls

from helpers.api_client import build_api_url, transcribe_chunk, transcribe_all_chunks  # Functions under test


class TestBuildApiUrl:
    """Tests for the build_api_url() function."""

    def test_basic_url_no_port_no_prefix(self):
        """Verify URL construction with no port and no prefix."""
        result = build_api_url('http://127.0.0.1', '', '')  # No port, no prefix
        assert result == 'http://127.0.0.1'  # Just the base URL

    def test_url_with_port(self):
        """Verify URL construction with a port number."""
        result = build_api_url('http://127.0.0.1', '8101', '')  # Port, no prefix
        assert result == 'http://127.0.0.1:8101'  # Base URL with port

    def test_url_with_prefix(self):
        """Verify URL construction with an API prefix."""
        result = build_api_url('http://127.0.0.1', '', '/v1')  # No port, with prefix
        assert result == 'http://127.0.0.1/v1'  # Base URL with prefix

    def test_url_with_port_and_prefix(self):
        """Verify URL construction with both port and prefix."""
        result = build_api_url('http://127.0.0.1', '8101', '/v1')  # Both port and prefix
        assert result == 'http://127.0.0.1:8101/v1'  # Full URL

    def test_https_url_ignores_port(self):
        """Verify HTTPS URLs do not get port appended."""
        result = build_api_url('https://api.example.com', '8101', '/v1')  # HTTPS with port
        assert result == 'https://api.example.com/v1'  # Port should be ignored for HTTPS
        assert ':8101' not in result  # Confirm port not present

    def test_trailing_slash_removed(self):
        """Verify trailing slash is stripped from base URL."""
        result = build_api_url('http://127.0.0.1/', '', '/v1')  # Trailing slash on base
        assert result == 'http://127.0.0.1/v1'  # Slash cleaned up
        assert '//' not in result.replace('http://', '')  # No double slashes


class TestTranscribeChunk:
    """Tests for the transcribe_chunk() function."""

    def test_missing_chunk_file_returns_error(self):
        """Verify transcribe_chunk returns error when chunk file does not exist."""
        result = transcribe_chunk('/nonexistent/chunk.wav', 'http://localhost/v1', 'model')  # Missing file
        assert result['success'] is False  # Must fail
        assert 'not found' in result['error']  # Error mentions missing file

    def test_result_dict_structure(self):
        """Verify transcribe_chunk returns dict with expected keys."""
        result = transcribe_chunk('/nonexistent/chunk.wav', 'http://localhost/v1', 'model')  # Any call
        assert 'success' in result  # Must have success key
        assert 'text' in result  # Must have text key
        assert 'latency_ms' in result  # Must have latency_ms key
        assert 'error' in result  # Must have error key

    def test_successful_transcription(self, sample_wav):
        """Verify transcribe_chunk succeeds with mocked successful API response."""
        mock_response = MagicMock()  # Create mock response object
        mock_response.status_code = 200  # Simulate HTTP 200 OK
        mock_response.json.return_value = {'text': 'Hello world from test.'}  # Transcript text

        with patch('helpers.api_client.requests.post', return_value=mock_response):  # Mock HTTP POST
            result = transcribe_chunk(sample_wav, 'http://localhost/v1', 'test-model')  # Call with mock

        assert result['success'] is True  # Must succeed
        assert result['text'] == 'Hello world from test.'  # Must contain transcript text
        assert result['latency_ms'] >= 0  # Latency must be non-negative

    def test_api_returns_http_error(self, sample_wav):
        """Verify transcribe_chunk handles HTTP error status codes."""
        mock_response = MagicMock()  # Create mock response object
        mock_response.status_code = 500  # Simulate HTTP 500 Server Error
        mock_response.text = 'Internal Server Error'  # Error body

        with patch('helpers.api_client.requests.post', return_value=mock_response):  # Mock HTTP POST
            with patch('helpers.api_client.time.sleep'):  # Skip retry delays
                result = transcribe_chunk(sample_wav, 'http://localhost/v1', 'test-model')  # Call

        assert result['success'] is False  # Must fail
        assert 'HTTP 500' in result['error']  # Error mentions status code

    def test_api_returns_empty_transcript(self, sample_wav):
        """Verify transcribe_chunk fails when API returns empty text."""
        mock_response = MagicMock()  # Create mock response object
        mock_response.status_code = 200  # HTTP OK
        mock_response.json.return_value = {'text': ''}  # Empty transcript

        with patch('helpers.api_client.requests.post', return_value=mock_response):  # Mock HTTP POST
            result = transcribe_chunk(sample_wav, 'http://localhost/v1', 'test-model')  # Call

        assert result['success'] is False  # Must fail
        assert 'empty transcript' in result['error'].lower()  # Error mentions empty result

    def test_connection_error_retries(self, sample_wav):
        """Verify transcribe_chunk retries on connection errors."""
        import requests as req  # Import for ConnectionError
        with patch('helpers.api_client.requests.post',  # Mock to always raise ConnectionError
                   side_effect=req.exceptions.ConnectionError('refused')):
            with patch('helpers.api_client.time.sleep'):  # Skip retry delays
                result = transcribe_chunk(sample_wav, 'http://localhost/v1', 'test-model')  # Call

        assert result['success'] is False  # Must fail after retries
        assert 'Connection failed' in result['error']  # Error mentions connection failure

    def test_timeout_retries(self, sample_wav):
        """Verify transcribe_chunk retries on request timeouts."""
        import requests as req  # Import for Timeout exception
        with patch('helpers.api_client.requests.post',  # Mock to always raise Timeout
                   side_effect=req.exceptions.Timeout('timed out')):
            with patch('helpers.api_client.time.sleep'):  # Skip retry delays
                result = transcribe_chunk(sample_wav, 'http://localhost/v1', 'test-model')  # Call

        assert result['success'] is False  # Must fail after retries
        assert 'timed out' in result['error'].lower()  # Error mentions timeout

    def test_api_key_included_in_headers(self, sample_wav):
        """Verify API key is sent as Bearer token when provided."""
        mock_response = MagicMock()  # Create mock response object
        mock_response.status_code = 200  # HTTP OK
        mock_response.json.return_value = {'text': 'Test transcript.'}  # Valid response

        with patch('helpers.api_client.requests.post', return_value=mock_response) as mock_post:  # Capture call
            transcribe_chunk(sample_wav, 'http://localhost/v1', 'model', api_key='sk-test123')  # With API key

        # Verify the Authorization header was sent
        call_kwargs = mock_post.call_args  # Get the call arguments
        headers = call_kwargs.kwargs.get('headers') or call_kwargs[1].get('headers', {})  # Extract headers
        assert 'Authorization' in headers  # Must include auth header
        assert headers['Authorization'] == 'Bearer sk-test123'  # Must be Bearer format

    def test_no_api_key_no_auth_header(self, sample_wav):
        """Verify no Authorization header is sent when API key is None."""
        mock_response = MagicMock()  # Create mock response object
        mock_response.status_code = 200  # HTTP OK
        mock_response.json.return_value = {'text': 'Test transcript.'}  # Valid response

        with patch('helpers.api_client.requests.post', return_value=mock_response) as mock_post:  # Capture call
            transcribe_chunk(sample_wav, 'http://localhost/v1', 'model', api_key=None)  # No API key

        call_kwargs = mock_post.call_args  # Get the call arguments
        headers = call_kwargs.kwargs.get('headers') or call_kwargs[1].get('headers', {})  # Extract headers
        assert 'Authorization' not in headers  # Must not include auth header


class TestTranscribeAllChunks:
    """Tests for the transcribe_all_chunks() function."""

    def test_all_chunks_succeed(self, sample_wav):
        """Verify transcribe_all_chunks succeeds when all chunks pass."""
        mock_response = MagicMock()  # Create mock response object
        mock_response.status_code = 200  # HTTP OK
        mock_response.json.return_value = {'text': 'Chunk transcript.'}  # Valid response

        with patch('helpers.api_client.requests.post', return_value=mock_response):  # Mock all API calls
            result = transcribe_all_chunks(
                [sample_wav, sample_wav],  # Two chunks (same file for testing)
                'http://localhost/v1', 'model'  # API params
            )

        assert result['success'] is True  # Must succeed
        assert len(result['texts']) == 2  # Must have 2 transcript texts
        assert result['errors'] == []  # No errors
        assert result['total_latency_ms'] >= 0  # Latency must be non-negative

    def test_first_chunk_fails_fast(self, sample_wav):
        """Verify transcribe_all_chunks stops on first failure."""
        mock_response = MagicMock()  # Create mock response object
        mock_response.status_code = 500  # HTTP error
        mock_response.text = 'Server Error'  # Error body

        with patch('helpers.api_client.requests.post', return_value=mock_response):  # Mock API failure
            with patch('helpers.api_client.time.sleep'):  # Skip retry delays
                result = transcribe_all_chunks(
                    [sample_wav, sample_wav],  # Two chunks
                    'http://localhost/v1', 'model'  # API params
                )

        assert result['success'] is False  # Must fail
        assert len(result['errors']) > 0  # Must have at least one error
        assert len(result['texts']) == 0  # No texts since first chunk failed

    def test_result_dict_structure(self, sample_wav):
        """Verify transcribe_all_chunks returns dict with expected keys."""
        mock_response = MagicMock()  # Create mock response
        mock_response.status_code = 200  # HTTP OK
        mock_response.json.return_value = {'text': 'Test.'}  # Valid response

        with patch('helpers.api_client.requests.post', return_value=mock_response):  # Mock
            result = transcribe_all_chunks([sample_wav], 'http://localhost/v1', 'model')  # Call

        assert 'success' in result  # Must have success key
        assert 'texts' in result  # Must have texts key
        assert 'errors' in result  # Must have errors key
        assert 'total_latency_ms' in result  # Must have total_latency_ms key
