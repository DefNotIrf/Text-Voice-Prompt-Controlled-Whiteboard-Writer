import cv2
import numpy as np
import easyocr
import torch
import re
from transformers import AutoTokenizer, AutoModelForCausalLM
from erase_com import send_gcode_sequence
from new_socket_write_com import get_gcode_for_text, send_gcode, calculate_writing_position
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
import queue
import time

# Voice recognition imports
import os
import sounddevice as sd
import sys
import json
import pyttsx3
from vosk import Model, KaldiRecognizer
from fuzzywuzzy import fuzz

# ----------------------------- System Setup -----------------------------

STEP_SIZE = 5
INIT_COMMANDS = ['G1 F1000', 'G90 Z-4']
width, height = 1280, 720
gcode_corners = np.array([[0, 0], [415, 0], [415, 195], [0, 195]], dtype="float32")

image_pts = []
matrix = None
ocr_results = []
selected_regions = []
frame = None
cap = cv2.VideoCapture(1)
cap.set(3, width)
cap.set(4, height)
freeze_frame = False
frozen_frame = None
erasing_in_progress = False
writing_in_progress = False

# Initialize EasyOCR with GPU support
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())

# ----------------------------- Voice Recognition Setup -----------------------------

# Setup TTS
engine = pyttsx3.init()

def speak(text):
    print(f"Assistant: {text}")
    engine.say(text)
    engine.runAndWait()

# Setup Vosk
model_path = "models/vosk-model-small-en-us-0.15"
try:
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)
    voice_available = True
except:
    print("[Warning] Voice model not found. Voice recognition disabled.")
    voice_available = False

voice_queue = queue.Queue()

def voice_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    voice_queue.put(bytes(indata))

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

# ----------------------------- GUI Class -----------------------------

class WhiteboardGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Whiteboard Assistant")
        self.root.geometry("1600x900")
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Video display
        self.video_frame = ttk.LabelFrame(main_frame, text="Whiteboard View")
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.video_label = tk.Label(self.video_frame)
        self.video_label.pack(pady=10)
        
        # Right side - Control interface
        control_frame = ttk.LabelFrame(main_frame, text="Assistant Controls", width=400)
        control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        control_frame.pack_propagate(False)
        
        # Mode selection frame
        self.mode_frame = ttk.Frame(control_frame)
        self.mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        mode_label = ttk.Label(self.mode_frame, text="Select Input Mode:", font=('Arial', 12, 'bold'))
        mode_label.pack(pady=(0, 10))
        
        self.text_mode_button = ttk.Button(
            self.mode_frame, 
            text="Text Prompt", 
            command=self.activate_text_mode,
            width=20
        )
        self.text_mode_button.pack(pady=5)
        
        self.voice_mode_button = ttk.Button(
            self.mode_frame, 
            text="Voice Prompt", 
            command=self.activate_voice_mode,
            width=20,
            state=tk.NORMAL if voice_available else tk.DISABLED
        )
        self.voice_mode_button.pack(pady=5)
        
        if not voice_available:
            no_voice_label = ttk.Label(self.mode_frame, text="Voice recognition unavailable", 
                                     foreground="red", font=('Arial', 8))
            no_voice_label.pack(pady=2)
        
        # Text input frame (initially hidden)
        self.text_frame = ttk.Frame(control_frame)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            self.text_frame, 
            wrap=tk.WORD, 
            height=20, 
            state=tk.DISABLED,
            font=('Arial', 10)
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input frame
        input_frame = ttk.Frame(self.text_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.input_entry = tk.Entry(input_frame, font=('Arial', 10))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.bind('<Return>', self.send_message)
        
        self.send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=(0, 5))
        
        self.return_text_button = ttk.Button(input_frame, text="Return", 
                                           command=self.return_to_mode_selection)
        self.return_text_button.pack(side=tk.RIGHT)
        
        # Voice input frame (initially hidden)
        self.voice_frame = ttk.Frame(control_frame)
        
        # Voice status display
        self.voice_status = scrolledtext.ScrolledText(
            self.voice_frame, 
            wrap=tk.WORD, 
            height=15, 
            state=tk.DISABLED,
            font=('Arial', 10)
        )
        self.voice_status.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Voice control buttons
        voice_control_frame = ttk.Frame(self.voice_frame)
        voice_control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.start_voice_button = ttk.Button(
            voice_control_frame, 
            text="Start Listening", 
            command=self.start_voice_recognition
        )
        self.start_voice_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_voice_button = ttk.Button(
            voice_control_frame, 
            text="Stop Listening", 
            command=self.stop_voice_recognition,
            state=tk.DISABLED
        )
        self.stop_voice_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.return_voice_button = ttk.Button(
            voice_control_frame, 
            text="Return", 
            command=self.return_to_mode_selection
        )
        self.return_voice_button.pack(side=tk.RIGHT)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initialize assistant and voice recognition
        self.assistant = None
        self.frame_queue = queue.Queue()
        self.calibration_complete = False
        self.current_mode = "selection"
        self.voice_stream = None
        self.voice_listening = False
        self.voice_mode_active = "idle"  # 'idle', 'writer', 'eraser', 'whiteboard'
        
        # Start video processing thread
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()
        
        # Start GUI update thread
        self.update_thread = threading.Thread(target=self.update_gui, daemon=True)
        self.update_thread.start()
        
        self.add_status_message("System", "Starting camera for calibration...")
        self.add_status_message("Assistant", "Please click 4 corners of the whiteboard in the video to calibrate.")
        
    def add_chat_message(self, sender, message):
        """Add a message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
    def add_voice_message(self, sender, message):
        """Add a message to the voice status display"""
        self.voice_status.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.voice_status.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        self.voice_status.config(state=tk.DISABLED)
        self.voice_status.see(tk.END)
        
    def add_status_message(self, sender, message):
        """Add a message to the appropriate display based on current mode"""
        if self.current_mode == "text":
            self.add_chat_message(sender, message)
        elif self.current_mode == "voice":
            self.add_voice_message(sender, message)
        else:
            print(f"[{sender}] {message}")
            
    def activate_text_mode(self):
        """Switch to text input mode"""
        if not self.calibration_complete:
            tk.messagebox.showwarning("Warning", "Please complete calibration first.")
            return
            
        self.current_mode = "text"
        self.mode_frame.pack_forget()
        self.voice_frame.pack_forget()
        self.text_frame.pack(fill=tk.BOTH, expand=True)
        self.input_entry.focus()
        
    def activate_voice_mode(self):
        """Switch to voice input mode"""
        if not self.calibration_complete:
            tk.messagebox.showwarning("Warning", "Please complete calibration first.")
            return
            
        if not voice_available:
            tk.messagebox.showerror("Error", "Voice recognition is not available.")
            return
            
        self.current_mode = "voice"
        self.mode_frame.pack_forget()
        self.text_frame.pack_forget()
        self.voice_frame.pack(fill=tk.BOTH, expand=True)
        self.add_voice_message("System", "Voice mode activated. Click 'Start Listening' to begin.")
        
    def return_to_mode_selection(self):
        """Return to mode selection screen"""
        if self.voice_listening:
            self.stop_voice_recognition()
            
        self.current_mode = "selection"
        self.text_frame.pack_forget()
        self.voice_frame.pack_forget()
        self.mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
    def start_voice_recognition(self):
        """Start voice recognition"""
        if not voice_available:
            return
            
        try:
            self.voice_stream = sd.RawInputStream(
                samplerate=16000, blocksize=8000, dtype='int16',
                channels=1, callback=voice_callback
            )
            self.voice_stream.start()
            self.voice_listening = True
            self.start_voice_button.config(state=tk.DISABLED)
            self.stop_voice_button.config(state=tk.NORMAL)
            
            self.add_voice_message("System", "Listening... Say 'Hey Writer', 'Hey Eraser', or 'Hey Whiteboard' to begin.")
            
            # Start voice processing thread
            self.voice_thread = threading.Thread(target=self.process_voice, daemon=True)
            self.voice_thread.start()
            
        except Exception as e:
            self.add_voice_message("Error", f"Failed to start voice recognition: {e}")
            
    def stop_voice_recognition(self):
        """Stop voice recognition"""
        if self.voice_stream:
            self.voice_stream.stop()
            self.voice_stream.close()
            self.voice_stream = None
            
        self.voice_listening = False
        self.voice_mode_active = "idle"
        self.start_voice_button.config(state=tk.NORMAL)
        self.stop_voice_button.config(state=tk.DISABLED)
        self.add_voice_message("System", "Stopped listening.")
        
    def process_voice(self):
        """Process voice input"""
        while self.voice_listening:
            try:
                data = voice_queue.get(timeout=0.1)
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").lower().strip()
                    if not text:
                        continue
                        
                    self.add_voice_message("User", text)
                    
                    # Check for activation phrases
                    if fuzz.partial_ratio(text, "hey writer") > 80:
                        self.voice_mode_active = "writer"
                        self.add_voice_message("System", "Writer mode activated. Say your text to write.")
                        speak("Writer mode activated. What would you like me to write?")
                        continue
                        
                    elif fuzz.partial_ratio(text, "hey eraser") > 80:
                        self.voice_mode_active = "eraser"
                        self.add_voice_message("System", "Eraser mode activated. Say the text to erase.")
                        speak("Eraser mode activated. What would you like me to erase?")
                        continue
                        
                    elif fuzz.partial_ratio(text, "hey whiteboard") > 80:
                        self.voice_mode_active = "whiteboard"
                        self.add_voice_message("System", "Whiteboard chat mode activated. Ask me anything about the whiteboard.")
                        speak("Whiteboard chat mode activated. How can I help you?")
                        continue
                        
                    elif fuzz.partial_ratio(text, "end program") > 80:
                        speak("Ending voice recognition.")
                        self.stop_voice_recognition()
                        break
                        
                    # Process commands based on active mode
                    if self.voice_mode_active == "writer":
                        self.handle_voice_write(text)
                    elif self.voice_mode_active == "eraser":
                        self.handle_voice_erase(text)
                    elif self.voice_mode_active == "whiteboard":
                        self.handle_voice_chat(text)
                    else:
                        self.add_voice_message("System", "Say 'Hey Writer', 'Hey Eraser', or 'Hey Whiteboard' to activate a mode.")
                        
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Voice processing error: {e}")
                
    def handle_voice_write(self, text):
        """Handle voice writing commands"""
        if erasing_in_progress or writing_in_progress:
            speak("Please wait, operation in progress.")
            return
            
        expression = convert_sentence(text)
        self.add_voice_message("Assistant", f"You want to write: '{expression}'. Say 'Yes' to confirm or 'No' to cancel.")
        speak(f"You want to write: {expression}. Say Yes to confirm or No to cancel.")
        
        # Wait for confirmation
        self.wait_for_voice_confirmation("write", expression)
        
    def handle_voice_erase(self, text):
        """Handle voice erasing commands"""
        if erasing_in_progress or writing_in_progress:
            speak("Please wait, operation in progress.")
            return
            
        erase_target = text.lower().strip()
        matches = [bbox for text_ocr, bbox in ocr_results if erase_target in text_ocr]
        
        if not matches:
            self.add_voice_message("Assistant", f"Could not find '{erase_target}' on the whiteboard.")
            speak(f"Could not find {erase_target} on the whiteboard.")
            self.voice_mode_active = "idle"
            return
            
        self.add_voice_message("Assistant", f"Found '{erase_target}' on the whiteboard. Say 'Yes' to erase or 'No' to cancel.")
        speak(f"Found {erase_target} on the whiteboard. Say Yes to erase or No to cancel.")
        
        # Wait for confirmation
        self.wait_for_voice_confirmation("erase", erase_target)
        
    def handle_voice_chat(self, text):
        """Handle voice chat with LLM"""
        if self.assistant:
            response = self.assistant.generate_response(text)
            self.add_voice_message("Assistant", response)
            speak(response)
        else:
            speak("Assistant not available.")
            
        self.voice_mode_active = "idle"
        
    def wait_for_voice_confirmation(self, action, target):
        """Wait for voice confirmation"""
        def confirmation_thread():
            confirmation_timeout = time.time() + 10  # 10 second timeout
            
            while self.voice_listening and time.time() < confirmation_timeout:
                try:
                    data = voice_queue.get(timeout=0.1)
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        confirmation_text = result.get("text", "").lower().strip()
                        if not confirmation_text:
                            continue
                            
                        self.add_voice_message("User", confirmation_text)
                        
                        if fuzz.partial_ratio(confirmation_text, "yes") > 80:
                            if action == "write":
                                self.add_voice_message("Assistant", f"Writing: {target}")
                                speak(f"Writing {target}")
                                threading.Thread(target=self.voice_write_text, args=(target,), daemon=True).start()
                            elif action == "erase":
                                self.add_voice_message("Assistant", f"Erasing: {target}")
                                speak(f"Erasing {target}")
                                threading.Thread(target=self.voice_erase_text, args=(target,), daemon=True).start()
                            break
                            
                        elif fuzz.partial_ratio(confirmation_text, "no") > 80:
                            self.add_voice_message("Assistant", "Cancelled.")
                            speak("Cancelled.")
                            break
                        else:
                            self.add_voice_message("System", "Please say 'Yes' to confirm or 'No' to cancel.")
                            speak("Please say Yes to confirm or No to cancel.")
                            
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Confirmation error: {e}")
                    break
                    
            self.voice_mode_active = "idle"
            
        threading.Thread(target=confirmation_thread, daemon=True).start()
        
    def voice_write_text(self, text):
        """Write text from voice command"""
        global writing_in_progress
        writing_in_progress = True
        self.status_var.set("Writing...")
        send_to_whiteboard(text)
        writing_in_progress = False
        self.status_var.set("Ready")
        
    def voice_erase_text(self, text):
        """Erase text from voice command"""
        global selected_regions
        matches = [bbox for text_ocr, bbox in ocr_results if text in text_ocr]
        if matches:
            selected_regions.clear()
            selected_regions.extend(matches)
            threading.Thread(target=generate_gcode_for_selected_regions, daemon=True).start()
        
    def video_loop(self):
        """Main video processing loop"""
        global frame, frozen_frame, freeze_frame, matrix, image_pts
        last_ocr_time = 0
        ocr_interval = 2.0  # Run OCR every 2 seconds for real-time updates
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
                
            display_frame = frame.copy()
            current_time = time.time()
            
            if not self.calibration_complete:
                # Calibration mode
                if len(image_pts) < 4:
                    cv2.putText(display_frame, f"Click {4 - len(image_pts)} corners", 
                              (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    # Show clicked points
                    for i, pt in enumerate(image_pts):
                        cv2.circle(display_frame, tuple(pt), 5, (0, 255, 0), -1)
                        cv2.putText(display_frame, str(i+1), (pt[0]+10, pt[1]), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    if matrix is None:
                        calibrate_camera(image_pts, gcode_corners)
                        self.calibration_complete = True
                        self.status_var.set("Calibration complete - Select input mode")
                        self.add_status_message("System", "Calibration complete! Select your input mode.")
                        
                        # Initialize assistant
                        model_name = "HuggingFaceTB/SmolLM2-360M-Instruct"
                        tokenizer = AutoTokenizer.from_pretrained(model_name)
                        model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
                        self.assistant = WhiteboardAssistant(model, tokenizer)
                        
                        # Detect initial text
                        detect_text_with_easyocr(frame)
            else:
                # Normal operation mode - real-time updates
                # Run OCR periodically for real-time text detection
                if current_time - last_ocr_time > ocr_interval:
                    threading.Thread(target=detect_text_with_easyocr, args=(frame.copy(),), daemon=True).start()
                    last_ocr_time = current_time
                
                # Always draw current OCR results on live frame
                draw_ocr_boxes(display_frame)
                    
                if erasing_in_progress:
                    cv2.putText(display_frame, "Erasing...", (50, 60), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                    
                if writing_in_progress:
                    cv2.putText(display_frame, "Writing...", (50, 60), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                              
                # Show voice mode status
                if self.current_mode == "voice" and self.voice_listening:
                    mode_text = f"Voice: {self.voice_mode_active.title()}"
                    cv2.putText(display_frame, mode_text, (50, 100), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            
            # Put frame in queue for GUI update
            if not self.frame_queue.full():
                try:
                    self.frame_queue.put_nowait(display_frame)
                except queue.Full:
                    pass
                    
    def update_gui(self):
        """Update GUI with latest frame"""
        while True:
            try:
                frame = self.frame_queue.get(timeout=0.1)
                # Convert frame to PhotoImage
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Resize frame to fit in GUI
                h, w = rgb_frame.shape[:2]
                max_width, max_height = 1200, 800
                scale = min(max_width/w, max_height/h)
                new_w, new_h = int(w*scale), int(h*scale)
                rgb_frame = cv2.resize(rgb_frame, (new_w, new_h))
                
                img = Image.fromarray(rgb_frame)
                photo = ImageTk.PhotoImage(image=img)
                
                # Update video label
                self.video_label.configure(image=photo)
                self.video_label.image = photo  # Keep a reference
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"GUI update error: {e}")
                
    def on_video_click(self, event):
        """Handle mouse clicks on video display"""
        global image_pts
        
        if not self.calibration_complete and len(image_pts) < 4:
            # Scale click coordinates back to original frame size
            label_width = self.video_label.winfo_width()
            label_height = self.video_label.winfo_height()
            
            if label_width > 0 and label_height > 0:
                scale_x = width / label_width
                scale_y = height / label_height
                
                orig_x = int(event.x * scale_x)
                orig_y = int(event.y * scale_y)
                
                image_pts.append([orig_x, orig_y])
                self.add_status_message("System", f"Corner {len(image_pts)} selected at ({orig_x}, {orig_y})")
        
    def send_message(self, event=None):
        """Handle sending text messages"""
        user_input = self.input_entry.get().strip()
        if not user_input:
            return
            
        self.input_entry.delete(0, tk.END)
        self.add_chat_message("User", user_input)
        
        if user_input.lower() in ["exit", "quit"]:
            self.root.quit()
            return
            
        if not self.calibration_complete:
            self.add_chat_message("System", "Please complete calibration first.")
            return
            
        if erasing_in_progress:
            self.add_chat_message("Assistant", "Please wait, erasing in progress...")
            return
            
        if writing_in_progress:
            self.add_chat_message("Assistant", "Please wait, writing in progress...")
            return
            
        # Process user input in separate thread
        threading.Thread(target=self.process_user_input, args=(user_input,), daemon=True).start()
        
    def process_user_input(self, user_input):
        """Process user input and generate response"""
        global writing_in_progress
        
        # Skip robot commands if this is a question
        if not is_question(user_input):
            # Erase command detection
            erase_target = check_erase_command(user_input)
            if erase_target:
                matches = [bbox for text, bbox in ocr_results if erase_target in text]
                if not matches:
                    self.add_chat_message("Assistant", f"Could not find '{erase_target}' on the board.")
                    return
                    
                selected_regions.clear()
                selected_regions.extend(matches)
                self.add_chat_message("