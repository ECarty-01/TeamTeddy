import pyaudio
import numpy as np
import math
from pitch_listener import calibrate_silence_threshold
threshold = calibrate_silence_threshold(seconds=5.0)

def frequency_to_notes(freq):
    # Converts a freq in Hz to closest musical
    if freq < 16.35: # If frequency is below the threshold for C0
        return "Unknown"

    A4 = 440
    C0 = A4 * math.pow(2,-4.75)  # Calculate the frequency of C0
    notes = ["C0", "C#0", "D0", "D#0", "E0", "F0", "F#0", "G0", "G#0", "A0", "A#0", "B0"]
    
    # Calculate the number of half-steps from C0
    half = round(12 * math.log2(freq / C0))

    octaves = half // 12
    note_index = half % 12

    return notes[note_index] + f" {octaves}"


# Config Mic
format = pyaudio.paInt16 # Audio format
channels = 1 # Number of audio channels
rate = 44100 # Sample rate
chunk = 1024 # Size of audio chunks

# Initialize PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)

# Calibrate microphone


try:
    while True:
        # Read audio data from the stream
        data = stream.read(chunk)
        # Process the audio data (example: convert to numpy array)
        audio_data = np.frombuffer(data, dtype=np.int16)
        # Perform frequency analysis (example: using FFT)
        freq = np.fft.fftfreq(len(audio_data), 1/rate)
        # Find the dominant frequency
        dominant_freq = freq[np.argmax(np.abs(np.fft.fft(audio_data)))]
        # Convert frequency to musical note
        note = frequency_to_notes(dominant_freq)
        print(f"Detected note: {note} (Frequency: {dominant_freq:.2f} Hz)")
except KeyboardInterrupt:
    print("Stopping audio processing...")
    stream.stop_stream()
    stream.close()
    p.terminate()