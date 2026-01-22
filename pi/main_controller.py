"""Main orchestration logic for Voice Rover."""

import logging
from typing import Optional
import signal
import sys

from .audio_input.microphone import MicrophoneInterface
from .wake_word.detector import WakeWordDetector
from .whisper.transcriber import WhisperTranscriber
from .command_parser.parser import CommandParser
from .command_queue.queue_manager import CommandQueueManager
from .serial_comm.serial_interface import SerialInterface
from .config import *


class VoiceRoverController:
    """Main controller orchestrating all voice rover components."""

    def __init__(self):
        """Initialize voice rover controller."""
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.microphone = MicrophoneInterface(SAMPLE_RATE, AUDIO_CHANNELS)
        self.wake_word = WakeWordDetector(WAKE_WORD, WAKE_WORD_SENSITIVITY)
        self.transcriber = WhisperTranscriber(WHISPER_MODEL_SIZE)
        self.parser = CommandParser()
        self.queue = CommandQueueManager(MAX_QUEUE_SIZE)
        self.serial = SerialInterface(SERIAL_PORT, SERIAL_BAUDRATE)

        self._running = False

    def start(self) -> None:
        """Start the voice rover system."""
        self.logger.info("Starting Voice Rover...")
        raise NotImplementedError("To be implemented")

    def stop(self) -> None:
        """Stop the voice rover system."""
        self.logger.info("Stopping Voice Rover...")
        raise NotImplementedError("To be implemented")

    def _listen_for_wake_word(self) -> None:
        """Listen continuously for wake word."""
        raise NotImplementedError("To be implemented")

    def _process_voice_command(self) -> None:
        """Capture audio, transcribe, parse, and queue command."""
        raise NotImplementedError("To be implemented")

    def _command_executor_loop(self) -> None:
        """Continuously execute commands from queue."""
        raise NotImplementedError("To be implemented")

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info("Received shutdown signal")
        self.stop()
        sys.exit(0)


def main():
    """Main entry point."""
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)

    controller = VoiceRoverController()
    controller._setup_signal_handlers()

    try:
        controller.start()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        controller.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
