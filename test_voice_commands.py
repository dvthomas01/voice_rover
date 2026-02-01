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

try:
    import sounddevice as sd
except ImportError:
    print("Error: sounddevice not installed. Run: pip install sounddevice")
    sys.exit(1)

try:
    import whisper
except ImportError:
    print("Error: whisper not installed. Run: pip install openai-whisper")
    sys.exit(1)


# Audio settings
# Force USB microphone (Go Mic Video)
MIC_INDEX = 1  # Go Mic Video: USB Audio (hw:3,0)
SAMPLE_RATE = 44100  # Mic's hardware sample rate
WHISPER_SAMPLE_RATE = 16000  # Whisper expects 16kHz
CHANNELS = 1
BLOCK_DURATION = 0.5  # seconds per audio block
SILENCE_THRESHOLD = 0.01  # RMS threshold for silence detection
SILENCE_DURATION = 1.0  # seconds of silence to end recording
MAX_RECORD_DURATION = 5.0  # max seconds to record

# Command patterns with default speeds
COMMANDS = {
    "move_forward": {
        "patterns": [r"move\s+forward", r"go\s+forward", r"^forward$"],
        "speed": 0.4,
        "display": "MOVE FORWARD",
    },
    "move_backward": {
        "patterns": [r"move\s+backward", r"go\s+backward", r"^backward$", r"back\s*up"],
        "speed": 0.4,
        "display": "MOVE BACKWARD",
    },
    "rotate_clockwise": {
        "patterns": [r"rotate\s+clockwise", r"turn\s+right", r"spin\s+right"],
        "speed": 0.4,
        "display": "ROTATE CLOCKWISE",
    },
    "rotate_counterclockwise": {
        "patterns": [
            r"rotate\s+counter\s*clockwise",
            r"turn\s+left",
            r"spin\s+left",
        ],
        "speed": 0.4,
        "display": "ROTATE COUNTERCLOCKWISE",
    },
    "stop": {
        "patterns": [r"^stop$", r"halt", r"emergency\s+stop"],
        "speed": None,
        "display": "STOP",
    },
}


def calculate_rms(audio_data: np.ndarray) -> float:
    """Calculate RMS (root mean square) of audio data."""
    return np.sqrt(np.mean(audio_data**2))


# Resample audio to 16kHz for Whisper
def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Resample 1D audio array from orig_sr to target_sr using linear interpolation."""
    if orig_sr == target_sr or audio.size == 0:
        return audio

    duration = audio.shape[0] / float(orig_sr)
    target_len = int(round(duration * target_sr))

    # Use indices in time to interpolate
    old_times = np.linspace(0.0, duration, num=audio.shape[0], endpoint=False)
    new_times = np.linspace(0.0, duration, num=target_len, endpoint=False)

    return np.interp(new_times, old_times, audio).astype(np.float32)


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
    print("\nLoading Whisper model (base)...")
    
    # Load Whisper model
    model = whisper.load_model("base")
    print("Model loaded!\n")
    
    print("Listening for commands:")
    print("  - Move forward")
    print("  - Move backward")
    print("  - Rotate clockwise")
    print("  - Rotate counterclockwise")
    print("  - Stop")
    print("\nPress Ctrl+C to exit.\n")
    print("-" * 60)
    
    # Audio queue for callback
    audio_queue = queue.Queue()
    
    def audio_callback(indata, frames, time_info, status):
        """Callback for audio stream."""
        if status:
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

                        # Skip if too short (use recording sample rate)
                        if len(audio_data) < SAMPLE_RATE * 0.3:  # Less than 0.3 seconds
                            print(" (too short)", flush=True)
                            continue

                        # Resample to Whisper's expected sample rate
                        audio_for_whisper = resample_audio(audio_data, SAMPLE_RATE, WHISPER_SAMPLE_RATE)

                        print(" [Transcribing...]", end="", flush=True)

                        # Transcribe with Whisper (16kHz mono float32)
                        result = model.transcribe(
                            audio_for_whisper,
                            language="en",
                            fp16=False,  # Use fp32 for CPU compatibility
                        )
                        
                        text = result["text"].strip()
                        
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
