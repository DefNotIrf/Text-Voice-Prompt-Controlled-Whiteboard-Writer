import cv2
import numpy as np

# Size
width = 1280
height = 720

# Predefined G-code (physical) dimensions in cm (adjust these based on your whiteboard size)
gcode_corners = np.array([
    [0, 0],         # (xmin, ymin) - bottom left corner
    [430, 0],       # (xmax, ymin) - bottom right corner
    [430, 190],     # (xmax, ymax) - top right corner
    [0, 190]        # (xmin, ymax) - top left corner
], dtype="float32")

# Initialize an empty list for the corner points from the user input
image_pts = []
matrix = None  # Store the perspective transform matrix

# This function will be called when the user clicks on the corners in the camera feed
def click_event(event, x, y, flags, params):
    global image_pts, matrix, frame
    
    # If user clicks, append the point to image_pts
    if event == cv2.EVENT_LBUTTONDOWN:
        # If points are not yet calibrated
        if len(image_pts) < 4:
            # Append the coordinates of the clicked point to the list
            image_pts.append([x, y])
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)  # Draw a red dot at the clicked point
            cv2.imshow("Frame", frame)
            
            # If four points have been clicked, proceed with the calibration
            if len(image_pts) == 4:
                print("4 points selected, calibrating now...")
                # Apply perspective transform
                calibrate_camera(image_pts, gcode_corners)
        else:
            # Once calibration is done, let the user select a point to convert to G-code
            if matrix is not None:
                point = np.array([[[x, y]]], dtype="float32")  # The point clicked by the user
                transformed_point = cv2.perspectiveTransform(point, matrix)  # Apply the transformation
                gx, gy = transformed_point[0][0]
                print(f"Selected point ({x}, {y}) transformed to G-code: ({gx:.2f}, {gy:.2f})")
                cv2.putText(frame, f"G-code: ({gx:.2f}, {gy:.2f})", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.imshow("Frame", frame)

def calibrate_camera(image_pts, gcode_corners):
    global matrix, frame
    # Convert the list of points to numpy arrays
    image_pts = np.array(image_pts, dtype="float32")
    
    # Compute the perspective transform matrix
    matrix = cv2.getPerspectiveTransform(image_pts, gcode_corners)
    print(f"Perspective Transform Matrix: \n{matrix}")

    # You can save this matrix for future use to convert image coordinates to G-code
    np.savetxt('transform_matrix.txt', matrix)

    # Draw the bounding box using the selected points
    image_pts = np.int32(image_pts)
    for i in range(4):
        cv2.line(frame, tuple(image_pts[i]), tuple(image_pts[(i + 1) % 4]), (0, 255, 0), 2)
    cv2.imshow("Frame", frame)

# Open the camera feed
cap = cv2.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

while True:
    ret, frame = cap.read()
    
    if not ret:
        break
    
    # Display the camera feed with the instructions for the user
    cv2.putText(frame, "Click on 4 corners of the whiteboard", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, "After calibration, click any point to convert to G-code", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Frame", frame)
    
    # Wait for user input (clicking the corners or points)
    cv2.setMouseCallback("Frame", click_event)

    # Break the loop if 'Esc' key is pressed
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Release the camera and close the OpenCV windows
cap.release()
cv2.destroyAllWindows()