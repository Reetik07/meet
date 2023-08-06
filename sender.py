import socket
import pyaudio
import tkinter as tk
from tkinter import ttk
from threading import Thread
import numpy as np

CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345
frequency = 1000  # Frequency of the sine wave (in Hz)
amplitude = 0.5  # Amplitude of the sine wave (between 0 and 1)

class AudioSender:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Sender")

        self.label = tk.Label(root, text="Press 'Start' to send audio to the server.")
        self.label.pack(pady=10)

        self.current_value = tk.DoubleVar()
        self.current_value.set(0)

        self.slider = ttk.Scale(root, from_=0, to=5000, orient='horizontal', command=self.slider_changed, variable=self.current_value)
        self.slider.pack(pady=10)

        self.value_label = ttk.Label(root, text=self.get_current_value())
        self.value_label.pack(pady=10)

        self.p = None
        self.stream = None
        self.client_socket = None
        self.start_sending()

    def get_current_value(self):
        return '{: .2f}'.format(self.current_value.get())

    def slider_changed(self, event):
        self.value_label.configure(text=self.get_current_value())

    def start_sending(self):
        self.label.config(text="Sending audio...")

        self.p = pyaudio.PyAudio()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((SERVER_IP, SERVER_PORT))

        self.stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
        self.send_audio_thread = Thread(target=self.send_audio)
        self.send_audio_thread.start()

    def send_audio(self):
        while True:
            data = self.stream.read(CHUNK_SIZE)
            # Convert the audio data to a numpy array
            audio_array = np.frombuffer(data, dtype=np.int16)
            
            # Generate the sine wave for the same length as the audio data
            time = np.arange(len(audio_array)) / RATE
            sine_wave = amplitude * np.sin(2 * np.pi * int(self.current_value.get()) * time)
            sine_wave = np.int16(sine_wave * 32767)
            
            # Mix the audio data with the sine wave
            mixed_audio = audio_array + sine_wave.astype(np.int16)
            
            # Convert the mixed audio back to bytes
            mixed_audio_data = mixed_audio.astype(np.int16).tobytes()
            
            # Transmit the mixed audio data to the device
            #transmit_stream.write(mixed_audio_data)
            self.client_socket.sendall(mixed_audio_data)

    def stop_sending(self):
        self.client_socket.close()
        self.send_audio_thread.join()

        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

def closing():
    app.stop_sending()
    root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x200")
    app = AudioSender(root)
    root.protocol("WM_DELETE_WINDOW", closing)
    root.mainloop()
