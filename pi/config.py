"""Configuration constants for Voice Rover."""

# Audio settings (Samson Go Mic USB supports 44.1kHz and 48kHz)
SAMPLE_RATE = 44100  # Options: 44100 (CD quality) or 48000 (higher quality)
# Note: MicrophoneInterface will auto-detect device's native sample rate if None
AUDIO_CHANNELS = 1  # Mono (or 2 for stereo if needed)
CHUNK_SIZE = 1024  # Buffer size for low latency
AUDIO_DEVICE_INDEX = None  # Optional: Override device selection (None = auto-detect)

# Wake word settings
WAKE_WORD = "jarvis"
WAKE_WORD_SENSITIVITY = 0.5

# Whisper settings
WHISPER_MODEL_SIZE = "base"  # Options: tiny, base, small, medium, large
WHISPER_LANGUAGE = "en"

# Serial communication settings
SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUDRATE = 115200
SERIAL_TIMEOUT = 1.0

# Command queue settings
MAX_QUEUE_SIZE = 100
COMMAND_TIMEOUT = 5.0

# Audio capture settings
AUDIO_CAPTURE_DURATION = 6.0  # Duration in seconds to capture audio after wake word

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
