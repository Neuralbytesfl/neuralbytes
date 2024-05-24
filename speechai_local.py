import os
import pyaudio
import wave
import msvcrt
from openai import OpenAI
import subprocess  # Import subprocess module
import json  # Import json module

# Initialize OpenAI client
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

# Load history from JSON file if it exists
history = []
if os.path.exists("history.json"):
    with open("history.json", "r") as json_file:
        history += json.load(json_file)

# Define a function to read text from file and remove timestamps
def read_text(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        # Filter out lines containing timestamps
        text_lines = [line.strip() for line in lines if not line.startswith("[")]
        return " ".join(text_lines)

# Define a function to transcribe audio using Whisper
def transcribe_audio(audio_filename):
    whisper_output_filename = 'output.txt'
    with open(os.devnull, 'w') as devnull:
        subprocess.run(["whisper", audio_filename, "--language", "en"], stdout=devnull)
    return read_text(whisper_output_filename)

# Define a function to record audio
def record_audio(output_filename):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 5

    audio = pyaudio.PyAudio()

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Recording... Press 'P' to stop.")

    frames = []
    while True:
        data = stream.read(CHUNK)
        frames.append(data)
        if msvcrt.kbhit():
            key_press = msvcrt.getch()
            if key_press == b"P" or key_press == b"p":
                print("Recording stopped.")
                break

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(output_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    return output_filename

# Main loop
while True:
    # Record audio
    audio_filename = record_audio('output.wav')

    # Transcribe audio using Whisper
    user_input_text = transcribe_audio(audio_filename)

    # Send direct text to OpenAI model for response
    completion_text = client.chat.completions.create(
        model="Orenguteng/Llama-3-8B-Lexi-Uncensored-GGUF",
        messages=[
            {"role": "system", "content": "Be a good ai thats helpful and follows direction. Summarize data but dont leave details out"},
            {"role": "user", "content": user_input_text}  # Use content from output.txt as user input
        ],
        max_tokens=5000,  # Adjust max_tokens value here
        temperature=0.7,
        stream=True,
    )

    # Print assistant responses for direct text input
    new_message_text = {"role": "assistant", "content": ""}
    for chunk in completion_text:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
            new_message_text["content"] += chunk.choices[0].delta.content
    print()

    # Append to history
    history.append({"input": user_input_text, "response": new_message_text["content"]})

    # Save history to a JSON file
    with open("history.json", "w") as json_file:
        json.dump(history, json_file, indent=4)
