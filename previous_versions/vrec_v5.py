import os
import queue
import sounddevice as sd
import sys
import json
import pyttsx3
from vosk import Model, KaldiRecognizer
from fuzzywuzzy import fuzz
import re

# Setup TTS
engine = pyttsx3.init()
def speak(text):
    print(f"Assistant: {text}")
    engine.say(text)
    engine.runAndWait()

# Setup Vosk
model_path = "models/vosk-model-small-en-us-0.15"

model = Model(model_path)
recognizer = KaldiRecognizer(model, 16000)
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# Math phrase converter
units = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19
}
tens = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90
}
math_words = {
    "plus": "+", "minus": "-", "times": "*", "multiplied by": "*",
    "divided by": "/", "over": "/", "equals": "=", "equal to": "=",
    "equalise to": "=", "is": "="
}

def word_to_number(phrase):
    words = phrase.lower().split()
    total = 0
    current = 0
    for word in words:
        if word in units:
            current += units[word]
        elif word in tens:
            current += tens[word]
        elif word == "hundred":
            current *= 100
        elif word == "thousand":
            current *= 1000
            total += current
            current = 0
    return str(total + current)

def replace_number_words(text):
    number_word_pattern = re.compile(
        r'\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|'
        r'eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|'
        r'twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)'
        r'(?:\s(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|'
        r'eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|'
        r'twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand))*\b',
        re.IGNORECASE
    )

    def replacer(match):
        return word_to_number(match.group(0))
    return number_word_pattern.sub(replacer, text)

def replace_math_words(text):
    for word, symbol in math_words.items():
        pattern = r'\b' + re.escape(word) + r'\b'
        text = re.sub(pattern, symbol, text, flags=re.IGNORECASE)
    return text

def convert_sentence(sentence):
    sentence = replace_math_words(sentence)
    sentence = replace_number_words(sentence)
    return sentence

# Store captured sentences
captured_sentences = []

# Voice assistant loop
results = []
mode = "idle"  # 'idle', 'recording'

speak("Voice writer is ready. Say 'Hey Writer' to begin.")

with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                       channels=1, callback=callback):
    while True:
        data = q.get()
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").lower()
            if not text:
                continue

            # Fuzzy matching
            if fuzz.partial_ratio(text, "hey writer") > 80:
                print("Ready to write.")
                mode = "recording"
                continue
            elif fuzz.partial_ratio(text, "end program") > 80:
                speak("Ending program. Goodbye.")
                break
            elif mode == "recording":
                expression = convert_sentence(text)
                results.append(expression)
                speak(f"You said: {expression}. Say 'Yes' to confirm or 'No' to cancel.")
                
                # Enter confirmation mode
                while True:
                    data = q.get()
                    if recognizer.AcceptWaveform(data):
                        confirmation_result = json.loads(recognizer.Result())
                        confirmation_text = confirmation_result.get("text", "").lower()
                        if not confirmation_text:
                            continue

                        if fuzz.partial_ratio(confirmation_text, "yes") > 90:
                            captured_sentences.append(expression)
                            speak(f"Confirmed. Writing: {expression}")
                            break
                        elif fuzz.partial_ratio(confirmation_text, "no") > 80:
                            speak("Cancelled. Say 'Hey Writer' to try again.")
                            break
                        else:
                            speak("I didn't catch that. Please say 'Yes' to confirm or 'No' to cancel.")

                mode = "idle"

# Final printout
print("\nCaptured Sentences:")
for i, s in enumerate(captured_sentences, 1):
    print(f"{s}")