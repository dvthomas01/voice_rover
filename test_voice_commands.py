#!/usr/bin/env python3
"""Test script for voice command recognition.

Records audio from the microphone, transcribes with Whisper,
and detects primitive rover commands.

Usage:
    python scripts/test_voice_commands.py

Commands detected:
    - "Move forward" (default speed 0.4)
    - "Move backward" (default speed 0.4)
    - "Rotate clockwise" (default speed 0.4)
    - "Rotate counterclockwise" (default speed 0.4)
    - "Stop"
"""

import re
import sys
import queue
import numpy as np
import json
import os

try:
    import sounddevice as sd
except ImportError:
    print("Error: sounddevice not installed. Run: pip install sounddevice")
    sys.exit(1)

try:
    from vosk import Model, KaldiRecognizer
except ImportError:
    print("Error: vosk not installed. Run: pip install vosk")
    sys.exit(1)


# Audio settings
# On Mac, use default input device (set MIC_INDEX = None); on Pi you can set it explicitly.
MIC_INDEX = None  # use default microphone; set to an index from sd.query_devices() if needed
SAMPLE_RATE = 16000  # Vosk models typically expect 16kHz mono
CHANNELS = 1
BLOCK_DURATION = 0.5  # seconds per audio block
SILENCE_THRESHOLD = 0.01  # RMS threshold for silence detection
SILENCE_DURATION = 1.0  # seconds of silence to end recording
MAX_RECORD_DURATION = 5.0  # max seconds to record

# Path to Vosk model - use absolute path relative to this script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "vosk-model-small-en-us-0.15")

# Command patterns with default speeds (primitive motion commands)
COMMANDS = {
    "forward": {
        "patterns": [r"\bforward\b", r"go\s+forward", r"move\s+forward"],
        "speed": 0.4,
        "display": "FORWARD",
    },
    "backward": {
        "patterns": [r"\bbackward\b", r"go\s+backward", r"move\s+backward", r"back\s*up"],
        "speed": 0.4,
        "display": "BACKWARD",
    },
    "left": {
        "patterns": [r"\bleft\b", r"turn\s+left", r"rotate\s+left"],
        "speed": 0.4,
        "display": "LEFT",
    },
    "right": {
        "patterns": [r"\bright\b", r"turn\s+right", r"rotate\s+right"],
        "speed": 0.4,
        "display": "RIGHT",
    },
}


def calculate_rms(audio_data: np.ndarray) -> float:
    """Calculate RMS (root mean square) of audio data."""
    return np.sqrt(np.mean(audio_data**2))




def detect_command(text: str) -> dict | None:
    """Match transcribed text against known commands.
    
    Args:
        text: Transcribed text (will be lowercased and stripped)
        
    Returns:
        Dict with command info or None if no match
    """
    text = text.strip().lower()
    
    for cmd_name, cmd_info in COMMANDS.items():
        for pattern in cmd_info["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "command": cmd_name,
                    "display": cmd_info["display"],
                    "speed": cmd_info["speed"],
                    "raw_text": text,
                }
    return None


def record_until_silence(
    audio_queue: queue.Queue,
    sample_rate: int = SAMPLE_RATE,
    silence_threshold: float = SILENCE_THRESHOLD,
    silence_duration: float = SILENCE_DURATION,
    max_duration: float = MAX_RECORD_DURATION,
) -> np.ndarray:
    """Record audio until silence is detected.
    
    Args:
        audio_queue: Queue to receive audio blocks
        sample_rate: Audio sample rate
        silence_threshold: RMS threshold below which is considered silence
        silence_duration: How long silence must persist to stop recording
        max_duration: Maximum recording duration
        
    Returns:
        Recorded audio as numpy array
    """
    audio_blocks = []
    silence_blocks = 0
    blocks_for_silence = int(silence_duration / BLOCK_DURATION)
    max_blocks = int(max_duration / BLOCK_DURATION)
    
    for _ in range(max_blocks):
        try:
            block = audio_queue.get(timeout=BLOCK_DURATION * 2)
            audio_blocks.append(block)
            
            rms = calculate_rms(block)
            if rms < silence_threshold:
                silence_blocks += 1
                if silence_blocks >= blocks_for_silence and len(audio_blocks) > blocks_for_silence:
                    break
            else:
                silence_blocks = 0
                
        except queue.Empty:
            break
    
    if audio_blocks:
        return np.concatenate(audio_blocks)
    return np.array([], dtype=np.float32)


def main():
    print("=" * 60)
    print("Voice Command Test")
    print("=" * 60)
    print("\nLoading Vosk model...")

    # Load Vosk model
    model = Model(MODEL_PATH)
    print("Model loaded!\n")

    print("Listening for commands:")
    print("  - forward")
    print("  - backward")
    print("  - left")
    print("  - right")
    print("\nPress Ctrl+C to exit.\n")
    print("-" * 60)
    
    # Audio queue for callback
    audio_queue = queue.Queue()
    
    def audio_callback(indata, frames, time_info, status):
        """Callback for audio stream."""
        # Ignore benign overflow messages to avoid spamming the console
        if status and "overflow" not in str(status).lower():
            print(f"Audio status: {status}", file=sys.stderr)
        audio_queue.put(indata.copy().flatten())
    
    try:
        # Open audio stream
        with sd.InputStream(
            device=MIC_INDEX,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=np.float32,
            blocksize=int(SAMPLE_RATE * BLOCK_DURATION),
            callback=audio_callback,
            latency='high',  # extra buffering to reduce overflows on the Pi
        ):
            while True:
                # Wait for audio above threshold (voice activity)
                try:
                    block = audio_queue.get(timeout=0.1)
                    rms = calculate_rms(block)
                    
                    if rms > SILENCE_THRESHOLD:
                        print("\n[Listening...]", end="", flush=True)
                        
                        # Start recording with the triggering block
                        audio_blocks = [block]
                        
                        # Continue recording until silence
                        remaining_audio = record_until_silence(audio_queue)
                        if len(remaining_audio) > 0:
                            audio_blocks.append(remaining_audio)
                        
                        audio_data = np.concatenate(audio_blocks)

                        # Skip if too short
                        if len(audio_data) < SAMPLE_RATE * 0.3:  # Less than 0.3 seconds
                            print(" (too short)", flush=True)
                            continue

                        print(" [Recognizing...]", end="", flush=True)

                        # Convert float32 audio (-1..1) to 16-bit PCM bytes for Vosk
                        audio_int16 = (audio_data * 32767).astype(np.int16).tobytes()

                        # Create a fresh recognizer per utterance
                        rec = KaldiRecognizer(model, SAMPLE_RATE)

                        if rec.AcceptWaveform(audio_int16):
                            res = json.loads(rec.Result())
                        else:
                            res = json.loads(rec.FinalResult())

                        text = res.get("text", "").strip()
                        
                        if text:
                            print(f'\n  Heard: "{text}"')
                            
                            # Try to detect command
                            command = detect_command(text)
                            
                            if command:
                                print(f"\n  >>> COMMAND DETECTED: {command['display']}", end="")
                                if command["speed"] is not None:
                                    print(f" (speed: {command['speed']})")
                                else:
                                    print()
                            else:
                                print("  (no command matched)")
                        else:
                            print(" (no speech detected)")
                            
                except queue.Empty:
                    pass
                    
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
