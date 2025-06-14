import socket
import time

def convert_command(command):
    if command == 'M3':
        return 'G1 Z-5'
    elif command == 'M5':
        return 'G1 Z1'
    elif command == 'M1':
        return 'G1 Z0'
    return command

def send_gcode_sequence(commands, ip='192.168.0.1', port=23, init_commands=None):
    """
    Send a sequence of G-code commands to the eraser system.

    :param commands: List of G-code commands to execute.
    :param ip: ESP32 IP address.
    :param port: ESP32 port number.
    :param init_commands: Optional list of G-code commands to run before the main sequence.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            print(f"Connected to {ip}:{port}")

            all_commands = (init_commands or []) + commands

            for command in all_commands:
                command_to_send = convert_command(command)
                s.sendall((command_to_send + '\n').encode('utf-8'))
                print(f"Sent: {command_to_send}")
                time.sleep(0.5)
                response = s.recv(1024)
                print("Received:", response.decode('utf-8').strip())

    except socket.error as e:
        print(f"Failed to connect or send data: {e}")

