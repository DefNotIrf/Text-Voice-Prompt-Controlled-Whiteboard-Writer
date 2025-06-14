import serial
import time

# Calibrate Z-axis
def convert_command(command):
    """Convert M3/M5/M1 commands to G1 Z commands."""
    if command == 'M3':
        return 'G1 Z5.5'
    elif command == 'M5':
        return 'G1 Z-5.5'
    elif command == 'M1':
        return 'G1 Z-2.5'
    return command

def send_test_gcode_serial(port, baudrate):
    """Send G-code commands to the DLC32 via COM port."""
    try:
        # Open the serial connection
        with serial.Serial(port, baudrate, timeout=1) as ser:
            time.sleep(2)  # Wait for board to reset after opening port

            # List of G-code commands to send
            #commands = ['$x']
            #commands = ['$h']
            #commands = ['G92 X0 Y0 Z0']
            commands = ['G1 F1000', 'G90 Z0']

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

    except serial.SerialException as e:
        print(f"Serial error: {e}")

# Configuration: Replace with your COM port and baudrate
com_port = 'COM4'     # Example: COM3 (Windows) or /dev/ttyUSB0 (Linux)
baud_rate = 115200    # Typical for GRBL-based boards like DLC32

# Call the function to test the COM connection
send_test_gcode_serial(com_port, baud_rate)
