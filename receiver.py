import socket
import pyaudio
import tkinter as tk
import numpy as np
from threading import Thread
from scipy import signal
from scipy.io import wavfile

CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
SERVER_PORT = 12345

class AudioReceiver:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Receiver")

        self.label = tk.Label(root, text="Waiting for audio from the client...")
        self.label.pack(pady=10)

        self.frequency_label = tk.Label(root, text="Frequency:")
        self.frequency_label.pack(pady=5)

        self.p = pyaudio.PyAudio()
        self.stream = None
        self.server_socket = None
        self.connection = None

        self.start_listening()

    def start_listening(self):
        self.label.config(text="Listening for audio...")

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', SERVER_PORT))
        self.server_socket.listen(1)
        print("Server listening on port", SERVER_PORT)

        self.connection, address = self.server_socket.accept()
        print(f"Connection established from {address}")

        self.stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK_SIZE)

        self.receive_audio_thread = Thread(target=self.receive_audio)
        self.receive_audio_thread.start()

    def receive_audio(self):
        while True:
            data = self.connection.recv(CHUNK_SIZE)
            if not data:
                break
            
            mixed_audio_array = np.frombuffer(data, dtype=np.int16)
            # Apply spectral analysis to identify the dominant frequency component
            frequencies, spectrum = signal.periodogram(mixed_audio_array, fs=RATE)
            dominant_frequency = frequencies[np.argmax(spectrum)]
            
            # Define the parameters for the notch filter
            notch_frequency = dominant_frequency  # Rounded to the nearest integer
            #self.frequency_label.config(text=f"Frequency: {notch_frequency:.2f} Hz")
            bandwidth = 50  # Width of the frequency range to attenuate (in Hz)

            fft_data = np.abs(np.fft.fft(mixed_audio_array))
            max_frequency_index = np.argmax(fft_data)
            max_frequency = max_frequency_index * RATE / CHUNK_SIZE

            self.frequency_label.config(text=f"Frequency: {notch_frequency:.2f} Hz")
            
            # Create the notch filter
            nyquist_frequency = 0.5 * RATE
            b, a = signal.iirnotch(notch_frequency / nyquist_frequency, Q=10, fs=RATE)
            # b, a = signal.iirnotch(notch_frequency, Q=10, fs=RATE)
            
            # Apply the notch filter to the mixed audio
            filtered_audio = signal.lfilter(b, a, mixed_audio_array).astype(np.int16)
                        
            # Convert the audio data to a numpy array
            self.stream.write(filtered_audio.tobytes())

        self.connection.close()
        self.start_listening()

    def stop_listening(self):
        self.label.config(text="Waiting for audio from the client...")
        self.connection.close()
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x200")
    app = AudioReceiver(root)
    root.mainloop()
