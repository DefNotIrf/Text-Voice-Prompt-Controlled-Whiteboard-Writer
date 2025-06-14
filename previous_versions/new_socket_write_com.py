import serial
import time
from gcode_data import char_gcode  # Import the character G-code mappings
import socket
import numpy as np
import cv2

# Configuration: Replace with your COM port and baudrate
com_port = 'COM4'     # Example: COM3 (Windows) or /dev/ttyUSB0 (Linux)
baud_rate = 115200    # Typical for GRBL-based boards like DLC32

# Text positioning constants
CHAR_HEIGHT = 20  # Maximum height per character
CHAR_WIDTH = 12   # Average width per character (for estimation)
LINE_SPACING = 10 # Vertical spacing between lines
BASE_X = 60       # Base X position for writing
BASE_Y = 80      # Base Y position for writing


def convert_command(command):
    """Convert M3/M5 commands to G1 Z commands."""
    if command.strip() == 'M3':
        return 'G1 Z-4'
    elif command.strip() == 'M5':
        return 'G1 Z4'
    return command

def get_gcode_for_text(text):
    """Convert text into a list of G-code commands."""
    commands = []
    for char in text:
        if char in char_gcode:
            char_commands = [convert_command(cmd) for cmd in char_gcode[char]]
            commands.extend(char_commands)
        else:
            print(f"Warning: No G-code defined for character '{char}'")
    return commands

def calculate_text_bounds(ocr_results, matrix):
    """Calculate the bounds of existing text in G-code coordinates."""
    if not ocr_results or matrix is None:
        return None
    
    all_bounds = []
    for text, (x, y, w, h) in ocr_results:
        # Convert image coordinates to G-code coordinates
        # Top-left corner
        pt1 = np.array([[[x, y]]], dtype="float32")
        # Bottom-right corner
        pt2 = np.array([[[x + w, y + h]]], dtype="float32")
        
        gpt1 = cv2.perspectiveTransform(pt1, matrix)[0][0]
        gpt2 = cv2.perspectiveTransform(pt2, matrix)[0][0]
        
        # Store bounds as (min_x, min_y, max_x, max_y)
        min_x, max_x = min(gpt1[0], gpt2[0]), max(gpt1[0], gpt2[0])
        min_y, max_y = min(gpt1[1], gpt2[1]), max(gpt1[1], gpt2[1])
        
        all_bounds.append((min_x, min_y, max_x, max_y))
    
    if not all_bounds:
        return None
    
    # Calculate overall bounds
    overall_min_x = min(bound[0] for bound in all_bounds)
    overall_min_y = min(bound[1] for bound in all_bounds)
    overall_max_x = max(bound[2] for bound in all_bounds)
    overall_max_y = max(bound[3] for bound in all_bounds)
    
    return {
        'bounds': all_bounds,
        'overall': (overall_min_x, overall_min_y, overall_max_x, overall_max_y),
        'lines': group_text_by_lines(all_bounds)
    }

def group_text_by_lines(bounds):
    """Group text bounds by horizontal lines (similar Y coordinates)."""
    if not bounds:
        return []
    
    lines = []
    tolerance = CHAR_HEIGHT * 0.5  # Half character height tolerance for same line
    
    for bound in bounds:
        min_x, min_y, max_x, max_y = bound
        center_y = (min_y + max_y) / 2
        
        # Find if this belongs to an existing line
        found_line = False
        for line in lines:
            line_center_y = sum((b[1] + b[3]) / 2 for b in line['bounds']) / len(line['bounds'])
            if abs(center_y - line_center_y) <= tolerance:
                line['bounds'].append(bound)
                line['min_x'] = min(line['min_x'], min_x)
                line['max_x'] = max(line['max_x'], max_x)
                line['min_y'] = min(line['min_y'], min_y)
                line['max_y'] = max(line['max_y'], max_y)
                found_line = True
                break
        
        if not found_line:
            lines.append({
                'bounds': [bound],
                'min_x': min_x,
                'max_x': max_x,
                'min_y': min_y,
                'max_y': max_y,
                'center_y': center_y
            })
    
    # Sort lines by Y coordinate (top to bottom)
    lines.sort(key=lambda line: line['center_y'])
    return lines

def calculate_writing_position(text_to_write, ocr_results, matrix):
    """Calculate the best position to write new text without overlapping."""
    text_bounds = calculate_text_bounds(ocr_results, matrix)
    
    # If no existing text, use base position
    if not text_bounds:
        return BASE_X, BASE_Y
    
    # Estimate dimensions of text to write
    estimated_width = len(text_to_write) * CHAR_WIDTH
    
    # Try to find space on existing lines first
    for line in text_bounds['lines']:
        # Check if we can fit at the end of this line
        available_space_right = 415 - line['max_x']  # 415 is whiteboard width
        if available_space_right >= estimated_width + 10:  # 10 units margin
            return line['max_x'] + 10, line['center_y']
    
    # If no space on existing lines, write on a new line below
    lowest_y = text_bounds['overall'][3]  # max_y of all text
    new_y = lowest_y + LINE_SPACING
    
    # Make sure we don't go below whiteboard bounds
    if new_y + CHAR_HEIGHT > 195:  # 195 is whiteboard height
        # If we're running out of vertical space, start a new column
        rightmost_x = text_bounds['overall'][2]  # max_x of all text
        new_x = rightmost_x + 50  # Start new column with some margin
        new_y = BASE_Y  # Start from top again
        
        # Check if new column fits
        if new_x + estimated_width > 415:
            # If even new column doesn't fit, overwrite at base position
            return BASE_X, BASE_Y
        
        return new_x, new_y
    
    return BASE_X, new_y

def send_gcode(commands, writing_position=None):
    """Send G-code commands over socket to the ESP32."""
    try:
        # Open the serial connection
        with serial.Serial(com_port, baud_rate, timeout=1) as ser:
            time.sleep(2)  # Wait for board to reset after opening port

            # Initialize with calculated position or default
            if writing_position:
                x_pos, y_pos = writing_position
                init_commands = ['G1 F700', 'G90 Z0', 'G91', f'G1 X{x_pos} Y{y_pos}']
            else:
                init_commands = ['G1 F700', 'G90 Z0', 'G91', f'G1 X{BASE_X} Y{BASE_Y}']

            for command in init_commands:
                command_to_send = convert_command(command)
                ser.write((command_to_send + '\n').encode('utf-8'))  # Send command
                print(f"Sent: {command_to_send}")

                time.sleep(0.7)  # Allow time for processing

                # Read response (if any)
                while ser.in_waiting:
                    response = ser.readline().decode('utf-8').strip()
                    if response:
                        print("Received:", response)

            for command in commands:
                command_to_send = convert_command(command)
                ser.write((command_to_send + '\n').encode('utf-8'))  # Send command
                print(f"Sent: {command_to_send}")

                time.sleep(0.7)  # Allow time for processing

                # Read response (if any)
                while ser.in_waiting:
                    response = ser.readline().decode('utf-8').strip()
                    if response:
                        print("Received:", response)

    except socket.error as e:
        print(f"Failed to connect or send data: {e}")

def send_gcode_command(command):
    """Send a single G-code command over serial."""
    try:
        # Open the serial connection
        with serial.Serial(com_port, baud_rate, timeout=1) as ser:
            time.sleep(0.5)  # Brief wait for connection
            
            # Convert and send the command
            command_to_send = convert_command(command)
            ser.write((command_to_send + '\n').encode('utf-8'))
            print(f"Sent: {command_to_send}")
            
            time.sleep(0.7)  # Allow time for processing
            
            # Read response (if any)
            while ser.in_waiting:
                response = ser.readline().decode('utf-8').strip()
                if response:
                    print("Received:", response)
                    
    except serial.SerialException as e:
        print(f"Failed to send command '{command}': {e}")
    except Exception as e:
        print(f"Unexpected error sending command '{command}': {e}")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    user_text = input("Enter the text to convert to G-code: ")
    gcode_commands = get_gcode_for_text(user_text)
    send_gcode(gcode_commands)