import serial
import time
from gcode_data import char_gcode  # Import the character G-code mappings
import socket

# Configuration: Replace with your COM port and baudrate
com_port = 'COM4'     # Example: COM3 (Windows) or /dev/ttyUSB0 (Linux)
baud_rate = 115200    # Typical for GRBL-based boards like DLC32


def convert_command(command):
    """Convert M3/M5 commands to G1 Z commands."""
    if command.strip() == 'M3':
        return 'G1 Z-5'
    elif command.strip() == 'M5':
        return 'G1 Z5'
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

def send_gcode(commands):
    """Send G-code commands over serially."""
    try:
        # Open the serial connection
        with serial.Serial(com_port, baud_rate, timeout=1) as ser:
            time.sleep(2)  # Wait for board to reset after opening port

            # Optional: Send initialization/homing commands first
            #init_commands = ['$h', 'G1 F700', 'G90 Z-4', 'G91', 'G1 X50 Y100', ]
            init_commands = ['G1 F700', 'G90 Z-3', 'G91', 'G1 X60 Y150']

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

# === MAIN EXECUTION ===
if __name__ == "__main__":
    user_text = input("Enter the text to convert to G-code: ")
    gcode_commands = get_gcode_for_text(user_text)
    send_gcode(gcode_commands)
