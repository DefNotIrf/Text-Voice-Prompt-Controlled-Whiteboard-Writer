import socket
import time
from gcode_data import char_gcode  # Import the character G-code mappings

def convert_command(command):
    """Convert M3/M5 commands to G1 Z commands."""
    if command.strip() == 'M3':
        return 'G1 Z-5.5'
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

def send_gcode(ip, port, commands):
    """Send G-code commands over socket to the ESP32."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            print(f"Connected to {ip}:{port}")

            # Optional: Send initialization/homing commands first
            #init_commands = ['$h', 'G1 F700', 'G90 Z-4', 'G91', 'G1 X50 Y100', ]
            init_commands = ['G1 F700', 'G90 Z0', 'G91']
            for command in init_commands:
                s.sendall((command + '\n').encode('utf-8'))
                print(f"Sent init: {command}")
                time.sleep(0.7)
                print("Received:", s.recv(1024).decode('utf-8').strip())

            # Send actual text G-code
            for command in commands:
                s.sendall((command + '\n').encode('utf-8'))
                print(f"Sent: {command}")
                time.sleep(0.7)
                print("Received:", s.recv(1024).decode('utf-8').strip())

    except socket.error as e:
        print(f"Failed to connect or send data: {e}")

# === MAIN EXECUTION ===

if __name__ == "__main__":
    esp_ip = '192.168.0.1'  # Replace with your ESP32's IP
    esp_port = 23

    user_text = input("Enter the text to convert to G-code: ")
    gcode_commands = get_gcode_for_text(user_text)
    send_gcode(esp_ip, esp_port, gcode_commands)
