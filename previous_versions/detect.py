import cv2
import numpy as np
#from erase import send_gcode_sequence
from erase_com import send_gcode_sequence

STEP_SIZE = 5  # You can modify this as needed
MERGE_DISTANCE_THRESHOLD = 50  # pixels (you can tune this)
INIT_COMMANDS = ['G1 F1000', 'G90 Z-4']

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
highlighted_region = None
detected_regions = []
selected_regions = []
start_point = None
frozen_frame = None

# Mouse callback for both calibration and box selection
def mouse_callback(event, x, y, flags, param):
    global image_pts, matrix, frame, selected_regions

    if matrix is None:
        # Calibration clicks
        if event == cv2.EVENT_LBUTTONDOWN and len(image_pts) < 4:
            image_pts.append([x, y])
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
            if len(image_pts) == 4:
                calibrate_camera(image_pts, gcode_corners)
    elif freeze_frame:
        # Box selection clicks
        if event == cv2.EVENT_LBUTTONDOWN:
            for region in detected_regions:
                x1, y1, w, h = region
                if x1 <= x <= x1+w and y1 <= y <= y1+h:
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
        cv2.line(frame, tuple(image_pts_np[i]), tuple(image_pts_np[(i+1)%4]), (0, 255, 0), 2)


def iou(boxA, boxB):
    # Compute the intersection over union of two boxes
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = boxA[2] * boxA[3]
    boxBArea = boxB[2] * boxB[3]
    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-5)
    return iou

def merge_boxes(boxes):
    merged = []
    used = [False] * len(boxes)

    for i in range(len(boxes)):
        if used[i]:
            continue
        x, y, w, h = boxes[i]
        current = [x, y, x + w, y + h]

        for j in range(i + 1, len(boxes)):
            if used[j]:
                continue
            x2, y2, w2, h2 = boxes[j]
            candidate = [x2, y2, x2 + w2, y2 + h2]

            # Heuristic: overlap or near-horizontal neighbors
            hor_dist = abs(x2 - (x + w))
            vert_align = abs(y2 - y) < max(h, h2) * 0.5
            if iou((x, y, w, h), (x2, y2, w2, h2)) > 0.1 or (hor_dist < MERGE_DISTANCE_THRESHOLD and vert_align):
                # Merge
                x_min = min(current[0], candidate[0])
                y_min = min(current[1], candidate[1])
                x_max = max(current[2], candidate[2])
                y_max = max(current[3], candidate[3])
                current = [x_min, y_min, x_max, y_max]
                used[j] = True

        used[i] = True
        merged.append((current[0], current[1], current[2] - current[0], current[3] - current[1]))

    return merged

def filter_boxes(boxes, max_width=500, max_height=300):
    return [b for b in boxes if b[2] < max_width and b[3] < max_height]

def enhance_and_detect_content(frame):
    global detected_regions
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (13, 13), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 10]

    # Step 1: Get bounding boxes
    boxes = [cv2.boundingRect(c) for c in contours]
    boxes = sorted(boxes, key=lambda b: b[0])  # Sort left to right

    # Step 2: Merge close boxes
    merged_boxes = merge_boxes(boxes)
    merged_boxes = filter_boxes(merged_boxes)

    # Step 3: Draw and store merged boxes
    detected_regions = []
    for x, y, w, h in merged_boxes:
        detected_regions.append((x, y, w, h))
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return frame

def draw_selected_regions(frame):
    for x, y, w, h in selected_regions:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

def generate_gcode_for_selected_regions():
    print("\nG-code for selected regions:")
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

        commands = (f"G1 X{x0:.2f} Y{y0:.2f}")
        commands = ['M5']  # Lower eraser

        for i in range(steps + 1):
            y_step = y0 + i * dy
            commands.append(f"G1 X{x0:.2f} Y{y_step:.2f}")
            commands.append(f"G1 X{x1:.2f} Y{y_step:.2f}")

        commands.append('M3')  # Raise eraser

        print("\n".join(commands))
        print("-" * 30)

        # Send the G-code commands to the eraser
        send_gcode_sequence(commands, init_commands=INIT_COMMANDS)

    selected_regions.clear()

# Main program
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
        display_frame = enhance_and_detect_content(display_frame)
    else:
        display_frame = frozen_frame.copy()
        draw_selected_regions(display_frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC to quit
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