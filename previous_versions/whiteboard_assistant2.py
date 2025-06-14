import cv2
import numpy as np
import easyocr
import torch
import re
from transformers import AutoTokenizer, AutoModelForCausalLM
from erase_com import send_gcode_sequence
from new_socket_write_com import get_gcode_for_text, send_gcode, send_gcode_command, calculate_writing_position
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
import queue
import time
import os
import sounddevice as sd
import sys
import json
import pyttsx3
from vosk import Model, KaldiRecognizer
from fuzzywuzzy import fuzz
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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
if os.path.exists(model_path):
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)
else:
    print("Warning: Vosk model not found. Voice recognition will be disabled.")
    model = None
    recognizer = None

# Voice recognition queue
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

# ----------------------------- Google Drive Setup (add after existing setup) -----------------------------

# Google Drive scopes and credentials
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_ID = '1LtO4g8B6tWDX3msP9UlH1YNEc5ohiKSJ'  # Your target folder ID

def authenticate_drive():
    """Authenticate with Google Drive API"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', DRIVE_SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('IDPcredentials.json', DRIVE_SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def upload_image_to_drive(service, file_path, folder_id=None):
    """Upload image to Google Drive"""
    file_metadata = {
        'name': os.path.basename(file_path),
    }
    if folder_id:
        file_metadata['parents'] = [folder_id]

    media = MediaFileUpload(file_path, mimetype='image/jpeg')
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name'
    ).execute()
    
    return uploaded

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
        
        # Right side - Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Control Panel", width=400)
        control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        control_frame.pack_propagate(False)
        
        # Mode selection frame
        self.mode_frame = ttk.Frame(control_frame)
        self.mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Text prompt frame
        self.text_frame = ttk.Frame(control_frame)
        
        # Voice prompt frame
        self.voice_frame = ttk.Frame(control_frame)
        
        # Setup mode selection
        self.setup_mode_selection()
        
        # Setup text prompt interface
        self.setup_text_interface()
        
        # Setup voice prompt interface
        self.setup_voice_interface()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initialize variables
        self.assistant = None
        self.frame_queue = queue.Queue()
        self.calibration_complete = False
        self.current_mode = "selection"
        self.voice_mode = "idle"  # 'idle', 'writer', 'eraser', 'whiteboard'
        self.voice_stream = None
        self.voice_thread = None
        self.voice_listening = False

        # Add screenshot-related variables (add after existing variables)
        self.drive_service = None
        self.screenshots_folder = "screenshots"
        
        # Create screenshots folder if it doesn't exist
        if not os.path.exists(self.screenshots_folder):
            os.makedirs(self.screenshots_folder)
            
        # Initialize Google Drive service
        try:
            self.drive_service = authenticate_drive()
            print("Google Drive authentication successful")
        except Exception as e:
            print(f"Google Drive authentication failed: {e}")
            self.drive_service = None
        
        # Start video processing thread
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()
        
        # Start GUI update thread
        self.update_thread = threading.Thread(target=self.update_gui, daemon=True)
        self.update_thread.start()
        
        self.add_chat_message("System", "Starting camera for calibration...")
        self.add_chat_message("Assistant", "Please click 4 corners of the whiteboard in the video to calibrate.")

        
    def setup_mode_selection(self):
        """Setup the mode selection interface"""
        ttk.Label(self.mode_frame, text="Choose Input Mode:", font=('Arial', 12, 'bold')).pack(pady=10)
        
        ttk.Button(self.mode_frame, text="Text Prompt", 
                  command=self.switch_to_text_mode, width=20).pack(pady=5)
                  
        ttk.Button(self.mode_frame, text="Voice Prompt", 
                  command=self.switch_to_voice_mode, width=20).pack(pady=5)
        
    def setup_text_interface(self):
        """Setup the text prompt interface"""
        # Title
        ttk.Label(self.text_frame, text="Text Mode", font=('Arial', 12, 'bold')).pack(pady=10)
        
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

         # Screenshot button to text interface
        ttk.Button(self.text_frame, text="Screenshot", command=self.take_screenshot, width=15).pack(pady=5)
        
        # Return button
        ttk.Button(self.text_frame, text="Return", command=self.return_to_selection).pack(pady=5)
        
    def setup_voice_interface(self):
        """Setup the voice prompt interface"""
        # Title
        ttk.Label(self.voice_frame, text="Voice Mode", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Instructions
        instructions = (
            "Voice Commands:\n"
            "• 'Hey Writer' - Write text on whiteboard\n"
            "• 'Hey Eraser' - Erase text from whiteboard\n"
            "• 'Hey Whiteboard' - Chat with assistant\n"
            "• 'End Program' - Stop voice recognition"
        )
        ttk.Label(self.voice_frame, text=instructions, justify=tk.LEFT, 
                 font=('Arial', 9)).pack(pady=10, padx=10)
        
        # Voice status
        self.voice_status_var = tk.StringVar()
        self.voice_status_var.set("Voice recognition ready")
        ttk.Label(self.voice_frame, textvariable=self.voice_status_var, 
                 font=('Arial', 10, 'bold')).pack(pady=10)
        
        # Voice log
        self.voice_log = scrolledtext.ScrolledText(
            self.voice_frame, 
            wrap=tk.WORD, 
            height=15, 
            state=tk.DISABLED,
            font=('Arial', 9)
        )
        self.voice_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control buttons
        button_frame = ttk.Frame(self.voice_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_voice_button = ttk.Button(button_frame, text="Start Listening", 
                                           command=self.start_voice_recognition)
        self.start_voice_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_voice_button = ttk.Button(button_frame, text="Stop Listening", 
                                          command=self.stop_voice_recognition, state=tk.DISABLED)
        self.stop_voice_button.pack(side=tk.LEFT, padx=(0, 5))

        # Screenshot button to voice interface
        ttk.Button(self.voice_frame, text="Screenshot", command=self.take_screenshot, width=15).pack(pady=5)
        
        # Return button
        ttk.Button(self.voice_frame, text="Return", command=self.return_to_selection).pack(pady=5)

    def take_screenshot(self):
        """Take a screenshot of the current frame"""
        global frame
        
        if frame is None:
            self.add_chat_message("System", "No frame available for screenshot.")
            return
        
        # Generate filename with current date and time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.jpg"
        filepath = os.path.join(self.screenshots_folder, filename)
        
        try:
            # Save the screenshot locally
            cv2.imwrite(filepath, frame)
            self.add_chat_message("System", f"Screenshot saved: {filename}")
            
            # Upload to Google Drive in a separate thread
            if self.drive_service:
                threading.Thread(target=self.upload_screenshot_to_drive, 
                            args=(filepath, filename), daemon=True).start()
            else:
                self.add_chat_message("System", "Screenshot saved locally only (Google Drive not available)")
                
        except Exception as e:
            self.add_chat_message("System", f"Error taking screenshot: {str(e)}")

    def upload_screenshot_to_drive(self, filepath, filename):
        """Upload screenshot to Google Drive"""
        try:
            self.add_chat_message("System", "Uploading to Google Drive...")
            uploaded = upload_image_to_drive(self.drive_service, filepath, FOLDER_ID)
            self.add_chat_message("System", f"Screenshot uploaded to Google Drive: {uploaded['name']}")
        except Exception as e:
            self.add_chat_message("System", f"Error uploading to Google Drive: {str(e)}")

    # Add this method for voice interface support
    def add_voice_message(self, sender, message):
        """Add a message to the voice log"""
        if hasattr(self, 'voice_log'):
            self.voice_log.config(state=tk.NORMAL)
            timestamp = time.strftime("%H:%M:%S")
            self.voice_log.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
            self.voice_log.config(state=tk.DISABLED)
            self.voice_log.see(tk.END)
        
        # Also add to chat display if in text mode
        if hasattr(self, 'chat_display') and self.current_mode == "text":
            self.add_chat_message(sender, message)
        
    def switch_to_text_mode(self):
        """Switch to text prompt mode"""
        if not self.calibration_complete:
            self.add_chat_message("System", "Please complete calibration first.")
            return
            
        self.current_mode = "text"
        self.mode_frame.pack_forget()
        self.text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.input_entry.focus()
        
    def switch_to_voice_mode(self):
        """Switch to voice prompt mode"""
        if not self.calibration_complete:
            self.add_voice_message("System", "Please complete calibration first.")
            return
            
        if not model:
            self.add_voice_message("System", "Voice recognition not available - Vosk model not found.")
            return
            
        self.current_mode = "voice"
        self.mode_frame.pack_forget()
        self.voice_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def return_to_selection(self):
        """Return to mode selection"""
        if self.current_mode == "voice":
            self.stop_voice_recognition()
            self.voice_frame.pack_forget()
        elif self.current_mode == "text":
            self.text_frame.pack_forget()
            
        self.current_mode = "selection"
        self.mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
    def start_voice_recognition(self):
        """Start voice recognition"""
        if not recognizer:
            self.add_voice_message("System", "Voice recognition not available.")
            return
            
        self.voice_listening = True
        self.voice_mode = "idle"
        self.start_voice_button.config(state=tk.DISABLED)
        self.stop_voice_button.config(state=tk.NORMAL)
        self.voice_status_var.set("Listening... Say 'Hey Writer', 'Hey Eraser', or 'Hey Whiteboard'")
        
        # Start voice stream
        self.voice_stream = sd.RawInputStream(
            samplerate=16000, blocksize=8000, dtype='int16',
            channels=1, callback=voice_callback
        )
        self.voice_stream.start()
        
        # Start voice processing thread
        self.voice_thread = threading.Thread(target=self.voice_processing_loop, daemon=True)
        self.voice_thread.start()
        
        self.add_voice_message("System", "Voice recognition started. Say 'Hey Writer', 'Hey Eraser', or 'Hey Whiteboard'.")
        
    def stop_voice_recognition(self):
        """Stop voice recognition"""
        self.voice_listening = False
        self.voice_mode = "idle"
        
        if self.voice_stream:
            self.voice_stream.stop()
            self.voice_stream.close()
            self.voice_stream = None
            
        self.start_voice_button.config(state=tk.NORMAL)
        self.stop_voice_button.config(state=tk.DISABLED)
        self.voice_status_var.set("Voice recognition stopped")
        
        # Clear the queue
        while not voice_queue.empty():
            try:
                voice_queue.get_nowait()
            except queue.Empty:
                break
                
        self.add_voice_message("System", "Voice recognition stopped.")
        
    def voice_processing_loop(self):
        """Main voice processing loop"""
        while self.voice_listening:
            try:
                data = voice_queue.get(timeout=0.1)
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").lower()
                    if not text:
                        continue
                        
                    self.process_voice_input(text)
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Voice processing error: {e}")

    def process_voice_input(self, text):
        """Process voice input based on current mode"""
        if self.voice_mode == "idle":
            # Check for activation commands
            if fuzz.partial_ratio(text, "hey writer") > 80:
                self.voice_mode = "writer"
                self.voice_status_var.set("Writer mode - Say what to write")
                self.add_voice_message("System", "Writer mode activated. Say what you want to write.")
                speak("Ready to write. Say what you want to write.")
                
            elif fuzz.partial_ratio(text, "hey eraser") > 80:
                self.voice_mode = "eraser"
                self.voice_status_var.set("Eraser mode - Say what to erase")
                self.add_voice_message("System", "Eraser mode activated. Say what you want to erase.")
                speak("Ready to erase. Say what you want to erase.")
                
            elif fuzz.partial_ratio(text, "hey whiteboard") > 80:
                self.voice_mode = "whiteboard"
                self.voice_status_var.set("Chat mode - Ask a question")
                self.add_voice_message("System", "Chat mode activated. Ask your question.")
                speak("Chat mode activated. What would you like to know?")
                
            elif fuzz.partial_ratio(text, "end program") > 80:
                self.add_voice_message("System", "Ending voice recognition.")
                speak("Ending voice recognition.")
                self.stop_voice_recognition()
                
        elif self.voice_mode == "writer":
            self.handle_voice_writer(text)
            
        elif self.voice_mode == "eraser":
            self.handle_voice_eraser(text)
            
        elif self.voice_mode == "whiteboard":
            self.handle_voice_whiteboard(text)
            
        # Handle confirmation modes
        elif self.voice_mode in ["confirm_write", "confirm_erase"]:
            self.handle_voice_confirmation(text)
            
    def handle_voice_writer(self, text):
        """Handle voice input for writing"""
        if fuzz.partial_ratio(text, "cancel") > 80:
            self.voice_mode = "idle"
            self.voice_status_var.set("Listening... Say 'Hey Writer', 'Hey Eraser', or 'Hey Whiteboard'")
            speak("Write mode cancelled.")
            return
            
        expression = convert_sentence(text)
        self.add_voice_message("User", f"Write: {expression}")
        speak(f"You want to write: {expression}. Say 'Yes' to confirm or 'No' to cancel.")
        
        # Enter confirmation mode
        self.voice_mode = "confirm_write"
        self.pending_text = expression
        
    def handle_voice_eraser(self, text):
        """Handle voice input for erasing"""
        if fuzz.partial_ratio(text, "cancel") > 80:
            self.voice_mode = "idle"
            self.voice_status_var.set("Listening... Say 'Hey Writer', 'Hey Eraser', or 'Hey Whiteboard'")
            speak("Erase mode cancelled.")
            return
            
        erase_target = text.strip().lower()
        self.add_voice_message("User", f"Erase: {erase_target}")
        
        # Check if target exists on whiteboard
        matches = [bbox for text_ocr, bbox in ocr_results if erase_target in text_ocr]
        if not matches:
            speak(f"Could not find '{erase_target}' on the whiteboard.")
            self.add_voice_message("Assistant", f"Could not find '{erase_target}' on the whiteboard.")
            self.voice_mode = "idle"
            self.voice_status_var.set("Listening... Say 'Hey Writer', 'Hey Eraser', or 'Hey Whiteboard'")
            return
            
        speak(f"Found '{erase_target}' on the whiteboard. Say 'Yes' to erase or 'No' to cancel.")
        self.voice_mode = "confirm_erase"
        self.pending_erase = erase_target
        
    def handle_voice_whiteboard(self, text):
        """Handle voice input for chatting with assistant"""
        if fuzz.partial_ratio(text, "cancel") > 80:
            self.voice_mode = "idle"
            self.voice_status_var.set("Listening... Say 'Hey Writer', 'Hey Eraser', or 'Hey Whiteboard'")
            speak("Chat mode cancelled.")
            return
            
        self.add_voice_message("User", text)
        
        if self.assistant:
            response = self.assistant.generate_response(text)
            self.add_voice_message("Assistant", response)
            speak(response)
        else:
            response = "Assistant not available."
            self.add_voice_message("System", response)
            speak(response)
            
        self.voice_mode = "idle"
        self.voice_status_var.set("Listening... Say 'Hey Writer', 'Hey Eraser', or 'Hey Whiteboard'")
        
    def handle_voice_confirmation(self, text):
        """Handle confirmation responses"""
        if self.voice_mode == "confirm_write":
            if fuzz.partial_ratio(text, "yes") > 80:
                self.add_voice_message("Assistant", f"Writing: {self.pending_text}")
                speak(f"Writing: {self.pending_text}")
                threading.Thread(target=self.execute_write, args=(self.pending_text,), daemon=True).start()
            elif fuzz.partial_ratio(text, "no") > 80:
                speak("Write cancelled.")
                self.add_voice_message("Assistant", "Write cancelled.")
            else:
                speak("Please say 'Yes' to confirm or 'No' to cancel.")
                return
                
        elif self.voice_mode == "confirm_erase":
            if fuzz.partial_ratio(text, "yes") > 80:
                self.add_voice_message("Assistant", f"Erasing: {self.pending_erase}")
                speak(f"Erasing: {self.pending_erase}")
                threading.Thread(target=self.execute_erase, args=(self.pending_erase,), daemon=True).start()
            elif fuzz.partial_ratio(text, "no") > 80:
                speak("Erase cancelled.")
                self.add_voice_message("Assistant", "Erase cancelled.")
            else:
                speak("Please say 'Yes' to confirm or 'No' to cancel.")
                return
                
        self.voice_mode = "idle"
        self.voice_status_var.set("Listening... Say 'Hey Writer', 'Hey Eraser', or 'Hey Whiteboard'")
        
    def execute_write(self, text):
        """Execute writing command"""
        global writing_in_progress
        writing_in_progress = True
        self.status_var.set("Writing...")
        send_to_whiteboard(text)
        # Send home command after writing is complete
        send_gcode_command('$h')
        writing_in_progress = False
        self.status_var.set("Ready")
        
    def execute_erase(self, target):
        """Execute erasing command"""
        matches = [bbox for text_ocr, bbox in ocr_results if target in text_ocr]
        if matches:
            selected_regions.clear()
            selected_regions.extend(matches)
            threading.Thread(target=generate_gcode_for_selected_regions, daemon=True).start()
            
    def add_chat_message(self, sender, message):
        """Add a message to the chat display"""
        if hasattr(self, 'chat_display'):
            self.chat_display.config(state=tk.NORMAL)
            timestamp = time.strftime("%H:%M:%S")
            self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)
        
    def add_voice_message(self, sender, message):
        """Add a message to the voice log"""
        if hasattr(self, 'voice_log'):
            self.voice_log.config(state=tk.NORMAL)
            timestamp = time.strftime("%H:%M:%S")
            self.voice_log.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
            self.voice_log.config(state=tk.DISABLED)
            self.voice_log.see(tk.END)
        
    def video_loop(self):
        """Main video processing loop"""
        global frame, frozen_frame, freeze_frame, matrix, image_pts
        last_ocr_time = 0
        ocr_interval = 2.0
        
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
                        self.status_var.set("Calibration complete - Choose input mode")
                        self.add_chat_message("System", "Calibration complete! Choose your input mode.")
                        
                        # Initialize assistant
                        model_name = "HuggingFaceTB/SmolLM2-360M-Instruct"
                        tokenizer = AutoTokenizer.from_pretrained(model_name)
                        model_llm = AutoModelForCausalLM.from_pretrained(model_name).to(device)
                        self.assistant = WhiteboardAssistant(model_llm, tokenizer)
                        
                        # Detect initial text
                        detect_text_with_easyocr(frame)
            else:
                # Normal operation mode
                if current_time - last_ocr_time > ocr_interval:
                    threading.Thread(target=detect_text_with_easyocr, args=(frame.copy(),), daemon=True).start()
                    last_ocr_time = current_time
                
                draw_ocr_boxes(display_frame)
                    
                if erasing_in_progress:
                    cv2.putText(display_frame, "Erasing...", (50, 60), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                    
                if writing_in_progress:
                    cv2.putText(display_frame, "Writing...", (50, 60), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            
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
                self.add_chat_message("System", f"Corner {len(image_pts)} selected at ({orig_x}, {orig_y})")
                
    def send_message(self, event=None):
        """Handle sending messages in text mode"""
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
                self.add_chat_message("Assistant", f"Found '{erase_target}' on the board. Erasing now...")
                threading.Thread(target=generate_gcode_for_selected_regions).start()
                return
            else:
                # Flexible write command detection
                write_match = re.search(
                    r"(?:write(?:\s*this)?|can you write|please write|i want you to write)[:\s]*['\"]?(.*?)['\"]?$",
                    user_input.strip(),
                    re.IGNORECASE
                )
                if write_match:
                    text_to_write = write_match.group(1).strip()
                    writing_in_progress = True
                    self.status_var.set("Writing...")
                    self.add_chat_message("Assistant", f"Writing '{text_to_write}' on the whiteboard...")
                    send_to_whiteboard(text_to_write)
                    writing_in_progress = False
                    self.status_var.set("Ready")
                    return
                    
        # Generate assistant response
        if self.assistant:
            response = self.assistant.generate_response(user_input)
            self.add_chat_message("Assistant", response)
            
    def run(self):
        """Start the GUI"""
        self.video_label.bind("<Button-1>", self.on_video_click)
        self.root.mainloop()

# ----------------------------- OCR + Erasing -----------------------------

def calibrate_camera(image_pts, gcode_corners):
    global matrix
    image_pts_np = np.array(image_pts, dtype="float32")
    matrix = cv2.getPerspectiveTransform(image_pts_np, gcode_corners)
    np.savetxt('transform_matrix.txt', matrix)
    print("[System] Calibration complete.")

def detect_text_with_easyocr(frame):
    global ocr_results
    ocr_results.clear()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    results = ocr_reader.readtext(gray)
    for (bbox, text, conf) in results:
        if conf > 0.5 and len(text.strip()) > 0:
            x_coords = [pt[0] for pt in bbox]
            y_coords = [pt[1] for pt in bbox]
            x, y = int(min(x_coords)), int(min(y_coords))
            w, h = int(max(x_coords) - x), int(max(y_coords) - y)
            ocr_results.append((text.strip().lower(), (x, y, w, h)))

def draw_ocr_boxes(frame):
    for text, (x, y, w, h) in ocr_results:
        color = (0, 0, 255) if (x, y, w, h) in selected_regions else (0, 255, 0)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

def generate_gcode_for_selected_regions():
    global selected_regions, erasing_in_progress
    erasing_in_progress = True
    print("[System] Erasing...")

    for x, y, w, h in selected_regions:
        pt1 = np.array([[[x, y]]], dtype="float32")
        pt2 = np.array([[[x + w, y + h]]], dtype="float32")
        gpt1 = cv2.perspectiveTransform(pt1, matrix)[0][0]
        gpt2 = cv2.perspectiveTransform(pt2, matrix)[0][0]

        x0, y0 = gpt1[0], gpt2[1]
        x1, y1 = gpt2[0], gpt1[1]
        height = abs(y1 - y0)
        steps = max(1, int(height / STEP_SIZE))
        dy = (y1 - y0) / steps

        commands = [f"G1 X{x0:.2f} Y{y0:.2f}", "touch"]
        for i in range(steps + 1):
            y_step = y0 + i * dy
            commands.append(f"G1 X{x0:.2f} Y{y_step:.2f}")
            commands.append(f"G1 X{x1:.2f} Y{y_step:.2f}")
        commands.append("lift")

        send_gcode_sequence(commands, init_commands=INIT_COMMANDS)
    
    # Send home command after erasing is complete
    send_gcode_command('$h')
    selected_regions.clear()
    erasing_in_progress = False

# ----------------------------- LLM Assistant -----------------------------

class WhiteboardAssistant:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.history = [
            {
                "role": "system",
                "content": (
                    "You are Whiteboard Assistant, a voice interface for a whiteboard robot.\n"
                    "Your only functions are:\n"
                    "1. Writing text on the whiteboard.\n"
                    "2. Erasing the whiteboard.\n"
                    "3. Explaining these two functions.\n\n"
                    "⚠️ You must NEVER answer questions outside of your functions.\n"
                    "If the user asks anything unrelated (e.g., general knowledge, jokes, personal questions), reply:\n"
                    "'Sorry, I can only help with writing or erasing on the whiteboard.'\n\n"
                    "You must keep your answers short and on-topic.\n"
                    "Always redirect unrelated questions back to your whiteboard tasks.\n\n"
                    "Example interactions:\n"
                    "User: What's the weather today?\n"
                    "Assistant: Sorry, I can only help with writing or erasing on the whiteboard.\n\n"
                    "User: Please write 'Meeting at 10AM'\n"
                    "Assistant: Okay, writing 'Meeting at 10AM' on the whiteboard.\n"
                )
            }
        ]

    def generate_response(self, user_input):
        self.history.append({"role": "user", "content": user_input})
        input_text = self.tokenizer.apply_chat_template(
            self.history,
            tokenize=False,
            add_generation_prompt=True
        )
        inputs = self.tokenizer(input_text, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
        self.history.append({"role": "assistant", "content": response})
        return response
    
# List of question words to check
QUESTION_WORDS = ["what", "how", "why", "when", "where", "who", "whom", "which", "whose", "is", "are", "do", "does", "can", "could", "would", "should"]

def is_question(user_input):
    """Check if the input is a question based on common question words."""
    return any(user_input.lower().strip().startswith(word) for word in QUESTION_WORDS)

def send_to_whiteboard(text):
    """Convert text to G-code and send it to the whiteboard robot via socket."""
    global ocr_results, matrix
    
    print(f"[Whiteboard] Writing: {text}")
    
    # Calculate optimal writing position based on existing text
    writing_position = calculate_writing_position(text, ocr_results, matrix)
    print(f"[Positioning] Writing at position: X={writing_position[0]:.2f}, Y={writing_position[1]:.2f}")
    
    # Generate G-code for the text
    gcode_commands = get_gcode_for_text(text)
    
    # Send G-code with calculated position
    send_gcode(gcode_commands, writing_position)

def check_erase_command(user_input):
    match = re.search(r"erase\s+(.*)", user_input.strip(), re.IGNORECASE)
    return match.group(1).strip().lower() if match else None

# ----------------------------- Main Program -----------------------------

def main():
    print("[System] Starting Whiteboard Assistant GUI...")
    gui = WhiteboardGUI()
    
    try:
        gui.run()
    finally:
        # Cleanup
        if hasattr(gui, 'voice_stream') and gui.voice_stream:
            gui.voice_stream.stop()
            gui.voice_stream.close()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()