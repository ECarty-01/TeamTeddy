"""
pitch_listener.py

Listens to the microphone and yields stable, confirmed musical notes
(as MIDI note numbers) in real time.

Fixes vs. the original script:
  - `A4 * 2 ** (2, -4.75)` was a syntax error (tuple passed to **).
    Should just be `2 ** -4.75`.
  - `np.argmax(np.abs(np.fft.fft(...)))` almost always locked onto bin 0
    (DC / near-zero frequency) or noise, because it searched the *entire*
    fft output including negative frequencies and the near-zero bin.
    This version uses rfft (positive freqs only) and zeroes out sub-50Hz
    content.
  - No noise gate -> it printed "notes" even during silence. Added an
    RMS silence threshold.
  - No debouncing -> a single noisy frame could register as a note.
    Now a note only "confirms" once several consecutive chunks agree.
"""

import math
from collections import deque

import numpy as np
import pyaudio

# ---------- Audio config ----------
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 2048                   # bigger chunk -> better low-freq resolution
SILENCE_RMS_THRESHOLD = 300    # tune to your mic / room noise floor
CONFIRM_FRAMES = 4             # consecutive chunks that must agree
                                # before a note counts as "confirmed"

A4 = 440.0
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def freq_to_midi(freq):
    """Convert a frequency in Hz to the nearest MIDI note number."""
    if not freq or freq <= 0:
        return None
    return round(69 + 12 * math.log2(freq / A4))


def midi_to_name(midi):
    if midi is None:
        return "Unknown"
    name = NOTE_NAMES[midi % 12]
    octave = midi // 12 - 1  # MIDI numbering: A4 = 69
    return f"{name}{octave}"


def dominant_frequency(samples, rate):
    """Return the dominant frequency (Hz) in a block of audio samples."""
    windowed = samples * np.hanning(len(samples))
    spectrum = np.fft.rfft(windowed)                # positive freqs only
    freqs = np.fft.rfftfreq(len(samples), d=1.0 / rate)
    magnitude = np.abs(spectrum)

    magnitude[freqs < 50] = 0  # ignore mic rumble / DC bias

    peak_index = np.argmax(magnitude)
    if magnitude[peak_index] == 0:
        return None
    return freqs[peak_index]


def calibrate_silence_threshold(seconds=2.0, margin=4.0):
    """
    Measures your actual room/mic noise floor and returns a good
    SILENCE_RMS_THRESHOLD for it, instead of guessing a fixed number.

    Records `seconds` of ambient audio (stay quiet while it runs), then
    sets the threshold to (mean noise RMS) + margin * (std dev of that
    noise) -- comfortably above the noise floor, low enough that a real
    played note still clears it.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)

    print(f"Calibrating silence threshold -- stay quiet for {seconds:.0f}s...")
    readings = []
    try:
        n_chunks = int(seconds * RATE / CHUNK)
        for _ in range(max(n_chunks, 1)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float64)
            readings.append(np.sqrt(np.mean(samples ** 2)))
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    mean, std = np.mean(readings), np.std(readings)
    threshold = mean + margin * std
    print(f"Ambient RMS: mean={mean:.1f}, std={std:.1f} -> "
          f"threshold={threshold:.1f}\n")
    return threshold


def listen_for_notes(on_reading=None, stop_flag=None, threshold=None):
    """
    Generator that yields confirmed MIDI note numbers as they're played.

    on_reading(midi, freq, rms): optional callback fired every chunk,
        useful for debugging / a live meter.
    stop_flag(): optional callable; stops listening when it returns True.
    threshold: RMS silence threshold to use. Defaults to
        SILENCE_RMS_THRESHOLD; pass the result of
        calibrate_silence_threshold() for a value tuned to your room.
    """
    if threshold is None:
        threshold = SILENCE_RMS_THRESHOLD

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)

    recent = deque(maxlen=CONFIRM_FRAMES)
    last_confirmed = None

    try:
        while stop_flag is None or not stop_flag():
            data = stream.read(CHUNK, exception_on_overflow=False)
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float64)

            rms = np.sqrt(np.mean(samples ** 2))
            if rms < threshold:
                recent.clear()
                if on_reading:
                    on_reading(None, None, rms)
                continue

            freq = dominant_frequency(samples, RATE)
            midi = freq_to_midi(freq)

            if on_reading:
                on_reading(midi, freq, rms)

            if midi is None:
                recent.clear()
                continue

            recent.append(midi)

            if (len(recent) == CONFIRM_FRAMES
                    and len(set(recent)) == 1
                    and recent[0] != last_confirmed):
                last_confirmed = recent[0]
                yield last_confirmed

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    import sys

    if "--calibrate" in sys.argv:
        calibrate_silence_threshold()
        sys.exit()

    if "--meter" in sys.argv:
        # Live RMS meter -- handy for watching the number while you play
        # softly/loudly, or while background noise happens, to pick a
        # threshold by eye instead of trusting calibration alone.
        print("RMS meter running (Ctrl+C to stop)...")

        def show(midi, freq, rms):
            note = midi_to_name(midi) if midi is not None else "-"
            print(f"RMS: {rms:7.1f}   note: {note}")

        try:
            for _ in listen_for_notes(on_reading=show):
                pass
        except KeyboardInterrupt:
            print("\nStopping.")
        sys.exit()

    print("Listening... (Ctrl+C to stop)")
    try:
        for midi_note in listen_for_notes():
            print(f"Detected note: {midi_to_name(midi_note)} (MIDI {midi_note})")
    except KeyboardInterrupt:
        print("\nStopping.")
