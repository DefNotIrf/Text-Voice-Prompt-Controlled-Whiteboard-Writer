import cv2
import numpy as np
import easyocr
#from erase import send_gcode_sequence
from erase_com import send_gcode_sequence

STEP_SIZE = 5
INIT_COMMANDS = ['G1 F1000', 'G90 Z-5']

# Calibration parameters
width, height = 1280, 720
gcode_corners = np.array([
    [0, 0],
    [415, 0],
    [415, 195],
    [0, 195]
], dtype="float32")

# Global variables
image_pts = []
matrix = None
freeze_frame = False
frozen_frame = None
ocr_results = []  # (text, (x, y, w, h))
selected_regions = []

# EasyOCR
ocr_reader = easyocr.Reader(['en'])

# --- Callback and calibration ---
def mouse_callback(event, x, y, flags, param):
    global image_pts, matrix, frame

    if matrix is None:
        if event == cv2.EVENT_LBUTTONDOWN and len(image_pts) < 4:
            image_pts.append([x, y])
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
            if len(image_pts) == 4:
                calibrate_camera(image_pts, gcode_corners)

    elif freeze_frame:
        if event == cv2.EVENT_LBUTTONDOWN:
            for _, (x1, y1, w, h) in ocr_results:
                if x1 <= x <= x1 + w and y1 <= y <= y1 + h:
                    region = (x1, y1, w, h)
                    if region in selected_regions:
                        selected_regions.remove(region)
                    else:
                        selected_regions.append(region)
                    break

def calibrate_camera(image_pts, gcode_corners):
    global matrix, frame
    image_pts_np = np.array(image_pts, dtype="float32")
    matrix = cv2.getPerspectiveTransform(image_pts_np, gcode_corners)
    print("Calibration complete.")
    np.savetxt('transform_matrix.txt', matrix)
    for i in range(4):
        cv2.line(frame, tuple(image_pts_np[i]), tuple(image_pts_np[(i + 1) % 4]), (0, 255, 0), 2)

# --- OCR ---
def detect_text_with_easyocr(frame):
    global ocr_results
    ocr_results.clear()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    results = ocr_reader.readtext(gray)

    for (bbox, text, conf) in results:
        if conf > 0.5 and len(text.strip()) > 0:
            # Convert polygon to bounding box
            (tl, tr, br, bl) = bbox
            x_coords = [pt[0] for pt in bbox]
            y_coords = [pt[1] for pt in bbox]
            x, y = int(min(x_coords)), int(min(y_coords))
            w, h = int(max(x_coords) - x), int(max(y_coords) - y)
            ocr_results.append((text, (x, y, w, h)))
            print(f"OCR: '{text}' at {(x, y, w, h)}")

def draw_ocr_boxes(frame):
    for text, (x, y, w, h) in ocr_results:
        color = (0, 0, 255) if (x, y, w, h) in selected_regions else (0, 255, 0)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

def draw_selected_regions(frame):
    for x, y, w, h in selected_regions:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

# --- G-code generation ---
def generate_gcode_for_selected_regions():
    print("\nG-code for selected OCR text regions:")
    for x, y, w, h in selected_regions:
        pt1 = np.array([[[x, y]]], dtype="float32")
        pt2 = np.array([[[x + w, y + h]]], dtype="float32")
        gpt1 = cv2.perspectiveTransform(pt1, matrix)[0][0]
        gpt2 = cv2.perspectiveTransform(pt2, matrix)[0][0]

        # Movement bounds
        x0, y0 = gpt1[0], gpt2[1]
        x1, y1 = gpt2[0], gpt1[1]
        height = abs(y1 - y0)
        steps = max(1, int(height / STEP_SIZE))
        dy = (y1 - y0) / steps

        # Start with movement to initial position
        commands = [f"G1 X{x0:.2f} Y{y0:.2f}"]
        commands.append("touch")  # Send 'touch' after arriving

        # Erasing sweep
        for i in range(steps + 1):
            y_step = y0 + i * dy
            commands.append(f"G1 X{x0:.2f} Y{y_step:.2f}")
            commands.append(f"G1 X{x1:.2f} Y{y_step:.2f}")

        # End with lift
        commands.append("lift")

        # Output for debugging
        print("\n".join(commands))
        print("-" * 30)

        # Send to eraser
        send_gcode_sequence(commands, init_commands=INIT_COMMANDS)

    selected_regions.clear()

# --- Main loop ---
cap = cv2.VideoCapture(1)
cap.set(3, width)
cap.set(4, height)
cv2.namedWindow('Detection')
cv2.setMouseCallback('Detection', mouse_callback)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    display_frame = frame.copy()

    if matrix is None:
        cv2.putText(display_frame, "Click 4 corners for calibration", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    elif not freeze_frame:
        detect_text_with_easyocr(display_frame)
        draw_ocr_boxes(display_frame)
    else:
        display_frame = frozen_frame.copy()
        draw_selected_regions(display_frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break
    elif key == ord('d') and matrix is not None:
        freeze_frame = not freeze_frame
        if freeze_frame:
            frozen_frame = display_frame.copy()
        else:
            generate_gcode_for_selected_regions()
            selected_regions.clear()

    cv2.imshow('Detection', display_frame)

cap.release()
cv2.destroyAllWindows()
