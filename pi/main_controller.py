"""Main orchestration logic for Voice Rover.

INTEGRATION POINT: All modules come together here
ARCHITECTURE: Multi-threaded (wake word listener, command executor, serial communicator)
"""

import logging
import signal
import sys
import threading
import time

from .audio_input.microphone import MicrophoneInterface
from .wake_word.detector import WakeWordDetector
from .whisper.transcriber import WhisperTranscriber
from .command_parser.parser import CommandParser
from .command_queue.queue_manager import CommandQueueManager
from .serial_comm.serial_interface import SerialInterface
from .command_parser.command_schema import Command, CommandType, PRIORITY_STOP
from .config import (
    SAMPLE_RATE, AUDIO_CHANNELS, WAKE_WORD, WAKE_WORD_SENSITIVITY,
    WHISPER_MODEL_SIZE, MAX_QUEUE_SIZE, SERIAL_PORT, SERIAL_BAUDRATE,
    COMMAND_TIMEOUT, AUDIO_CAPTURE_DURATION, LOG_LEVEL, LOG_FORMAT
)


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
        self._wake_word_thread = None
        self._command_executor_thread = None
        self._processing_command = False
        self._processing_lock = threading.Lock()

    def start(self) -> None:
        """Start the voice rover system.
        
        Initializes components in dependency order:
        1. SerialInterface (connect to ESP32)
        2. WhisperTranscriber (load model - blocking)
        3. MicrophoneInterface (start audio stream)
        4. WakeWordDetector (initialize Porcupine)
        5. Start threads (wake word listener, command executor)
        """
        self.logger.info("Starting Voice Rover...")
        
        try:
            # 1. Connect to ESP32 (non-blocking, will retry in executor if fails)
            if not self.serial.connect():
                self.logger.warning("Serial connection failed on startup, will retry in executor")
            else:
                self.logger.info("Serial connection established")
            
            # 2. Load Whisper model (blocking, critical dependency)
            try:
                self.transcriber.load_model()
                self.logger.info("Whisper model loaded")
            except Exception as e:
                self.logger.error(f"Failed to load Whisper model: {e}")
                raise
            
            # 3. Start microphone (critical dependency)
            try:
                self.microphone.start()
                self.logger.info("Microphone started")
            except Exception as e:
                self.logger.error(f"Failed to start microphone: {e}")
                raise
            
            # 4. Initialize wake word detector (non-critical, can continue without it)
            try:
                self.wake_word.initialize()
                self.logger.info("Wake word detector initialized")
            except Exception as e:
                self.logger.warning(f"Wake word initialization failed: {e} - continuing without wake word")
            
            # 5. Start threads
            self._running = True
            self._wake_word_thread = threading.Thread(
                target=self._listen_for_wake_word,
                daemon=True,
                name="WakeWordListener"
            )
            self._command_executor_thread = threading.Thread(
                target=self._command_executor_loop,
                daemon=True,
                name="CommandExecutor"
            )
            
            self._wake_word_thread.start()
            self._command_executor_thread.start()
            
            self.logger.info("Voice Rover started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Voice Rover: {e}", exc_info=True)
            self.stop()
            raise

    def stop(self) -> None:
        """Stop the voice rover system.
        
        Gracefully shuts down all components in reverse order:
        1. Stop threads
        2. Send STOP command to ESP32
        3. Cleanup components (microphone, wake word, transcriber, serial)
        """
        self.logger.info("Stopping Voice Rover...")
        
        # Stop threads
        self._running = False
        
        if self._wake_word_thread:
            self._wake_word_thread.join(timeout=2.0)
            if self._wake_word_thread.is_alive():
                self.logger.warning("Wake word thread did not stop gracefully")
        
        if self._command_executor_thread:
            self._command_executor_thread.join(timeout=2.0)
            if self._command_executor_thread.is_alive():
                self.logger.warning("Command executor thread did not stop gracefully")
        
        # Send STOP command to ESP32
        try:
            stop_cmd = Command(CommandType.STOP, {}, PRIORITY_STOP)
            self.serial.send_command(stop_cmd)
            self.logger.info("STOP command sent to ESP32")
        except Exception as e:
            self.logger.warning(f"Failed to send STOP command: {e}")
        
        # Cleanup components (reverse order)
        try:
            self.microphone.stop()
        except Exception as e:
            self.logger.error(f"Error stopping microphone: {e}")
        
        try:
            self.wake_word.cleanup()
        except Exception as e:
            self.logger.error(f"Error cleaning up wake word: {e}")
        
        try:
            self.transcriber.unload_model()
        except Exception as e:
            self.logger.error(f"Error unloading Whisper model: {e}")
        
        try:
            self.serial.disconnect()
        except Exception as e:
            self.logger.error(f"Error disconnecting serial: {e}")
        
        self.logger.info("Voice Rover stopped")

    def _listen_for_wake_word(self) -> None:
        """Listen continuously for wake word.
        
        Processes audio chunks through wake word detector.
        When wake word is detected, callback handles command processing.
        """
        self.wake_word.set_callback(self._on_wake_word_detected)
        
        while self._running:
            try:
                chunk = self.microphone.get_audio_chunk()
                if chunk is not None:
                    # Pass sample rate so wake word detector can resample if needed
                    self.wake_word.process_audio(chunk, sample_rate=self.microphone.sample_rate)
            except Exception as e:
                self.logger.error(f"Error in wake word listener: {e}")
            
            time.sleep(0.01)  # Prevent CPU spinning

    def _on_wake_word_detected(self) -> None:
        """Handle wake word detection.
        
        Serializes wake word detections to prevent overlapping processing.
        Captures audio, transcribes with Whisper, parses commands, and either
        enqueues them or sends STOP immediately (bypassing queue).
        """
        # Serialize wake word detections
        with self._processing_lock:
            if self._processing_command:
                self.logger.debug("Ignoring wake word detection - command processing in progress")
                return
            
            self._processing_command = True
        
        try:
            self.logger.info("Wake word detected")
            
            # Capture audio
            try:
                audio = self.microphone.capture_audio(duration=AUDIO_CAPTURE_DURATION)
            except Exception as e:
                self.logger.error(f"Failed to capture audio: {e}")
                return
            
            # Transcribe
            try:
                text = self.transcriber.transcribe(audio)
                self.logger.info(f"Transcribed: {text}")
            except Exception as e:
                self.logger.error(f"Failed to transcribe audio: {e}")
                return
            
            if not text:
                self.logger.warning("Empty transcription")
                return
            
            # Parse commands
            commands = self.parser.parse(text)
            if not commands:
                self.logger.warning("No commands parsed from transcription")
                return
            
            # Process each command
            for cmd in commands:
                if cmd.command_type == CommandType.STOP:
                    # STOP always wins: clear queue and send immediately
                    self.logger.info("STOP command detected - clearing queue and sending immediately")
                    self.queue.clear()
                    if self.serial.send_command(cmd):
                        self.logger.info("STOP command sent to ESP32")
                    else:
                        self.logger.error("Failed to send STOP command")
                else:
                    # Enqueue normal commands
                    if self.queue.enqueue(cmd):
                        self.logger.info(f"Enqueued command: {cmd.command_type}")
                    else:
                        self.logger.warning("Queue full, command dropped")
        
        except Exception as e:
            self.logger.error(f"Error processing wake word: {e}", exc_info=True)
        finally:
            with self._processing_lock:
                self._processing_command = False

    def _command_executor_loop(self) -> None:
        """Continuously execute commands from queue.
        
        Dequeues commands sequentially and sends them to ESP32 via serial.
        Reads and logs responses. Handles errors gracefully without crashing.
        """
        while self._running:
            try:
                # Dequeue command with timeout
                command = self.queue.dequeue(timeout=1.0)
                
                if command:
                    self.logger.info(f"Executing command: {command.command_type}")
                    
                    # Send to ESP32 (SerialInterface handles retries)
                    if self.serial.send_command(command):
                        # Read response (non-blocking with timeout)
                        response = self.serial.read_response(
                            blocking=True,
                            timeout=COMMAND_TIMEOUT
                        )
                        if response:
                            self.logger.info(f"ESP32 response: {response}")
                        else:
                            self.logger.warning("No response from ESP32")
                    else:
                        self.logger.error("Failed to send command to ESP32")
            
            except Exception as e:
                self.logger.error(f"Error in command executor: {e}", exc_info=True)
            
            time.sleep(0.1)  # Small delay to prevent CPU spinning

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown.
        
        Installs handlers for SIGINT (Ctrl+C) and SIGTERM.
        """
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_names = {
            signal.SIGINT: "SIGINT",
            signal.SIGTERM: "SIGTERM"
        }
        signal_name = signal_names.get(signum, f"Signal {signum}")
        self.logger.info(f"Received {signal_name}")
        self.stop()
        sys.exit(0)


def main():
    """Main entry point for Voice Rover."""
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
    logger = logging.getLogger(__name__)

    controller = VoiceRoverController()
    controller._setup_signal_handlers()

    try:
        controller.start()
        logger.info("Voice Rover running. Press Ctrl+C to stop.")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        controller.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        controller.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
