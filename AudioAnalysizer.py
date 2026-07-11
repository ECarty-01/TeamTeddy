import json
import pyaudio
import numpy as np
import math
import time

THRESHOLD_FILE = "threshold.json"

def load_threshold():
    """Load pre-calibrated silence threshold"""
    try:
        with open(THRESHOLD_FILE, "r") as f:
            return json.load(f)["threshold"]
    except FileNotFoundError:
        print(f"Warning: {THRESHOLD_FILE} not found. Using default threshold of 300.")
        return 300

def frequency_to_notes(freq):
    """Converts a frequency in Hz to the closest musical note (note name only)"""
    if freq < 16.35:  # Below C0
        return "Unknown"

    A4 = 440
    C0 = A4 * math.pow(2, -4.75)  # Calculate the frequency of C0
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    half = round(12 * math.log2(freq / C0))
    octaves = half // 12
    note_index = half % 12

    return notes[note_index]  # Return just the note name (e.g., "C", not "C 4")

def get_dominant_freq(audio_data, rate):
    """Extract the dominant frequency from audio samples using Harmonic Product Spectrum"""
    windowed = audio_data * np.hanning(len(audio_data))
    spectrum = np.abs(np.fft.rfft(windowed))  # rfft avoids negative-freq issue
    freqs = np.fft.rfftfreq(len(windowed), 1 / rate)

    spectrum[0] = 0  # Kill DC component

    # Harmonic Product Spectrum for better fundamental detection
    hps = spectrum.copy()
    num_harmonics = 5
    for h in range(2, num_harmonics + 1):
        downsampled = spectrum[::h]
        hps[:len(downsampled)] *= downsampled

    peak_idx = np.argmax(hps)

    # Parabolic interpolation for sub-bin accuracy
    if 1 <= peak_idx < len(hps) - 1:
        alpha, beta, gamma = hps[peak_idx - 1], hps[peak_idx], hps[peak_idx + 1]
        denom = (alpha - 2 * beta + gamma)
        if denom != 0:
            shift = 0.5 * (alpha - gamma) / denom
            peak_idx = peak_idx + shift

    return peak_idx * rate / len(windowed)


def detect_one_note(timeout_seconds=5):
    """
    Listen for ONE note from the microphone and return it.
    
    Args:
        timeout_seconds: Maximum time to wait for a note (default 5 seconds)
    
    Returns:
        str: The detected note name (e.g., "C", "D#", "E"), or None if timeout
    """
    # Audio config
    format = pyaudio.paInt16
    channels = 1
    rate = 44100
    chunk = 2048
    STABLE_CHUNKS_REQUIRED = 3

    threshold = load_threshold()

    # Initialize PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(format=format, channels=channels, rate=rate, 
                    input=True, frames_per_buffer=chunk)

    candidate_note = None
    candidate_count = 0
    start_time = time.time()

    print(f"Listening for note (up to {timeout_seconds}s)...")

    try:
        while time.time() - start_time < timeout_seconds:
            # Read audio chunk
            data = stream.read(chunk, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)

            # Check if above silence threshold
            rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
            if rms < threshold:
                candidate_note = None
                candidate_count = 0
                continue

            # Detect frequency and convert to note
            dominant_freq = get_dominant_freq(audio_data, rate)
            note = frequency_to_notes(dominant_freq)

            # Debounce: track if same note appears in consecutive chunks
            if note == candidate_note:
                candidate_count += 1
            else:
                candidate_note = note
                candidate_count = 1

            # If stable for N chunks, return the note
            if candidate_count >= STABLE_CHUNKS_REQUIRED and note != "Unknown":
                print(f"✓ Detected note: {note} (Frequency: {dominant_freq:.2f} Hz)")
                return note  # ← RETURN instead of break

        # Timeout reached
        print(f"✗ No note detected within {timeout_seconds}s")
        return None

    except KeyboardInterrupt:
        print("Listening stopped by user")
        return None

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


# Test the function
if __name__ == "__main__":
    print("Test: Detecting a single note...")
    note = detect_one_note(timeout_seconds=5)
    if note:
        print(f"You played: {note}")
    else:
        print("No note detected")
