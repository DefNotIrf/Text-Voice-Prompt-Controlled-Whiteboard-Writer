import cv2
import numpy as np
import easyocr
import torch
import re
from transformers import AutoTokenizer, AutoModelForCausalLM
from erase_com import send_gcode_sequence
from socket_write_com import get_gcode_for_text, send_gcode
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
import queue
import time

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
        
        # Right side - Chat interface
        chat_frame = ttk.LabelFrame(main_frame, text="Assistant Chat", width=400)
        chat_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        chat_frame.pack_propagate(False)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, 
            wrap=tk.WORD, 
            height=25, 
            state=tk.DISABLED,
            font=('Arial', 10)
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input frame
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.input_entry = tk.Entry(input_frame, font=('Arial', 10))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.bind('<Return>', self.send_message)
        
        self.send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initialize assistant
        self.assistant = None
        self.frame_queue = queue.Queue()
        self.calibration_complete = False
        
        # Start video processing thread
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()
        
        # Start GUI update thread
        self.update_thread = threading.Thread(target=self.update_gui, daemon=True)
        self.update_thread.start()
        
        self.add_chat_message("System", "Starting camera for calibration...")
        self.add_chat_message("Assistant", "Please click 4 corners of the whiteboard in the video to calibrate.")
        
    def add_chat_message(self, sender, message):
        """Add a message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        
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
                        self.status_var.set("Calibration complete - Detecting text...")
                        self.add_chat_message("System", "Calibration complete! Detecting text...")
                        
                        # Initialize assistant
                        model_name = "HuggingFaceTB/SmolLM2-360M-Instruct"
                        tokenizer = AutoTokenizer.from_pretrained(model_name)
                        model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
                        self.assistant = WhiteboardAssistant(model, tokenizer)
                        
                        # Detect initial text
                        detect_text_with_easyocr(frame)
                        
                        self.add_chat_message("Assistant", "How can I help you today?")
                        self.status_var.set("Ready")
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
                
        # Bind click event
        self.video_label.bind("<Button-1>", self.on_video_click)
        
    def send_message(self, event=None):
        """Handle sending messages"""
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
    selected_regions.clear()
    erasing_in_progress = False

# ----------------------------- LLM Assistant -----------------------------

# Define the assistant class
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
    print(f"[Whiteboard] Writing: {text}")
    gcode_commands = get_gcode_for_text(text)
    send_gcode(gcode_commands)

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
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()