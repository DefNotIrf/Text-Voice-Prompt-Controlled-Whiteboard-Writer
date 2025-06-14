import os
import tempfile
import pyttsx3
import psutil
import warnings
from pydub import AudioSegment
from fuzzywuzzy import fuzz
import speech_recognition as sr
from faster_whisper import WhisperModel

# Suppress warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")

# Init TTS, recognizer, model
engine = pyttsx3.init()
recognizer = sr.Recognizer()
model = WhisperModel("tiny", device="cpu", compute_type="int8")

# Assistant state
listening_active = False

def speak(text):
    print(text)
    engine.say(text)
    engine.runAndWait()

def record_audio():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1.5)
        audio = recognizer.listen(source)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            path = f.name
            with open(path, "wb") as file:
                file.write(audio.get_wav_data())
    return path

def preprocess_audio(path):
    sound = AudioSegment.from_wav(path)
    sound = sound.set_frame_rate(16000).set_channels(1)
    clean_path = path.replace(".wav", "_cleaned.wav")
    sound.export(clean_path, format="wav")
    return clean_path

def recognize_audio(path):
    segments, _ = model.transcribe(path)
    return "".join(segment.text for segment in segments).strip().lower()

def match_command(text):
    for key, action in command_map.items():
        if fuzz.partial_ratio(text, key) > 80:
            return action
    return None

# Command map
command_map = {
    "start": "start_listening",
    "pause": "pause_listening",
    "write": "trigger_write",
    "erase": "trigger_erase",
    "end": "end_program"
}

speak("Voice assistant ready. Say 'Start' to begin.")

while True:
    try:
        audio_path = record_audio()
        cleaned_path = preprocess_audio(audio_path)
        spoken = recognize_audio(cleaned_path)
        print("You said:", spoken)

        action = match_command(spoken)

        if action == "start_listening":
            listening_active = True
            speak("Listening started.")

        elif action == "pause_listening":
            listening_active = False
            speak("Paused.")

        elif action == "end_program":
            speak("Goodbye.")
            break

        elif listening_active:
            if action == "trigger_write":
                speak("Writing command triggered.")
                # PLACEHOLDER: Call your G-code write function here
                # gcode_write(spoken) or similar

            elif action == "trigger_erase":
                speak("Erase command triggered.")
                # PLACEHOLDER: Call your G-code erase/clear function here
                # gcode_erase()

            elif action:
                speak("Command received.")
            else:
                speak("Command not recognised.")

        else:
            print("Paused. Say 'Start' to resume.")

    except Exception as e:
        print("Error:", e)

print("Program ended.")
