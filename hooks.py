# hooks.py — Plugin lifecycle hooks for the EVTC Voice Transcriber plugin
# Called by the A0 plugin framework during install/uninstall events
# Ensures required system dependencies (ffmpeg) are present

import subprocess  # Used to run apt-get for installing ffmpeg if missing
import shutil      # Used to check if ffmpeg binary is available in PATH


def install():  # Called by A0 when the plugin is first enabled or installed
    """Check for ffmpeg and attempt to install it if missing."""
    print("EVTC Voice Transcriber: Checking dependencies...")  # Status message

    if shutil.which('ffmpeg'):  # Check if ffmpeg is already available in PATH
        print("✓ ffmpeg found")  # Dependency satisfied
    else:  # ffmpeg not found — attempt automatic installation
        print("⚠ ffmpeg not found. Attempting install...")  # Warning before install attempt
        result = subprocess.run(  # Run apt-get to install ffmpeg package
            ['apt-get', 'install', '-y', 'ffmpeg'],  # Non-interactive install command
            capture_output=True,  # Capture stdout and stderr for logging
            text=True  # Return output as string instead of bytes
        )
        if result.returncode == 0:  # Check if apt-get succeeded
            print("✓ ffmpeg installed successfully")  # Confirm successful installation
        else:  # apt-get failed — report error and suggest manual install
            print(f"✗ ffmpeg installation failed: {result.stderr}")  # Include stderr for debugging
            print("Please install ffmpeg manually: apt-get install ffmpeg")  # Manual install instructions
