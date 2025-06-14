def generate_gcode_for_opencv(regions):    
    gcode_commands = []
    x_scale = 400 / 1280  # Conversion factor for x-axis from pixels to mm
    y_scale = 150 / 720  # Conversion factor for y-axis from pixels to mm

    erasing_z = load_calibration('erasing_z')
    idle_z = load_calibration('idle_z')

    gcode_commands.append("G90")  # Absolute positioning

    for region in regions:
        # Check if region is a contour or a direct rectangle
        if isinstance(region, np.ndarray):
            # It's a contour, compute bounding rectangle
            x, y, w, h = cv2.boundingRect(region)
        else:
            # It's a directly provided rectangle (x, y, w, h)
            x, y, w, h = region

        x1, y1 = x * x_scale, (150 - (y * y_scale))
        x2, y2 = (x + w) * x_scale, (150 - ((y + h) * y_scale))

        # Generate G-code for the movements
        gcode_commands.append(f"G00X{x1:.2f}Y{y1:.2f}")  # Move to start position
        gcode_commands.append(f"G00Z{erasing_z:.2f}")  # Lower the eraser to touch the board
        gcode_commands.append(f"G00X{x2:.2f}Y{y1:.2f}")
        gcode_commands.append(f"G00X{x1:.2f}Y{y2:.2f}")
        gcode_commands.append(f"G00X{x2:.2f}Y{y2:.2f}")  # Perform erasing action to the end position
        gcode_commands.append(f"G00Z{idle_z:.2f}")  # Raise the eraser back to origin

    gcode_commands.append("G90X420Y0")
    return gcode_commands #this the code we used to do the erasing motion for ur reference