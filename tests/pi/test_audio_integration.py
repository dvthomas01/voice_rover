"""Integration tests for command parser with audio transcription.

This module provides infrastructure for testing the command parser
with audio files. Audio files should be provided in WAV format
(16kHz, mono, 16-bit) for compatibility with Whisper.

To use:
1. Place audio files in tests/pi/audio_samples/ directory
2. Update test cases with expected commands
3. Run tests with: pytest tests/pi/test_audio_integration.py
"""

import pytest
import os
from pathlib import Path
from pi.command_parser.parser import CommandParser
from pi.command_parser.command_schema import CommandType


AUDIO_SAMPLES_DIR = Path(__file__).parent / "audio_samples"


class TestAudioIntegration:
    """Integration tests using audio files."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CommandParser()
        if not AUDIO_SAMPLES_DIR.exists():
            AUDIO_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    def test_audio_sample_exists(self):
        """Test that audio sample files exist."""
        audio_files = ["single_command.wav", "sequence.wav", "with_modifier.wav"]
        for audio_file in audio_files:
            audio_path = AUDIO_SAMPLES_DIR / audio_file
            if audio_path.exists():
                assert audio_path.exists(), f"Audio file should exist: {audio_file}"

    @pytest.mark.skipif(
        not (AUDIO_SAMPLES_DIR / "single_command.wav").exists(),
        reason="Audio file not provided"
    )
    def test_single_command_audio(self):
        """Test parsing single command from audio file."""
        audio_path = AUDIO_SAMPLES_DIR / "single_command.wav"
        
        from pi.whisper.transcriber import WhisperTranscriber
        transcriber = WhisperTranscriber()
        text = transcriber.transcribe_file(str(audio_path))
        
        result = self.parser.parse(text)
        assert result is not None
        assert len(result) == 1
        assert result[0].command_type == CommandType.MOVE_FORWARD

    @pytest.mark.skipif(
        not (AUDIO_SAMPLES_DIR / "sequence.wav").exists(),
        reason="Audio file not provided"
    )
    def test_sequence_audio(self):
        """Test parsing command sequence from audio file."""
        audio_path = AUDIO_SAMPLES_DIR / "sequence.wav"
        
        from pi.whisper.transcriber import WhisperTranscriber
        transcriber = WhisperTranscriber()
        text = transcriber.transcribe_file(str(audio_path))
        
        result = self.parser.parse(text)
        assert result is not None
        assert len(result) >= 2

    @pytest.mark.skipif(
        not (AUDIO_SAMPLES_DIR / "with_modifier.wav").exists(),
        reason="Audio file not provided"
    )
    def test_modifier_audio(self):
        """Test parsing command with speed modifier from audio file."""
        audio_path = AUDIO_SAMPLES_DIR / "with_modifier.wav"
        
        from pi.whisper.transcriber import WhisperTranscriber
        transcriber = WhisperTranscriber()
        text = transcriber.transcribe_file(str(audio_path))
        
        result = self.parser.parse(text)
        assert result is not None
        assert result[0].parameters["speed"] == 0.7

    @pytest.mark.skipif(
        not (AUDIO_SAMPLES_DIR / "stop_command.wav").exists(),
        reason="Audio file not provided"
    )
    def test_stop_command_audio(self):
        """Test parsing stop command from audio file."""
        audio_path = AUDIO_SAMPLES_DIR / "stop_command.wav"
        
        from pi.whisper.transcriber import WhisperTranscriber
        transcriber = WhisperTranscriber()
        text = transcriber.transcribe_file(str(audio_path))
        
        result = self.parser.parse(text)
        assert result is not None
        assert result[0].command_type == CommandType.STOP

    def test_audio_directory_structure(self):
        """Test that audio samples directory exists."""
        assert AUDIO_SAMPLES_DIR.exists() or AUDIO_SAMPLES_DIR.parent.exists()
