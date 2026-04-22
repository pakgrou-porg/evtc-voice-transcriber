# conftest.py — Shared pytest fixtures for EVTC Voice Transcriber tests
# Provides common test infrastructure: paths, temp dirs, sample audio, mock config

import pytest  # Test framework for fixture registration
import sys  # Used to manipulate sys.path for plugin imports
import os  # File path operations
import tempfile  # Create temporary directories for test isolation
import shutil  # Cleanup temp directories after tests
import subprocess  # Used to run ffmpeg for sample audio generation
from pathlib import Path  # Resolve plugin directory paths

# Add plugin root to sys.path so helpers are importable in tests
PLUGIN_DIR = Path(__file__).resolve().parents[1]  # /path/to/voice-transcriber/
sys.path.insert(0, str(PLUGIN_DIR))  # Allow 'from helpers.X import Y' in tests

# Session-scoped temp dir for generated test audio (shared across all tests)
_SESSION_TMP = tempfile.mkdtemp(prefix='evtc_session_')  # Created once at import time


def _generate_test_mp3():
    """Generate a synthetic 6.77s MP3 file for testing if not already present."""
    mp3_path = os.path.join(_SESSION_TMP, 'test.mp3')  # Path for synthetic MP3
    if not os.path.exists(mp3_path):  # Only generate once per session
        subprocess.run(  # Generate 6.77-second 440Hz sine wave MP3
            ['ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=6.77',
             '-codec:a', 'libmp3lame', '-b:a', '128k', '-y', mp3_path],
            capture_output=True  # Suppress ffmpeg output
        )
    return mp3_path  # Return path to generated MP3


@pytest.fixture
def plugin_dir():
    """Return the absolute path to the plugin root directory."""
    return PLUGIN_DIR  # Consistent reference to the plugin root


@pytest.fixture
def test_mp3_path():
    """Return the absolute path to a test MP3 file (generated synthetically)."""
    return _generate_test_mp3()  # Generate if needed, return path


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for test artifacts, cleaned up after test."""
    d = tempfile.mkdtemp(prefix='evtc_test_')  # Create unique temp dir
    yield d  # Provide the path to the test
    shutil.rmtree(d, ignore_errors=True)  # Cleanup after test completes


@pytest.fixture
def sample_wav(test_mp3_path, tmp_dir):
    """Create a real 16kHz mono WAV from the test MP3 using ffmpeg."""
    wav_path = os.path.join(tmp_dir, 'test.wav')  # Output WAV path in temp dir
    subprocess.run(  # Run ffmpeg to convert MP3 to normalized WAV
        ['ffmpeg', '-i', test_mp3_path, '-ac', '1', '-ar', '16000', '-y', wav_path],
        capture_output=True  # Suppress ffmpeg output during tests
    )
    return wav_path  # Return path to the generated WAV file


@pytest.fixture
def mock_config():
    """Return a standard mock plugin configuration dict."""
    return {  # Mimics the structure returned by plugins.get_plugin_config()
        'engine_type': 'local-cohere',  # Engine type identifier
        'transcription_api_url': 'http://127.0.0.1:8101',  # Local API base URL
        'transcription_api_port': '',  # Empty port (included in URL)
        'transcription_api_prefix': '/v1',  # API version prefix
        'transcription_model_name': 'test-model',  # Model identifier
        'transcription_language': 'en',  # Language code
        'source_auto_remove': False,  # Don't delete source during tests
    }


@pytest.fixture
def sample_chunks_text():
    """Return a list of sample transcript chunk strings with known overlap."""
    return [  # Three chunks with deliberate overlap at boundaries
        'The quick brown fox jumps over the lazy dog.',  # Chunk 0: base text
        'over the lazy dog. The rain in Spain falls mainly on the plain.',  # Chunk 1: overlaps with chunk 0
        'mainly on the plain. Pack my box with five dozen liquor jugs.',  # Chunk 2: overlaps with chunk 1
    ]
