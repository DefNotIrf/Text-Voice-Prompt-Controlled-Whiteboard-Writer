import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

def parse_gcode(file_path):
    """Parses GCode including G0, G1 (linear), and G2/G3 (arc) commands."""
    commands = []
    x, y, z = 0, 0, 0
    mode_absolute = True

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('G90'):
                mode_absolute = True
            elif line.startswith('G91'):
                mode_absolute = False

            parts = line.split()
            cmd_type = parts[0]

            if cmd_type in ['G0', 'G1']:
                new_x, new_y, new_z = x, y, z
                for part in parts[1:]:
                    if part.startswith('X'):
                        new_x = float(part[1:]) if mode_absolute else x + float(part[1:])
                    elif part.startswith('Y'):
                        new_y = float(part[1:]) if mode_absolute else y + float(part[1:])
                    elif part.startswith('Z'):
                        new_z = float(part[1:]) if mode_absolute else z + float(part[1:])
                commands.append((new_x, new_y, new_z, cmd_type == 'G0'))
                x, y, z = new_x, new_y, new_z

            elif cmd_type in ['G2', 'G3']:  # Arc CW or CCW
                new_x, new_y = x, y
                i_val, j_val = 0.0, 0.0

                for part in parts[1:]:
                    if part.startswith('X'):
                        new_x = float(part[1:]) if mode_absolute else x + float(part[1:])
                    elif part.startswith('Y'):
                        new_y = float(part[1:]) if mode_absolute else y + float(part[1:])
                    elif part.startswith('I'):
                        i_val = float(part[1:])
                    elif part.startswith('J'):
                        j_val = float(part[1:])

                cx = x + i_val
                cy = y + j_val
                radius = np.sqrt(i_val**2 + j_val**2)

                start_angle = np.arctan2(y - cy, x - cx)
                end_angle = np.arctan2(new_y - cy, new_x - cx)

                # Normalize angle direction
                if cmd_type == 'G2' and end_angle > start_angle:
                    end_angle -= 2 * np.pi
                elif cmd_type == 'G3' and end_angle < start_angle:
                    end_angle += 2 * np.pi

                # Generate arc points
                arc_points = 100
                arc_angles = np.linspace(start_angle, end_angle, arc_points)
                for angle in arc_angles[1:]:
                    arc_x = cx + radius * np.cos(angle)
                    arc_y = cy + radius * np.sin(angle)
                    commands.append((arc_x, arc_y, z, False))
                x, y = new_x, new_y

    return commands

def plot_gcode(commands):
    """Plots the parsed GCode movements in 3D, including arc segments."""
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    x_vals, y_vals, z_vals = [], [], []
    x_vals_g0, y_vals_g0, z_vals_g0 = [], [], []

    for i in range(len(commands) - 1):
        x1, y1, z1, is_g0 = commands[i]
        x2, y2, z2, _ = commands[i + 1]

        if is_g0:
            x_vals_g0.extend([x1, x2])
            y_vals_g0.extend([y1, y2])
            z_vals_g0.extend([z1, z2])
        else:
            x_vals.extend([x1, x2])
            y_vals.extend([y1, y2])
            z_vals.extend([z1, z2])

    ax.plot(x_vals_g0, y_vals_g0, z_vals_g0, 'g--', label='G0 Rapid Move')
    ax.plot(x_vals, y_vals, z_vals, 'b-', label='G1/G2/G3 Move')
    ax.scatter(*zip(*[(x, y, z) for x, y, z, _ in commands]), c='red', marker='o', label='Waypoints')

    ax.scatter(commands[0][0], commands[0][1], commands[0][2], c='green', marker='o', s=100, label='Start')
    ax.scatter(commands[-1][0], commands[-1][1], commands[-1][2], c='black', marker='o', s=100, label='End')

    ax.set_xlabel('X Axis')
    ax.set_ylabel('Y Axis')
    ax.set_zlabel('Z Axis')
    ax.set_title('GCode Simulation with Arcs (G2/G3)')
    ax.legend()
    plt.show()

# Example usage
gcode_file = 'letters.gcode'  # Replace with your GCode file
commands = parse_gcode(gcode_file)
plot_gcode(commands)
