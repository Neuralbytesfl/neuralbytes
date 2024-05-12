import pyaudio
import wave
import msvcrt
import os

class AudioRecorder:
    def __init__(self):
        self.init()

    def init(self):
        while True:
            prompt = input("PROMPT:> ")
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
            output_wav_filename = 'output.wav'
            wav_file = wave.open(output_wav_filename, 'w')
            wav_file.setnchannels(1)
            wav_file.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wav_file.setframerate(44100)

            print("Recording... Press 'P' to stop.")

            while True:
                audio_data = stream.read(1024)
                wav_file.writeframes(audio_data)

                if msvcrt.kbhit():
                    key_press = msvcrt.getch()
                    if key_press == b"P" or key_press == b"p":
                        print("Recording stopped. File saved:", output_wav_filename)
                        break

            stream.stop_stream()
            stream.close()
            p.terminate()
            wav_file.close()

            whisper_output_filename = 'whisper_output.txt'
            os.system(f"whisper {output_wav_filename} --language en > {whisper_output_filename}")
            whisper_output = ""
            if os.path.exists(whisper_output_filename):
                with open(whisper_output_filename, 'r') as whisper_output_file:
                    whisper_output = whisper_output_file.read()

            output_text_filename = 'output.txt'
            file_content = ""
            if os.path.exists(output_text_filename):
                with open(output_text_filename, 'r') as f:
                    file_content = f.read()

            ollama_output_filename = 'ollama_output.txt'

            os.system(f"ollama run llama3 {prompt}:{file_content}")
            ollama_output = ""
            if os.path.exists(ollama_output_filename):
                with open(ollama_output_filename, 'r') as ollama_output_file:
                    ollama_output = ollama_output_file.read()

            print("Ollama output:", ollama_output)

    

# Usage
while True:
    audio = AudioRecorder()
