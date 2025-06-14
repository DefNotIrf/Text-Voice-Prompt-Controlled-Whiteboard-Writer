import socket
import time

# Calibrate Z-axis
def convert_command(command):
    """Convert M3/M5 commands to G1 Z commands."""
    if command == 'M3':
        return 'G1 Z0.5'
    elif command == 'M5':
        return 'G1 Z-5.5'
    elif command == 'M1':
        return 'G1 Z-2.5'
    return command

def send_test_gcode(ip, port):
    """Send G-code commands to test the connection to the ESP32."""
    try:
        # Open a socket connection
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))

            # List of G-code commands to send
            commands = ['G1 F1000', 'G90 Z0', 'G91', 'G1 X100']
            #commands = ['$h']

            for command in commands:
                command_to_send = convert_command(command)

                s.sendall((command_to_send + '\n').encode('utf-8'))  # Add newline for proper termination
                print(f"Sent: {command_to_send}")
                time.sleep(0.7)  # Wait between commands

                # Wait to receive a response
                response = s.recv(1024)
                print("Received:", response.decode('utf-8').strip())

    except socket.error as e:
        print(f"Failed to connect or send data: {e}")

# Configuration: Replace with your ESP32's IP address and port
esp_ip = '192.168.0.1'  # Change to your ESP32's IP address
esp_port = 23           # Common port for Telnet communication

# Call the function to test the connection
send_test_gcode(esp_ip, esp_port)
