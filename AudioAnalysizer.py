import json
import pyaudio
import numpy as np
import math

THRESHOLD_FILE = "threshold.json"

def load_threshold():
    try:
        with open(THRESHOLD_FILE, "r") as f:
            return json.load(f)["threshold"]
    except FileNotFoundError:
        raise SystemExit(
            f"No threshold found. Run calibrate.py first to create {THRESHOLD_FILE}."
        )

def frequency_to_notes(freq):
    # Converts a freq in Hz to closest musical note
    if freq < 16.35:  # If frequency is below the threshold for C0
        return "Unknown"

    A4 = 440
    C0 = A4 * math.pow(2, -4.75)  # Calculate the frequency of C0
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    half = round(12 * math.log2(freq / C0))
    octaves = half // 12
    note_index = half % 12

    return notes[note_index] + f" {octaves}"

def get_dominant_freq(audio_data, rate):
    windowed = audio_data * np.hanning(len(audio_data))
    spectrum = np.abs(np.fft.rfft(windowed))  # rfft avoids negative-freq issue entirely
    freqs = np.fft.rfftfreq(len(windowed), 1 / rate)

    spectrum[0] = 0  # kill DC

    # Harmonic Product Spectrum
    hps = spectrum.copy()
    num_harmonics = 5
    for h in range(2, num_harmonics + 1):
        downsampled = spectrum[::h]
        hps[:len(downsampled)] *= downsampled

    peak_idx = np.argmax(hps)

    # parabolic interpolation for sub-bin accuracy
    if 1 <= peak_idx < len(hps) - 1:
        alpha, beta, gamma = hps[peak_idx - 1], hps[peak_idx], hps[peak_idx + 1]
        denom = (alpha - 2 * beta + gamma)
        if denom != 0:
            shift = 0.5 * (alpha - gamma) / denom
            peak_idx = peak_idx + shift

    return peak_idx * rate / len(windowed)


# Config Mic
format = pyaudio.paInt16  # Audio format
channels = 1  # Number of audio channels
rate = 44100  # Sample rate
chunk = 2048  # Size of audio chunks

STABLE_CHUNKS_REQUIRED = 3  # consecutive matching chunks needed to confirm a note

# Load the pre-calibrated threshold instead of calibrating in this process
threshold = load_threshold()

# Initialize PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)

candidate_note = None
candidate_count = 0

try:
    while True:
        data = stream.read(chunk, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)

        rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
        if rms < threshold:
            candidate_note = None
            candidate_count = 0
            continue

        freq = np.fft.fftfreq(len(audio_data), 1 / rate)
        dominant_freq = get_dominant_freq(audio_data, rate)
        print(f"  [debug] raw freq: {dominant_freq:.2f} Hz")
        note = frequency_to_notes(dominant_freq)

        if note == candidate_note:
            candidate_count += 1
        else:
            candidate_note = note
            candidate_count = 1

        if candidate_count >= STABLE_CHUNKS_REQUIRED and note != "Unknown":
            print(f"Detected note: {note} (Frequency: {dominant_freq:.2f} Hz)")
            break

except KeyboardInterrupt:
    print("Stopping audio processing...")

finally:
    stream.stop_stream()
    stream.close()
    p.terminate()