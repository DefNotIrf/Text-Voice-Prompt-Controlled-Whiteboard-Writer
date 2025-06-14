import serial
import time
import json

# Configuration: Replace with your COM port and baudrate
com_port = 'COM4'     # Example: COM3 (Windows) or /dev/ttyUSB0 (Linux)
baud_rate = 115200    # Typical for GRBL-based boards like DLC32

CONFIG_PATH = "config.json"
try:
    with open(CONFIG_PATH, "r") as f:
        CONFIG = json.load(f)
except:
    CONFIG = {
        "erase_touch_z": 5, "erase_lift_z": 0
    }

def convert_command(command):
    if command == 'touch':
        return f'G1 Z{CONFIG.get("erase_touch_z", 5)}'
    elif command == 'lift':
        return f'G1 Z{CONFIG.get("erase_lift_z", 0)}'
    return command

def send_gcode_sequence(commands, init_commands=None):
    """
    Send a sequence of G-code commands to the eraser system.

    :param commands: List of G-code commands to execute.
    :param ip: ESP32 IP address.
    :param port: ESP32 port number.
    :param init_commands: Optional list of G-code commands to run before the main sequence.
    """
    try:
        # Open the serial connection
        with serial.Serial(com_port, baud_rate, timeout=1) as ser:
            time.sleep(2)  # Wait for board to reset after opening port

            all_commands = (init_commands or []) + commands

            for command in all_commands:
                command_to_send = convert_command(command)
                ser.write((command_to_send + '\n').encode('utf-8'))  # Send command
                print(f"Sent: {command_to_send}")

                time.sleep(0.7)  # Allow time for processing

                # Read response (if any)
                while ser.in_waiting:
                    response = ser.readline().decode('utf-8').strip()
                    if response:
                        print("Received:", response)

    except serial.SerialException as e:
        print(f"Serial error: {e}")
