import cv2
import numpy as np
import easyocr
import torch
import re
from transformers import AutoTokenizer, AutoModelForCausalLM
from erase_com import send_gcode_sequence
from socket_write_com import get_gcode_for_text, send_gcode
import threading

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

ocr_reader = easyocr.Reader(['en'])

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

    # Load the model and tokenizer
model_name = "HuggingFaceTB/SmolLM2-360M-Instruct"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

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
    global frame, frozen_frame, freeze_frame

    print("[System] Starting camera for calibration...")
    cv2.namedWindow('Calibration')
    while matrix is None:
        ret, frame = cap.read()
        if not ret:
            continue
        display = frame.copy()
        if len(image_pts) < 4:
            cv2.setMouseCallback('Calibration', lambda event, x, y, flags, param: image_pts.append([x, y]) if event == cv2.EVENT_LBUTTONDOWN and len(image_pts) < 4 else None)
            cv2.putText(display, f"Click {4 - len(image_pts)} corners", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        else:
            calibrate_camera(image_pts, gcode_corners)
            cv2.destroyWindow('Calibration')
            break
        cv2.imshow('Calibration', display)
        if cv2.waitKey(1) & 0xFF == 27:
            return

    print("[System] Detecting text...")
    ret, frame = cap.read()
    detect_text_with_easyocr(frame)
    frozen_frame = frame.copy()
    freeze_frame = True

    assistant = WhiteboardAssistant(model, tokenizer)
    print("[Assistant] How can I help you today?")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        display_frame = frozen_frame.copy()
        draw_ocr_boxes(display_frame)
        if erasing_in_progress:
            cv2.putText(display_frame, "Erasing...", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        cv2.imshow('Whiteboard Assistant', display_frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        if erasing_in_progress:
            print("[Assistant] Please wait, erasing in progress...")
            continue

        if writing_in_progress:
            print("[Assistant] Please wait, writing in progress...")
            continue

        # Skip robot commands if this is a question
        if not is_question(user_input):
            # Erase command detection
            erase_target = check_erase_command(user_input)
            if erase_target:
                matches = [bbox for text, bbox in ocr_results if erase_target in text]
                if not matches:
                    print(f"[Assistant] Could not find '{erase_target}' on the board.")
                    continue
                selected_regions.clear()
                selected_regions.extend(matches)
                print(f"[Assistant] Found '{erase_target}' on the board. Do you want to erase it? (yes/no)")
                confirm = input("User: ").strip().lower()
                if confirm in ["yes", "y", "Yes", "Y"]:
                    threading.Thread(target=generate_gcode_for_selected_regions).start()
                else:
                    selected_regions.clear()
                    print("[Assistant] Erase cancelled.")
            else:
                # Flexible write command detection
                write_match = re.search(
                    r"(?:write(?:\s*this)?|can you write|please write|i want you to write)[:\s]*['\"]?(.*?)['\"]?$",
                    user_input.strip(),
                    re.IGNORECASE
                )
                if write_match:
                    text_to_write = write_match.group(1).strip()
                    send_to_whiteboard(text_to_write)
                    continue

        # Otherwise let the model respond
        response = assistant.generate_response(user_input)
        print(f"Assistant: {response}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
